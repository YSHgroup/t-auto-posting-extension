from sqlalchemy.orm import Session

from app.models.entities import Group, Opportunity
from app.providers.ai.factory import get_ai_provider
from app.providers.data.factory import get_data_provider
from app.services.group_service import GroupService


class OpportunityService:
    def __init__(self, db: Session):
        self.db = db
        self.data = get_data_provider(db)

    async def scan_group(self, external_id: str) -> list[dict]:
        g = GroupService(self.db)._ensure_group(external_id)
        pg = self.data.get_group(external_id)
        if not pg:
            raise ValueError("Group not found")
        messages = self.data.get_messages(external_id, limit=500)
        ai = get_ai_provider(self.db)
        result = await ai.analyze_opportunities(pg, messages)
        self.db.query(Opportunity).filter(Opportunity.group_id == g.id).delete(
            synchronize_session=False
        )
        stored: list[dict] = []
        for cand in result.investment + result.partnership:
            row = Opportunity(
                group_id=g.id,
                user_id=cand.user_id,
                username=cand.username,
                category=cand.category,
                evidence=cand.evidence,
                evidence_level=cand.evidence_level,
                confidence=cand.confidence,
            )
            self.db.add(row)
            stored.append(cand.model_dump())
        self.db.commit()
        return stored

    def list_all(self, category: str | None = None) -> list[dict]:
        q = self.db.query(Opportunity).order_by(Opportunity.created_at.desc())
        if category:
            q = q.filter(Opportunity.category == category)
        rows = q.limit(200).all()
        out = []
        for r in rows:
            group = self.db.query(Group).filter(Group.id == r.group_id).first()
            out.append(
                {
                    "id": str(r.id),
                    "group_id": str(r.group_id),
                    "group_name": group.name if group else "",
                    "user_id": r.user_id,
                    "username": r.username,
                    "category": r.category,
                    "evidence": r.evidence,
                    "evidence_level": r.evidence_level,
                    "confidence": round(r.confidence * 100, 1),
                    "created_at": r.created_at.isoformat(),
                }
            )
        return out
