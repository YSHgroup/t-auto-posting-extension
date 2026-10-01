from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.entities import (
    Account,
    FeedItem,
    PostAssignment,
    Post,
    ObservedGroupMessage,
    Reply,
    Notification,
    Opportunity,
    GroupAnalysis,
    BotState,
    AISettings,
    AppSettings,
    SchedulerSettings,
)


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def clear_data(self) -> None:
        """Delete most installation-scoped user data but preserve post_history."""
        owner = self.db.info.get("telegram_username")
        if not owner:
            return
        # Delete common installation-scoped tables except PostHistory
        models = [
            FeedItem,
            PostAssignment,
            Post,
            ObservedGroupMessage,
            Reply,
            Notification,
            Opportunity,
            GroupAnalysis,
            BotState,
            AISettings,
            AppSettings,
            SchedulerSettings,
        ]
        for m in models:
            try:
                self.db.query(m).filter(m.owner_id == owner).delete(synchronize_session=False)
            except Exception:
                pass
        self.db.commit()

    def remove_account(self) -> None:
        """Mark the account deleted and clear data (preserve histories).

        This renames the account's username to a 'deleted:' sentinel so future requests
        by the same original username won't match existing installation-scoped rows.
        """
        owner = self.db.info.get("telegram_username")
        if not owner:
            return
        acc = self.db.query(Account).filter(Account.telegram_username == owner).first()
        if not acc:
            return
        # clear installation data but keep post history
        self.clear_data()
        # mark account deleted and rename username
        acc.deleted_at = datetime.utcnow()
        acc.telegram_username = f"deleted:{uuid.uuid4()}"
        self.db.commit()
