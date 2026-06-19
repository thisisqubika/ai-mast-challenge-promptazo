from datetime import datetime, timezone

from fastapi import HTTPException

from app.services import registry

# ---------------------------------------------------------------------------
# In-process persistent store (survives for the lifetime of the process).
# Keys:
#   _events       : event_id -> event dict
#   _predictions  : (user_id, event_id) -> prediction dict
#   _attendees    : event_id -> set of user_ids
# ---------------------------------------------------------------------------

_events: dict[str, dict] = {
    "evt-001": {
        "id": "evt-001",
        "home_team": "Argentina",
        "home_flag": "\U0001f1e6\U0001f1f7",
        "away_team": "Brasil",
        "away_flag": "\U0001f1e7\U0001f1f7",
        "venue_name": "La Bombonera",
        "venue_address": "Brandsen 805, Buenos Aires",
        "organizer": "FanFest HQ",
        "kickoff_iso": "2030-01-01T18:00:00Z",
        "match_start_time": datetime(2030, 1, 1, 18, 0, tzinfo=timezone.utc),
        "invite_link": "http://localhost:8000/api/v1/events/evt-001/invite",
        "calendar_link": (
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE"
            "&text=Argentina+vs+Brasil"
            "&dates=20300101T180000Z/20300101T200000Z"
            "&location=Brandsen+805%2C+Buenos+Aires"
        ),
        "maps_link": (
            "https://www.google.com/maps/dir/"
            "?api=1&destination=Brandsen+805%2C+Buenos+Aires"
        ),
    }
}

_predictions: dict[tuple, dict] = {}

_attendees: dict[str, set] = {"evt-001": set()}


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
