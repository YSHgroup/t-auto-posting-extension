from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class FeedItemCreate(BaseModel):
    group_id: str


class FeedItemUpdate(BaseModel):
    enabled: bool | None = None
    order_index: int | None = None
    post_id: UUID | None = None
    selected_by: str = "user"


class FeedReorderItem(BaseModel):
    id: UUID
    order_index: int


class FeedReorderRequest(BaseModel):
    items: list[FeedReorderItem]


class FeedItemOut(ORMModel):
    id: UUID
    group_id: UUID
    order_index: int
    enabled: bool
    post_count: int
    last_posted_at: datetime | None
    next_scheduled_at: datetime | None
    group_name: str | None = None
    group_external_id: str | None = None
    selected_post_id: UUID | None = None
    selected_post_title: str | None = None
