from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4
from app.providers.ai.providers import build_ai_provider
from app.providers.data.mock import MockDataProvider
from app.schemas import BotStatus, Dashboard, FeedItem, GroupAnalysis, HistoryItem, Notification, Opportunity, Post, Reply, SchedulerSettings

class DemoStore:
    def __init__(self) -> None:
        self.data = MockDataProvider()
        self.ai = build_ai_provider()
        self.posts: dict[str, Post] = {}
        self.feed: list[FeedItem] = []
        self.analyses: dict[str, GroupAnalysis] = {}
        self.history: list[HistoryItem] = []
        self.opportunities: list[Opportunity] = []
        self.replies: list[Reply] = []
        self.notifications: list[Notification] = []
        self.scheduler = SchedulerSettings()
        self.bot = BotStatus(state="STOPPED", current_feed_index=0, updated_at=datetime.now(UTC))
        self._seed_posts()
        self._seed_replies()

    def _seed_posts(self) -> None:
        for title, post_type, content in [("Strategic partnership", "Partnership", "We are looking for thoughtful strategic partners to build the next chapter together."), ("Product builders wanted", "Job", "Seeking experienced builders interested in a focused, remote collaboration."), ("Early-stage investment", "Investment", "We are opening a small conversation with investors who understand ambitious technical teams.")]:
            post = Post(id=str(uuid4()), title=title, post_type=post_type, content=content, created_at=datetime.now(UTC))
            self.posts[post.id] = post

    def _seed_replies(self) -> None:
        post_id = next(iter(self.posts))
        group = self.data.groups[0]
        for index, message in enumerate(["I'm interested in learning more about the partnership.", "Would love to compare notes on the integration.", "Can you share a little more about the product?"]):
            reply = Reply(id=f"reply_{index + 1}", group_id=group.id, group_name=group.name, post_id=post_id, username=["alex", "maria_dev", "jordan"][index], message=message, created_at=datetime.now(UTC), read=False)
            self.replies.append(reply)
            self.notifications.append(Notification(id=f"notification_{index + 1}", group_name=group.name, username=reply.username, message=message, post_id=post_id, created_at=reply.created_at, read=False))

    def dashboard(self) -> Dashboard:
        return Dashboard(groups=len(self.data.groups), active_feed=sum(item.enabled for item in self.feed), total_posts=len(self.posts), posts_today=sum(item.status == "success" and item.posted_at.date() == datetime.now(UTC).date() for item in self.history), skipped_posts=sum(item.status == "skipped" for item in self.history), replies=len(self.replies), unread_notifications=sum(not item.read for item in self.notifications), investors=12, partners=19)

    def add_to_feed(self, group_id: str) -> FeedItem:
        group = self.data.get_group(group_id)
        if group is None:
            raise ValueError("Group not found")
        existing = next((item for item in self.feed if item.group.id == group_id), None)
        if existing:
            return existing
        item = FeedItem(id=str(uuid4()), group=group, position=len(self.feed), selected_post_id=next(iter(self.posts), None))
        self.feed.append(item)
        return item

    def run_once(self) -> None:
        if self.bot.state != "RUNNING" or not self.feed:
            return
        item = self.feed[self.bot.current_feed_index % len(self.feed)]
        now = datetime.now(UTC)
        if not item.enabled:
            self.bot.current_feed_index = (self.bot.current_feed_index + 1) % len(self.feed)
            return
        if self.data.messages_since_last_post(item.group.id) < self.scheduler.minimum_messages:
            status = "skipped"
            reason = f"Only {self.data.messages_since_last_post(item.group.id)} messages since previous post. Minimum required: {self.scheduler.minimum_messages}."
            post = None
        else:
            post = self.posts.get(item.selected_post_id or "")
            status = "success" if post else "failed"
            reason = "Mock post published and previous mock post replaced." if post else "No post selected for this feed group."
        self.history.insert(0, HistoryItem(id=str(uuid4()), group_id=item.group.id, group_name=item.group.name, post_id=post.id if post else None, post_title=post.title if post else None, status=status, reason=reason, message_id=f"mock_message_{uuid4().hex[:8]}" if post else None, posted_at=now))
        if post:
            post.usage_count += 1
            item.post_count += 1
            item.last_posted = now
        self.bot.current_feed_index = (self.bot.current_feed_index + 1) % len(self.feed)
        self.bot.updated_at = now
