from datetime import datetime

from sqlalchemy.orm import Session

from app.models.entities import FeedItem, Group, Notification, Opportunity, Post, PostHistory, Reply
from app.schemas.scheduler import DashboardOut


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> DashboardOut:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return DashboardOut(
            total_groups=self.db.query(Group).count(),
            active_feed_groups=self.db.query(FeedItem).filter(FeedItem.enabled.is_(True)).count(),
            total_posts=self.db.query(Post).count(),
            posts_today=self.db.query(PostHistory)
            .filter(PostHistory.posted_at >= start, PostHistory.status == "success")
            .count(),
            skipped_posts=self.db.query(PostHistory).filter(PostHistory.status == "skipped").count(),
            replies=self.db.query(Reply).count(),
            unread_notifications=self.db.query(Notification).filter(Notification.read.is_(False)).count(),
            potential_investors=self.db.query(Opportunity).filter(Opportunity.category == "investment").count(),
            potential_partners=self.db.query(Opportunity).filter(Opportunity.category == "partnership").count(),
        )
