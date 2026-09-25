from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def list_notifications(self, filter: str = "all") -> list[dict]:
        q = self.db.query(Notification).order_by(Notification.created_at.desc())
        if filter == "unread":
            q = q.filter(Notification.read.is_(False))
        elif filter == "read":
            q = q.filter(Notification.read.is_(True))
        rows = q.limit(100).all()
        return [
            {
                "id": str(n.id),
                "group_id": str(n.group_id) if n.group_id else None,
                "username": n.username,
                "message": n.message,
                "related_post_id": str(n.related_post_id) if n.related_post_id else None,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in rows
        ]

    def mark_read(self, notification_id: UUID) -> None:
        row = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if row:
            row.read = True
            self.db.commit()

    def mark_all_read(self) -> None:
        for row in self.db.query(Notification).filter(Notification.read.is_(False)).all():
            row.read = True
        self.db.commit()
