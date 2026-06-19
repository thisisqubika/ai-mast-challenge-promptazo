from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# FEST-02: Event detail, predictions, check-in
# ---------------------------------------------------------------------------


class AttendeeOut(BaseModel):
    user_id: str
    name: str
    checked_in: bool


class EventDetail(BaseModel):
    id: str
    home_team: str
    home_flag: str
    away_team: str
    away_flag: str
    kickoff_iso: str
    match_start_time: datetime
    venue_name: str
    venue_address: str
    organizer: str
    attendees: list[AttendeeOut]
    invite_link: str
    calendar_link: str
    maps_link: str


class PredictionRequest(BaseModel):
    user_id: str
    name: str
    home_score: int = Field(ge=0, le=9)
    away_score: int = Field(ge=0, le=9)


class PredictionResponse(BaseModel):
    user_id: str
    event_id: str
    home_score: int
    away_score: int


class CheckinRequest(BaseModel):
    user_id: str | None = None
    name: str | None = None


class CheckinResponse(BaseModel):
    user_id: str
    event_id: str
    checked_in: bool


# ---------------------------------------------------------------------------
# FEST-03: Live match state, Hype Wall photos
# ---------------------------------------------------------------------------


class Goal(BaseModel):
    player: str
    team: str
    minute: int


class MatchState(BaseModel):
    event_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: Literal["pre", "live", "ended"]
    clock_seconds: int
    venue: str
    goals: list[Goal]


class Photo(BaseModel):
    id: str
    url: str
    uploader_name: str
    uploaded_at: datetime


class PhotoList(BaseModel):
    photos: list[Photo]


class PhotoUploadForm(BaseModel):
    uploader_id: str
    uploader_name: str


class MatchStateUpdate(BaseModel):
    action: Literal["goal", "end", "reset"]
    player: str | None = None
    team: str | None = None
    minute: int | None = None


# ---------------------------------------------------------------------------
# FEST-04: AI-generated event recap
# ---------------------------------------------------------------------------


class RecapRequest(BaseModel):
    tone: Literal["emocionante", "inspirador", "humorístico", "nostálgico"] = "emocionante"
    slide_count: int = Field(4, ge=1, le=10)


class RecapHighlight(BaseModel):
    label: str
    description: str


class RecapResponse(BaseModel):
    event_id: str
    narrative: str
    highlights: list[RecapHighlight]
    correct_predictors: list[str] = []
    fallback: bool = False
    home_score: int
    away_score: int
    home_team: str
    away_team: str
    photo_count: int


# ---------------------------------------------------------------------------
# Events list
# ---------------------------------------------------------------------------


class EventSummary(BaseModel):
    id: str
    home_team: str
    home_flag: str
    home_abbr: str
    away_team: str
    away_flag: str
    away_abbr: str
    kickoff_iso: str
    status: str
    recap_event_id: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    photo_count: int = 0
