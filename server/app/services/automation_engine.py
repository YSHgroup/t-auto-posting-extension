import logging
from datetime import datetime, time

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.entities import BotState, FeedItem, Group, Post, PostAssignment, PostHistory, SchedulerSettings
from app.providers.data.mock import get_data_provider

logger = logging.getLogger(__name__)


class AutomationEngine:
    def __init__(self, db: Session | None = None):
        self._external_db = db

    def _session(self) -> Session:
        if self._external_db:
            return self._external_db
        return SessionLocal()

    def _within_schedule(self, s: SchedulerSettings) -> bool:
        now = datetime.utcnow()
        if now.weekday() not in (s.working_days or []):
            return False
        t = now.time()
        return s.start_time <= t <= s.end_time

    def _posts_today(self, db: Session) -> int:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return db.query(PostHistory).filter(PostHistory.posted_at >= start, PostHistory.status == "success").count()

    def tick(self) -> None:
        db = self._session()
        own = self._external_db is None
        try:
            bot = db.query(BotState).filter(BotState.id == 1).first()
            sched = db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first()
            if not bot or bot.state != "RUNNING":
                return
            if not sched or not sched.auto_mode:
                return
            if not self._within_schedule(sched):
                return
            if self._posts_today(db) >= (sched.maximum_posts_per_day or 50):
                return

            items = (
                db.query(FeedItem)
                .filter(FeedItem.enabled.is_(True))
                .order_by(FeedItem.order_index.asc())
                .all()
            )
            if not items:
                return

            idx = bot.current_feed_index % len(items)
            item = items[idx]
            group = db.query(Group).filter(Group.id == item.group_id).first()
            if not group:
                bot.current_feed_index = (idx + 1) % len(items)
                db.commit()
                return

            data = get_data_provider(db)
            last_app_seq = data.get_last_app_post_sequence(group.external_id)
            latest_seq = data.get_latest_sequence(group.external_id)
            if last_app_seq is None:
                msg_count = latest_seq
            else:
                msg_count = data.count_messages_between(group.external_id, last_app_seq, latest_seq)

            min_msgs = sched.minimum_messages or 20
            assignment = db.query(PostAssignment).filter(PostAssignment.feed_item_id == item.id).first()
            if msg_count < min_msgs:
                db.add(
                    PostHistory(
                        group_id=group.id,
                        post_id=assignment.post_id if assignment else None,
                        feed_item_id=item.id,
                        status="skipped",
                        reason=f"Only {msg_count} messages since previous post. Minimum required: {min_msgs}.",
                    )
                )
                bot.current_feed_index = (idx + 1) % len(items)
                db.commit()
                return

            if not assignment:
                db.add(
                    PostHistory(
                        group_id=group.id,
                        feed_item_id=item.id,
                        status="skipped",
                        reason="No post selected for this feed group.",
                    )
                )
                bot.current_feed_index = (idx + 1) % len(items)
                db.commit()
                return

            post = db.query(Post).filter(Post.id == assignment.post_id, Post.enabled.is_(True)).first()
            if not post:
                db.add(
                    PostHistory(
                        group_id=group.id,
                        post_id=assignment.post_id,
                        feed_item_id=item.id,
                        status="failed",
                        reason="Selected post missing or disabled.",
                    )
                )
                bot.current_feed_index = (idx + 1) % len(items)
                db.commit()
                return

            try:
                msg_id, _seq = data.publish_post(group.external_id, post.content, str(post.id))
                db.add(
                    PostHistory(
                        group_id=group.id,
                        post_id=post.id,
                        feed_item_id=item.id,
                        status="success",
                        message_id=msg_id,
                    )
                )
                post.usage_count += 1
                item.post_count += 1
                item.last_posted_at = datetime.utcnow()
            except Exception as exc:
                logger.exception("Post failed for group %s", group.external_id)
                db.add(
                    PostHistory(
                        group_id=group.id,
                        post_id=post.id,
                        feed_item_id=item.id,
                        status="failed",
                        reason=str(exc),
                    )
                )
                bot.last_error = str(exc)

            bot.current_feed_index = (idx + 1) % len(items)
            db.commit()
        finally:
            if own:
                db.close()
