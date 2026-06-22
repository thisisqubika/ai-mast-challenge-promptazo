"""Tests for FEST-13: API-Football integration endpoints and services."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EVENT_ID = "event_001"
FIXTURE_ID = 12345

_API_MATCH_STATE = {
    "status": "ended",
    "home_score": 2,
    "away_score": 1,
    "goals": [
        {"player": "Gallardo", "team": "River Plate", "minute": 34},
        {"player": "Tevez", "team": "Boca Juniors", "minute": 55},
        {"player": "Mora", "team": "River Plate", "minute": 78},
    ],
}


# ---------------------------------------------------------------------------
# Status mapping — pure unit test, no I/O
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "short, expected",
    [
        ("NS", "pre"),
        ("1H", "live"),
        ("HT", "live"),
        ("2H", "live"),
        ("ET", "live"),
        ("BT", "live"),
        ("P", "live"),
        ("LIVE", "live"),
        ("FT", "ended"),
        ("AET", "ended"),
        ("PEN", "ended"),
        ("TBD", "pre"),
        ("CANC", "pre"),
    ],
)
def test_status_mapping(short: str, expected: str) -> None:
    from app.services.football_api import _map_status

    assert _map_status(short) == expected


# ---------------------------------------------------------------------------
# Endpoints — no API key configured -> 503
# ---------------------------------------------------------------------------


def test_search_fixtures_no_api_key_returns_503() -> None:
    with patch("app.api.v1.endpoints.events.settings") as mock_settings:
        mock_settings.api_football_key = ""
        response = client.get("/api/v1/events/fixtures/search?team=river&date=2026-06-22")
    assert response.status_code == 503
    assert "API_FOOTBALL_KEY" in response.json()["detail"]


def test_sync_fixture_no_api_key_returns_503() -> None:
    import app.services.match_state as ms

    ms._fixture_links[EVENT_ID] = FIXTURE_ID
    with patch("app.services.match_state.settings") as mock_settings:
        mock_settings.api_football_key = ""
        response = client.post(f"/api/v1/events/{EVENT_ID}/sync-fixture")
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# link-fixture endpoint — mocks football_api at service boundary
# ---------------------------------------------------------------------------


def test_link_fixture_endpoint_syncs_and_returns_match_state() -> None:
    with patch(
        "app.services.football_api.get_fixture_state",
        new=AsyncMock(return_value=_API_MATCH_STATE),
    ), patch("app.services.match_state.settings") as ms_settings:
        ms_settings.api_football_key = "test-key"
        response = client.post(
            f"/api/v1/events/{EVENT_ID}/link-fixture",
            json={"fixture_id": FIXTURE_ID},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ended"
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert len(data["goals"]) == 3


def test_link_fixture_unknown_event_returns_404() -> None:
    response = client.post(
        "/api/v1/events/no_such_event/link-fixture",
        json={"fixture_id": FIXTURE_ID},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# sync-fixture — throttle guard
# ---------------------------------------------------------------------------


def test_sync_fixture_returns_cached_within_throttle_window() -> None:
    import time

    import app.services.match_state as ms

    ms._fixture_links[EVENT_ID] = FIXTURE_ID
    ms._last_sync[EVENT_ID] = time.monotonic()

    with patch("app.services.match_state.settings") as mock_settings, patch(
        "app.services.football_api.get_fixture_state",
        new=AsyncMock(return_value=_API_MATCH_STATE),
    ) as mock_get:
        mock_settings.api_football_key = "test-key"
        response = client.post(f"/api/v1/events/{EVENT_ID}/sync-fixture")
        mock_get.assert_not_called()

    assert response.status_code == 200


def test_sync_fixture_no_fixture_linked_returns_404() -> None:
    with patch("app.services.match_state.settings") as mock_settings:
        mock_settings.api_football_key = "test-key"
        response = client.post(f"/api/v1/events/{EVENT_ID}/sync-fixture")
    assert response.status_code == 404
    assert "No fixture linked" in response.json()["detail"]


# ---------------------------------------------------------------------------
# search-fixtures endpoint — mocks football_api at endpoint boundary
# ---------------------------------------------------------------------------


def test_search_fixtures_returns_list() -> None:
    mock_fixtures = [
        {
            "fixture_id": FIXTURE_ID,
            "home_team": "River Plate",
            "away_team": "Boca Juniors",
            "date": "2026-06-22T20:00:00+00:00",
            "status": "pre",
            "home_score": 0,
            "away_score": 0,
        }
    ]
    with patch(
        "app.api.v1.endpoints.events.football_api.search_fixtures",
        new=AsyncMock(return_value=mock_fixtures),
    ), patch("app.api.v1.endpoints.events.settings") as mock_settings:
        mock_settings.api_football_key = "test-key"
        response = client.get(
            "/api/v1/events/fixtures/search?team=river&date=2026-06-22"
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["fixture_id"] == FIXTURE_ID
    assert data[0]["home_team"] == "River Plate"


def test_search_fixtures_empty_when_no_team_found() -> None:
    with patch(
        "app.api.v1.endpoints.events.football_api.search_fixtures",
        new=AsyncMock(return_value=[]),
    ), patch("app.api.v1.endpoints.events.settings") as mock_settings:
        mock_settings.api_football_key = "test-key"
        response = client.get(
            "/api/v1/events/fixtures/search?team=unknown_team_xyz&date=2026-06-22"
        )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# sync-fixture — successful API call updates match state
# ---------------------------------------------------------------------------


def test_sync_fixture_updates_state_after_throttle_window() -> None:
    import app.services.match_state as ms

    ms._fixture_links[EVENT_ID] = FIXTURE_ID
    ms._last_sync[EVENT_ID] = 0.0

    with patch(
        "app.services.football_api.get_fixture_state",
        new=AsyncMock(return_value=_API_MATCH_STATE),
    ), patch("app.services.match_state.settings") as mock_settings:
        mock_settings.api_football_key = "test-key"
        response = client.post(f"/api/v1/events/{EVENT_ID}/sync-fixture")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ended"
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert len(data["goals"]) == 3
