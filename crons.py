import pycron
import asyncio
from decorators import error_handler
from functools import partial

class CronManager:
    def __init__(self, _logManager, _controller):
        self.logManager = _logManager
        self.controller = _controller
        self.loop = asyncio.get_event_loop()
        self.logManager.log("CronManager loaded!")
        
    def start(self):
        
        # Create wrapper functions that schedule coroutines in the existing event loop, pycron is passing DATETIME so we need to wrap it
        def lcd_wrapper(dt):
            return self.loop.create_task(self.getDataAndWriteToLCD())
            
        def heating_wrapper(dt):
            return self.loop.create_task(self.checkWaterHeating())
            
        def price_wrapper(dt):
            return self.loop.create_task(self.checkPrice())

        pycron.add_job("* * * * * */15", lcd_wrapper)
        pycron.add_job("* * * * * */30", heating_wrapper)
        pycron.add_job("* * * * * */60", price_wrapper)
        pycron.start()

    @error_handler  
    async def getDataAndWriteToLCD(self):  
        self.logManager.log("Running cron getDataAndWriteToLCD()")
        data = await self.controller.get_data_and_write_to_lcd()
        await self.controller.check_grid_limit(data)
        self.logManager.log("Cron getDataAndWriteToLCD() finished running!")

    @error_handler  
    async def checkWaterHeating(self):  
        self.logManager.log("Running cron checkWaterHeating()")
        data = await self.controller.get_data()
        await self.controller.check_water_heating(data)
        self.logManager.log("Cron checkWaterHeating() finished running!")
        
    @error_handler
    async def checkPrice(self):
        self.logManager.log("Running cron checkPrice()")
        await self.controller.check_price_and_disable_enable_sell()
        self.logManager.log("Cron checkPrice() finished running!")