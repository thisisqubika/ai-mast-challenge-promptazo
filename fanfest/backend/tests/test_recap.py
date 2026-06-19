"""Tests for POST /api/v1/events/{event_id}/recap."""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


RECAP_URL = "/api/v1/events/event_001/recap"
DEFAULT_BODY = {"tone": "emocionante", "slide_count": 4}


def _make_anthropic_response(highlights: list[dict], narrative: str) -> MagicMock:
    content_block = MagicMock()
    content_block.text = json.dumps({"highlights": highlights, "narrative": narrative})
    message = MagicMock()
    message.content = [content_block]
    return message


def _end_match(client: TestClient) -> None:
    client.post("/api/v1/events/event_001/match-state", json={"action": "end"})


def test_create_recap_returns_narrative(client: TestClient) -> None:
    _end_match(client)
    mock_highlights = [
        {"label": "Gol épico", "description": "Un golazo impresionante en el minuto 45"},
        {"label": "Atajada", "description": "El arquero salvó al equipo"},
    ]
    mock_response = _make_anthropic_response(mock_highlights, "Un partido increíble.")

    with patch("app.services.recap_service.anthropic.Anthropic") as mock_cls, \
         patch("app.services.recap_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_model = "claude-sonnet-4-6"
        mock_cls.return_value.messages.create.return_value = mock_response
        response = client.post(RECAP_URL, json=DEFAULT_BODY)

    assert response.status_code == 200
    data = response.json()
    assert data["narrative"] == "Un partido increíble."
    assert len(data["highlights"]) > 0
    assert len(data["highlights"]) <= DEFAULT_BODY["slide_count"]
    assert data["fallback"] is False


def test_create_recap_fallback_on_ai_failure(client: TestClient) -> None:
    _end_match(client)

    with patch("app.services.recap_service.anthropic.Anthropic") as mock_cls, \
         patch("app.services.recap_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_model = "claude-sonnet-4-6"
        mock_cls.return_value.messages.create.side_effect = RuntimeError("API failure")
        response = client.post(RECAP_URL, json=DEFAULT_BODY)

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] is True
    assert len(data["highlights"]) > 0
    assert data["narrative"] != ""


def test_create_recap_empty_key_returns_fallback(client: TestClient) -> None:
    _end_match(client)

    with patch("app.services.recap_service.anthropic.Anthropic") as mock_cls, \
         patch("app.services.recap_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = ""
        response = client.post(RECAP_URL, json=DEFAULT_BODY)

    mock_cls.assert_not_called()
    assert response.status_code == 200
    assert response.json()["fallback"] is True


def test_create_recap_before_match_ends_returns_409(client: TestClient) -> None:
    client.post("/api/v1/events/event_001/match-state", json={"action": "goal", "player": "Diaz", "team": "River Plate", "minute": 10})
    response = client.post(RECAP_URL, json=DEFAULT_BODY)
    assert response.status_code == 409
    assert response.json()["detail"] == "Recap is only available after the match ends"


def test_create_recap_unknown_event_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/events/no_such_event/recap", json=DEFAULT_BODY)
    assert response.status_code == 404


def test_create_recap_invalid_tone_returns_422(client: TestClient) -> None:
    _end_match(client)
    response = client.post(RECAP_URL, json={"tone": "invalid", "slide_count": 4})
    assert response.status_code == 422


def test_create_recap_slide_count_caps_highlights(client: TestClient) -> None:
    _end_match(client)
    mock_highlights = [
        {"label": f"Momento {i}", "description": f"Descripcion {i}"}
        for i in range(5)
    ]
    mock_response = _make_anthropic_response(mock_highlights, "Gran partido.")

    with patch("app.services.recap_service.anthropic.Anthropic") as mock_cls, \
         patch("app.services.recap_service.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_model = "claude-sonnet-4-6"
        mock_cls.return_value.messages.create.return_value = mock_response
        response = client.post(RECAP_URL, json={"tone": "humorístico", "slide_count": 2})

    assert response.status_code == 200
    assert len(response.json()["highlights"]) <= 2
