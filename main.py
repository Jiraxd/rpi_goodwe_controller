import asyncio
import goodwe
import utils
from datetime import datetime, timedelta
from display_manager import LCDManager
from crons import CronManager
from types import SimpleNamespace
from logger import LoggerCustom


config = SimpleNamespace(
    ip_address='192.168.0.114',
    max_export=5000,
    min_battery_charge_for_water_heating = 75, # percentage
    min_solar_output_for_water_heating = 1500, # minimum solar output to start heating water
    min_minutes_before_deactivate_limit = 30
)


inverter: goodwe.Inverter = None

lcdmanager : LCDManager = None

cronManager : CronManager = None

logManager : LoggerCustom = None

lastActivateLimit = datetime.now() - timedelta(minutes=30)

offlineMode = False # Set to True for testing purposes without connection to goodwe inverter


async def main():
    global lcdmanager, cronManager, logManager

    logManager = LoggerCustom()
    logManager.log("Initializing managers")

    lcdmanager = LCDManager(20, 4)
    cronManager = CronManager()
    
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
    
    pass

    


asyncio.run(main())