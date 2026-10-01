from sqlalchemy.orm import Session

from app.providers.data.base import DataProvider
from app.providers.data.manual import ManualDataProvider
from app.providers.data.mock import MockDataProvider
from app.core.config import get_settings


def get_data_provider(db: Session) -> DataProvider:
    settings = get_settings()
    mode = (settings.data_mode or "manual").lower()
    if mode == "mock":
        return MockDataProvider(db)
    # default to manual provider which requires manual imports and does not support automation
    return ManualDataProvider(db)
