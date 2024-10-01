import asyncio
import goodwe
import utils
import display_manager


ip_address = '192.168.0.114'

inverter: goodwe.Inverter = None


async def main():
    lcdmanager = display_manager.lcdManager(20, 4, ip_address)

    failed = await try_connection(lcdmanager)
    if(failed):
        lcdmanager.write_lines(["Failed to connect!","Script disabled!"])
        return
    lcdmanager.write_lines(["Connected!", "Production: " + str(inverter.read_setting("grid_export")), "Export: " + str(inverter.read_setting("grid_export")),])



async def try_connection(lcdmanager, retries=0):
    global inverter
    if(retries == 3):
        return True
    try:
        inverter = await goodwe.connect(ip_address)
        await print_runtime_data()
        return False
    except Exception as e:
        lcdmanager.write_lines(["Failed to connect!", "Retrying in 5s"])
        await asyncio.sleep(5)
        await try_connection(lcdmanager, retries + 1)

async def print_runtime_data():
    
    runtime_data = await inverter.read_runtime_data()
    
    for sensor in inverter.sensors():
        if sensor.id_ in runtime_data:
            print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")


utils.run_async(main)