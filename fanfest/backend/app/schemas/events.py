from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
