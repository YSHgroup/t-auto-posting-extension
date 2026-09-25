from __future__ import annotations
from datetime import UTC, datetime
from app.services.store import DemoStore

class AutomationEngine:
    def __init__(self, store: DemoStore) -> None:
        self.store = store

    def within_schedule(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        settings = self.store.scheduler
        if not settings.auto_mode or current.strftime("%a") not in settings.working_days:
            return False
        return settings.start_time <= current.strftime("%H:%M") <= settings.end_time

    def daily_successes(self) -> int:
        today = datetime.now(UTC).date()
        return sum(item.status == "success" and item.posted_at.date() == today for item in self.store.history)

    def tick(self) -> None:
        if self.store.bot.state != "RUNNING" or not self.within_schedule():
            return
        if self.daily_successes() >= self.store.scheduler.maximum_posts_per_day:
            return
        self.store.run_once()
