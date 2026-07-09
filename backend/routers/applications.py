from fastapi import APIRouter, HTTPException
from models import ApplicationUpdate
import database as db
import uuid
from datetime import datetime

router = APIRouter()


@router.get("/")
async def list_applications():
    apps = db.get_all_applications()
    return {"applications": apps, "total": len(apps)}


@router.post("/")
async def create_application(payload: dict):
    """Registra una postulación realizada."""
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id requerido")

    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    application = {
        "id": str(uuid.uuid4())[:8],
        "job_id": job_id,
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "source": job.get("source", ""),
        "url": job.get("url", ""),
        "applied_at": datetime.utcnow().isoformat(),
        "status": "enviada",
        "cover_letter": payload.get("cover_letter", ""),
        "notes": payload.get("notes", ""),
    }

    db.save_application(application)
    db.update_job_status(job_id, "postulada")

    return {"message": "Postulación registrada", "application": application}


@router.get("/{app_id}")
async def get_application(app_id: str):
    app = db.get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    return app


@router.patch("/{app_id}")
async def update_application(app_id: str, update: ApplicationUpdate):
    updates = {}
    if update.status:
        updates["status"] = update.status
    if update.notes is not None:
        updates["notes"] = update.notes

    ok = db.update_application(app_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    return {"message": "Postulación actualizada"}
