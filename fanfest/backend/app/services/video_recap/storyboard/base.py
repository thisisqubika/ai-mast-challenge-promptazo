"""Storyboard generator interface and provider factory."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from ..config import RecapConfig
from ..models import EventInput, Storyboard, TimelineScene


class StoryboardGenerator(ABC):
    name: str = "base"

    @abstractmethod
    def generate(
        self, event: EventInput, scenes: list[TimelineScene], config: RecapConfig
    ) -> Storyboard:
        ...


def anthropic_api_key() -> str:
    """Key from the process env, else from app settings (loaded from backend/.env)."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    try:
        from app.core.config import settings

        return settings.anthropic_api_key or ""
    except Exception:
        return ""


def _gemini():
    from .llm_gemini import GeminiStoryboardGenerator

    return GeminiStoryboardGenerator()


def _gemini_configured() -> bool:
    try:
        from app.services import gemini_client

        return gemini_client.is_configured()
    except Exception:
        return False


def _anthropic():
    from .llm_anthropic import AnthropicStoryboardGenerator

    return AnthropicStoryboardGenerator()


def _openai():
    from .llm_openai import OpenAIStoryboardGenerator

    return OpenAIStoryboardGenerator()


def _offline():
    from .offline import OfflineStoryboardGenerator

    return OfflineStoryboardGenerator()


def get_generator(config: RecapConfig) -> StoryboardGenerator:
    if config.provider == "offline":
        return _offline()
    if config.provider == "gemini":
        return _gemini()
    if config.provider == "anthropic":
        return _anthropic()
    if config.provider == "openai":
        return _openai()

    # auto: prefer Gemini (same provider as the text recap), then Claude, OpenAI, offline.
    if _gemini_configured():
        return _gemini()
    if anthropic_api_key():
        return _anthropic()
    if os.environ.get("OPENAI_API_KEY"):
        return _openai()
    return _offline()
