from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Монтируем статические файлы
www_dir = os.path.join(os.path.dirname(__file__), "www")
if not os.path.exists(www_dir):
    os.makedirs(www_dir)
app.mount("/static", StaticFiles(directory=www_dir), name="static")

@app.get("/")
async def index():
    return FileResponse(os.path.join(www_dir, "index.html"))

@app.get("/main.dart.js")
async def dart_js():
    return FileResponse(os.path.join(www_dir, "main.dart.js"))
