"""Gemini-backed storyboard generator (Google AI Studio free tier)."""

from __future__ import annotations

import json

from ..config import RecapConfig
from ..errors import StoryboardGenerationError
from ..models import EventInput, Storyboard, TimelineScene
from .base import StoryboardGenerator
from .draft import LLMStoryboardDraft, assemble_storyboard
from .prompt import build_system_prompt, build_user_prompt


class GeminiStoryboardGenerator(StoryboardGenerator):
    name = "gemini"

    def generate(
        self, event: EventInput, scenes: list[TimelineScene], config: RecapConfig
    ) -> Storyboard:
        from app.core.config import settings
        from app.services import gemini_client

        schema = json.dumps(LLMStoryboardDraft.model_json_schema(), ensure_ascii=False)
        system = (
            build_system_prompt(config)
            + "\n\nReturn ONLY a JSON object matching this JSON Schema:\n"
            + schema
        )
        try:
            raw = gemini_client.generate_json(build_user_prompt(event, scenes, config), system=system)
            draft = LLMStoryboardDraft.model_validate_json(raw)
        except Exception as exc:
            raise StoryboardGenerationError(f"Gemini storyboard request failed: {exc}") from exc

        return assemble_storyboard(
            draft, event, scenes, config, generated_by=self.name, model=settings.gemini_model
        )
