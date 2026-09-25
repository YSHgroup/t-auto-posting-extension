from app.providers.data.base import ProviderGroup, ProviderMessage
from app.schemas.ai_outputs import (
    GroupAnalysisAIOutput,
    OpportunityAIOutput,
    OpportunityCandidate,
    PostRecommendationAIOutput,
    PostRecommendationItem,
    RiskItem,
    SuitabilityResult,
)


class MockAIProvider:
    provider_name = "mock"
    model_name = "mock-structured"

    async def analyze_group(
        self, group: ProviderGroup, sample_messages: list[ProviderMessage]
    ) -> GroupAnalysisAIOutput:
        cats = ", ".join(group.categories[:2]) if group.categories else "general"
        return GroupAnalysisAIOutput(
            summary=f"Members discuss topics related to {cats}. (AI inference — not verified facts.)",
            activities=[
                "Startup discussions",
                "Networking",
                f"{cats} trends",
            ],
            member_types=["Founders", "Developers", "Investors", "Entrepreneurs"],
            partnership=SuitabilityResult(
                status="suitable" if "Startup" in group.categories else "possibly_suitable",
                reason="Group description suggests collaboration-focused conversation (AI inference).",
                confidence=0.84,
            ),
            job=SuitabilityResult(
                status="possibly_suitable" if "Jobs" in group.categories else "not_recommended",
                reason="Job posts may be acceptable if non-spammy (general recommendation).",
                confidence=0.71,
            ),
            recommended_post_style=["Concise", "Value-first", "Ask a question"],
            risks=[
                RiskItem(text="Avoid repetitive messages", source="general recommendation"),
                RiskItem(text="Avoid excessive promotional language", source="general recommendation"),
                RiskItem(
                    text="Observed: mixed promotional and discussion content in sample",
                    source="observed group behavior",
                ),
            ],
        )

    async def recommend_post(
        self,
        group: ProviderGroup,
        analysis_summary: str,
        posts: list[dict],
    ) -> PostRecommendationAIOutput:
        ranked: list[PostRecommendationItem] = []
        for i, p in enumerate(posts):
            conf = max(0.5, 0.9 - i * 0.08)
            ranked.append(
                PostRecommendationItem(
                    post_id=str(p["id"]),
                    reason=f"Aligns with {group.name} focus ({p.get('post_type', 'General')}).",
                    confidence=conf,
                )
            )
        ranked.sort(key=lambda x: x.confidence, reverse=True)
        return PostRecommendationAIOutput(recommendations=ranked)

    async def analyze_opportunities(
        self, group: ProviderGroup, messages: list[ProviderMessage]
    ) -> OpportunityAIOutput:
        investment: list[OpportunityCandidate] = []
        partnership: list[OpportunityCandidate] = []
        invest_phrases = ("invest", "fund", "capital", "angel")
        partner_phrases = ("partner", "collaborat", "integration", "affiliate")
        for m in messages:
            if not m.username or not m.content:
                continue
            lower = m.content.lower()
            if any(p in lower for p in invest_phrases):
                level = "explicit" if "i invest" in lower or "we invest" in lower else "strong_indication"
                investment.append(
                    OpportunityCandidate(
                        user_id=m.user_id or m.username,
                        username=m.username,
                        category="investment",
                        evidence=m.content[:280],
                        evidence_level=level,
                        confidence=0.86 if level == "explicit" else 0.72,
                    )
                )
            if any(p in lower for p in partner_phrases):
                level = "explicit" if "looking for partners" in lower else "possible"
                partnership.append(
                    OpportunityCandidate(
                        user_id=m.user_id or m.username,
                        username=m.username,
                        category="partnership",
                        evidence=m.content[:280],
                        evidence_level=level,
                        confidence=0.81 if level == "explicit" else 0.65,
                    )
                )
        return OpportunityAIOutput(
            investment=investment[:20],
            partnership=partnership[:20],
        )
