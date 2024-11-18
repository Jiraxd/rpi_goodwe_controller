import goodwe
import asyncio
from tapo import ApiClient
import os



## test to read current data from inverter and print data from tapo device


async def getData():
    
    inverter = await goodwe.connect("192.168.0.114")
    runtime_data = await inverter.read_runtime_data()
    for sensor in inverter.sensors():
            if sensor.id_ in runtime_data:
                print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")
    settings = inverter.settings()
    
    print(settings)
    
    
async def printDataTAPO():
    tapo = ApiClient(os.getenv("TAPO_USERNAME"), os.getenv("TAPO_PASS"))
    device_info = await tapo.get_device_info()
    print(f"Device info: {device_info.to_dict()}")

    device_usage = await tapo.get_device_usage()
    print(f"Device usage: {device_usage.to_dict()}")
    
                
                
asyncio.run(getData())
asyncio.run(printDataTAPO())