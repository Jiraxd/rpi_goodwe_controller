import asyncio
import goodwe
import utils
from display_manager import LCDManager


ip_address = '192.168.0.114'

inverter: goodwe.Inverter = None

lcdmanager : LCDManager = None

offlineMode = False # Set to True for testing purposes without connection to goodwe inverter


async def main():
    global lcdmanager
    lcdmanager = LCDManager(20, 4)
    await lcdmanager.write_init_message(ip_address)

    if offlineMode:
        lcdmanager.write_lines(["Offline Mode", "Production: 0 kw", "Export: 0 kw"])
    else:
        failed = await try_connection()
        if(failed):
            lcdmanager.write_lines(["Failed to connect!","Script disabled!"])
            return
        data = await inverter.read_runtime_data()
        print(data)
        lcdmanager.write_lines(["Connected!", "Production: " + str(data.get("ppv", 0)) + "W", "Export: " + str(data.get("active_power", 0)) + "W", "House: " + str(data.get("house_consumption:", 0)) + "W"])



async def try_connection():
    global inverter
    for i in range(3):
        if(i == 3):
            return True
        try:
            inverter = await goodwe.connect(ip_address)
        #   await print_runtime_data()
            return False
        except Exception:
            lcdmanager.write_lines(["Failed to connect!", "Retrying in 5s"])
            await asyncio.sleep(5)

    return False

async def print_runtime_data():
    
    runtime_data = await inverter.read_runtime_data()
    
    for sensor in inverter.sensors():
        if sensor.id_ in runtime_data:
            print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")


asyncio.run(main())