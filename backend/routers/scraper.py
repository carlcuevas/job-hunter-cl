from fastapi import APIRouter, BackgroundTasks
from models import ScrapeRequest
import database as db
import asyncio
from datetime import datetime

router = APIRouter()

_scraping_status = {"running": False, "last_run": None, "last_count": 0, "error": None}


def get_status_dict():
    return _scraping_status


@router.post("/run")
async def run_scraper(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Lanza el scraper en background."""
    if _scraping_status["running"]:
        return {"message": "El scraper ya está corriendo", "status": _scraping_status}

    background_tasks.add_task(_do_scrape, request)
    return {"message": "Scraping iniciado", "portals": request.portals}


@router.get("/status")
async def get_status():
    return _scraping_status


# ── Configuración de búsqueda automática ───────────────────────────────────────

@router.get("/schedule")
async def get_schedule():
    """Devuelve la configuración actual de búsqueda automática."""
    settings = db.get_settings()
    next_run = None
    try:
        from scheduler import get_next_run
        next_run = get_next_run()
    except Exception:
        pass
    return {**settings, "next_run": next_run}


@router.post("/schedule")
async def update_schedule(payload: dict):
    """Actualiza la configuración de búsqueda automática y reprograma el job."""
    settings = db.update_settings(payload)
    # Reprogramar el scheduler con la nueva config
    try:
        from scheduler import reschedule
        reschedule()
    except Exception as e:
        print(f"[Scheduler] No se pudo reprogramar: {e}")
    return {"message": "Configuración actualizada", "settings": settings}


@router.post("/cron")
async def cron_trigger(background_tasks: BackgroundTasks):
    """
    Endpoint para disparar la búsqueda desde un cron EXTERNO (ej: cron-job.org).
    Útil en Render free: el request 'despierta' el servicio y ejecuta el scrape.
    Solo corre si la búsqueda automática está habilitada.
    """
    settings = db.get_settings()
    if not settings.get("auto_search_enabled"):
        return {"message": "Búsqueda automática deshabilitada", "ran": False}
    if _scraping_status["running"]:
        return {"message": "Ya hay un scrape en curso", "ran": False}

    req = ScrapeRequest(
        portals=settings.get("portals", ["computrabajo", "getonboard", "chiletrabajos"]),
        limit=settings.get("limit", 60),
    )
    background_tasks.add_task(_do_scrape, req, True)
    return {"message": "Búsqueda automática iniciada", "ran": True, "portals": req.portals}


async def _do_scrape(request: ScrapeRequest, is_auto: bool = False):
    global _scraping_status
    _scraping_status["running"] = True
    _scraping_status["error"] = None

    all_jobs = []

    try:
        tasks = []

        if "laborum" in request.portals:
            from scrapers.laborum import scrape as scrape_laborum
            tasks.append(scrape_laborum(limit=request.limit, keywords=request.keywords))

        if "getonboard" in request.portals:
            from scrapers.getonboard import scrape as scrape_getonboard
            tasks.append(scrape_getonboard(limit=request.limit, keywords=request.keywords))

        if "chiletrabajos" in request.portals:
            from scrapers.chiletrabajos import scrape as scrape_chiletrabajos
            tasks.append(scrape_chiletrabajos(limit=request.limit, keywords=request.keywords))

        if "computrabajo" in request.portals:
            from scrapers.computrabajo import scrape as scrape_computrabajo
            tasks.append(scrape_computrabajo(limit=request.limit, keywords=request.keywords))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                print(f"[Scraper] Error en portal: {result}")

        # Deduplicar ofertas repetidas entre portales
        from dedup import deduplicate, dedup_stats
        before = len(all_jobs)
        all_jobs = deduplicate(all_jobs)
        after = len(all_jobs)
        print(f"[Scraper] Dedup: {before} → {after} ({before - after} duplicados)")

        db.save_jobs_bulk(all_jobs)
        _scraping_status["last_count"] = len(all_jobs)
        _scraping_status["dedup"] = dedup_stats(before, after)
        _scraping_status["last_run"] = datetime.utcnow().isoformat()

        if is_auto:
            db.update_settings({"last_auto_run": _scraping_status["last_run"]})
            print(f"[Scraper] Búsqueda AUTOMÁTICA completada: {after} ofertas")

    except Exception as e:
        _scraping_status["error"] = str(e)
        print(f"[Scraper] Error general: {e}")
    finally:
        _scraping_status["running"] = False


async def run_auto_scrape():
    """Ejecuta un scrape automático usando la configuración guardada. Llamado por el scheduler."""
    settings = db.get_settings()
    if not settings.get("auto_search_enabled"):
        return
    if _scraping_status["running"]:
        return
    req = ScrapeRequest(
        portals=settings.get("portals", ["computrabajo", "getonboard", "chiletrabajos"]),
        limit=settings.get("limit", 60),
    )
    await _do_scrape(req, is_auto=True)
