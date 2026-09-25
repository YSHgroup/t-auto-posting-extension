from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class GroupSearchResult(BaseModel):
    id: str
    name: str
    username: str
    description: str
    member_count: int
    categories: list[str]
    joined: bool
    relevance: float


class GroupDetail(ORMModel):
    id: UUID
    external_id: str
    name: str
    username: str
    description: str
    member_count: int
    categories: list[str]
    joined: bool


class GroupMessageOut(BaseModel):
    id: str
    username: str | None
    content: str
    created_at: datetime
    is_app_post: bool


class GroupAnalysisOut(ORMModel):
    id: UUID
    group_id: UUID
    summary: str
    member_types: list
    activities: list
    partnership_status: str
    partnership_reason: str
    partnership_confidence: float
    job_status: str
    job_reason: str
    job_confidence: float
    posting_style: list
    risks: list
    ai_provider: str
    ai_model: str
    created_at: datetime
