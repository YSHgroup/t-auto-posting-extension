from sqlalchemy.orm import Session

from app.models.entities import Group, ObservedGroupMessage
from app.providers.data.base import DataProvider, ProviderGroup, ProviderMessage


class ManualDataProvider:
    """Uses only groups and message text explicitly supplied by this installation."""

    supports_automation = False

    def __init__(self, db: Session):
        self.db = db

    def search_groups(
        self, query: str, exclude_external_ids: set[str], limit: int = 50
    ) -> list[tuple[ProviderGroup, float]]:
        # There is no live Telegram search integration. Users add groups directly.
        return []

    def get_group(self, group_id: str) -> ProviderGroup | None:
        group = (
            self.db.query(Group)
            .filter(Group.external_id == group_id, Group.data_origin == "manual")
            .first()
        )
        if not group:
            return None
        return ProviderGroup(
            id=group.external_id,
            name=group.name,
            username=group.username,
            description=group.description,
            member_count=group.member_count,
            categories=list(group.categories or []),
            keywords=list(group.keywords or []),
            joined=group.joined,
        )

    def validate_group_id(self, group_id: str) -> bool:
        return self.get_group(group_id) is not None

    def get_messages(
        self, group_id: str, limit: int = 100, after_sequence: int | None = None
    ) -> list[ProviderMessage]:
        group = (
            self.db.query(Group)
            .filter(Group.external_id == group_id, Group.data_origin == "manual")
            .first()
        )
        if not group:
            return []
        query = self.db.query(ObservedGroupMessage).filter(
            ObservedGroupMessage.group_id == group.id
        )
        if after_sequence is not None:
            query = query.filter(ObservedGroupMessage.sequence_num > after_sequence)
        rows = (
            query.order_by(ObservedGroupMessage.sequence_num.desc())
            .limit(min(max(limit, 0), 500))
            .all()
        )
        rows.reverse()
        return [
            ProviderMessage(
                id=str(row.id),
                user_id=None,
                username=row.username,
                content=row.content,
                sequence_num=row.sequence_num,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def count_messages_between(self, group_id: str, after_sequence: int, before_sequence: int) -> int:
        group = (
            self.db.query(Group)
            .filter(Group.external_id == group_id, Group.data_origin == "manual")
            .first()
        )
        if not group:
            return 0
        return (
            self.db.query(ObservedGroupMessage)
            .filter(
                ObservedGroupMessage.group_id == group.id,
                ObservedGroupMessage.sequence_num > after_sequence,
                ObservedGroupMessage.sequence_num <= before_sequence,
            )
            .count()
        )

    def get_latest_sequence(self, group_id: str) -> int:
        messages = self.get_messages(group_id, limit=1)
        return messages[-1].sequence_num if messages else 0

    def get_last_app_post_sequence(self, group_id: str) -> int | None:
        # Real Telegram send actions are manual and are not represented as provider posts.
        return None

    def publish_post(self, group_id: str, content: str, app_post_id: str) -> tuple[str, int]:
        raise RuntimeError("Automatic Telegram posting is not supported by the manual provider")

    def simulate_reply(
        self, group_id: str, username: str, message: str, post_id: str | None = None
    ) -> ProviderMessage:
        raise RuntimeError("Replies must be copied and logged manually for real groups")
