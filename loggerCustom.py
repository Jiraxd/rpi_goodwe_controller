import logging
import os
from datetime import datetime

class LoggerCustom:
    def __init__(self):
        os.makedirs("Logs", exist_ok=True)

        log_file = "Logs/log.txt"
        if os.path.isfile(log_file):
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            os.rename(log_file, f"Logs/log_{timestamp}.txt")

        self.logger = logging.getLogger("loggercustom")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file, mode='a')
            formatter = logging.Formatter(
                '[%(asctime)s,%(msecs)d] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.info("Logger successfully initialized!")

    def log(self, text: str, level: int = logging.INFO):
        self.logger.log(level, text)
        print(text)

logger = LoggerCustom()