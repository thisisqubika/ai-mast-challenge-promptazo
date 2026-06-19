"""Domain entity dataclasses for FanFest.

These are the canonical in-memory model layer. They live here (models/)
rather than in schemas/ because schemas/ owns the API contract (Pydantic);
models/ owns the domain shape (dataclasses, no runtime validation overhead).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    id: str
    home_team: str
    home_flag: str
    away_team: str
    away_flag: str
    venue_name: str
    venue_address: str
    organizer: str
    kickoff_iso: str
    match_start_time: datetime
    invite_link: str
    calendar_link: str
    maps_link: str
    # "future" | "live" | "past"
    status: str = "future"
    # ID of the match state entity used for AI recap (only set when status="past")
    recap_event_id: str | None = None


@dataclass
class Fan:
    user_id: str
    name: str
    location: str | None = None


@dataclass
class Registration:
    user_id: str
    event_id: str
    registered_at: datetime
    checked_in: bool = False
    checked_in_at: datetime | None = None


@dataclass
class Goal:
    player: str
    team: str
    minute: int


@dataclass
class Match:
    event_id: str
    home_team: str
    away_team: str
    venue: str
    home_score: int = 0
    away_score: int = 0
    status: str = "pre"
    clock_seconds: int = 0
    goals: list[Goal] = field(default_factory=list)


@dataclass
class Prediction:
    user_id: str
    event_id: str
    home_score: int
    away_score: int
    submitted_at: datetime


@dataclass
class Photo:
    id: str
    event_id: str
    url: str
    uploader_id: str
    uploader_name: str
    uploaded_at: datetime
