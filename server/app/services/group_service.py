from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import Group, GroupAnalysis
from app.providers.ai.factory import get_ai_provider
from app.providers.data.factory import get_data_provider
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
        joined_ids = {
            g.external_id for g in self.db.query(Group).filter(Group.joined.is_(True)).all()
        }
        exclude = joined_ids
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

    def get_detail(self, external_id: str) -> GroupDetail:
        g = self._ensure_group(external_id)
        self.db.commit()
        return GroupDetail.model_validate(g)

    def get_messages(self, external_id: str, limit: int = 100) -> list[GroupMessageOut]:
        g = self._ensure_group(external_id)
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

    def simulate_reply(
        self, external_id: str, username: str, message: str, post_id: str | None = None
    ) -> GroupMessageOut:
        self._ensure_group(external_id)
        simulated = self.data.simulate_reply(external_id, username, message, post_id)
        self.db.commit()
        return GroupMessageOut(
            id=simulated.id,
            username=simulated.username,
            content=simulated.content,
            created_at=simulated.created_at,
            is_app_post=False,
        )

    async def analyze(self, external_id: str) -> GroupAnalysisOut:
        g = self._ensure_group(external_id)
        pg = self.data.get_group(external_id)
        assert pg
        sample = self.data.get_messages(external_id, limit=50)
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
