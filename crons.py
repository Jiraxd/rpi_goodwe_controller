import pycron
import json
import os
from decorators import error_handler
from datetime import datetime, timedelta

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
    

@pycron.cron("* * * * * */2") 
async def getDataAndCheck(timestamp: datetime):
    logManager.log("Running cron getDataAndCheck()")
    data = await controller.get_data()
    if(controller.status == "Off"):
        return  
    await controller.check_grid_limit(data)
    logManager.log("Cron getDataAndCheck() finished running!")

@pycron.cron("* * * * * */10") 
async def writeToLCD(timestamp: datetime):
    logManager.log("Running cron writeToLCD()")
    await controller.write_to_lcd()
    logManager.log("Cron writeToLCD() finished running!")

#@pycron.cron("* * * * * */30")
async def checkWaterHeating(timestamp: datetime):  
    if(controller.status == "Off"):
        return 
    logManager.log("Running cron checkWaterHeating()")
    data = controller.cachedData
    await controller.check_water_heating(data)
    logManager.log("Cron checkWaterHeating() finished running!")
        
#@pycron.cron("* * * * * */60")
async def checkPrice(timestamp: datetime):
    if(controller.status == "Off"):
        return 
    logManager.log("Running cron checkPrice()")
    await controller.check_price_and_disable_enable_sell()
    logManager.log("Cron checkPrice() finished running!")
    
@pycron.cron("*/30 * * * *")
@error_handler
async def storeHistoricalData(timestamp: datetime):
    logManager.log("Running cron storeHistoricalData()")
    
    try:
        full_data = controller.cachedData
        if full_data:
            data = {
                "timestamp": timestamp.isoformat(),
                "ppv": full_data.get("ppv", 0),
                "house_consumption": full_data.get("house_consumption", 0),
                "active_power": full_data.get("active_power", 0)
            }
            await controller.store_historical_data(data)
            logManager.log(f"Historical data stored at {timestamp}")
        else:
            logManager.log("No data available to store", level=30)
    except Exception as e:
        logManager.log(f"Error storing historical data: {str(e)}", level=40)
        
    logManager.log("Cron storeHistoricalData() finished running!")
    
