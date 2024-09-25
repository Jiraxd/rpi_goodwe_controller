import asyncio
import goodwe


async def get_runtime_data():
    ip_address = '192.168.0.114'

    inverter = await goodwe.connect(ip_address)
    runtime_data = await inverter.read_runtime_data()
    
    return
    for sensor in inverter.sensors():
        if sensor.id_ in runtime_data:
            print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")


asyncio.run(get_runtime_data())

async def disable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 0)

async def enable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 1)
