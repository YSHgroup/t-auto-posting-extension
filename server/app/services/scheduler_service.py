from datetime import datetime, time

from sqlalchemy.orm import Session

from app.models.entities import BotState, SchedulerSettings
from app.schemas.scheduler import BotStatusOut, SchedulerOut, SchedulerUpdate


class SchedulerService:
    def __init__(self, db: Session):
        self.db = db

    def _get_scheduler(self) -> SchedulerSettings:
        row = self.db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
        if not row:
            row = SchedulerSettings(id=1)
            self.db.add(row)
            self.db.commit()
        return row

    def _get_bot(self) -> BotState:
        row = self.db.query(BotState).filter(BotState.id == 1).first()
        if not row:
            row = BotState(id=1)
            self.db.add(row)
            self.db.commit()
        return row

    def get_scheduler(self) -> SchedulerOut:
        s = self._get_scheduler()
        return SchedulerOut(
            auto_mode=s.auto_mode,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            working_days=list(s.working_days or []),
            posting_interval_minutes=s.posting_interval_minutes,
            minimum_messages=s.minimum_messages,
            maximum_posts_per_day=s.maximum_posts_per_day,
            timezone=s.timezone,
        )

    def update_scheduler(self, payload: SchedulerUpdate) -> SchedulerOut:
        s = self._get_scheduler()
        data = payload.model_dump(exclude_unset=True)
        if "start_time" in data and data["start_time"]:
            h, m = data["start_time"].split(":")
            s.start_time = time(int(h), int(m))
            del data["start_time"]
        if "end_time" in data and data["end_time"]:
            h, m = data["end_time"].split(":")
            s.end_time = time(int(h), int(m))
            del data["end_time"]
        for k, v in data.items():
            setattr(s, k, v)
        self.db.commit()
        return self.get_scheduler()

    def bot_status(self) -> BotStatusOut:
        b = self._get_bot()
        return BotStatusOut(state=b.state, current_feed_index=b.current_feed_index, last_error=b.last_error)

    def start_bot(self) -> BotStatusOut:
        b = self._get_bot()
        b.state = "RUNNING"
        b.last_error = None
        b.updated_at = datetime.utcnow()
        self.db.commit()
        return self.bot_status()

    def stop_bot(self) -> BotStatusOut:
        b = self._get_bot()
        b.state = "STOPPED"
        b.updated_at = datetime.utcnow()
        self.db.commit()
        return self.bot_status()
