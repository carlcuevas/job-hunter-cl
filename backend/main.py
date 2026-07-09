import sys
import os

# Asegurar que backend/ esté en sys.path para imports relativos
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import jobs, applications, scraper

app = FastAPI(title="Job Hunter CL", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])

# Rutas al frontend — funciona tanto local como en Render
_root_dir = os.path.join(_backend_dir, "..")
frontend_path = os.path.abspath(os.path.join(_root_dir, "frontend"))

app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/health")
async def health():
    return {"status": "ok", "app": "Job Hunter CL"}
