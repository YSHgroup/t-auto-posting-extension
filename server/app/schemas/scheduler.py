from pydantic import BaseModel

from app.schemas.common import ORMModel


class SchedulerOut(ORMModel):
    auto_mode: bool
    start_time: str
    end_time: str
    working_days: list[int]
    posting_interval_minutes: int
    minimum_messages: int
    maximum_posts_per_day: int
    timezone: str


class SchedulerUpdate(BaseModel):
    auto_mode: bool | None = None
    start_time: str | None = None
    end_time: str | None = None
    working_days: list[int] | None = None
    posting_interval_minutes: int | None = None
    minimum_messages: int | None = None
    maximum_posts_per_day: int | None = None
    timezone: str | None = None


class BotStatusOut(BaseModel):
    state: str
    current_feed_index: int
    last_error: str | None = None


class DashboardOut(BaseModel):
    total_groups: int
    active_feed_groups: int
    total_posts: int
    posts_today: int
    skipped_posts: int
    replies: int
    unread_notifications: int
    potential_investors: int
    potential_partners: int
