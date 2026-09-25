from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

PostType = Literal["Partnership", "Job", "Investment", "Business", "General", "Custom"]
BotState = Literal["STOPPED", "RUNNING", "PAUSED", "ERROR"]

class Group(BaseModel):
    id: str
    name: str
    username: str
    description: str
    member_count: int
    category: str
    keywords: list[str]
    joined: bool = False

class GroupMessage(BaseModel):
    id: str
    group_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime

class Suitability(BaseModel):
    status: Literal["suitable", "possibly_suitable", "not_recommended", "insufficient_information"]
    reason: str
    confidence: float = Field(ge=0, le=1)

class GroupAnalysis(BaseModel):
    id: str
    group_id: str
    activities: list[str]
    member_types: list[str]
    partnership: Suitability
    job: Suitability
    posting_style: list[str]
    risks: list[str]
    ai_provider: str
    ai_model: str
    created_at: datetime

class Post(BaseModel):
    id: str
    title: str
    post_type: PostType
    content: str
    enabled: bool = True
    usage_count: int = 0
    created_at: datetime

class FeedItem(BaseModel):
    id: str
    group: Group
    position: int
    enabled: bool = True
    selected_post_id: str | None = None
    last_posted: datetime | None = None
    post_count: int = 0
    next_scheduled_time: str = "Ready"

class HistoryItem(BaseModel):
    id: str
    group_id: str
    group_name: str
    post_id: str | None
    post_title: str | None
    status: Literal["success", "skipped", "failed"]
    reason: str
    message_id: str | None
    posted_at: datetime

class SchedulerSettings(BaseModel):
    auto_mode: bool = True
    start_time: str = "09:00"
    end_time: str = "20:00"
    working_days: list[str] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    posting_interval: int = 30
    minimum_messages: int = 20
    maximum_posts_per_day: int = 25
    timezone: str = "UTC"

class BotStatus(BaseModel):
    state: BotState
    current_feed_index: int
    updated_at: datetime

class Opportunity(BaseModel):
    id: str
    group_id: str
    group_name: str
    username: str
    category: Literal["investment", "partnership"]
    evidence: str
    evidence_level: Literal["explicit", "strong_indication", "possible", "insufficient"]
    confidence: float = Field(ge=0, le=1)

class Reply(BaseModel):
    id: str
    group_id: str
    group_name: str
    post_id: str
    username: str
    message: str
    created_at: datetime
    read: bool = False

class Notification(BaseModel):
    id: str
    group_name: str
    username: str
    message: str
    post_id: str
    created_at: datetime
    read: bool = False

class Dashboard(BaseModel):
    groups: int
    active_feed: int
    total_posts: int
    posts_today: int
    skipped_posts: int
    replies: int
    unread_notifications: int
    investors: int
    partners: int
