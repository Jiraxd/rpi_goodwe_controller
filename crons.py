import pycron
from decorators import error_handler
from logger import LoggerCustom

class CronManager:
    def __init__(self, _logManager: LoggerCustom, _controller):
        self.logManager = _logManager
        self.controller = _controller
        self.logManager.log("CronManager loaded!")
        
    def start(self):
        pycron.start()

    @pycron.cron("*/15 * * * * *")
    @error_handler  
    async def getDataAndWriteToLCD(self):  
        self.logManager.log("Running cron getDataAndWriteToLCD()")
        data = await self.controller.get_data_and_write_to_lcd()
        await self.controller.check_grid_limit(data)
        self.logManager.log("Cron getDataAndWriteToLCD() finished running!")

    @pycron.cron("*/30 * * * * *")
    @error_handler  
    async def checkWaterHeating(self):  
        self.logManager.log("Running cron checkWaterHeating()")
        data = await self.controller.get_data()
        await self.controller.check_water_heating(data)
        self.logManager.log("Cron checkWaterHeating() finished running!")
        
    @pycron.cron("*/60 * * * * *")
    @error_handler
    async def checkPrice(self):
        self.logManager.log("Running cron checkPrice()")
        await self.controller.check_price_and_disable_enable_sell()
        self.logManager.log("Cron checkPrice() finished running!")
