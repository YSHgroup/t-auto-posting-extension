"""create core automation tables"""
from alembic import op
from sqlalchemy import inspect
from app.database.models import Base
from app.database.session import engine

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Keep the first migration aligned with the declarative model metadata.
    Base.metadata.create_all(bind=engine)

def downgrade() -> None:
    inspector = inspect(engine)
    for table in reversed(inspector.get_table_names()):
        if table in Base.metadata.tables:
            Base.metadata.tables[table].drop(bind=engine)
