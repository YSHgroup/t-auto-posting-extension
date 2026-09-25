import copy
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import FeedItem, Group, Post, PostAssignment
from app.providers.ai.factory import get_ai_provider
from app.providers.data.factory import get_data_provider
from app.schemas.posts import PostCreate, PostOut, PostUpdate, RecommendPostRequest, RecommendPostResponse


class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.data = get_data_provider(db)

    def list_posts(self) -> list[PostOut]:
        rows = self.db.query(Post).order_by(Post.created_at.desc()).all()
        return [PostOut.model_validate(r) for r in rows]

    def create(self, payload: PostCreate) -> PostOut:
        row = Post(
            title=payload.title,
            post_type=payload.post_type,
            content=payload.content,
            status=payload.status,
            enabled=payload.enabled,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return PostOut.model_validate(row)

    def get(self, post_id: UUID) -> PostOut:
        row = self.db.query(Post).filter(Post.id == post_id).first()
        if not row:
            raise ValueError("Post not found")
        return PostOut.model_validate(row)

    def update(self, post_id: UUID, payload: PostUpdate) -> PostOut:
        row = self.db.query(Post).filter(Post.id == post_id).first()
        if not row:
            raise ValueError("Post not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return PostOut.model_validate(row)

    def delete(self, post_id: UUID) -> None:
        row = self.db.query(Post).filter(Post.id == post_id).first()
        if not row:
            raise ValueError("Post not found")
        self.db.query(PostAssignment).filter(PostAssignment.post_id == post_id).delete(
            synchronize_session=False
        )
        self.db.delete(row)
        self.db.commit()

    def duplicate(self, post_id: UUID) -> PostOut:
        row = self.db.query(Post).filter(Post.id == post_id).first()
        if not row:
            raise ValueError("Post not found")
        new_row = Post(
            title=f"{row.title} (Copy)",
            post_type=row.post_type,
            content=row.content,
            status=row.status,
            enabled=row.enabled,
        )
        self.db.add(new_row)
        self.db.commit()
        self.db.refresh(new_row)
        return PostOut.model_validate(new_row)

    async def recommend(self, req: RecommendPostRequest) -> RecommendPostResponse:
        item = self.db.query(FeedItem).filter(FeedItem.id == req.feed_item_id).first()
        if not item:
            raise ValueError("Feed item not found")
        group = self.db.query(Group).filter(Group.id == item.group_id).first()
        if not group:
            raise ValueError("Group not found")
        pg = self.data.get_group(group.external_id)
        if not pg:
            raise ValueError("Group not found in provider")
        posts = self.db.query(Post).filter(Post.enabled.is_(True)).all()
        post_dicts = [
            {"id": str(p.id), "title": p.title, "post_type": p.post_type, "content": p.content[:200]}
            for p in posts
        ]
        from app.models.entities import GroupAnalysis

        analysis = (
            self.db.query(GroupAnalysis)
            .filter(GroupAnalysis.group_id == group.id)
            .order_by(GroupAnalysis.created_at.desc())
            .first()
        )
        summary = analysis.summary if analysis else group.description
        ai = get_ai_provider(self.db)
        result = await ai.recommend_post(pg, summary, post_dicts)
        recs = [
            {
                "post_id": r.post_id,
                "reason": r.reason,
                "confidence": round(r.confidence * 100, 1),
            }
            for r in result.recommendations
        ]
        return RecommendPostResponse(
            feed_item_id=item.id,
            group_name=group.name,
            recommendations=recs,
        )
