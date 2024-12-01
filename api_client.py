import httpx
from decorators import error_handler
from logger import LoggerCustom

class ApiClient:
    def __init__(self, logManager: LoggerCustom):
        self.logManager = logManager
        self.client = httpx.AsyncClient(timeout=10.0)
        self.logManager.log("ApiClient loaded!")
    
    @error_handler
    async def get_electricity_price(self):
        url = "https://spotovaelektrina.cz/api/v1/price/get-actual-price-json"
        self.logManager.log(f"Fetching electricity price from {url}...")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
            
        except httpx.TimeoutException:
            self.logManager.log("API request timed out", level=40)
        except httpx.HTTPError as e:
            self.logManager.log(f"HTTP error occurred: {str(e)}", level=40)
            
        return None

    async def close(self):
        await self.client.aclose()