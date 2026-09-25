from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import AISettings
from app.providers.ai.base import AIProvider
from app.providers.ai.claude_provider import ClaudeProvider
from app.providers.ai.mock_ai import MockAIProvider
from app.providers.ai.openai_provider import OpenAIProvider


def get_ai_provider(db: Session) -> AIProvider:
    settings = get_settings()
    ai_settings = db.query(AISettings).filter(AISettings.id == 1).first()
    provider = ai_settings.provider if ai_settings else settings.ai_provider

    if provider == "anthropic" and settings.anthropic_api_key:
        model = ai_settings.anthropic_model if ai_settings else settings.anthropic_model
        return ClaudeProvider(settings.anthropic_api_key, model)
    if provider == "openai" and settings.openai_api_key:
        model = ai_settings.openai_model if ai_settings else settings.openai_model
        return OpenAIProvider(settings.openai_api_key, model)
    if settings.ai_mock_when_no_key:
        return MockAIProvider()
    raise RuntimeError("AI provider not configured. Set API keys or AI_MOCK_WHEN_NO_KEY=true.")
