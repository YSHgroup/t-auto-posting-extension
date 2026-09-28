"""scope user-owned rows to an extension installation

Revision ID: 002
Revises: 001
Create Date: 2026-09-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OWNED_TABLES = (
    "group_analysis",
    "posts",
    "feed_items",
    "post_assignments",
    "post_history",
    "replies",
    "notifications",
    "scheduler_settings",
    "bot_state",
    "opportunities",
    "ai_settings",
    "app_settings",
)
SINGLETON_TABLES = ("scheduler_settings", "bot_state", "ai_settings", "app_settings")


def upgrade() -> None:
    for table in OWNED_TABLES:
        op.add_column(table, sa.Column("owner_id", sa.String(length=64), nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET owner_id = 'legacy' WHERE owner_id IS NULL"))
        op.alter_column(table, "owner_id", nullable=False)
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])

    for table in SINGLETON_TABLES:
        op.alter_column(table, "id", type_=sa.BigInteger(), existing_type=sa.Integer())

    op.add_column(
        "groups",
        sa.Column("telegram_url", sa.String(length=2048), nullable=False, server_default=""),
    )

    op.create_table(
        "skipped_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "group_id", name="uq_skipped_group_owner_group"),
    )
    op.create_index("ix_skipped_groups_owner_id", "skipped_groups", ["owner_id"])
    op.create_index("ix_skipped_groups_group_id", "skipped_groups", ["group_id"])
    op.create_index("ix_skipped_groups_created_at", "skipped_groups", ["created_at"])
    op.create_table(
        "observed_group_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "group_id", "sequence_num", name="uq_observed_group_sequence"),
    )
    op.create_index("ix_observed_group_messages_owner_id", "observed_group_messages", ["owner_id"])
    op.create_index("ix_observed_group_messages_group_id", "observed_group_messages", ["group_id"])
    op.create_index("ix_observed_group_messages_created_at", "observed_group_messages", ["created_at"])
    op.create_unique_constraint(
        "uq_feed_items_owner_group", "feed_items", ["owner_id", "group_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_feed_items_owner_group", "feed_items", type_="unique")
    op.drop_table("skipped_groups")
    op.drop_table("observed_group_messages")
    op.drop_column("groups", "telegram_url")
    for table in reversed(SINGLETON_TABLES):
        op.alter_column(table, "id", type_=sa.Integer(), existing_type=sa.BigInteger())
    for table in reversed(OWNED_TABLES):
        op.drop_index(f"ix_{table}_owner_id", table_name=table)
        op.drop_column(table, "owner_id")
