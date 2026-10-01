"""mark existing catalog rows as legacy and switch to manual data

Revision ID: 003
Revises: 002
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("data_origin", sa.String(length=16), nullable=False, server_default="legacy"),
    )
    op.create_index("ix_groups_data_origin", "groups", ["data_origin"])
    op.execute(sa.text("UPDATE app_settings SET data_mode = 'manual'"))


def downgrade() -> None:
    op.drop_index("ix_groups_data_origin", table_name="groups")
    op.drop_column("groups", "data_origin")
