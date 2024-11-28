import traceback
import pycron
from logger import LoggerCustom

def cron_error_handler(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            self.logManager.log(f"Error in cron {func.__name__}: {str(e)}", level=40)
            self.logManager.log(traceback.format_exc(), level=40)
    return wrapper

class CronManager:
    def __init__(self, logManager: LoggerCustom, controller):
        self.logManager = logManager
        self.controller = controller
        self.logManager.log("CronManager loaded!")
        
    def start(self):
        pycron.start()

    @pycron.cron("*/5 * * * * *")
    @cron_error_handler  
    async def getDataAndWriteToLCD(self):  
        self.logManager.log("Running cron getDataAndWriteToLCD()")
        data = await self.controller.get_data_and_write_to_lcd()
        await self.controller.check_grid_limit(data)
        self.logManager.log("Cron getDataAndWriteToLCD() finished running!")

    @pycron.cron("*/15 * * * * *")
    @cron_error_handler  
    async def checkWaterHeating(self):  
        self.logManager.log("Running cron checkWaterHeating()")
        data = await self.controller.get_data()
        await self.controller.check_water_heating(data)
        self.logManager.log("Cron checkWaterHeating() finished running!")
        
    @pycron.cron("*/60 * * * * *")
    @cron_error_handler
    async def checkPrice(self):
        self.logManager.log("Running cron checkPrice()")
        await self.controller.check_price_and_disable_enable_sell()
        self.logManager.log("Cron checkPrice() finished running!")
