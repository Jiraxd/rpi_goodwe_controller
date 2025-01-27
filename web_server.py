from starlette.responses import FileResponse 
from fastapi import FastAPI, APIRouter
import uvicorn
import asyncio
import threading

class WebServer:
    def __init__(self, control):
        self.controller = control
        self.app = FastAPI()
        self.router = APIRouter()
        self.router.add_api_route("/", self.index_page, methods=["GET"])
        self.router.add_api_route("/status", self.get_status, methods=["GET"])
        self.router.add_api_route("/start", self.stop_script, methods=["GET"])
        self.router.add_api_route("/stop", self.start_script, methods=["GET"])
        self.app.include_router(self.router)

    def index_page(self):
        return FileResponse('index.html')
    
    def get_status(self):
        return {"status": self.controller.status}

    def stop_script(self):
        self.controller.status = "Off"
        return {"status":"Stopped script!"}

    def start_script(self):
        self.controller.status = "On"
        return {"status":"Started script!"}

    def run(self, host="0.0.0.0", port=8000):
        print(f"Starting server on {host}:{port}")
        config = uvicorn.Config(self.app, host=host, port=port)
        server = uvicorn.Server(config)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())

    def start_in_thread(self, host="0.0.0.0", port=8000):
        thread = threading.Thread(target=self.run, args=(host, port))
        thread.start()