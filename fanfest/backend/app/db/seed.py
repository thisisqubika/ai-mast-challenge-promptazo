"""Idempotent seed: runs once on first boot, skipped on restarts."""

import json

from app.data.seed import EVENTS, PHOTOS, REGISTRATIONS
from app.db.database import get_session
from app.db.models import EventModel, PhotoModel, RegistrationModel

# Pre-generated recap videos shipped with the repo (event_id → relative URL).
# evt-002 removed so the AI video generation can be triggered fresh.
_PRE_GENERATED_VIDEOS: dict[str, str] = {}


def run_seed() -> None:
    with get_session() as db:
        if db.query(EventModel).count() > 0:
            _backfill_video_recaps(db)
            return

        for e in EVENTS:
            db.add(
                EventModel(
                    id=e.id,
                    home_team=e.home_team,
                    home_flag=e.home_flag,
                    away_team=e.away_team,
                    away_flag=e.away_flag,
                    venue_name=e.venue_name,
                    venue_address=e.venue_address,
                    organizer=e.organizer,
                    kickoff_iso=e.kickoff_iso,
                    match_start_time=e.match_start_time,
                    invite_link=e.invite_link,
                    calendar_link=e.calendar_link,
                    maps_link=e.maps_link,
                    status=e.status,
                    recap_event_id=e.recap_event_id,
                    competition=e.competition,
                    venue_distance=e.venue_distance,
                    amenities=json.dumps(e.amenities),
                    home_score=e.home_score,
                    away_score=e.away_score,
                )
            )

        for r in REGISTRATIONS:
            db.add(
                RegistrationModel(
                    user_id=r.user_id,
                    event_id=r.event_id,
                    user_name=r.user_id,
                    registered_at=r.registered_at,
                    checked_in=r.checked_in,
                    checked_in_at=r.checked_in_at,
                )
            )

        for p in PHOTOS:
            db.add(
                PhotoModel(
                    id=p.id,
                    event_id=p.event_id,
                    url=p.url,
                    uploader_id=p.uploader_id,
                    uploader_name=p.uploader_name,
                    uploaded_at=p.uploaded_at,
                )
            )

        _backfill_video_recaps(db)


def _backfill_video_recaps(db) -> None:
    for event_id, video_url in _PRE_GENERATED_VIDEOS.items():
        event = db.get(EventModel, event_id)
        if event and not event.recap_video_url:
            event.recap_video_url = video_url
