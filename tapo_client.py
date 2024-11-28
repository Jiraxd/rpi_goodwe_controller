from tapo import ApiClient
import os

from logger import LoggerCustom

class TapoClient:
    def __init__(self, logManager: LoggerCustom):
        self.logManager = logManager  
        self.client = ApiClient(os.getenv("TAPO_USERNAME"), os.getenv("TAPO_PASS"))
        self.device = None


    async def init_device(self, config):
        """Initialize the device asynchronously."""
        self.device = await self.client.p110(config.tapo_ip_address)
        device_info = await self.device.get_device_info()

        self.logManager.log(f"Tapo startup info: {device_info.to_dict()}")
        self.logManager.log("TapoClient successfully initialized")

    async def start_device(self):
        """Start the Tapo device."""
        if self.device:
            self.logManager.log("Starting Tapo device")
            await self.device.on()
        else:
            self.logManager.log("Device not initialized")

    async def stop_device(self):
        """Stop the Tapo device."""
        if self.device:
            self.logManager.log("Stopping Tapo device")
            await self.device.off()
        else:
            self.logManager.log("Device not initialized")

    async def print_device_info(self):
        """Print the device information and usage."""
        if self.device:
            device_info = await self.device.get_device_info()
            self.logManager.log(f"Device info: {device_info.to_dict()}")

            device_usage = await self.device.get_device_usage()
            self.logManager.log(f"Device usage: {device_usage.to_dict()}")
        else:
            self.logManager.log("Device not initialized")

    async def check_is_active(self):
      return False
