from starlette.responses import FileResponse 

# pip install fastapi


class WebServer:

    def __init__(self, control):
        self.controller = control
        self.router = APIRouter()
        self.router.add_api_route("/", self.index_page, methods=["GET"])
        self.router.add_api_route("/status", self.get_status, methods=["GET"])
        self.router.add_api_route("/start", self.stop_script, methods=["GET"])
        self.router.add_api_route("/stop", self.start_script, methods=["GET"])

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