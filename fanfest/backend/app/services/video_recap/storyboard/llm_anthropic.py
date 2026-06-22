"""Claude-backed storyboard generator."""

from __future__ import annotations

from ..config import RecapConfig
from ..errors import StoryboardGenerationError
from ..models import EventInput, Storyboard, TimelineScene
from .base import StoryboardGenerator
from .draft import LLMStoryboardDraft, assemble_storyboard
from .prompt import build_system_prompt, build_user_prompt

MAX_TOKENS = 8000


class AnthropicStoryboardGenerator(StoryboardGenerator):
    name = "anthropic"

    def generate(
        self, event: EventInput, scenes: list[TimelineScene], config: RecapConfig
    ) -> Storyboard:
        try:
            import anthropic
        except ImportError as exc:
            raise StoryboardGenerationError(
                "The 'anthropic' package is required for provider=anthropic."
            ) from exc

        client = anthropic.Anthropic()
        try:
            response = client.messages.parse(
                model=config.model,
                max_tokens=MAX_TOKENS,
                system=build_system_prompt(config),
                messages=[{"role": "user", "content": build_user_prompt(event, scenes, config)}],
                output_format=LLMStoryboardDraft,
            )
        except anthropic.APIError as exc:
            raise StoryboardGenerationError(f"Claude storyboard request failed: {exc}") from exc

        draft = response.parsed_output
        if draft is None:
            raise StoryboardGenerationError("Claude returned no parsable storyboard.")

        return assemble_storyboard(
            draft, event, scenes, config, generated_by=self.name, model=config.model
        )
