from datetime import datetime, timezone

from fastapi import HTTPException

from app.db.database import get_session
from app.db.models import EventModel, PredictionModel, RegistrationModel


def _event_to_dict(e: EventModel) -> dict:
    return {
        "id": e.id,
        "home_team": e.home_team,
        "home_flag": e.home_flag,
        "away_team": e.away_team,
        "away_flag": e.away_flag,
        "venue_name": e.venue_name,
        "venue_address": e.venue_address,
        "organizer": e.organizer,
        "kickoff_iso": e.kickoff_iso,
        "match_start_time": e.match_start_time,
        "invite_link": e.invite_link,
        "calendar_link": e.calendar_link,
        "maps_link": e.maps_link,
        "status": e.status,
        "recap_event_id": e.recap_event_id,
    }


def list_events(status: str | None = None) -> list[dict]:
    with get_session() as db:
        query = db.query(EventModel)
        if status:
            query = query.filter(EventModel.status == status)
        return [_event_to_dict(e) for e in query.all()]


def get_event(event_id: str) -> dict:
    with get_session() as db:
        event = db.query(EventModel).filter_by(id=event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_dict(event)


def get_attendees(event_id: str) -> list[dict]:
    with get_session() as db:
        rows = (
            db.query(RegistrationModel)
            .filter_by(event_id=event_id, checked_in=True)
            .all()
        )
        return [{"user_id": r.user_id, "name": r.user_name or r.user_id} for r in rows]


def upsert_prediction(
    event_id: str,
    user_id: str,
    name: str,
    home_score: int,
    away_score: int,
) -> dict:
    event = get_event(event_id)

    now = datetime.now(tz=timezone.utc)
    match_start = event["match_start_time"]
    if match_start.tzinfo is None:
        match_start = match_start.replace(tzinfo=timezone.utc)
    if now >= match_start:
        raise HTTPException(
            status_code=409,
            detail="Predictions are closed (match has started)",
        )

    with get_session() as db:
        pred = (
            db.query(PredictionModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .first()
        )
        if pred is None:
            pred = PredictionModel(
                user_id=user_id,
                event_id=event_id,
                user_name=name,
                home_score=home_score,
                away_score=away_score,
                submitted_at=datetime.now(timezone.utc),
            )
            db.add(pred)
        else:
            pred.home_score = home_score
            pred.away_score = away_score
            pred.user_name = name
            pred.submitted_at = datetime.now(timezone.utc)

    return {
        "user_id": user_id,
        "event_id": event_id,
        "name": name,
        "home_score": home_score,
        "away_score": away_score,
    }


def checkin_user(event_id: str, user_id: str, name: str) -> dict:
    get_event(event_id)  # raises 404 if missing

    with get_session() as db:
        reg = (
            db.query(RegistrationModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        if reg is None:
            db.add(
                RegistrationModel(
                    user_id=user_id,
                    event_id=event_id,
                    user_name=name,
                    registered_at=now,
                    checked_in=True,
                    checked_in_at=now,
                )
            )
        else:
            reg.checked_in = True
            reg.checked_in_at = now
            reg.user_name = name

    return {"user_id": user_id, "event_id": event_id, "checked_in": True}


# ── Test helpers ──────────────────────────────────────────────────────────────

def has_prediction(user_id: str, event_id: str) -> bool:
    with get_session() as db:
        return (
            db.query(PredictionModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .count()
            > 0
        )


def is_attendee(event_id: str, user_id: str) -> bool:
    with get_session() as db:
        return (
            db.query(RegistrationModel)
            .filter_by(event_id=event_id, user_id=user_id, checked_in=True)
            .count()
            > 0
        )


def count_predictions_for_user(user_id: str) -> int:
    with get_session() as db:
        return db.query(PredictionModel).filter_by(user_id=user_id).count()


def set_match_start_time(event_id: str, dt: datetime) -> None:
    with get_session() as db:
        event = db.query(EventModel).filter_by(id=event_id).first()
        if event:
            event.match_start_time = dt
