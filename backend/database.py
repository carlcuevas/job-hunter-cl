"""
Base de datos simple usando JSON en disco.
En producción se puede reemplazar por SQLite o PostgreSQL.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
JOBS_FILE = os.path.join(DB_DIR, "jobs.json")
APPLICATIONS_FILE = os.path.join(DB_DIR, "applications.json")
SETTINGS_FILE = os.path.join(DB_DIR, "settings.json")

# Configuración por defecto de la búsqueda automática
DEFAULT_SETTINGS = {
    "auto_search_enabled": False,
    "search_hour": 8,          # hora del día (0-23), zona horaria de Chile
    "search_minute": 0,
    "portals": ["computrabajo", "getonboard", "chiletrabajos"],
    "limit": 60,
    "last_auto_run": None,
}


def _ensure_db():
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.path.exists(JOBS_FILE):
        _write(JOBS_FILE, {})
    if not os.path.exists(APPLICATIONS_FILE):
        _write(APPLICATIONS_FILE, {})


def _read(filepath: str) -> Dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write(filepath: str, data: Dict):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ── JOBS ──────────────────────────────────────────────────────────────────────

def get_all_jobs() -> List[Dict]:
    _ensure_db()
    data = _read(JOBS_FILE)
    jobs = list(data.values())
    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return jobs


def get_job(job_id: str) -> Optional[Dict]:
    _ensure_db()
    data = _read(JOBS_FILE)
    return data.get(job_id)


def save_job(job: Dict):
    _ensure_db()
    data = _read(JOBS_FILE)
    data[job["id"]] = job
    _write(JOBS_FILE, data)


def save_jobs_bulk(jobs: List[Dict]):
    _ensure_db()
    data = _read(JOBS_FILE)
    for job in jobs:
        # No sobreescribir si ya fue guardada/postulada/descartada
        existing = data.get(job["id"])
        if existing and existing.get("status") in ("guardada", "postulada", "descartada"):
            continue
        data[job["id"]] = job
    _write(JOBS_FILE, data)


def update_job_status(job_id: str, status: str) -> bool:
    _ensure_db()
    data = _read(JOBS_FILE)
    if job_id not in data:
        return False
    data[job_id]["status"] = status
    _write(JOBS_FILE, data)
    return True


def update_job_cover_letter(job_id: str, cover_letter: str, gob_experience: str = "", gob_education: str = "") -> bool:
    _ensure_db()
    data = _read(JOBS_FILE)
    if job_id not in data:
        return False
    data[job_id]["cover_letter"]   = cover_letter
    data[job_id]["gob_experience"] = gob_experience
    data[job_id]["gob_education"]  = gob_education
    _write(JOBS_FILE, data)
    return True


def delete_job(job_id: str) -> bool:
    _ensure_db()
    data = _read(JOBS_FILE)
    if job_id not in data:
        return False
    del data[job_id]
    _write(JOBS_FILE, data)
    return True


# ── APPLICATIONS ──────────────────────────────────────────────────────────────

def get_all_applications() -> List[Dict]:
    _ensure_db()
    data = _read(APPLICATIONS_FILE)
    apps = list(data.values())
    apps.sort(key=lambda x: x.get("applied_at", ""), reverse=True)
    return apps


def get_application(app_id: str) -> Optional[Dict]:
    _ensure_db()
    data = _read(APPLICATIONS_FILE)
    return data.get(app_id)


def save_application(application: Dict):
    _ensure_db()
    data = _read(APPLICATIONS_FILE)
    data[application["id"]] = application
    _write(APPLICATIONS_FILE, data)


def update_application(app_id: str, updates: Dict) -> bool:
    _ensure_db()
    data = _read(APPLICATIONS_FILE)
    if app_id not in data:
        return False
    data[app_id].update(updates)
    _write(APPLICATIONS_FILE, data)
    return True


def get_stats() -> Dict:
    _ensure_db()
    jobs = get_all_jobs()
    apps = get_all_applications()

    return {
        "total_jobs": len(jobs),
        "new_jobs": sum(1 for j in jobs if j.get("status") == "nueva"),
        "saved_jobs": sum(1 for j in jobs if j.get("status") == "guardada"),
        "applied_jobs": sum(1 for j in jobs if j.get("status") == "postulada"),
        "total_applications": len(apps),
        "interviews": sum(1 for a in apps if a.get("status") == "entrevista"),
        "offers": sum(1 for a in apps if a.get("status") == "oferta"),
        "avg_score": round(
            sum(j.get("match_score", 0) for j in jobs) / len(jobs), 1
        ) if jobs else 0,
    }



# ── SETTINGS (configuración de búsqueda automática) ────────────────────────────

def get_settings() -> Dict:
    _ensure_db()
    if not os.path.exists(SETTINGS_FILE):
        _write(SETTINGS_FILE, DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    data = _read(SETTINGS_FILE)
    # Rellenar claves faltantes con defaults
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data or {})
    return merged


def update_settings(updates: Dict) -> Dict:
    _ensure_db()
    settings = get_settings()
    for k, v in updates.items():
        if k in DEFAULT_SETTINGS or k == "last_auto_run":
            settings[k] = v
    _write(SETTINGS_FILE, settings)
    return settings
