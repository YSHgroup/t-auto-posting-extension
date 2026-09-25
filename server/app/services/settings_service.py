from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import AISettings, AppSettings, SchedulerSettings
from app.schemas.scheduler import SchedulerUpdate
from app.services.scheduler_service import SchedulerService


class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> dict:
        settings = get_settings()
        ai = self.db.query(AISettings).filter(AISettings.id == 1).first()
        app = self.db.query(AppSettings).filter(AppSettings.id == 1).first()
        sched = self.db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
        return {
            "data_mode": app.data_mode if app else settings.data_mode,
            "ai_provider": ai.provider if ai else settings.ai_provider,
            "openai_model": ai.openai_model if ai else settings.openai_model,
            "anthropic_model": ai.anthropic_model if ai else settings.anthropic_model,
            "minimum_messages": sched.minimum_messages if sched else 20,
            "maximum_posts_per_day": sched.maximum_posts_per_day if sched else 50,
            "posting_interval_minutes": sched.posting_interval_minutes if sched else 30,
            "timezone": sched.timezone if sched else "UTC",
        }

    def update_settings(self, payload: dict) -> dict:
        if payload.get("data_mode") not in (None, "mock"):
            raise ValueError("Only mock data mode is currently implemented")
        scheduler_keys = {
            "minimum_messages",
            "maximum_posts_per_day",
            "posting_interval_minutes",
            "timezone",
        }
        scheduler_payload = {key: payload[key] for key in scheduler_keys if key in payload}
        if scheduler_payload:
            SchedulerService(self.db).update_scheduler(SchedulerUpdate(**scheduler_payload))

        ai = self.db.query(AISettings).filter(AISettings.id == 1).first()
        if not ai:
            ai = AISettings(id=1)
            self.db.add(ai)
        app = self.db.query(AppSettings).filter(AppSettings.id == 1).first()
        if not app:
            app = AppSettings(id=1)
            self.db.add(app)
        sched = self.db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()

        if "ai_provider" in payload:
            ai.provider = payload["ai_provider"]
        if "openai_model" in payload:
            ai.openai_model = payload["openai_model"]
        if "anthropic_model" in payload:
            ai.anthropic_model = payload["anthropic_model"]
        if "data_mode" in payload:
            app.data_mode = payload["data_mode"]
        self.db.commit()
        return self.get_settings()
