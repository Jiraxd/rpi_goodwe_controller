import asyncio
import json
import goodwe
from decorators import error_handler
import utils
from datetime import datetime, timedelta
from display_manager import LCDManager 
from crons import CronManager
from loggerCustom import LoggerCustom
from tapo_client import TapoClient
from api_client import ApiClient
from config import config
from dotenv import load_dotenv
import signal
from web_server import WebServer
import os

# sensors
# ppv - current production in W
# battery_soc - current battery in %
# house_consumption - current house consumption in W
# active_power - current export in W, if - value, importing from grid, if + value, exporting to grid


# settings
# grid_export_limit - limit of export to grid in W
# grid_export - 1 - enables limiter, 0 - disables limiter

async def cleanup(server):
    # Close httpx client
    if controller.apiClient:
        await controller.apiClient.close()
    
    # Write close message
    if controller.lcdmanager:
        controller.lcdmanager.write_lines(["Shutting down..."])
        
    # Stop cron jobs
    if controller.cronManager:
        controller.cronManager.stop()
        
    server.stop()

class MainController:
    def __init__(self):
        self.status: "Off" | "On" = "On" 
        self.inverter = None
        self.lcdmanager = None 
        self.cronManager = None
        self.logManager = None
        self.tapoClient = None
        self.apiClient = None
        self.lastActivateLimit = datetime.now() - timedelta(minutes=30)
        self.lastActivateLimitTapo = datetime.now() - timedelta(minutes=config.min_minutes_activation_time_tapo)
        self.lastSwitchGridExport = datetime.now() - timedelta(minutes=config.min_minutes_between_gridexport_switch)
        self.priceLowerThanZero = False
        self.sellingDisabledLowerThanOne = False
        self.offlineMode = False # Set to True for testing purposes without connection to goodwe inverter
        # TODO offline mode
        
    
    # Initializes managers, clients, also tries to connect to the inverter and runs default limit settings
    async def initialize(self):
        self.logManager = LoggerCustom()
        self.logManager.log("Initializing managers")

        self.lcdmanager = LCDManager(20, 4)
        self.tapoClient = TapoClient(self.logManager) 
        self.apiClient = ApiClient(self.logManager)
        self.cronManager = CronManager(self.logManager, self)


        await self.tapoClient.init_device(config)
        
        self.logManager.log("Managers initialized")
        
        await self.lcdmanager.write_init_message(config.ip_address)
        
        if self.offlineMode:
            self.lcdmanager.write_lines(["Offline Mode", "Production: 0 kw", "Export: 0 kw"])
        else:
            failed = await self.try_connection()
            if failed:
                self.lcdmanager.write_lines(["Failed to connect!","Script disabled!"])
                return

            await self.check_limit_disabled_on_init()
            self.cronManager.start()


    async def try_connection(self):
        for i in range(3):
            if(i == 3):
                return True
            try:
                self.inverter = await goodwe.connect(config.ip_address)
                return False
            except Exception:
                self.lcdmanager.write_lines(["Failed to connect!", "Retrying in 5s"])
                await asyncio.sleep(5)
        return False

    # Called after connecting to inverter, it sets limit and limit enabled to default values
    @error_handler
    async def check_limit_disabled_on_init(self):
        await utils.enable_grid_limit(self.inverter, self.logManager)
        


    # Gets data from inverter, if printData is set to true it also prints it, it does not log it!
    @error_handler
    async def get_runtime_data(self, printData = False):
        runtime_data = await self.inverter.read_runtime_data()
        if(printData):
            for sensor in self.inverter.sensors():
                if sensor.id_ in runtime_data:
                    print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")
        return runtime_data

    # Called by cron from cros.py
    # Gets latest data from inverter and prints it to LCD display
    # This also returns the fetched data back to the cron, which then calls check_grid_limit
    async def get_data_and_write_to_lcd(self):
        data = await self.get_runtime_data(False)
        self.lcdmanager.write_lines([
            "Connected!", 
            f"Production: {str(data.get('ppv', 0))}W",
            f"Export: {str(data.get('active_power', 0))}W", 
            f"House: {str(data.get('house_consumption', 0))}W"
        ])
        return data

    # Calls method to get data without printing the data it got
    async def get_data(self):
        return await self.get_runtime_data(False)

    # Called by cron from crons.py
    # Checks if we're exporting more than allowed, if yes, enables limit and sets it to maximum export allowed
    # If not, disables grid export limit (Inverter doesn't take that much energz from grid if limit is disabled)
    async def check_grid_limit(self, data):
        export = data.get("active_power", 0)

        enabled = await self.inverter.read_setting("grid_export")


        # Controlled by check_price_and_disable_enable_sell, if the current price for electricity is in minus, we keep grid export disabled
        if(self.priceLowerThanZero):
            self.logManager.log("Price is lower than 0, not continueing with check grid limit")
            return


        self.logManager.log(f"Export: {export}")
        self.logManager.log(f"Grid export enabled: {enabled}")
        self.logManager.log(f"Max export: {config.max_export}")
        # If we're exporting more than the max limit (i suggest 200 less than actual limit) we enable the limit
        if(export > config.max_export):
            await utils.enable_grid_limit(self.inverter, self.logManager)
        else:
            # No need to deactivate the limit everytime the solar panel output changes
            if(datetime.now() - self.lastActivateLimit > timedelta(minutes=config.min_minutes_before_deactivate_limit)):
                if(enabled == 0):
                    self.logManager.log("Grid export is already disabled")
                    return
                self.lastActivateLimit = datetime.now()
                if(self.sellingDisabledLowerThanOne):
                    self.logManager.log("Could not disable grid limit, price is too low!")
                    return
                await utils.disable_grid_limit(self.inverter, self.logManager)
            else:
                if(enabled == 0):
                    self.logManager.log("Grid export is already disabled")
                    return
                self.logManager.log("Could not disable grid limit, it hasn't been minimum amount of minutes yet")

    # Called by cron from crons.py
    # Checks if we can start heating water using electricity (heated water is stored and is used to heat up the house)
    # Heating start only if battery is charged above certain level and if the solar panels are outputting more than certain amount

    async def check_water_heating(self, data):
        await self.tapoClient.print_device_info()

        # If device is enabled for more than X minutes, it automatically disables, it takes approximately 2-2.5h to fully heat up water
        active = await self.tapoClient.check_is_active()
        if(active):
            if(datetime.now() - self.lastActivateLimitTapo > timedelta(minutes=config.max_minutes_activation_time_tapo)):
                await self.tapoClient.stop_device()
                self.logManager.log("Stopping water heating via TapoClient due to exceeding the max activation limit")
                return
        
        self.logManager.log(f"Battery level: {data.get('battery_soc', 0)}")
        if(config.min_battery_charge_for_water_heating > data.get("battery_soc", 0)):
            if(active):
                if(datetime.now() - self.lastActivateLimitTapo < timedelta(minutes=config.min_minutes_activation_time_tapo)):
                    self.logManager.log("Water heating cannot be stopped, it hasn't been minimum amount yet!")
                    return
                await self.tapoClient.stop_device()
                self.logManager.log("Water heating stopped because batteries are too low!")
            else:
                self.logManager.log("Water heating could not start, battery too low!")
            return

        if(config.min_solar_output_for_water_heating < data.get("ppv", 0)):
            if(active):
                if(datetime.now() - self.lastActivateLimitTapo < timedelta(minutes=config.min_minutes_activation_time_tapo)):
                    self.logManager.log("Water heating cannot be stopped, it hasn't been minimum amount yet!")
                    return
                await self.tapoClient.stop_device()
                self.logManager.log("Water heating stopped because power generation is too low!")
            else:
                self.logManager.log("Water heating could not start, power generation is too low!")
            return
        
        await self.tapoClient.start_device()
        self.lastActivateLimitTapo = datetime.now()
        self.logManager.log("Starting water heating via TapoClient")

    # If check_for_electricity_price is enabled in configuraton, it checks for selling price of electricity and disables selling to grid if the price is too low
    # Works only for CZK price
    async def check_price_and_disable_enable_sell(self):
        if(config.check_for_electricity_price == False):
            self.logManager.log("check_price_and_disable_enable_sell is disabled in configuration!")
            return
        
        # Gets current price from API in CZK/KwH and logs it
        apiOutput = await self.apiClient.get_electricity_price()
        priceJSON = json.loads(apiOutput)
        calculatedPrice = int(priceJSON["priceCZK"]) / 1000
        self.logManager.log(f"Current price : {calculatedPrice}")


        gridEnabled = await self.inverter.read_setting("grid_export")
        data = await self.get_data()
        export = data.get("active_power", 0)

        # If price is lower than 0, we need to disable export
        if(calculatedPrice < 0):
            self.logManager.log("Price is lower than 0, disabling selling!")
            self.priceLowerThanZero = True
            if(gridEnabled == 0):
                self.logManager.log("Grid export is already disabled")
                return
            utils.disable_grid_export(self.inverter, self.logManager)
            return
        else:
            self.priceLowerThanZero = False

            # Enables selling while also enabling or disabling export limit based on the current export
            if(export > config.max_export):
                utils.enable_grid_limit(self.inverter, self.logManager)
            else:
                utils.disable_grid_limit(self.inverter, self.logManager)



        # Ensures that it's been minimum 5 minutes between enabling or disabling export
        if(datetime.now() - self.lastSwitchGridExport < timedelta(minutes=config.min_minutes_between_gridexport_switch)):
            self.logManager.log("Could not continue with price check, it hasnt been minimum amount of minutes yet")
            return
        self.lastSwitchGridExport = datetime.now()


        # Enabling or disabling selling also changes the limit, we need to make sure it does not override each other
        if(export > config.max_export):
            self.logManager.log("Could not continue with price check, the export is more than max_export limit")
            return


        
        if(calculatedPrice < 1):
            if(gridEnabled == 0):
                self.logManager.log("Grid export is already disabled")
                return
            self.logManager.log("Disabling grid export! - Price too low")
            self.sellingDisabledLowerThanOne = True
            utils.disable_grid_export(self.inverter, self.logManager)
        else:
            if(gridEnabled == 1):
                self.logManager.log("Grid export is already enabled")
                return
            self.logManager.log("Enabling grid export! - Price is higher than 1 CZK")
            self.sellingDisabledLowerThanOne = False
            utils.enable_grid_export(self.inverter, self.logManager)
    @error_handler
    async def store_historical_data(self, data):
        if not os.path.exists('data'):
            os.makedirs('data')
        
        history_file = 'data/history.json'
        
        # Load existing data
        if os.path.isfile(history_file):
            with open(history_file, 'r') as f:
                historical_data = json.load(f)
        else:
            historical_data = []

        # Append new data
        historical_data.append(data)

        # Retain only the last week of data
        one_week_ago = datetime.now() - timedelta(weeks=1)
        historical_data = [entry for entry in historical_data 
                        if datetime.fromisoformat(entry['timestamp']) > one_week_ago]

        # Save updated data
        with open(history_file, 'w') as f:
            json.dump(historical_data, f)
        
        return historical_data

    @error_handler
    async def get_historical_data(self, period='all'):
        history_file = 'data/history.json'
        
        if not os.path.isfile(history_file):
            return []
        
        with open(history_file, 'r') as f:
            historical_data = json.load(f)
        
        # Filter by period if specified
        if period == 'day':
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            historical_data = [entry for entry in historical_data 
                            if datetime.fromisoformat(entry['timestamp']) >= today]
        elif period == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            historical_data = [entry for entry in historical_data 
                            if datetime.fromisoformat(entry['timestamp']) >= week_ago]
        
        return historical_data


async def main():
    global controller
    controller = MainController() 

    server = WebServer(controller)
    server.start_in_thread(host="127.0.0.1", port=8000)


    loop = asyncio.get_running_loop()
    
    async def handle_shutdown(sig):
        controller.logManager.log(f"Received signal {sig}")
        cleanup(server)
        controller.logManager.log("Cleanup complete")
        await controller.inverter.write_setting("grid_export", 1)
        await controller.inverter.write_setting("grid_export_limit", config.max_export_set)
        
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(handle_shutdown(s))
        )
    
    try:
        await controller.initialize()
    finally:
        await cleanup(server)
        controller.logManager.log("Cleanup complete")
        await controller.inverter.write_setting("grid_export", 1)
        await controller.inverter.write_setting("grid_export_limit", config.max_export_set)
        
    print("program ended")

if __name__ == "__main__":
    # loads .env file, otherwise the values don't seem to load in
    load_dotenv()
    asyncio.run(main())