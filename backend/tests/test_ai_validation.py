import pytest
from app.providers.ai.providers import AIProviderError, RemoteAIProvider
from app.providers.data.mock import MockDataProvider

class InvalidProvider(RemoteAIProvider):
    provider_name = "test"
    model = "invalid"
    async def _complete(self, prompt: str) -> dict:
        return {"activities": "not-an-array"}

@pytest.mark.asyncio
async def test_invalid_group_analysis_is_rejected() -> None:
    group = MockDataProvider().get_group("group_001")
    assert group is not None
    with pytest.raises(AIProviderError):
        await InvalidProvider().analyze_group(group)
