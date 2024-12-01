from apiclient import APIClient

from decorators import error_handler
from logger import LoggerCustom
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ApiClient(APIClient):

    def __init__(self, logManager: LoggerCustom):
        self.logManager = logManager
        self.executor = ThreadPoolExecutor() # async wrapping, library doesnt support async
        self.logManager.log("ApiClient loaded!")
    
    @error_handler
    async def get_electricity_price(self):
        url = "https://spotovaelektrina.cz/api/v1/price/get-actual-price-json"

        self.logManager.log(f"Fetching electricity price from {url}...")

        # Run in async
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(self.executor, self.get, url)

        return response