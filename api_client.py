from main import logManager
from apiclient import APIClient

class ApiClient(APIClient):

    def __init__(self):
        logManager.log("ApiClient loaded!")
        pass

    def get_electricity_price(self):
        url = "https://spotovaelektrina.cz/api/v1/price/get-actual-price-json"
        return self.get(url)