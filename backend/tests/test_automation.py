from datetime import UTC, datetime
from app.services.automation import AutomationEngine
from app.services.store import DemoStore

def test_schedule_blocks_when_auto_mode_is_off() -> None:
    store = DemoStore()
    store.scheduler.auto_mode = False
    assert AutomationEngine(store).within_schedule(datetime(2026, 9, 24, 10, 0, tzinfo=UTC)) is False

def test_schedule_accepts_workday_window() -> None:
    store = DemoStore()
    assert AutomationEngine(store).within_schedule(datetime(2026, 9, 24, 10, 0, tzinfo=UTC)) is True

def test_rotation_advances_after_post() -> None:
    store = DemoStore()
    store.add_to_feed("group_001")
    store.add_to_feed("group_002")
    store.bot = store.bot.model_copy(update={"state": "RUNNING"})
    store.run_once()
    assert store.bot.current_feed_index == 1
    assert store.history[0].status == "success"
