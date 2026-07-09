from fastapi import APIRouter, BackgroundTasks
from models import ScrapeRequest
import database as db
import asyncio

router = APIRouter()

_scraping_status = {"running": False, "last_run": None, "last_count": 0, "error": None}


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


async def _do_scrape(request: ScrapeRequest):
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

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                print(f"[Scraper] Error en portal: {result}")

        db.save_jobs_bulk(all_jobs)
        _scraping_status["last_count"] = len(all_jobs)

        from datetime import datetime
        _scraping_status["last_run"] = datetime.utcnow().isoformat()

    except Exception as e:
        _scraping_status["error"] = str(e)
        print(f"[Scraper] Error general: {e}")
    finally:
        _scraping_status["running"] = False
