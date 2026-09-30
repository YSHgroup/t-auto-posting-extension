from sqlalchemy.orm import Session

from app.providers.data.base import DataProvider
from app.providers.data.manual import ManualDataProvider


def get_data_provider(db: Session) -> DataProvider:
    return ManualDataProvider(db)
