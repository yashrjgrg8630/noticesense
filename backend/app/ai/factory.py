from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.ollama_provider import OllamaProvider
from app.core.config import settings


def get_provider() -> AIProvider:
    """Instantiate the configured AI provider. Defaults to Ollama."""
    if settings.ai_provider == "gemini":
        return GeminiProvider()
    return OllamaProvider()
