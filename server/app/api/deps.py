from collections.abc import Generator

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.identity import normalize_installation_id


def get_installation_db(
    x_installation_id: str = Header(alias="X-Installation-ID"),
) -> Generator[Session, None, None]:
    try:
        installation_id = normalize_installation_id(x_installation_id)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid installation identity") from exc

    yield from _scoped_db(installation_id)


def _scoped_db(installation_id: str) -> Generator[Session, None, None]:
    db = SessionLocal()
    db.info["installation_id"] = installation_id
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_installation_db"]
