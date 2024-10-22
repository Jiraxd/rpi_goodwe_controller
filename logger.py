import logging
import os
from datetime import datetime

class LoggerCustom:
    def __init__(self):

        if(not os.path.isdir("Logs")):
            os.mkdir("Logs")
        if(os.path.isfile("Logs/log.txt")):
            os.rename("Logs/log.txt", f"Logs/log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        logging.basicConfig(filename="Logs/log.txt",
                    filemode='a',
                    format='[%(asctime)s,%(msecs)d] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
        self.logger = logging.getLogger("loggercustom")
        self.logger.log(logging.INFO, "Logger successfully initialized!")

    def log(self, text:str, level:int = 20):
        self.logger.log(level, text)
        print(text)

    


logger = LoggerCustom()