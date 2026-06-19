from datetime import datetime

from pydantic import BaseModel, Field


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
