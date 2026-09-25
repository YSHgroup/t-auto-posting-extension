from typing import Protocol

from app.providers.data.base import ProviderGroup, ProviderMessage
from app.schemas.ai_outputs import (
    GroupAnalysisAIOutput,
    OpportunityAIOutput,
    PostRecommendationAIOutput,
)


class AIProvider(Protocol):
    provider_name: str
    model_name: str

    async def analyze_group(
        self, group: ProviderGroup, sample_messages: list[ProviderMessage]
    ) -> GroupAnalysisAIOutput: ...

    async def recommend_post(
        self,
        group: ProviderGroup,
        analysis_summary: str,
        posts: list[dict],
    ) -> PostRecommendationAIOutput: ...

    async def analyze_opportunities(
        self, group: ProviderGroup, messages: list[ProviderMessage]
    ) -> OpportunityAIOutput: ...
