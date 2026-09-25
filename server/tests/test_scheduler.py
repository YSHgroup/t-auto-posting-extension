from datetime import time

from app.models.entities import BotState, SchedulerSettings
from app.services.automation_engine import AutomationEngine
from test_automation import _setup_feed


def test_outside_working_hours_no_post(db):
    _setup_feed(db)
    sched = db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
    sched.start_time = time(23, 0)
    sched.end_time = time(23, 30)
    db.commit()
    from app.models.entities import PostHistory

    before = db.query(PostHistory).count()
    AutomationEngine(db).tick()
    after = db.query(PostHistory).count()
    assert after == before


def test_inside_working_hours_allowed(db):
    _setup_feed(db)
    sched = db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
    sched.start_time = time(0, 0)
    sched.end_time = time(23, 59)
    db.commit()
    AutomationEngine(db).tick()
    from app.models.entities import PostHistory

    last = db.query(PostHistory).order_by(PostHistory.posted_at.desc()).first()
    assert last is not None
