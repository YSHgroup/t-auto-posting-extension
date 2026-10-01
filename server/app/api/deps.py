from collections.abc import Generator
import uuid

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.identity import normalize_telegram_username
from app.models.entities import Account


def get_installation_db(
    x_telegram_username: str = Header(alias="X-Telegram-Username"),
    x_installation_id: str | None = Header(default=None, alias="X-Installation-ID"),
) -> Generator[Session, None, None]:
    try:
        telegram_username = normalize_telegram_username(x_telegram_username)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    yield from _scoped_db(telegram_username, x_installation_id)


def _scoped_db(telegram_username: str, installation_id: str | None) -> Generator[Session, None, None]:
    db = SessionLocal()
    db.info["telegram_username"] = telegram_username
    account = db.query(Account).filter(Account.telegram_username == telegram_username).first()
    if account is None:
        account = Account(telegram_username=telegram_username)
        db.add(account)
        db.commit()
    db.info["account_id"] = account.id
    if installation_id:
        try:
            db.info["installation_id"] = str(uuid.UUID(installation_id))
        except ValueError:
            db.close()
            raise HTTPException(status_code=400, detail="Invalid installation identity")
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_installation_db"]
