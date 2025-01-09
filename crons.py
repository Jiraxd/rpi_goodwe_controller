import pycron
import asyncio
from decorators import error_handler
from datetime import datetime

logManager = None
controller = None

class CronManager:
    def __init__(self, _logManager, _controller):
        global logManager, controller
        logManager = _logManager
        controller = _controller
        logManager.log("CronManager loaded!")
        
    def start(self):
        pycron.start()
        
    def stop(self):
        pycron.stop()
    



@pycron.cron("* * * * * */15") 
async def getDataAndWriteToLCD(timestamp: datetime):  
    logManager.log("Running cron getDataAndWriteToLCD()")
    data = await controller.get_data_and_write_to_lcd()
    await controller.check_grid_limit(data)
    logManager.log("Cron getDataAndWriteToLCD() finished running!")

#@pycron.cron("* * * * * */30")
async def checkWaterHeating(timestamp: datetime):  
    logManager.log("Running cron checkWaterHeating()")
    data = await controller.get_data()
    await controller.check_water_heating(data)
    logManager.log("Cron checkWaterHeating() finished running!")
        
#@pycron.cron("* * * * * */60")
async def checkPrice(timestamp: datetime):
    logManager.log("Running cron checkPrice()")
    await controller.check_price_and_disable_enable_sell()
    logManager.log("Cron checkPrice() finished running!")