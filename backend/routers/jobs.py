from fastapi import APIRouter, HTTPException
from typing import Optional
import database as db
from profile import PROFILE

router = APIRouter()


def _is_remote(job: dict) -> bool:
    """Detecta si una oferta es remota por modalidad, ubicación o texto."""
    blob = " ".join([
        str(job.get("modality") or ""),
        str(job.get("location") or ""),
        str(job.get("title") or ""),
        str(job.get("description") or ""),
    ]).lower()
    return any(w in blob for w in ["remoto", "remote", "teletrabajo", "home office", "hibrido", "híbrido"])


@router.get("/")
async def list_jobs(
    source: Optional[str] = None,
    min_score: Optional[int] = 0,
    status: Optional[str] = None,
    exclude_status: Optional[str] = None,
    search: Optional[str] = None,
    remote_only: Optional[bool] = False,
):
    """Lista todas las ofertas con filtros opcionales."""
    jobs = db.get_all_jobs()

    if source:
        jobs = [j for j in jobs if j.get("source") == source]
    if min_score:
        jobs = [j for j in jobs if j.get("match_score", 0) >= min_score]
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    elif exclude_status:
        jobs = [j for j in jobs if j.get("status") != exclude_status]
    if remote_only:
        jobs = [j for j in jobs if _is_remote(j)]
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
    cover_letter   = payload.get("cover_letter", "")
    gob_experience = payload.get("gob_experience", "")
    gob_education  = payload.get("gob_education", "")
    ok = db.update_job_cover_letter(job_id, cover_letter, gob_experience, gob_education)
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

    # Detectar área del trabajo para seleccionar template de experiencia
    experience_text = _pick_experience_template(job)
    education_text  = PROFILE["gob_education_template"]

    return {
        "cover_letter": letter,
        "gob_experience": experience_text,
        "gob_education": education_text,
    }


def _pick_experience_template(job: dict) -> str:
    """Selecciona el template de experiencia según las keywords del trabajo."""
    text = (job.get("title", "") + " " + job.get("description", "")).lower()

    ti_keywords      = ["soporte", "helpdesk", "help desk", "it ", "ti ", "infraestructura",
                        "técnico", "aws", "cloud", "redes", "hardware", "software", "sistemas"]
    rrhh_keywords    = ["rrhh", "recursos humanos", "administración de personal",
                        "remuneraciones", "gestión de personas", "sap"]
    barista_keywords = ["barista", "espresso", "latte", "cappuccino", "cold brew",
                        "filtrado", "cafetería", "café de especialidad", "barra", "molino"]
    garzon_keywords  = ["garzón", "garzon", "mesero", "servicio de mesa", "restaurante",
                        "restaurant", "ayudante de cocina", "mozo", "salón"]
    cs_keywords      = ["atención al cliente", "customer", "ventas", "servicio al cliente",
                        "call center", "soporte cliente"]

    ti_score      = sum(1 for k in ti_keywords      if k in text)
    rrhh_score    = sum(1 for k in rrhh_keywords    if k in text)
    barista_score = sum(1 for k in barista_keywords if k in text)
    garzon_score  = sum(1 for k in garzon_keywords  if k in text)
    cs_score      = sum(1 for k in cs_keywords      if k in text)

    best = max(ti_score, rrhh_score, barista_score, garzon_score, cs_score)
    if best == 0:
        return PROFILE["gob_experience_templates"]["default"]
    if best == barista_score:
        return PROFILE["gob_experience_templates"]["barista"]
    if best == garzon_score:
        return PROFILE["gob_experience_templates"]["garzon"]
    if best == ti_score:
        return PROFILE["gob_experience_templates"]["ti"]
    if best == rrhh_score:
        return PROFILE["gob_experience_templates"]["rrhh"]
    return PROFILE["gob_experience_templates"]["atencion_cliente"]


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    ok = db.delete_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return {"message": "Oferta eliminada"}
