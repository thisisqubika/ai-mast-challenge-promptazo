"""
Tests for /api/v1/events/* endpoints.
FEST-02: event detail, predictions, check-in (5 BDD scenarios, 9 tests).
FEST-03: live match state and Hype Wall photos.
"""

import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import events_service

EVENT_ID = "evt-001"
MISSING_ID = "evt-999"

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_fest02_state():
    """Ensure evt-001 has a future match_start_time so predictions are open."""
    events_service.set_match_start_time(
        EVENT_ID, datetime(2030, 1, 1, 18, 0, tzinfo=timezone.utc)
    )
    yield


# ---------------------------------------------------------------------------
# FEST-02 — Scenario 1: view detail, predict, check in
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
    payload = {"user_id": "user-1", "name": "Alice", "home_score": 2, "away_score": 1}
    response = client.post(f"/api/v1/events/{EVENT_ID}/predictions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-1"
    assert data["event_id"] == EVENT_ID
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert events_service.has_prediction("user-1", EVENT_ID)


def test_checkin_marks_user_present():
    payload = {"user_id": "user-2", "name": "Bob"}
    response = client.post(f"/api/v1/events/{EVENT_ID}/checkin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-2"
    assert data["event_id"] == EVENT_ID
    assert data["checked_in"] is True
    assert events_service.is_attendee(EVENT_ID, "user-2")


# ---------------------------------------------------------------------------
# FEST-02 — Scenario 2: prediction locked after match start -> 409
# ---------------------------------------------------------------------------


def test_prediction_locked_after_match_start():
    events_service.set_match_start_time(
        EVENT_ID, datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    payload = {"user_id": "user-1", "name": "Alice", "home_score": 1, "away_score": 0}
    response = client.post(f"/api/v1/events/{EVENT_ID}/predictions", json=payload)
    assert response.status_code == 409
    assert "Predictions are closed" in response.json()["detail"]


# ---------------------------------------------------------------------------
# FEST-02 — Scenario 3: prediction overwrite before match start
# ---------------------------------------------------------------------------


def test_prediction_overwrite_before_match_start():
    base = {"user_id": "user-1", "name": "Alice"}
    client.post(
        f"/api/v1/events/{EVENT_ID}/predictions",
        json={**base, "home_score": 1, "away_score": 0},
    )
    response = client.post(
        f"/api/v1/events/{EVENT_ID}/predictions",
        json={**base, "home_score": 3, "away_score": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["home_score"] == 3
    assert data["away_score"] == 2
    assert events_service.count_predictions_for_user("user-1") == 1


# ---------------------------------------------------------------------------
# FEST-02 — Scenario 4: event not found -> 404
# ---------------------------------------------------------------------------


def test_event_not_found_returns_404():
    response = client.get(f"/api/v1/events/{MISSING_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_prediction_on_missing_event_returns_404():
    payload = {"user_id": "user-1", "name": "Alice", "home_score": 0, "away_score": 0}
    response = client.post(f"/api/v1/events/{MISSING_ID}/predictions", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_checkin_on_missing_event_returns_404():
    payload = {"user_id": "user-1", "name": "Alice"}
    response = client.post(f"/api/v1/events/{MISSING_ID}/checkin", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


# ---------------------------------------------------------------------------
# FEST-02 — Scenario 5: check-in without user identity -> 400
# ---------------------------------------------------------------------------


def test_checkin_without_user_identity_returns_400():
    response = client.post(
        f"/api/v1/events/{EVENT_ID}/checkin",
        json={"name": "Anonymous"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User identity required"


# ---------------------------------------------------------------------------
# FEST-03 — Live match state
# ---------------------------------------------------------------------------


def test_get_match_state(client: TestClient, sample_event_id: str) -> None:
    response = client.get(f"/api/v1/events/{sample_event_id}/match-state")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == sample_event_id
    assert data["status"] == "pre"
    assert data["home_score"] == 0
    assert data["away_score"] == 0


def test_get_match_state_unknown_event(client: TestClient) -> None:
    response = client.get("/api/v1/events/no_such_event/match-state")
    assert response.status_code == 404


def test_score_goal_updates_state(client: TestClient, sample_event_id: str) -> None:
    response = client.post(
        f"/api/v1/events/{sample_event_id}/match-state",
        json={"action": "goal", "player": "Gallardo", "team": "River Plate", "minute": 34},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert data["home_score"] == 1
    assert data["away_score"] == 0
    assert len(data["goals"]) == 1
    assert data["goals"][0]["player"] == "Gallardo"


def test_end_match_status(client: TestClient, sample_event_id: str) -> None:
    response = client.post(
        f"/api/v1/events/{sample_event_id}/match-state",
        json={"action": "end"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ended"


def test_reset_match_state(client: TestClient, sample_event_id: str) -> None:
    client.post(
        f"/api/v1/events/{sample_event_id}/match-state",
        json={"action": "goal", "player": "Tevez", "team": "Boca Juniors", "minute": 12},
    )
    response = client.post(
        f"/api/v1/events/{sample_event_id}/match-state",
        json={"action": "reset"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pre"
    assert data["home_score"] == 0
    assert data["goals"] == []


def test_upload_photo_checked_in(
    client: TestClient,
    sample_event_id: str,
    checked_in_user: dict[str, str],
) -> None:
    response = client.post(
        f"/api/v1/events/{sample_event_id}/photos",
        data={"uploader_id": checked_in_user["id"], "uploader_name": checked_in_user["name"]},
        files={"file": ("shot.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["uploader_name"] == checked_in_user["name"]
    assert "id" in data
    assert "url" in data


def test_upload_photo_not_checked_in_returns_403(
    client: TestClient,
    sample_event_id: str,
    non_checked_in_user: dict[str, str],
) -> None:
    response = client.post(
        f"/api/v1/events/{sample_event_id}/photos",
        data={
            "uploader_id": non_checked_in_user["id"],
            "uploader_name": non_checked_in_user["name"],
        },
        files={"file": ("shot.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")},
    )
    assert response.status_code == 403


def test_list_photos_returns_uploader(
    client: TestClient,
    sample_event_id: str,
    checked_in_user: dict[str, str],
) -> None:
    client.post(
        f"/api/v1/events/{sample_event_id}/photos",
        data={"uploader_id": checked_in_user["id"], "uploader_name": checked_in_user["name"]},
        files={"file": ("shot.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")},
    )
    response = client.get(f"/api/v1/events/{sample_event_id}/photos")
    assert response.status_code == 200
    photos = response.json()["photos"]
    assert len(photos) == 1
    assert photos[0]["uploader_name"] == checked_in_user["name"]
