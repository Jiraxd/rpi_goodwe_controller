import httpx
from decorators import error_handler
from loggerCustom import LoggerCustom

class ApiClient:
    def __init__(self, logManager: LoggerCustom):
        self.logManager = logManager
        self._client = None
        self.logManager.log("ApiClient loaded!")
    
    @property
    async def client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    @error_handler
    async def get_electricity_price(self):
        url = "https://spotovaelektrina.cz/api/v1/price/get-actual-price-json"
        self.logManager.log(f"Fetching electricity price from {url}...")
        
        try:
            client = await self.client
            response = await client.get(url)
            response.raise_for_status()
            return response.text
            
        except httpx.TimeoutException:
            self.logManager.log("API request timed out", level=40)
        except httpx.HTTPError as e:
            self.logManager.log(f"HTTP error occurred: {str(e)}", level=40)
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                self._client = None  # Reset client for next attempt
                self.logManager.log("Event loop was closed, will retry on next request", level=30)
            else:
                raise
            
        return None

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None