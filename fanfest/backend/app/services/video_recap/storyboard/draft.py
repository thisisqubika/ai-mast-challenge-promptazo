"""Shared LLM draft schema + merge logic for all LLM providers."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..config import RecapConfig
from ..errors import StoryboardGenerationError
from ..models import (
    EventInput,
    OverlayText,
    Storyboard,
    StoryboardMeta,
    StoryboardScene,
    TimelineScene,
    Transition,
    VisualTreatment,
)


class LLMVisualDraft(BaseModel):
    effect: str = "ken_burns"
    direction: str = "in"


class LLMTransitionDraft(BaseModel):
    type: str = "crossfade"
    duration: float = 0.6


class LLMOverlayDraft(BaseModel):
    event: Optional[str] = None
    championship: Optional[str] = None
    key_moment: Optional[str] = None


class LLMSceneDraft(BaseModel):
    index: int
    scene_title: str
    scene_description: str
    script_text: str
    subtitle_text: str
    visual_treatment: LLMVisualDraft = Field(default_factory=LLMVisualDraft)
    transition: LLMTransitionDraft = Field(default_factory=LLMTransitionDraft)
    duration: float
    overlay: LLMOverlayDraft = Field(default_factory=LLMOverlayDraft)
    highlight: Optional[str] = None
    social_summary: Optional[str] = None


class LLMStoryboardDraft(BaseModel):
    title: str
    scenes: list[LLMSceneDraft]


def opening_context_line(event: EventInput, scene: TimelineScene) -> str:
    venue = event.event_detail.venue_name
    date = scene.date_time.strftime("%d %b %Y")
    return f"{date} - {venue}" if venue else date


def assemble_storyboard(
    draft: LLMStoryboardDraft,
    event: EventInput,
    scenes: list[TimelineScene],
    config: RecapConfig,
    *,
    generated_by: str,
    model: str,
) -> Storyboard:
    drafts_by_index = {d.index: d for d in draft.scenes}

    sb_scenes: list[StoryboardScene] = []
    for scene in scenes:
        d = drafts_by_index.get(scene.scene_index)
        if d is None:
            raise StoryboardGenerationError(
                f"Model did not return a scene for chronological position {scene.scene_index}."
            )
        datetime_line = opening_context_line(event, scene) if scene.scene_index == 1 else None

        sb_scenes.append(
            StoryboardScene(
                scene_id=scene.source_id,
                source_image=scene.image_ref,
                chronological_position=scene.scene_index,
                source_timestamp=scene.date_time.isoformat(),
                scene_title=d.scene_title,
                scene_description=d.scene_description,
                script_text=d.script_text,
                subtitle_text=d.subtitle_text,
                visual_treatment=VisualTreatment(
                    effect=d.visual_treatment.effect,
                    direction=d.visual_treatment.direction,
                    fill="blurred",
                ),
                transition=Transition(type=d.transition.type, duration=d.transition.duration),
                duration=d.duration,
                overlay_text=OverlayText(
                    event=d.overlay.event,
                    datetime=datetime_line,
                    place=None,
                    championship=d.overlay.championship,
                    key_moment=d.overlay.key_moment,
                ),
                highlight=d.highlight,
                social_summary=d.social_summary,
            )
        )

    meta = StoryboardMeta(
        event_id=event.event_id,
        title=draft.title,
        language=config.language,
        total_duration=round(sum(s.duration for s in sb_scenes), 2),
        generated_by=generated_by,
        model=model,
    )
    return Storyboard(meta=meta, scenes=sb_scenes)
