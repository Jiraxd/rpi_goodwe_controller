from datetime import datetime
import pycron
from main import get_data_and_write_to_lcd, check_grid_limit, logManager, check_water_heating, get_data, check_price_and_disable_enable_sell

class CronManager:
    def __init__(self):
        logManager.log("CronManager loaded!")
        
    def start():
        pycron.start()
        

    @pycron.cron("*/5 * * * * *")
    async def getDataAndWriteToLCD():
        logManager.log("Running cron getDataAndWriteToLCD()")
        data = await get_data_and_write_to_lcd()
        check_grid_limit(data)

        logManager.log("Cron getDataAndWriteToLCD() finished runinng!")

    @pycron.cron("*/15 * * * * *")
    async def checkWaterHeating():
        logManager.log("Running cron checkWaterHeating()")
        data = await get_data()
        check_water_heating(data)
        logManager.log("Cron checkWaterHeating() finished runinng!")
        
    @pycron.cron("*/60 * * * * *")
    async def checkPrice():
        logManager.log("Running cron checkPrice()")
        check_price_and_disable_enable_sell()

        logManager.log("Cron checkPrice() finished runinng!")
        

    
    