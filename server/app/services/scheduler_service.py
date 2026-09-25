from datetime import datetime, time
from zoneinfo import ZoneInfo

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
        start_time = s.start_time
        end_time = s.end_time
        if "start_time" in data and data["start_time"]:
            try:
                h, m = data["start_time"].split(":")
                start_time = time(int(h), int(m))
            except (ValueError, TypeError) as exc:
                raise ValueError("Time must use HH:MM format") from exc
            del data["start_time"]
        if "end_time" in data and data["end_time"]:
            try:
                h, m = data["end_time"].split(":")
                end_time = time(int(h), int(m))
            except (ValueError, TypeError) as exc:
                raise ValueError("Time must use HH:MM format") from exc
            del data["end_time"]
        if start_time >= end_time:
            raise ValueError("End time must be later than start time")
        if "working_days" in data and any(day not in range(7) for day in data["working_days"]):
            raise ValueError("Working days must be between 0 and 6")
        if data.get("posting_interval_minutes", s.posting_interval_minutes) < 1:
            raise ValueError("Posting interval must be at least 1 minute")
        if data.get("minimum_messages", s.minimum_messages) < 0:
            raise ValueError("Minimum messages cannot be negative")
        if data.get("maximum_posts_per_day", s.maximum_posts_per_day) < 1:
            raise ValueError("Maximum posts per day must be at least 1")
        if "timezone" in data:
            try:
                ZoneInfo(data["timezone"])
            except (KeyError, ValueError) as exc:
                raise ValueError("Invalid timezone") from exc
            s.start_time = start_time
            s.end_time = end_time
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
