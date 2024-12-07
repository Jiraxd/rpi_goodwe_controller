import asyncio
import json
import sys
import traceback
import goodwe
from decorators import error_handler
import utils
from datetime import datetime, timedelta
from display_manager import LCDManager 
from crons import CronManager
from logger import LoggerCustom
from tapo_client import TapoClient
from api_client import ApiClient
from config import config
from dotenv import load_dotenv
import signal

load_dotenv()

# sensors
# ppv - current production in W
# battery_soc - current battery in %
# house_consumption - current house consumption in W
# active_power - current export in W, if - value, importing from grid, if + value, exporting to grid


# settings
# grid_export_limit - limit of export to grid in W
# grid_export - 1 - enables limiter, 0 - disables limiter

async def cleanup():
    # Close httpx client
    if controller.apiClient:
        await controller.apiClient.close()
    
    # Write close message
    if controller.lcdmanager:
        controller.lcdmanager.write_lines(["Shutting down..."])
        
    # Stop cron jobs
    if controller.cronManager:
        controller.cronManager.stop()

class MainController:
    def __init__(self):
        self.inverter = None
        self.lcdmanager = None 
        self.cronManager = None
        self.logManager = None
        self.tapoClient = None
        self.apiClient = None
        self.lastActivateLimit = datetime.now() - timedelta(minutes=30)
        self.lastActivateLimitTapo = datetime.now() - timedelta(minutes=config.min_minutes_activation_time_tapo)
        self.lastSwitchGridExport = datetime.now() - timedelta(minutes=config.min_minutes_between_gridexport_switch)
        self.offlineMode = False # Set to True for testing purposes without connection to goodwe inverter
        
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

    @error_handler
    async def check_limit_disabled_on_init(self):
        currentLimit = await self.inverter.read_setting("grid_export_limit")
        if(currentLimit != config.max_export_set):
            await utils.enable_grid_limit(self.inverter, self.logManager)
        


    @error_handler
    async def get_runtime_data(self, printData = False):
        runtime_data = await self.inverter.read_runtime_data()
        if(printData):
            for sensor in self.inverter.sensors():
                if sensor.id_ in runtime_data:
                    print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")
        return runtime_data

    async def get_data_and_write_to_lcd(self):
        data = await self.get_runtime_data(False)
        self.lcdmanager.write_lines([
            "Connected!", 
            f"Production: {str(data.get('ppv', 0))}W",
            f"Export: {str(data.get('active_power', 0))}W", 
            f"House: {str(data.get('house_consumption', 0))}W"
        ])
        return data

    async def get_data(self):
        return await self.get_runtime_data(False)

    async def check_grid_limit(self, data):
        export = data.get("active_power", 0)
        enabled = await self.inverter.read_setting("grid_export")
        if(export > config.max_export):
            await utils.enable_grid_limit(self.inverter, self.logManager)
        else:
            if(datetime.now() - self.lastActivateLimit > timedelta(minutes=config.min_minutes_before_deactivate_limit)):
                if(enabled == 0): 
                    return
                self.lastActivateLimit = datetime.now()
                await utils.disable_grid_limit(self.inverter, self.logManager)

    async def check_water_heating(self, data):
        await self.tapoClient.print_device_info()
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

    async def check_price_and_disable_enable_sell(self):
        apiOutput = await self.apiClient.get_electricity_price()
        priceJSON = json.loads(apiOutput)
        calculatedPrice = int(priceJSON["priceCZK"]) / 1000
        self.logManager.log(f"Current price : {calculatedPrice}")

        if(datetime.now() - self.lastSwitchGridExport < timedelta(minutes=config.min_minutes_between_gridexport_switch)):
            self.logManager.log("Could not continue with price check, it hasnt been minimum amount of minutes yet")
            return
        self.lastSwitchGridExport = datetime.now()

        gridEnabled = await self.inverter.read_setting("grid_export")
        if(calculatedPrice < 1):
            if(gridEnabled == 0):
                self.logManager.log("Grid export is already disabled")
                return
            self.logManager.log("Disabling grid export! - Price too low")
            utils.disable_grid_export(self.inverter, self.logManager)
        else:
            if(gridEnabled == 1):
                self.logManager.log("Grid export is already enabled")
                return
            self.logManager.log("Enabling grid export! - Price is higher than 1 CZK")
            utils.enable_grid_export(self.inverter, self.logManager)


async def main():
    global controller
    controller = MainController() 
    
    loop = asyncio.get_running_loop()
    
    async def handle_shutdown(sig):
        controller.logManager.log(f"Received signal {sig}")
        cleanup()
        controller.logManager.log("Cleanup complete")
        
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(handle_shutdown(s))
        )
    
    try:
        await controller.initialize()
    finally:
        await cleanup()
        controller.logManager.log("Cleanup complete")
        
    print("program ended")

if __name__ == "__main__":
    asyncio.run(main())