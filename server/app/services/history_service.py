from sqlalchemy.orm import Session

from app.models.entities import Group, Post, PostHistory


class HistoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_history(self, limit: int = 100) -> list[dict]:
        rows = self.db.query(PostHistory).order_by(PostHistory.posted_at.desc()).limit(limit).all()
        out = []
        for h in rows:
            group = self.db.query(Group).filter(Group.id == h.group_id).first()
            post = self.db.query(Post).filter(Post.id == h.post_id).first() if h.post_id else None
            out.append(
                {
                    "id": str(h.id),
                    "group_name": group.name if group else "",
                    "post_title": post.title if post else None,
                    "status": h.status,
                    "message_id": h.message_id,
                    "reason": h.reason,
                    "posted_at": h.posted_at.isoformat(),
                }
            )
        return out
