import tapo
import os
from main import config, logManager
import asyncio


# pip install python-dotenv

# pip install tapo

class TapoClient:
    def __init__(self):

        self.client = ApiClient(os.getenv("TAPO_USERNAME"), os.getenv("TAPO_PASS"))
        asyncio.run(self.init_device())
        logManager.log("TapoClient successfully initialized")
    
    async def init_device(self):
        self.device = await client.p110(config.tapo_ip_address)
        device_info = await self.device.get_device_info()

        logManager.log(f"Tapo startup info: {device_info.to_dict()}")

    async def start_device(self):
        await self.device.on()

    async def stop_device(self):
        await self.device.off()

    async def print_device_info(self):
        device_info = await self.device.get_device_info()
        logManager.log(f"Device info: {device_info.to_dict()}")

        device_usage = await self.device.get_device_usage()
        logManager.log(f"Device usage: {device_usage.to_dict()}")

    async def check_is_active(self):
        # TODO
        pass
