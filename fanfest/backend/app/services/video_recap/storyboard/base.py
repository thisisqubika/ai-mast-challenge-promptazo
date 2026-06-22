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
    if config.provider == "anthropic":
        return _anthropic()
    if config.provider == "openai":
        return _openai()

    # auto: prefer Claude, then OpenAI, then offline.
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic()
    if os.environ.get("OPENAI_API_KEY"):
        return _openai()
    return _offline()
