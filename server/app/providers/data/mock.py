import random
import re
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.models.entities import Group, GroupMessage, Notification, Reply
from app.providers.data.base import DataProvider, ProviderGroup, ProviderMessage
from app.providers.data.mock_catalog import MOCK_GROUPS


class MockDataProvider:
    """In-memory + DB-backed mock Telegram-like data."""

    def __init__(self, db: Session):
        self.db = db

    def _to_provider_group(self, g: Group | dict, joined: bool | None = None) -> ProviderGroup:
        if isinstance(g, Group):
            return ProviderGroup(
                id=g.external_id,
                name=g.name,
                username=g.username,
                description=g.description,
                member_count=g.member_count,
                categories=list(g.categories or []),
                keywords=list(g.keywords or []),
                joined=g.joined if joined is None else joined,
            )
        return ProviderGroup(
            id=g["id"],
            name=g["name"],
            username=g["username"],
            description=g["description"],
            member_count=g["member_count"],
            categories=g["categories"],
            keywords=g.get("keywords", []),
            joined=joined if joined is not None else False,
        )

    def _score(self, group: ProviderGroup, query: str) -> float:
        if not query.strip():
            return 0.5
        q = query.lower()
        tokens = re.split(r"\s+", q)
        text = " ".join(
            [group.name, group.username, group.description, " ".join(group.categories), " ".join(group.keywords)]
        ).lower()
        hits = sum(1 for t in tokens if t in text)
        base = hits / max(len(tokens), 1)
        return min(0.99, 0.4 + base * 0.3 + (group.member_count / 100000) * 0.1)

    def search_groups(
        self, query: str, exclude_external_ids: set[str], limit: int = 50
    ) -> list[tuple[ProviderGroup, float]]:
        results: list[tuple[ProviderGroup, float]] = []
        joined_map = {
            g.external_id: g.joined
            for g in self.db.query(Group).filter(Group.joined.is_(True)).all()
        }
        for raw in MOCK_GROUPS:
            if raw["id"] in exclude_external_ids:
                continue
            pg = self._to_provider_group(raw, joined=joined_map.get(raw["id"], False))
            if pg.joined:
                continue
            score = self._score(pg, query)
            if query.strip() and score < 0.45:
                continue
            results.append((pg, score))
        results.sort(key=lambda x: x[1], reverse=True)
        if not query.strip():
            results.sort(key=lambda x: x[0].member_count, reverse=True)
        return results[:limit]

    def get_group(self, group_id: str) -> ProviderGroup | None:
        for raw in MOCK_GROUPS:
            if raw["id"] == group_id:
                db_group = self.db.query(Group).filter(Group.external_id == group_id).first()
                joined = db_group.joined if db_group else False
                return self._to_provider_group(raw, joined=joined)
        db_group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if db_group:
            return self._to_provider_group(db_group)
        return None

    def validate_group_id(self, group_id: str) -> bool:
        return self.get_group(group_id) is not None

    def _messages_for_group(self, group_uuid) -> list[GroupMessage]:
        return (
            self.db.query(GroupMessage)
            .filter(GroupMessage.group_id == group_uuid, GroupMessage.replaced.is_(False))
            .order_by(GroupMessage.sequence_num.asc())
            .all()
        )

    def get_messages(
        self, group_id: str, limit: int = 100, after_sequence: int | None = None
    ) -> list[ProviderMessage]:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            return []
        q = self.db.query(GroupMessage).filter(
            GroupMessage.group_id == group.id, GroupMessage.replaced.is_(False)
        )
        if after_sequence is not None:
            q = q.filter(GroupMessage.sequence_num > after_sequence)
        rows = q.order_by(GroupMessage.sequence_num.desc()).limit(limit).all()
        rows.reverse()
        return [
            ProviderMessage(
                id=m.external_message_id,
                user_id=m.user_id,
                username=m.username,
                content=m.content,
                sequence_num=m.sequence_num,
                is_app_post=m.is_app_post,
                app_post_id=str(m.app_post_id) if m.app_post_id else None,
                replaced=m.replaced,
                created_at=m.created_at,
            )
            for m in rows
        ]

    def count_messages_between(
        self, group_id: str, after_sequence: int, before_sequence: int
    ) -> int:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            return 0
        return (
            self.db.query(GroupMessage)
            .filter(
                GroupMessage.group_id == group.id,
                GroupMessage.sequence_num > after_sequence,
                GroupMessage.sequence_num <= before_sequence,
                GroupMessage.replaced.is_(False),
            )
            .count()
        )

    def get_latest_sequence(self, group_id: str) -> int:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            return 0
        row = (
            self.db.query(GroupMessage.sequence_num)
            .filter(GroupMessage.group_id == group.id, GroupMessage.replaced.is_(False))
            .order_by(GroupMessage.sequence_num.desc())
            .first()
        )
        return row[0] if row else 0

    def get_last_app_post_sequence(self, group_id: str) -> int | None:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            return None
        row = (
            self.db.query(GroupMessage)
            .filter(
                GroupMessage.group_id == group.id,
                GroupMessage.is_app_post.is_(True),
                GroupMessage.replaced.is_(False),
            )
            .order_by(GroupMessage.sequence_num.desc())
            .first()
        )
        return row.sequence_num if row else None

    def publish_post(
        self, group_id: str, content: str, app_post_id: str
    ) -> tuple[str, int]:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            raise ValueError("Group not found")
        prev = (
            self.db.query(GroupMessage)
            .filter(
                GroupMessage.group_id == group.id,
                GroupMessage.is_app_post.is_(True),
                GroupMessage.replaced.is_(False),
            )
            .order_by(GroupMessage.sequence_num.desc())
            .first()
        )
        if prev:
            prev.replaced = True
        latest = self.get_latest_sequence(group_id)
        new_seq = latest + 1
        msg_id = f"msg_{group_id}_{new_seq}"
        import uuid

        from datetime import datetime

        new_msg = GroupMessage(
            group_id=group.id,
            external_message_id=msg_id,
            user_id="app_user",
            username="you",
            content=content,
            is_app_post=True,
            app_post_id=uuid.UUID(app_post_id),
            sequence_num=new_seq,
            created_at=datetime.utcnow(),
        )
        self.db.add(new_msg)
        self.db.flush()
        return msg_id, new_seq

    def simulate_reply(
        self, group_id: str, username: str, message: str, post_id: str | None = None
    ) -> ProviderMessage:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            raise ValueError("Group not found")
        latest = self.get_latest_sequence(group_id)
        message_id = f"reply_{group_id}_{latest + 1}"
        reply = GroupMessage(
            group_id=group.id,
            external_message_id=message_id,
            user_id=f"simulated_{username}",
            username=username,
            content=message,
            sequence_num=latest + 1,
        )
        self.db.add(reply)
        related_post = None
        if post_id:
            import uuid

            related_post = uuid.UUID(post_id)
        self.db.add(
            Reply(
                group_id=group.id,
                post_id=related_post,
                user_id=f"simulated_{username}",
                username=username,
                message=message,
            )
        )
        self.db.add(
            Notification(
                group_id=group.id,
                user_id=f"simulated_{username}",
                username=username,
                message=message,
                related_post_id=related_post,
            )
        )
        self.db.flush()
        return ProviderMessage(
            id=message_id,
            user_id=reply.user_id,
            username=username,
            content=message,
            sequence_num=reply.sequence_num,
            created_at=reply.created_at,
        )


def get_data_provider(db: Session) -> DataProvider:
    return MockDataProvider(db)
