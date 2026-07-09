import sys
import os

# Cuando se ejecuta como "cd backend && uvicorn main:app",
# el cwd es backend/ y el frontend está en ../frontend
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir    = os.path.abspath(os.path.join(_backend_dir, ".."))

# Asegurar que backend/ esté en sys.path para imports relativos
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import jobs, applications, scraper


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: iniciar el scheduler de búsqueda automática
    try:
        from scheduler import start_scheduler, shutdown_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[Startup] No se pudo iniciar el scheduler: {e}")
    yield
    # Shutdown
    try:
        from scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


app = FastAPI(title="Job Hunter CL", version="1.0.0", lifespan=lifespan)

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

# Frontend — siempre relativo a la raíz del repo
frontend_path = os.path.join(_root_dir, "frontend")

app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/health")
async def health():
    return {"status": "ok", "app": "Job Hunter CL"}
