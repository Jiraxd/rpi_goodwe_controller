import asyncio
import goodwe
import utils
from display_manager import LCDManager
from crons import CronManager
from types import SimpleNamespace


# Maybe better way to store config?
config = SimpleNamespace(
    ip_address='192.168.0.114',
    max_export=5000
)


inverter: goodwe.Inverter = None

lcdmanager : LCDManager = None

cronManager : CronManager = None

offlineMode = False # Set to True for testing purposes without connection to goodwe inverter


async def main():
    global lcdmanager, cronManager
    lcdmanager = LCDManager(20, 4)
    cronManager = CronManager()
    
    await lcdmanager.write_init_message(config.ip_address)

    if offlineMode:
        lcdmanager.write_lines(["Offline Mode", "Production: 0 kw", "Export: 0 kw"])
    else:
        failed = await try_connection()
        if(failed):
            lcdmanager.write_lines(["Failed to connect!","Script disabled!"])
            return
        
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

async def check_disable_grid_limit(data):
    export = data.get("active_power", 0)
    if(export > config.max_export):
        # Add turning on grid limit
        pass
    else:
        # Add turning off grid limit
        pass
    


asyncio.run(main())