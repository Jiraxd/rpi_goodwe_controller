from config import config
from starlette.responses import FileResponse 
from fastapi import FastAPI, APIRouter, Request, HTTPException
import uvicorn
import asyncio
import threading

password = "rpiadmin123"
class WebServer:
    def __init__(self, control):
        self.controller = control
        self.app = FastAPI()
        self.router = APIRouter()
        self.router.add_api_route("/", self.index_page, methods=["GET"])
        self.router.add_api_route("/status", self.get_status, methods=["GET"])
        self.router.add_api_route("/start", self.start_script, methods=["GET"])
        self.router.add_api_route("/stop", self.stop_script, methods=["GET"])
        self.router.add_api_route("/info", self.get_info, methods=["GET"])
        self.router.add_api_route("/historical-data", self.historical_data_handler, methods=["GET"])
        self.app.include_router(self.router)
        self.shutdown_event = threading.Event()

    async def get_info(self):
        data = self.controller.cachedData
        enabled = await self.controller.inverter.read_setting("grid_export")
        return {"production": data["ppv"],
               "consumption": data["house_consumption"],
               "battery": data["battery_soc"],
               "export": data["active_power"],
                "enabled": enabled,
        }
    def index_page(self):
        return FileResponse('index.html')
    
    def get_status(self):
        return {"status": self.controller.status}

    async def stop_script(self, request: Request):
        pwd = request.query_params.get("pass")
        if pwd != password:
            raise HTTPException(status_code=401, detail="Invalid password")
        self.controller.status = "Off"
        await self.controller.inverter.write_setting("grid_export", 1)
        await self.controller.inverter.write_setting("grid_export_limit", config.max_export_set)
        return {"status": "Stopped script!"}

    async def start_script(self, request: Request):
        pwd = request.query_params.get("pass")
        if pwd != password:
            raise HTTPException(status_code=401, detail="Invalid password")
        self.controller.status = "On"
        return {"status": "Started script!"}
    async def historical_data_handler(self, request: Request):
        period = request.query_params.get('period', 'all')
        data = await self.controller.get_historical_data(period)
        return data

    def run(self, host="0.0.0.0", port=8000):
        print(f"Starting server on {host}:{port}")
        configUvicorn = uvicorn.Config(self.app, host=host, port=port)
        server = uvicorn.Server(configUvicorn)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
        while not self.shutdown_event.is_set():
            loop.run_until_complete(asyncio.sleep(1))
    

    def start_in_thread(self, host="0.0.0.0", port=8000):
        self.server_thread = threading.Thread(target=self.run, args=(host, port))
        self.server_thread.start()

    def stop(self):
        self.shutdown_event.set()
        self.server_thread.join()
