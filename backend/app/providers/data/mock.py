from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol
from app.schemas import Group, GroupMessage

class DataProvider(Protocol):
    def search_groups(self, query: str) -> list[Group]: ...
    def get_group(self, group_id: str) -> Group | None: ...
    def get_messages(self, group_id: str, limit: int = 500) -> list[GroupMessage]: ...
    def messages_since_last_post(self, group_id: str) -> int: ...

class MockDataProvider:
    def __init__(self) -> None:
        categories = ["Blockchain", "Startups", "Developers", "Gaming", "Remote Jobs", "Investors", "Marketing", "Entrepreneurs", "Freelancers", "Technology"]
        self.groups = [
            Group(id=f"group_{index:03d}", name=f"{category} {['Founders', 'Builders', 'Network', 'Community', 'Opportunities'][index % 5]}", username=f"{category.lower().replace(' ', '_')}_{index}", description=f"A practical community for {category.lower()} discussions, collaboration, and new opportunities.", member_count=1800 + index * 347, category=category, keywords=[category.lower(), "startup", "community"], joined=index % 7 == 0)
            for index, category in enumerate(categories * 6, start=1)
        ]
        self.messages: dict[str, list[GroupMessage]] = {}
        for group in self.groups:
            self.messages[group.id] = [
                GroupMessage(id=f"{group.id}_message_{index}", group_id=group.id, user_id=f"user_{index % 18:03d}", username=f"member_{index % 18:03d}", content=self._message_for(group, index), created_at=datetime.now(UTC) - timedelta(minutes=index))
                for index in range(1, 61)
            ]

    def _message_for(self, group: Group, index: int) -> str:
        if index % 17 == 0:
            return "I invest in early-stage startups and am looking for strong teams."
        if index % 13 == 0:
            return "Looking for strategic partnerships and integration opportunities."
        return f"{group.category} discussion #{index}: sharing lessons and practical ideas with the community."

    def search_groups(self, query: str) -> list[Group]:
        terms = query.lower().split()
        if not terms:
            return [group for group in self.groups if not group.joined][:50]
        scored = []
        for group in self.groups:
            if group.joined:
                continue
            haystack = " ".join([group.name, group.username, group.description, group.category, *group.keywords]).lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, group))
        return [group for _, group in sorted(scored, key=lambda item: (-item[0], item[1].name))][:50]

    def get_group(self, group_id: str) -> Group | None:
        return next((group for group in self.groups if group.id == group_id), None)

    def get_messages(self, group_id: str, limit: int = 500) -> list[GroupMessage]:
        return self.messages.get(group_id, [])[: min(limit, 500)]

    def messages_since_last_post(self, group_id: str) -> int:
        return len(self.messages.get(group_id, []))
