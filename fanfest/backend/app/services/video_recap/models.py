"""Pydantic data models for the video recap pipeline.

Three groups:
  * Input contract  -- what the pipeline consumes from FanFest event data.
  * Normalized timeline -- internal sorted scenes written to ``normalized-input.json``.
  * Storyboard contract -- the boundary between the AI story layer and the renderer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Input contract
# --------------------------------------------------------------------------- #


class EventSummary(BaseModel):
    id: str
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    kickoff_iso: Optional[str] = None
    status: Optional[str] = None
    photo_count: Optional[int] = None


class EventDetail(BaseModel):
    id: str
    home_team: str
    away_team: str
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    organizer: Optional[str] = None
    kickoff_iso: Optional[str] = None


class MatchState(BaseModel):
    event_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: Optional[str] = None
    venue: Optional[str] = None


class ChampionshipContext(BaseModel):
    club: str
    competition: str
    result_label: str
    historical_angle: Optional[str] = None
    recap_angle: Optional[str] = None


class MediaComment(BaseModel):
    id: Optional[str] = None
    user_name: Optional[str] = None
    text: str
    created_at: Optional[datetime] = None


class MediaItem(BaseModel):
    id: str
    url: str
    uploaded_at: datetime
    media_type: str = "photo"
    caption: Optional[str] = None
    likes_count: int = 0
    comments: list[MediaComment] = Field(default_factory=list)
    uploader_name: Optional[str] = None


class EventImage(BaseModel):
    image_ref: str
    date_time: datetime
    event_name: str
    event_description: str
    place_location: str
    comments: list[str] = Field(default_factory=list)
    likes: int = 0


class ExcludedAsset(BaseModel):
    image_ref: str
    reason: Optional[str] = None


class EventInput(BaseModel):
    event_id: str
    event_summary: EventSummary
    event_detail: EventDetail
    match_state: MatchState
    championship_context: ChampionshipContext
    media: list[MediaItem]
    event_images: list[EventImage]
    excluded_assets: list[ExcludedAsset] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Normalized timeline (internal)
# --------------------------------------------------------------------------- #

Phase = Literal["arrival", "buildup", "peak", "closing"]


class TimelineScene(BaseModel):
    scene_index: int
    source_id: str
    image_ref: str
    image_path: Optional[str] = None  # absolute, filled by the assets stage
    width: Optional[int] = None
    height: Optional[int] = None
    date_time: datetime
    event_name: str
    description: str
    place: str
    comments: list[str] = Field(default_factory=list)
    likes: int = 0
    phase: Phase = "buildup"
    social_score: int = 0


class NormalizedInput(BaseModel):
    event_id: str
    title: str
    home_team: str
    away_team: str
    result_label: str
    venue: Optional[str] = None
    competition: Optional[str] = None
    language: str
    scene_count: int
    scenes: list[TimelineScene]


# --------------------------------------------------------------------------- #
# Storyboard contract (AI story layer -> deterministic renderer)
# --------------------------------------------------------------------------- #


class VisualTreatment(BaseModel):
    effect: str = "ken_burns"
    direction: str = "in"
    fill: str = "blurred"


class Transition(BaseModel):
    type: str = "crossfade"
    duration: float = 0.6


class OverlayText(BaseModel):
    event: Optional[str] = None
    datetime: Optional[str] = None
    place: Optional[str] = None
    championship: Optional[str] = None
    key_moment: Optional[str] = None


class StoryboardScene(BaseModel):
    scene_id: str
    source_image: str
    chronological_position: int
    source_timestamp: str
    scene_title: str
    scene_description: str
    script_text: str
    subtitle_text: str
    visual_treatment: VisualTreatment = Field(default_factory=VisualTreatment)
    transition: Transition = Field(default_factory=Transition)
    duration: float
    overlay_text: OverlayText = Field(default_factory=OverlayText)
    highlight: Optional[str] = None
    social_summary: Optional[str] = None


class StoryboardMeta(BaseModel):
    event_id: str
    title: str
    language: str
    total_duration: float
    generated_by: str
    model: Optional[str] = None


class Storyboard(BaseModel):
    meta: StoryboardMeta
    scenes: list[StoryboardScene]
