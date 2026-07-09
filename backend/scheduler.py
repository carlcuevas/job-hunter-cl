"""
Scheduler interno para búsqueda automática de ofertas.

Usa APScheduler con zona horaria de Chile (America/Santiago).
El job diario ejecuta run_auto_scrape() a la hora configurada.

IMPORTANTE (Render free tier): el servicio se duerme tras 15 min de
inactividad, por lo que el scheduler interno solo corre mientras la app
está despierta. Para garantizar la ejecución diaria, se recomienda además
un cron externo (cron-job.org) que golpee POST /api/scraper/cron y despierte
el servicio. Ambos mecanismos coexisten sin conflicto.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Santiago")
except Exception:
    TZ = None

_scheduler: AsyncIOScheduler = None
_JOB_ID = "daily_auto_scrape"


def _job_wrapper():
    """Wrapper para lanzar la corrutina de scrape desde el scheduler."""
    from routers.scraper import run_auto_scrape
    asyncio.create_task(run_auto_scrape())


def start_scheduler():
    """Inicia el scheduler y programa el job según la config guardada."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone=TZ) if TZ else AsyncIOScheduler()
    _scheduler.start()
    reschedule()
    print("[Scheduler] Iniciado")
    return _scheduler


def reschedule():
    """(Re)programa el job diario según la configuración actual en DB."""
    global _scheduler
    if _scheduler is None:
        return

    import database as db
    settings = db.get_settings()

    # Quitar job previo si existe
    existing = _scheduler.get_job(_JOB_ID)
    if existing:
        _scheduler.remove_job(_JOB_ID)

    if not settings.get("auto_search_enabled"):
        print("[Scheduler] Búsqueda automática deshabilitada — sin job programado")
        return

    hour = int(settings.get("search_hour", 8))
    minute = int(settings.get("search_minute", 0))

    trigger = CronTrigger(hour=hour, minute=minute, timezone=TZ) if TZ else CronTrigger(hour=hour, minute=minute)
    _scheduler.add_job(
        _job_wrapper,
        trigger=trigger,
        id=_JOB_ID,
        replace_existing=True,
        misfire_grace_time=3600,
    )
    print(f"[Scheduler] Job programado diariamente a las {hour:02d}:{minute:02d} (America/Santiago)")


def get_next_run():
    """Devuelve el próximo horario de ejecución del job, o None."""
    global _scheduler
    if _scheduler is None:
        return None
    job = _scheduler.get_job(_JOB_ID)
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None


def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
