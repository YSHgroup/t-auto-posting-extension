"""scope group metadata by manually entered username

Revision ID: 005
Revises: 004
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("groups", sa.Column("owner_id", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE groups SET owner_id = 'legacy' WHERE owner_id IS NULL"))
    op.alter_column("groups", "owner_id", nullable=False)
    op.create_index("ix_groups_owner_id", "groups", ["owner_id"])
    # 001 created this unique constraint alongside a separate external_id index.
    op.drop_constraint("groups_external_id_key", "groups", type_="unique")
    op.create_unique_constraint(
        "uq_groups_owner_external_id", "groups", ["owner_id", "external_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_groups_owner_external_id", "groups", type_="unique")
    op.create_unique_constraint("groups_external_id_key", "groups", ["external_id"])
    op.drop_index("ix_groups_owner_id", table_name="groups")
    op.drop_column("groups", "owner_id")
