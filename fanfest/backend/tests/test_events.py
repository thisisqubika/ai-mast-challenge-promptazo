"""
Tests for /api/v1/events/* endpoints.
Covers all 5 BDD scenarios from FEST-02.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import events_service

EVENT_ID = "evt-001"
MISSING_ID = "evt-999"

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Isolate test state: clear predictions and attendees before every test."""
    events_service._predictions.clear()
    events_service._attendees[EVENT_ID] = set()
    # Restore match_start_time in case a test moved it to the past.
    events_service._events[EVENT_ID]["match_start_time"] = datetime(
        2030, 1, 1, 18, 0, tzinfo=timezone.utc
    )
    yield


# ---------------------------------------------------------------------------
# Scenario 1 — Fan views event detail, submits prediction, checks in
# ---------------------------------------------------------------------------


def test_get_event_detail_returns_full_data():
    response = client.get(f"/api/v1/events/{EVENT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == EVENT_ID
    assert data["home_team"] == "Argentina"
    assert data["away_team"] == "Brasil"
    assert data["venue_name"] == "La Bombonera"
    assert data["organizer"] == "FanFest HQ"
    assert "invite_link" in data
    assert "calendar_link" in data
    assert "maps_link" in data
    assert isinstance(data["attendees"], list)


def test_submit_prediction_persisted_and_returned():
    payload = {
        "user_id": "user-1",
        "name": "Alice",
        "home_score": 2,
        "away_score": 1,
    }
    response = client.post(f"/api/v1/events/{EVENT_ID}/predictions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-1"
    assert data["event_id"] == EVENT_ID
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    # Side-effect: prediction stored in the service
    assert ("user-1", EVENT_ID) in events_service._predictions


def test_checkin_marks_user_present():
    payload = {"user_id": "user-2", "name": "Bob"}
    response = client.post(f"/api/v1/events/{EVENT_ID}/checkin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-2"
    assert data["event_id"] == EVENT_ID
    assert data["checked_in"] is True
    # Side-effect: user recorded in attendees set
    assert "user-2" in events_service._attendees[EVENT_ID]


# ---------------------------------------------------------------------------
# Scenario 2 — Prediction lock: match already started → 409
# ---------------------------------------------------------------------------


def test_prediction_locked_after_match_start():
    # Move match_start_time into the past to simulate a started match.
    events_service._events[EVENT_ID]["match_start_time"] = datetime(
        2000, 1, 1, tzinfo=timezone.utc
    )
    payload = {
        "user_id": "user-1",
        "name": "Alice",
        "home_score": 1,
        "away_score": 0,
    }
    response = client.post(f"/api/v1/events/{EVENT_ID}/predictions", json=payload)
    assert response.status_code == 409
    assert "Predictions are closed" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Scenario 3 — Prediction overwrite before match starts → last write wins
# ---------------------------------------------------------------------------


def test_prediction_overwrite_before_match_start():
    base_payload = {"user_id": "user-1", "name": "Alice"}

    # First prediction
    client.post(
        f"/api/v1/events/{EVENT_ID}/predictions",
        json={**base_payload, "home_score": 1, "away_score": 0},
    )
    # Second prediction (overwrite)
    response = client.post(
        f"/api/v1/events/{EVENT_ID}/predictions",
        json={**base_payload, "home_score": 3, "away_score": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["home_score"] == 3
    assert data["away_score"] == 2
    # Only one record should exist for this user/event pair.
    assert len([k for k in events_service._predictions if k[0] == "user-1"]) == 1


# ---------------------------------------------------------------------------
# Scenario 4 — Unknown event → 404
# ---------------------------------------------------------------------------


def test_event_not_found_returns_404():
    response = client.get(f"/api/v1/events/{MISSING_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_prediction_on_missing_event_returns_404():
    payload = {
        "user_id": "user-1",
        "name": "Alice",
        "home_score": 0,
        "away_score": 0,
    }
    response = client.post(f"/api/v1/events/{MISSING_ID}/predictions", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_checkin_on_missing_event_returns_404():
    payload = {"user_id": "user-1", "name": "Alice"}
    response = client.post(f"/api/v1/events/{MISSING_ID}/checkin", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


# ---------------------------------------------------------------------------
# Scenario 5 — Check-in without user identity → 400
# ---------------------------------------------------------------------------


def test_checkin_without_user_identity_returns_400():
    # Omit user_id entirely (it is Optional, so this is a valid JSON body)
    response = client.post(
        f"/api/v1/events/{EVENT_ID}/checkin",
        json={"name": "Anonymous"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User identity required"
