"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(255)),
        sa.Column("username", sa.String(128)),
        sa.Column("description", sa.Text()),
        sa.Column("member_count", sa.Integer()),
        sa.Column("categories", postgresql.JSONB()),
        sa.Column("keywords", postgresql.JSONB()),
        sa.Column("joined", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_groups_external_id", "groups", ["external_id"])
    op.create_index("ix_groups_username", "groups", ["username"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(64), unique=True),
        sa.Column("username", sa.String(128)),
        sa.Column("display_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255)),
        sa.Column("post_type", sa.String(32)),
        sa.Column("content", sa.Text()),
        sa.Column("status", sa.String(16)),
        sa.Column("usage_count", sa.Integer()),
        sa.Column("enabled", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "group_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("external_message_id", sa.String(64)),
        sa.Column("user_id", sa.String(64)),
        sa.Column("username", sa.String(128)),
        sa.Column("content", sa.Text()),
        sa.Column("is_app_post", sa.Boolean()),
        sa.Column("app_post_id", postgresql.UUID(as_uuid=True)),
        sa.Column("replaced", sa.Boolean()),
        sa.Column("sequence_num", sa.Integer()),
        sa.Column("created_at", sa.DateTime()),
        sa.UniqueConstraint("group_id", "external_message_id", name="uq_group_message"),
    )

    op.create_table(
        "group_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("summary", sa.Text()),
        sa.Column("member_types", postgresql.JSONB()),
        sa.Column("activities", postgresql.JSONB()),
        sa.Column("partnership_status", sa.String(32)),
        sa.Column("partnership_reason", sa.Text()),
        sa.Column("partnership_confidence", sa.Float()),
        sa.Column("job_status", sa.String(32)),
        sa.Column("job_reason", sa.Text()),
        sa.Column("job_confidence", sa.Float()),
        sa.Column("posting_style", postgresql.JSONB()),
        sa.Column("risks", postgresql.JSONB()),
        sa.Column("ai_provider", sa.String(32)),
        sa.Column("ai_model", sa.String(64)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "feed_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("order_index", sa.Integer()),
        sa.Column("enabled", sa.Boolean()),
        sa.Column("post_count", sa.Integer()),
        sa.Column("last_posted_at", sa.DateTime()),
        sa.Column("next_scheduled_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "post_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feed_items.id"), unique=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id")),
        sa.Column("selected_by", sa.String(16)),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "post_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id")),
        sa.Column("feed_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feed_items.id")),
        sa.Column("status", sa.String(16)),
        sa.Column("message_id", sa.String(64)),
        sa.Column("reason", sa.Text()),
        sa.Column("posted_at", sa.DateTime()),
    )

    op.create_table(
        "replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id")),
        sa.Column("user_id", sa.String(64)),
        sa.Column("username", sa.String(128)),
        sa.Column("message", sa.Text()),
        sa.Column("read", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("user_id", sa.String(64)),
        sa.Column("username", sa.String(128)),
        sa.Column("message", sa.Text()),
        sa.Column("related_post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id")),
        sa.Column("read", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "scheduler_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("auto_mode", sa.Boolean()),
        sa.Column("start_time", sa.Time()),
        sa.Column("end_time", sa.Time()),
        sa.Column("working_days", postgresql.JSONB()),
        sa.Column("posting_interval_minutes", sa.Integer()),
        sa.Column("minimum_messages", sa.Integer()),
        sa.Column("maximum_posts_per_day", sa.Integer()),
        sa.Column("timezone", sa.String(64)),
    )

    op.create_table(
        "bot_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state", sa.String(16)),
        sa.Column("current_feed_index", sa.Integer()),
        sa.Column("last_error", sa.Text()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id")),
        sa.Column("user_id", sa.String(64)),
        sa.Column("username", sa.String(128)),
        sa.Column("category", sa.String(32)),
        sa.Column("evidence", sa.Text()),
        sa.Column("evidence_level", sa.String(32)),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32)),
        sa.Column("openai_model", sa.String(64)),
        sa.Column("anthropic_model", sa.String(64)),
    )

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data_mode", sa.String(16)),
    )


def downgrade() -> None:
    for table in (
        "app_settings",
        "ai_settings",
        "opportunities",
        "bot_state",
        "scheduler_settings",
        "notifications",
        "replies",
        "post_history",
        "post_assignments",
        "feed_items",
        "group_analysis",
        "group_messages",
        "posts",
        "users",
        "groups",
    ):
        op.drop_table(table)
