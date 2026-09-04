"""
app/agents/providers/__init__.py
===================================
LLM provider factory.

Usage:
    provider = get_provider()   # uses settings.LLM_PROVIDER
    provider = get_provider("fake")
    provider = get_provider("openai")
"""
from __future__ import annotations

from app.agents.providers.base import LLMProvider, LLMProviderError
from app.core.config import settings


def get_provider(name: str | None = None) -> LLMProvider:
    """
    Return the configured LLM provider instance.

    Args:
        name: Provider name override. Defaults to settings.LLM_PROVIDER.

    Raises:
        LLMProviderError: If the provider name is unknown or misconfigured.
    """
    provider_name = (name or settings.LLM_PROVIDER).lower().strip()

    if provider_name == "fake":
        from app.agents.providers.fake import FakeLLMProvider
        return FakeLLMProvider()

    if provider_name == "openai":
        from app.agents.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if provider_name in ("gemini", "google"):
        from app.agents.providers.gemini_provider import GeminiProvider
        return GeminiProvider()

    raise LLMProviderError(
        f"Unknown LLM provider: '{provider_name}'. "
        "Supported values: 'fake', 'openai', 'gemini'."
    )


__all__ = ["LLMProvider", "LLMProviderError", "get_provider"]
