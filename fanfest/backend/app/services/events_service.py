import dataclasses
from datetime import datetime, timezone

from fastapi import HTTPException

from app.data.seed import EVENTS, FAN_NAMES, PREDICTIONS, REGISTRATIONS
from app.services import registry

# ---------------------------------------------------------------------------
# In-process persistent store (survives for the lifetime of the process).
# Keys:
#   _events       : event_id -> event dict
#   _predictions  : (user_id, event_id) -> prediction dict
#   _attendees    : event_id -> set of user_ids
# ---------------------------------------------------------------------------

_events: dict[str, dict] = {e.id: dataclasses.asdict(e) for e in EVENTS}

_predictions: dict[tuple, dict] = {
    (p.user_id, p.event_id): {
        "user_id": p.user_id,
        "event_id": p.event_id,
        "name": FAN_NAMES.get(p.user_id, p.user_id),
        "home_score": p.home_score,
        "away_score": p.away_score,
    }
    for p in PREDICTIONS
}


def _seed_attendees() -> dict[str, set]:
    acc: dict[str, set] = {}
    for r in REGISTRATIONS:
        if r.checked_in:
            acc.setdefault(r.event_id, set()).add(r.user_id)
    acc.setdefault("evt-001", set())
    return acc


_attendees: dict[str, set] = _seed_attendees()


# ---------------------------------------------------------------------------
# Helper: attendees set for an event (creates empty set if missing).
# ---------------------------------------------------------------------------


def _get_attendee_set(event_id: str) -> set:
    if event_id not in _attendees:
        _attendees[event_id] = set()
    return _attendees[event_id]


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


def get_event(event_id: str) -> dict:
    """Return the event dict or raise 404."""
    event = _events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def upsert_prediction(
    event_id: str,
    user_id: str,
    name: str,
    home_score: int,
    away_score: int,
) -> dict:
    """
    Persist (or overwrite) a prediction for (user_id, event_id).

    Raises:
        HTTPException 404 — event not found.
        HTTPException 409 — match has already started (predictions closed).
    """
    event = get_event(event_id)

    now = datetime.now(tz=timezone.utc)
    if now >= event["match_start_time"]:
        raise HTTPException(
            status_code=409,
            detail="Predictions are closed (match has started)",
        )

    prediction = {
        "user_id": user_id,
        "event_id": event_id,
        "name": name,
        "home_score": home_score,
        "away_score": away_score,
    }
    _predictions[(user_id, event_id)] = prediction
    return prediction


def checkin_user(event_id: str, user_id: str, name: str) -> dict:
    """
    Idempotently add user_id to the attendees set for event_id.

    Raises:
        HTTPException 404 — event not found.
    """
    get_event(event_id)  # validates event exists

    attendee_set = _get_attendee_set(event_id)
    attendee_set.add(user_id)
    registry.register(user_id, name)

    return {
        "user_id": user_id,
        "event_id": event_id,
        "checked_in": True,
    }
