import json

from openai import AsyncOpenAI

from app.providers.ai.structured import parse_with_retry
from app.providers.data.base import ProviderGroup, ProviderMessage
from app.schemas.ai_outputs import (
    GroupAnalysisAIOutput,
    OpportunityAIOutput,
    PostRecommendationAIOutput,
)

GROUP_SCHEMA = GroupAnalysisAIOutput.model_json_schema()
POST_SCHEMA = PostRecommendationAIOutput.model_json_schema()
OPP_SCHEMA = OpportunityAIOutput.model_json_schema()


class OpenAIProvider:
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model
        self.provider_name = "openai"

    async def _chat_json(self, system: str, user: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"

    async def _fix(self, broken: str, err: str) -> str:
        return await self._chat_json(
            "Fix JSON to match schema. Return only valid JSON.",
            f"Error: {err}\nBroken:\n{broken}",
        )

    async def analyze_group(
        self, group: ProviderGroup, sample_messages: list[ProviderMessage]
    ) -> GroupAnalysisAIOutput:
        msgs = "\n".join(f"- @{m.username}: {m.content[:200]}" for m in sample_messages[:30])
        user = f"""Group: {group.name} (@{group.username})
Description: {group.description}
Categories: {group.categories}
Sample messages:
{msgs}

Return JSON matching schema with partnership/job status in suitable|possibly_suitable|not_recommended|insufficient_information.
Mark risks with source observed|inference|recommendation. Do not claim restrictions will definitely happen.
Schema: {json.dumps(GROUP_SCHEMA)}"""
        raw = await self._chat_json("You analyze communities. Output JSON only.", user)
        return await parse_with_retry(raw, GroupAnalysisAIOutput, self._fix)

    async def recommend_post(
        self,
        group: ProviderGroup,
        analysis_summary: str,
        posts: list[dict],
    ) -> PostRecommendationAIOutput:
        user = f"""Group: {group.name}
Analysis: {analysis_summary}
Posts: {json.dumps(posts)}
Schema: {json.dumps(POST_SCHEMA)}"""
        raw = await self._chat_json("Recommend posts as JSON.", user)
        return await parse_with_retry(raw, PostRecommendationAIOutput, self._fix)

    async def analyze_opportunities(
        self, group: ProviderGroup, messages: list[ProviderMessage]
    ) -> OpportunityAIOutput:
        lines = "\n".join(f"{m.user_id}|{m.username}|{m.content[:300]}" for m in messages[:500])
        user = f"""Analyze messages for investment and partnership signals.
Evidence levels: explicit|strong_indication|possible|insufficient
Group: {group.name}
Messages:
{lines}
Schema: {json.dumps(OPP_SCHEMA)}"""
        raw = await self._chat_json("Identify opportunities. JSON only.", user)
        return await parse_with_retry(raw, OpportunityAIOutput, self._fix)
