from datetime import datetime, time

from app.models.entities import BotState, FeedItem, Group, Post, PostAssignment, SchedulerSettings
from app.services.automation_engine import AutomationEngine


def _setup_feed(db, external_id: str = "group_001"):
    group = db.query(Group).filter(Group.external_id == external_id).first()
    post = Post(
        title="Test",
        post_type="Partnership",
        content="Hello partners",
        status="Active",
        enabled=True,
    )
    db.add(post)
    db.flush()
    item = FeedItem(group_id=group.id, order_index=0, enabled=True)
    db.add(item)
    db.flush()
    db.add(PostAssignment(feed_item_id=item.id, post_id=post.id, selected_by="user"))
    sched = db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
    sched.auto_mode = True
    sched.minimum_messages = 20
    sched.working_days = [0, 1, 2, 3, 4, 5, 6]
    sched.start_time = time(0, 0)
    sched.end_time = time(23, 59)
    sched.maximum_posts_per_day = 100
    bot = db.query(BotState).filter(BotState.id == 1).first()
    bot.state = "RUNNING"
    bot.current_feed_index = 0
    db.commit()
    return item, post


def test_skip_when_fewer_than_minimum_messages(db):
    from app.models.entities import GroupMessage

    group = db.query(Group).filter(Group.external_id == "group_001").first()
    # Collapse message gap: set all non-app messages after app post to only 15
    app = (
        db.query(GroupMessage)
        .filter(GroupMessage.group_id == group.id, GroupMessage.is_app_post.is_(True))
        .first()
    )
    db.query(GroupMessage).filter(
        GroupMessage.group_id == group.id,
        GroupMessage.sequence_num > app.sequence_num,
    ).delete()
    for i in range(15):
        db.add(
            GroupMessage(
                group_id=group.id,
                external_message_id=f"msg_gap_{i}",
                username="test",
                content="filler",
                sequence_num=app.sequence_num + i + 1,
            )
        )
    db.commit()
    _setup_feed(db)
    AutomationEngine(db).tick()
    from app.models.entities import PostHistory

    last = db.query(PostHistory).order_by(PostHistory.posted_at.desc()).first()
    assert last.status == "skipped"


def test_post_when_enough_messages(db):
    _setup_feed(db)
    AutomationEngine(db).tick()
    from app.models.entities import PostHistory

    last = db.query(PostHistory).order_by(PostHistory.posted_at.desc()).first()
    assert last.status == "success"


def test_bot_stopped_no_post(db):
    _setup_feed(db)
    bot = db.query(BotState).filter(BotState.id == 1).first()
    bot.state = "STOPPED"
    db.commit()
    before = db.query(__import__("app.models.entities", fromlist=["PostHistory"]).PostHistory).count()
    AutomationEngine(db).tick()
    after = db.query(__import__("app.models.entities", fromlist=["PostHistory"]).PostHistory).count()
    assert after == before


def test_feed_rotation(db):
    group2 = db.query(Group).filter(Group.external_id == "group_002").first()
    item1, _ = _setup_feed(db)
    item2 = FeedItem(group_id=group2.id, order_index=1, enabled=True)
    db.add(item2)
    db.commit()
    bot = db.query(BotState).filter(BotState.id == 1).first()
    assert bot.current_feed_index == 0
    AutomationEngine(db).tick()
    db.refresh(bot)
    assert bot.current_feed_index == 1
