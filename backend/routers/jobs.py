from fastapi import APIRouter, HTTPException
from typing import Optional
import database as db
from profile import PROFILE

router = APIRouter()


@router.get("/")
async def list_jobs(
    source: Optional[str] = None,
    min_score: Optional[int] = 0,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    """Lista todas las ofertas con filtros opcionales."""
    jobs = db.get_all_jobs()

    if source:
        jobs = [j for j in jobs if j.get("source") == source]
    if min_score:
        jobs = [j for j in jobs if j.get("match_score", 0) >= min_score]
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    if search:
        q = search.lower()
        jobs = [j for j in jobs if q in j.get("title", "").lower()
                or q in j.get("company", "").lower()
                or q in j.get("description", "").lower()]

    return {"jobs": jobs, "total": len(jobs)}


@router.get("/stats")
async def get_stats():
    return db.get_stats()


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return job


@router.patch("/{job_id}/status")
async def update_status(job_id: str, payload: dict):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Campo 'status' requerido")
    ok = db.update_job_status(job_id, status)
    if not ok:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return {"message": "Estado actualizado", "job_id": job_id, "status": status}


@router.patch("/{job_id}/cover-letter")
async def update_cover_letter(job_id: str, payload: dict):
    cover_letter = payload.get("cover_letter", "")
    ok = db.update_job_cover_letter(job_id, cover_letter)
    if not ok:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return {"message": "Carta actualizada"}


@router.get("/{job_id}/cover-letter/generate")
async def generate_cover_letter(job_id: str):
    """Genera carta de presentación personalizada para la oferta."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    letter = PROFILE["cover_letter_template"].format(
        job_title=job.get("title", "el cargo"),
        company=job.get("company", "su empresa"),
    )
    return {"cover_letter": letter}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    ok = db.delete_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return {"message": "Oferta eliminada"}
