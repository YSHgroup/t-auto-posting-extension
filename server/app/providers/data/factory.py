from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import AppSettings
from app.providers.data.base import DataProvider
from app.providers.data.mock import MockDataProvider


def get_data_provider(db: Session) -> DataProvider:
    configured = db.query(AppSettings).filter(AppSettings.id == 1).first()
    mode = configured.data_mode if configured else get_settings().data_mode
    if mode == "mock":
        return MockDataProvider(db)
    raise ValueError(f"Data provider mode '{mode}' is not implemented; use 'mock'")
