from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class ProviderGroup:
    id: str
    name: str
    username: str
    description: str
    member_count: int
    categories: list[str]
    keywords: list[str]
    joined: bool


@dataclass
class ProviderMessage:
    id: str
    user_id: str | None
    username: str | None
    content: str
    sequence_num: int
    is_app_post: bool = False
    app_post_id: str | None = None
    replaced: bool = False
    created_at: datetime | None = None


class DataProvider(Protocol):
    def search_groups(
        self, query: str, exclude_external_ids: set[str], limit: int = 50
    ) -> list[tuple[ProviderGroup, float]]: ...

    def get_group(self, group_id: str) -> ProviderGroup | None: ...

    def validate_group_id(self, group_id: str) -> bool: ...

    def get_messages(
        self, group_id: str, limit: int = 100, after_sequence: int | None = None
    ) -> list[ProviderMessage]: ...

    def count_messages_between(
        self, group_id: str, after_sequence: int, before_sequence: int
    ) -> int: ...

    def publish_post(
        self, group_id: str, content: str, app_post_id: str
    ) -> tuple[str, int]: ...

    def get_latest_sequence(self, group_id: str) -> int: ...

    def get_last_app_post_sequence(self, group_id: str) -> int | None: ...

    def simulate_reply(
        self, group_id: str, username: str, message: str, post_id: str | None = None
    ) -> ProviderMessage: ...
