import goodwe
import asyncio



## test to read current data from inverter


async def getData():
    
    inverter = await goodwe.connect("192.168.0.114")
    runtime_data = await inverter.read_runtime_data()
    for sensor in inverter.sensors():
            if sensor.id_ in runtime_data:
                print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")
                
                
asyncio.run(getData())