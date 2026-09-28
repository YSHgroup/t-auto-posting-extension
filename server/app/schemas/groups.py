from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

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
    telegram_url: str


class GroupMessageOut(BaseModel):
    id: str
    username: str | None
    content: str
    created_at: datetime
    is_app_post: bool


class SimulatedReplyRequest(BaseModel):
    username: str
    message: str
    post_id: UUID | None = None


class TelegramGroupIntake(BaseModel):
    group_id: str
    group_name: str = ""
    source_url: str = ""
    action: str


class ObservedMessagesRequest(BaseModel):
    messages: list[str] = Field(max_length=500)


class ManualReplyRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=10000)
    post_id: UUID | None = None


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
