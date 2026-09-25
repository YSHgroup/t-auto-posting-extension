from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

def uuid() -> str:
    return str(uuid4())

class GroupModel(Base):
    __tablename__ = "groups"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    username: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)
    member_count: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(80), index=True)
    joined: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    messages: Mapped[list["GroupMessageModel"]] = relationship(cascade="all, delete-orphan")

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    display_name: Mapped[str] = mapped_column(String(200))

class GroupMessageModel(Base):
    __tablename__ = "group_messages"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class PostModel(Base):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uuid)
    title: Mapped[str] = mapped_column(String(200))
    post_type: Mapped[str] = mapped_column(String(40), index=True)
    content: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class FeedItemModel(Base):
    __tablename__ = "feed_items"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), unique=True, index=True)
    selected_post_id: Mapped[str | None] = mapped_column(ForeignKey("posts.id"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    post_count: Mapped[int] = mapped_column(Integer, default=0)

class PostHistoryModel(Base):
    __tablename__ = "post_history"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    post_id: Mapped[str | None] = mapped_column(ForeignKey("posts.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class SchedulerSettingsModel(Base):
    __tablename__ = "scheduler_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    auto_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    start_time: Mapped[str] = mapped_column(String(5), default="09:00")
    end_time: Mapped[str] = mapped_column(String(5), default="20:00")
    working_days: Mapped[str] = mapped_column(String(80), default="Mon,Tue,Wed,Thu,Fri")
    posting_interval: Mapped[int] = mapped_column(Integer, default=30)
    minimum_messages: Mapped[int] = mapped_column(Integer, default=20)
    maximum_posts_per_day: Mapped[int] = mapped_column(Integer, default=25)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")

class BotStateModel(Base):
    __tablename__ = "bot_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    state: Mapped[str] = mapped_column(String(20), default="STOPPED")
    current_feed_index: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class GroupAnalysisModel(Base):
    __tablename__ = "group_analysis"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    payload: Mapped[str] = mapped_column(Text)
    ai_provider: Mapped[str] = mapped_column(String(40))
    ai_model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class OpportunityModel(Base):
    __tablename__ = "opportunities"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    username: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30), index=True)
    evidence: Mapped[str] = mapped_column(Text)
    evidence_level: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

Index("ix_feed_position_enabled", FeedItemModel.position, FeedItemModel.enabled)
Index("ix_history_group_posted", PostHistoryModel.group_id, PostHistoryModel.posted_at)
