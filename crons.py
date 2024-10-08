from datetime import datetime
import pycron
from main import get_data_and_write_to_lcd, check_disable_grid_limit

class CronManager:
    def __init__(self):
        print("CronManager loaded!")
        
    def start():
        pycron.start()
        

    @pycron.cron("*/5 * * * * *")
    async def getDataAndWriteToLCD():
        print("Running cron getDataAndWriteToLCD()")
        data = await get_data_and_write_to_lcd()
        check_disable_grid_limit(data)
        print("Cron getDataAndWriteToLCD() finished runinng!")
        
        # Use custom logger in the future for logging and logs

    
    