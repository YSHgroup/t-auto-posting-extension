from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import FeedItem, Group, Post, PostAssignment
from app.providers.data.factory import get_data_provider
from app.schemas.feed import FeedItemCreate, FeedItemOut, FeedItemUpdate, FeedReorderRequest


class FeedService:
    def __init__(self, db: Session):
        self.db = db
        self.data = get_data_provider(db)

    def _to_out(self, item: FeedItem) -> FeedItemOut:
        group = self.db.query(Group).filter(Group.id == item.group_id).first()
        post_id = None
        post_title = None
        if item.assignment:
            post_id = item.assignment.post_id
            post = self.db.query(Post).filter(Post.id == post_id).first()
            post_title = post.title if post else None
        return FeedItemOut(
            id=item.id,
            group_id=item.group_id,
            order_index=item.order_index,
            enabled=item.enabled,
            post_count=item.post_count,
            last_posted_at=item.last_posted_at,
            next_scheduled_at=item.next_scheduled_at,
            group_name=group.name if group else None,
            group_external_id=group.external_id if group else None,
            selected_post_id=post_id,
            selected_post_title=post_title,
        )

    def list_feed(self) -> list[FeedItemOut]:
        items = self.db.query(FeedItem).order_by(FeedItem.order_index.asc()).all()
        return [self._to_out(i) for i in items]

    def add(self, payload: FeedItemCreate) -> FeedItemOut:
        if not self.data.validate_group_id(payload.group_id):
            raise ValueError("Invalid group ID")
        from app.services.group_service import GroupService

        g = GroupService(self.db)._ensure_group(payload.group_id)
        g.joined = True
        existing = self.db.query(FeedItem).filter(FeedItem.group_id == g.id).first()
        if existing:
            return self._to_out(existing)
        max_order = self.db.query(FeedItem).count()
        item = FeedItem(group_id=g.id, order_index=max_order, enabled=True)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self._to_out(item)

    def update(self, item_id: UUID, payload: FeedItemUpdate) -> FeedItemOut:
        item = self.db.query(FeedItem).filter(FeedItem.id == item_id).first()
        if not item:
            raise ValueError("Feed item not found")
        if payload.enabled is not None:
            item.enabled = payload.enabled
        if payload.order_index is not None:
            item.order_index = payload.order_index
        if payload.post_id is not None:
            post = self.db.query(Post).filter(Post.id == payload.post_id).first()
            if not post:
                raise ValueError("Post not found")
            if not post.enabled or post.status != "Active":
                raise ValueError("Post is not active")
            assignment = item.assignment
            if assignment:
                assignment.post_id = payload.post_id
                assignment.selected_by = payload.selected_by
            else:
                self.db.add(
                    PostAssignment(
                        feed_item_id=item.id,
                        post_id=payload.post_id,
                        selected_by=payload.selected_by,
                    )
                )
        self.db.commit()
        self.db.refresh(item)
        return self._to_out(item)

    def delete(self, item_id: UUID) -> None:
        item = self.db.query(FeedItem).filter(FeedItem.id == item_id).first()
        if not item:
            raise ValueError("Feed item not found")
        if item.assignment:
            self.db.delete(item.assignment)
        self.db.delete(item)
        self._reindex()
        self.db.commit()

    def reorder(self, req: FeedReorderRequest) -> list[FeedItemOut]:
        for entry in req.items:
            item = self.db.query(FeedItem).filter(FeedItem.id == entry.id).first()
            if item:
                item.order_index = entry.order_index
        self.db.commit()
        return self.list_feed()

    def _reindex(self) -> None:
        items = self.db.query(FeedItem).order_by(FeedItem.order_index.asc()).all()
        for i, item in enumerate(items):
            item.order_index = i
