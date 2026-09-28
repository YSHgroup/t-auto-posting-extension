from collections.abc import Generator

from sqlalchemy import String, create_engine, event
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker, with_loader_criteria

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InstallationScoped:
    """Mixin for application records owned by one extension installation."""

    owner_id: Mapped[str] = mapped_column(String(64), index=True)


@event.listens_for(Session, "do_orm_execute")
def scope_installation_queries(execute_state):
    if not (
        execute_state.is_select or execute_state.is_update or execute_state.is_delete
    ) or execute_state.execution_options.get("skip_owner_scope"):
        return
    owner_id = execute_state.session.info.get("installation_id", "legacy")
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            InstallationScoped,
            lambda model: model.owner_id == owner_id,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def assign_installation_owner(session: Session, _flush_context, _instances) -> None:
    owner_id = session.info.get("installation_id", "legacy")
    for instance in session.new:
        if isinstance(instance, InstallationScoped) and not getattr(instance, "owner_id", None):
            instance.owner_id = owner_id


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
