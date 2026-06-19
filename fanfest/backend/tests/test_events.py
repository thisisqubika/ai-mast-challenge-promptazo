import io

from fastapi.testclient import TestClient


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
        data={"uploader_id": non_checked_in_user["id"], "uploader_name": non_checked_in_user["name"]},
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
