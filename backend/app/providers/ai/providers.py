from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Protocol
import httpx
from pydantic import BaseModel, ValidationError
from app.core.config import get_settings
from app.schemas import Group, GroupAnalysis, Opportunity

class AIProvider(Protocol):
    async def analyze_group(self, group: Group) -> GroupAnalysis: ...
    async def analyze_opportunities(self, group: Group, messages: list[str]) -> list[Opportunity]: ...

class AIProviderError(RuntimeError):
    pass

class GroupAnalysisPayload(BaseModel):
    activities: list[str]
    member_types: list[str]
    partnership: dict
    job: dict
    posting_style: list[str]
    risks: list[str]

class MockAIProvider:
    async def analyze_group(self, group: Group) -> GroupAnalysis:
        return GroupAnalysis(id=f"analysis_{group.id}", group_id=group.id, activities=[f"{group.category} discussions", "Business networking", "Knowledge sharing"], member_types=["Founders", "Builders", "Entrepreneurs"], partnership={"status": "suitable", "reason": "The group's stated focus supports relevant collaboration, but this is an AI-assisted recommendation.", "confidence": 0.84}, job={"status": "possibly_suitable", "reason": "Job-related content may fit when it is clearly relevant to the group's focus.", "confidence": 0.71}, posting_style=["Specific and concise", "Value-led", "Low frequency"], risks=["Avoid repetitive messages", "Avoid aggressive sales language", "Respect the group's topic"], ai_provider="mock", ai_model="deterministic-demo", created_at=datetime.now(UTC))

    async def analyze_opportunities(self, group: Group, messages: list[str]) -> list[Opportunity]:
        return [Opportunity(id=f"opportunity_{group.id}_investment", group_id=group.id, group_name=group.name, username="member_017", category="investment", evidence="I invest in early-stage startups and am looking for strong teams.", evidence_level="explicit", confidence=0.86), Opportunity(id=f"opportunity_{group.id}_partnership", group_id=group.id, group_name=group.name, username="member_013", category="partnership", evidence="Looking for strategic partnerships and integration opportunities.", evidence_level="explicit", confidence=0.81)]

class RemoteAIProvider:
    provider_name = "remote"
    model = ""

    async def _complete(self, prompt: str) -> dict:
        raise NotImplementedError

    async def analyze_group(self, group: Group) -> GroupAnalysis:
        prompt = f"Return only JSON with activities (array), member_types (array), partnership (status, reason, confidence), job (status, reason, confidence), posting_style (array), risks (array). Analyze this community, and distinguish inference from observation. Group: {group.model_dump_json()}"
        payload = await self._complete(prompt)
        try:
            validated = GroupAnalysisPayload.model_validate(payload)
            return GroupAnalysis(id=f"analysis_{group.id}", group_id=group.id, **validated.model_dump(), ai_provider=self.provider_name, ai_model=self.model, created_at=datetime.now(UTC))
        except ValidationError as error:
            raise AIProviderError(f"AI returned invalid structured group analysis: {error}") from error

    async def analyze_opportunities(self, group: Group, messages: list[str]) -> list[Opportunity]:
        prompt = "Return only JSON shaped as {\"opportunities\": []}, where opportunities contains objects with username, category (investment or partnership), evidence, evidence_level, confidence. Use explicit evidence where possible and do not claim certainty. Messages: " + "\n".join(messages[:500])
        payload = await self._complete(prompt)
        if isinstance(payload, dict):
            payload = payload.get("opportunities", [])
        if not isinstance(payload, list):
            raise AIProviderError("AI opportunity response was not a JSON array")
        try:
            return [Opportunity(id=f"opportunity_{group.id}_{index}", group_id=group.id, group_name=group.name, **item) for index, item in enumerate(payload)]
        except ValidationError as error:
            raise AIProviderError(f"AI returned invalid structured opportunities: {error}") from error

class OpenAIProvider(RemoteAIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def _complete(self, prompt: str) -> dict:
        if not self.api_key:
            raise AIProviderError("OPENAI_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "messages": [{"role": "system", "content": "You are a cautious analysis service. Return valid JSON only."}, {"role": "user", "content": prompt}], "response_format": {"type": "json_object"}})
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)

class ClaudeProvider(RemoteAIProvider):
    provider_name = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model

    async def _complete(self, prompt: str) -> dict:
        if not self.api_key:
            raise AIProviderError("ANTHROPIC_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, json={"model": self.model, "max_tokens": 2000, "system": "Return valid JSON only.", "messages": [{"role": "user", "content": prompt}]})
            response.raise_for_status()
            content = response.json()["content"][0]["text"]
            return json.loads(content)

def build_ai_provider() -> AIProvider:
    selected = get_settings().ai_provider.lower()
    if selected == "openai":
        return OpenAIProvider()
    if selected in {"claude", "anthropic"}:
        return ClaudeProvider()
    return MockAIProvider()
