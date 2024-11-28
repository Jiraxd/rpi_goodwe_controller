import pycron
import asyncio
from decorators import error_handler
from datetime import datetime

class CronManager:
    def __init__(self, _logManager, _controller):
        self.logManager = _logManager
        self.controller = _controller
        self.loop = asyncio.get_event_loop()
        self.logManager.log("CronManager loaded!")
        
    def start(self):
        pycron.start()

    @pycron.cron("* * * * * */15") 
    async def getDataAndWriteToLCD(self, timestamp: datetime):  
        self.logManager.log("Running cron getDataAndWriteToLCD()")
        data = await self.controller.get_data_and_write_to_lcd()
        await self.controller.check_grid_limit(data)
        self.logManager.log("Cron getDataAndWriteToLCD() finished running!")

    @pycron.cron("* * * * * */30")
    async def checkWaterHeating(self, timestamp: datetime):  
        self.logManager.log("Running cron checkWaterHeating()")
        data = await self.controller.get_data()
        await self.controller.check_water_heating(data)
        self.logManager.log("Cron checkWaterHeating() finished running!")
        
    @pycron.cron("* * * * * */60")
    async def checkPrice(self, timestamp: datetime):
        self.logManager.log("Running cron checkPrice()")
        await self.controller.check_price_and_disable_enable_sell()
        self.logManager.log("Cron checkPrice() finished running!")