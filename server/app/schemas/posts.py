from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    post_type: str
    content: str = Field(min_length=1)
    status: str = "Active"
    enabled: bool = True


class PostUpdate(BaseModel):
    title: str | None = None
    post_type: str | None = None
    content: str | None = None
    status: str | None = None
    enabled: bool | None = None


class PostOut(ORMModel):
    id: UUID
    title: str
    post_type: str
    content: str
    status: str
    usage_count: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class RecommendPostRequest(BaseModel):
    feed_item_id: UUID


class RecommendPostResponse(BaseModel):
    feed_item_id: UUID
    group_name: str
    recommendations: list[dict]
