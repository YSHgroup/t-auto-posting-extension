import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.automation_engine import AutomationEngine

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler(interval_minutes: int = 1) -> BackgroundScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler
    _scheduler = BackgroundScheduler()
    engine = AutomationEngine()

    def job():
        try:
            engine.tick()
        except Exception:
            logger.exception("Automation tick failed")

    _scheduler.add_job(job, "interval", minutes=max(1, interval_minutes), id="automation_tick")
    _scheduler.start()
    logger.info("APScheduler started (interval=%sm)", interval_minutes)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
