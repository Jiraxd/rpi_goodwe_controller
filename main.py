import asyncio
import goodwe
import utils
from datetime import datetime, timedelta
from display_manager import LCDManager
from crons import CronManager
from types import SimpleNamespace
from logger import LoggerCustom
from tapo_client import TapoClient




config = SimpleNamespace(
    ip_address='192.168.0.114',
    tapo_ip_address="192.168.0.106",
    max_export=5000,
    min_battery_charge_for_water_heating = 75, # percentage
    min_solar_output_for_water_heating = 2500, # minimum solar output to start heating water
    min_minutes_before_deactivate_limit = 30,
    min_minutes_activation_time_tapo = 120,
    max_minutes_activation_time_tapo = 200
)


inverter: goodwe.Inverter = None

lcdmanager : LCDManager = None

cronManager : CronManager = None

logManager : LoggerCustom = None

tapoClient : TapoClient = None  

lastActivateLimit = datetime.now() - timedelta(minutes=30)

lastActivateLimitTapo = datetime.now() - timedelta(minutes=config.min_minutes_activation_time_tapo)

offlineMode = False # Set to True for testing purposes without connection to goodwe inverter




# sensors
# ppv - current production in W
# battery_soc - current battery in %
# house_consumption - current house consumption in W
# active_power - current export in W, if - value, importing from grid, if + value, exporting to grid

async def main():
    global lcdmanager, cronManager, logManager, tapoClient

    logManager = LoggerCustom()
    logManager.log("Initializing managers")

    lcdmanager = LCDManager(20, 4)
    cronManager = CronManager()
    tapoClient = TapoClient()
    
    logManager.log("Managers initialized")
    
    await lcdmanager.write_init_message(config.ip_address)
    
    if offlineMode:
        lcdmanager.write_lines(["Offline Mode", "Production: 0 kw", "Export: 0 kw"])
    else:
        failed = await try_connection()
        if(failed):
            lcdmanager.write_lines(["Failed to connect!","Script disabled!"])
            return

        await check_limit_disabled_on_init()
        cronManager.start()


async def try_connection():
    global inverter
    for i in range(3):
        if(i == 3):
            return True
        try:
            inverter = await goodwe.connect(config.ip_address)
        #   await print_runtime_data()
            return False
        except Exception:
            lcdmanager.write_lines(["Failed to connect!", "Retrying in 5s"])
            await asyncio.sleep(5)

    return False

async def check_limit_disabled_on_init():
    enabled = await inverter.read_setting("grid_export")
    if(enabled == 1):
        logManager.log("Grid limit is already enabled!")
    else:
        utils.enable_grid_limit(inverter)
        logManager.log("Grid limit enabled on startup!")

async def get_runtime_data(printData = False):
    
    runtime_data = await inverter.read_runtime_data()
    if(printData):
        for sensor in inverter.sensors():
            if sensor.id_ in runtime_data:
                print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")
    return runtime_data


async def get_data_and_write_to_lcd():
    data = await get_runtime_data(False) # Change to True to print runtime data
    lcdmanager.write_lines(["Connected!", "Production: " + str(data.get("ppv", 0)) + "W", "Export: " + str(data.get("active_power", 0)) + "W", "House: " + str(data.get("house_consumption", 0)) + "W"])
    return data

async def get_data():
     data = await get_runtime_data(False)
     return data

async def check_grid_limit(data):
    export = data.get("active_power", 0)
    enabled = await inverter.read_setting("grid_export")
    if(export > config.max_export):
        
        if(enabled == 1): 
            return
        logManager.log("Turning on grid limit")
        utils.enable_grid_limit(inverter)
    else:
        if(datetime.now - lastActivateLimit > timedelta(minutes=config.min_minutes_before_deactivate_limit)):
            if(enabled == 0): 
                return
            lastActivateLimit = datetime.now()
            logManager.log("Turning off grid limit")
            utils.disable_grid_limit(inverter)



async def check_water_heating(data):
    # temp device info
    tapoClient.print_device_info()
    
    active = tapoClient.check_is_active()
    
    if(active):
        if(datetime.now - lastActivateLimitTapo > timedelta(minutes=config.max_minutes_activation_time_tapo)):
            tapoClient.stop_device()
            logManager.log("Stopping water heating via TapoClient due to exceeding the max activation limit")
            return
    
    if(config.min_battery_charge_for_water_heating < data.get("battery_soc", 0)):
        if(active):
            if(datetime.now - lastActivateLimitTapo < timedelta(minutes=config.min_minutes_activation_time_tapo)):
                logManager.log("Water heating cannot be stopped, it hasn't been minimum amount yet!")
                return
            tapoClient.stop_device()
            logManager.log("Water heating stopped because batteries are too low!")
        else:
            logManager.log("Water heating could not start, battery too low!")
        return
    if(config.min_solar_output_for_water_heating < data.get("ppv", 0)):

        if(active):
            if(datetime.now - lastActivateLimitTapo < timedelta(minutes=config.min_minutes_activation_time_tapo)):
                logManager.log("Water heating cannot be stopped, it hasn't been minimum amount yet!")
                return
            tapoClient.stop_device()
            logManager.log("Water heating stopped because power generation is too low!")
        else:
            logManager.log("Water heating could not start, power generation is too low!")
        return
    
    tapoClient.start_device()
    lastActivateLimitTapo = datetime.now()
    logManager.log("Starting water heating via TapoClient")

    


asyncio.run(main())