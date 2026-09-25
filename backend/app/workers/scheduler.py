from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.automation import AutomationEngine
from app.services.store import DemoStore

class SchedulerWorker:
    def __init__(self, store: DemoStore) -> None:
        self.engine = AutomationEngine(store)
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        self.scheduler.add_job(self.engine.tick, "interval", minutes=1, id="automation_tick", replace_existing=True, max_instances=1, coalesce=True)
        self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
