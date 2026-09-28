from uuid import UUID
from urllib.parse import urlparse
import re

from sqlalchemy.orm import Session

from app.models.entities import (
    FeedItem,
    Group,
    GroupAnalysis,
    Notification,
    ObservedGroupMessage,
    Post,
    Reply,
    SkippedGroup,
)
from app.providers.ai.factory import get_ai_provider
from app.providers.data.factory import get_data_provider
from app.providers.data.base import ProviderGroup, ProviderMessage
from app.schemas.groups import GroupAnalysisOut, GroupDetail, GroupMessageOut, GroupSearchResult


class GroupService:
    def __init__(self, db: Session):
        self.db = db
        self.data = get_data_provider(db)

    def _ensure_group(self, external_id: str) -> Group:
        existing = self.db.query(Group).filter(Group.external_id == external_id).first()
        if existing:
            return existing
        pg = self.data.get_group(external_id)
        if not pg:
            raise ValueError("Group not found")
        g = Group(
            external_id=pg.id,
            name=pg.name,
            username=pg.username,
            description=pg.description,
            member_count=pg.member_count,
            categories=pg.categories,
            keywords=pg.keywords,
            joined=pg.joined,
        )
        self.db.add(g)
        self.db.flush()
        return g

    def search(self, query: str) -> list[GroupSearchResult]:
        exclude = {
            group.external_id
            for group in self.db.query(Group)
            .join(FeedItem, FeedItem.group_id == Group.id)
            .all()
        }
        exclude.update(
            group.external_id
            for group in self.db.query(Group)
            .join(SkippedGroup, SkippedGroup.group_id == Group.id)
            .all()
        )
        results = self.data.search_groups(query, exclude, limit=50)
        out: list[GroupSearchResult] = []
        for pg, score in results:
            self._ensure_group(pg.id)
            out.append(
                GroupSearchResult(
                    id=pg.id,
                    name=pg.name,
                    username=pg.username,
                    description=pg.description,
                    member_count=pg.member_count,
                    categories=pg.categories,
                    joined=pg.joined,
                    relevance=round(score * 100, 1),
                )
            )
        self.db.commit()
        return out

    def intake_telegram_group(
        self, group_id: str, group_name: str, source_url: str, action: str
    ) -> dict:
        normalized_id = group_id.strip()
        if not normalized_id or len(normalized_id) > 64:
            raise ValueError("A valid Telegram group ID is required")
        if action not in {"add", "skip"}:
            raise ValueError("Action must be add or skip")
        if source_url:
            parsed_url = urlparse(source_url)
            if parsed_url.scheme != "https" or parsed_url.hostname not in {
                "t.me",
                "www.t.me",
                "web.telegram.org",
                "telegram.org",
                "www.telegram.org",
            }:
                raise ValueError("Only Telegram HTTPS URLs are accepted")
        group = self.db.query(Group).filter(Group.external_id == normalized_id).first()
        if not group:
            group = Group(
                external_id=normalized_id,
                name=group_name.strip() or normalized_id,
                username="",
                description=f"User-confirmed group from {source_url}" if source_url else "",
                member_count=0,
                categories=[],
                keywords=[],
                joined=False,
            )
            self.db.add(group)
            self.db.flush()
        if source_url:
            group.telegram_url = source_url[:2048]
        if action == "add":
            existing_item = self.db.query(FeedItem).filter(FeedItem.group_id == group.id).first()
            if not existing_item:
                item = FeedItem(group_id=group.id, order_index=self.db.query(FeedItem).count())
                self.db.add(item)
            self.db.query(SkippedGroup).filter(SkippedGroup.group_id == group.id).delete(
                synchronize_session=False
            )
        else:
            existing = self.db.query(SkippedGroup).filter(SkippedGroup.group_id == group.id).first()
            if not existing:
                self.db.add(SkippedGroup(group_id=group.id, source_url=source_url))
        self.db.commit()
        return {"group_id": normalized_id, "action": action, "group_name": group.name}

    def telegram_group_decision(self, group_id: str) -> dict:
        group = self.db.query(Group).filter(Group.external_id == group_id).first()
        if not group:
            return {"decision": None}
        if self.db.query(FeedItem).filter(FeedItem.group_id == group.id).first():
            return {"decision": "add"}
        if self.db.query(SkippedGroup).filter(SkippedGroup.group_id == group.id).first():
            return {"decision": "skip"}
        return {"decision": None}

    def get_detail(self, external_id: str) -> GroupDetail:
        g = self._ensure_group(external_id)
        self.db.commit()
        return GroupDetail.model_validate(g)

    def get_messages(self, external_id: str, limit: int = 100) -> list[GroupMessageOut]:
        g = self._ensure_group(external_id)
        observed = (
            self.db.query(ObservedGroupMessage)
            .filter(ObservedGroupMessage.group_id == g.id)
            .order_by(ObservedGroupMessage.sequence_num.desc())
            .limit(min(max(limit, 1), 500))
            .all()
        )
        if observed:
            observed.reverse()
            return [
                GroupMessageOut(
                    id=str(message.id),
                    username=message.username,
                    content=message.content,
                    created_at=message.created_at,
                    is_app_post=False,
                )
                for message in observed
            ]
        msgs = self.data.get_messages(external_id, limit=min(max(limit, 1), 500))
        return [
            GroupMessageOut(
                id=m.id,
                username=m.username,
                content=m.content,
                created_at=m.created_at,
                is_app_post=m.is_app_post,
            )
            for m in msgs
        ]

    def import_observed_messages(self, external_id: str, contents: list[str]) -> int:
        group = self._ensure_group(external_id)
        cleaned = [content.strip() for content in contents if content.strip()]
        if len(cleaned) > 500:
            raise ValueError("Maximum 500 messages can be imported at once")
        current_max = (
            self.db.query(ObservedGroupMessage.sequence_num)
            .filter(ObservedGroupMessage.group_id == group.id)
            .order_by(ObservedGroupMessage.sequence_num.desc())
            .first()
        )
        next_sequence = current_max[0] + 1 if current_max else 1
        rows = []
        for offset, content in enumerate(cleaned):
            match = re.match(r"^@([A-Za-z0-9_]{3,})\s*:\s*(.*)$", content, re.DOTALL)
            rows.append(ObservedGroupMessage(
                group_id=group.id,
                username=match.group(1) if match else None,
                content=match.group(2) if match else content[:10000],
                sequence_num=next_sequence + offset,
            ))
        self.db.add_all(
            rows
        )
        self.db.commit()
        return len(cleaned)

    def simulate_reply(
        self, external_id: str, username: str, message: str, post_id: str | None = None
    ) -> GroupMessageOut:
        self._ensure_group(external_id)
        if not self.data.get_group(external_id):
            raise ValueError("Simulated replies are available only for mock catalog groups")
        simulated = self.data.simulate_reply(external_id, username, message, post_id)
        self.db.commit()
        return GroupMessageOut(
            id=simulated.id,
            username=simulated.username,
            content=simulated.content,
            created_at=simulated.created_at,
            is_app_post=False,
        )

    def log_manual_reply(self, external_id: str, username: str, message: str, post_id: UUID | None):
        group = self._ensure_group(external_id)
        if post_id and not self.db.query(Post).filter(Post.id == post_id).first():
            raise ValueError("Related post not found for this installation")
        reply = Reply(
            group_id=group.id,
            post_id=post_id,
            user_id=f"manual:{username[:57]}",
            username=username,
            message=message,
        )
        self.db.add(reply)
        self.db.add(
            Notification(
                group_id=group.id,
                user_id=f"manual:{username[:57]}",
                username=username,
                message=message,
                related_post_id=post_id,
            )
        )
        self.db.commit()
        return {"ok": True, "reply_id": str(reply.id)}

    async def analyze(self, external_id: str) -> GroupAnalysisOut:
        g = self._ensure_group(external_id)
        observed = self.db.query(ObservedGroupMessage).filter(
            ObservedGroupMessage.group_id == g.id
        ).order_by(ObservedGroupMessage.sequence_num.desc()).limit(50).all()
        sample = (
            [
                ProviderMessage(
                    id=str(message.id),
                    user_id=None,
                    username=message.username,
                    content=message.content,
                    sequence_num=message.sequence_num,
                    created_at=message.created_at,
                )
                for message in reversed(observed)
            ]
            if observed
            else self.data.get_messages(external_id, limit=50)
        )
        pg = self.data.get_group(external_id)
        if not pg and observed:
            pg = ProviderGroup(
                id=g.external_id,
                name=g.name,
                username=g.username,
                description=g.description,
                member_count=g.member_count,
                categories=list(g.categories or []),
                keywords=list(g.keywords or []),
                joined=g.joined,
            )
        if not pg:
            raise ValueError("Import message text before analyzing a real Telegram group.")
        ai = get_ai_provider(self.db)
        result = await ai.analyze_group(pg, sample)
        row = GroupAnalysis(
            group_id=g.id,
            summary=result.summary,
            member_types=result.member_types,
            activities=result.activities,
            partnership_status=result.partnership.status,
            partnership_reason=result.partnership.reason,
            partnership_confidence=result.partnership.confidence,
            job_status=result.job.status,
            job_reason=result.job.reason,
            job_confidence=result.job.confidence,
            posting_style=result.recommended_post_style,
            risks=[r.model_dump() for r in result.risks],
            ai_provider=ai.provider_name,
            ai_model=ai.model_name,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return GroupAnalysisOut.model_validate(row)

    def list_analyses(self, external_id: str) -> list[GroupAnalysisOut]:
        g = self.db.query(Group).filter(Group.external_id == external_id).first()
        if not g:
            raise ValueError("Group not found")
        rows = (
            self.db.query(GroupAnalysis)
            .filter(GroupAnalysis.group_id == g.id)
            .order_by(GroupAnalysis.created_at.desc())
            .all()
        )
        return [GroupAnalysisOut.model_validate(r) for r in rows]

    def get_group_uuid_by_external(self, external_id: str) -> UUID:
        return self._ensure_group(external_id).id
