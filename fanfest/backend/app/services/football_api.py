"""Async HTTP client for API-Football v3 (https://v3.football.api-sports.io)."""

import httpx
from fastapi import HTTPException

from app.core.config import settings

_BASE_URL = "https://v3.football.api-sports.io"

_LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE"}
_ENDED_STATUSES = {"FT", "AET", "PEN"}


def _auth_headers() -> dict[str, str]:
    return {"x-apisports-key": settings.api_football_key}


def _raise_for_errors(data: dict) -> None:
    errors = data.get("errors")
    if not errors:
        return
    if isinstance(errors, dict):
        msg = "; ".join(f"{k}: {v}" for k, v in errors.items())
    else:
        msg = str(errors)
    status = 503 if "token" in str(errors).lower() or "key" in str(errors).lower() else 422
    raise HTTPException(status_code=status, detail=f"API-Football error: {msg}")


def _map_status(short: str) -> str:
    if short in _LIVE_STATUSES:
        return "live"
    if short in _ENDED_STATUSES:
        return "ended"
    return "pre"


async def search_fixtures(team: str, date: str) -> list[dict]:
    """Search fixtures by team name substring and date (YYYY-MM-DD).

    Fetches all fixtures for the given date and filters by team name locally.
    Works on the API-Football free plan.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_BASE_URL}/fixtures",
                params={"date": date},
                headers=_auth_headers(),
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=503, detail="API-Football unreachable") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="API-Football unreachable") from exc

    if resp.status_code == 401:
        raise HTTPException(status_code=503, detail="API-Football authentication failed")

    data = resp.json()
    _raise_for_errors(data)

    needle = team.lower()
    return [
        {
            "fixture_id": f["fixture"]["id"],
            "league": f["league"]["name"],
            "home_team": f["teams"]["home"]["name"],
            "away_team": f["teams"]["away"]["name"],
            "date": f["fixture"]["date"],
            "status": _map_status(f["fixture"]["status"]["short"]),
            "home_score": f["goals"]["home"] if f["goals"]["home"] is not None else 0,
            "away_score": f["goals"]["away"] if f["goals"]["away"] is not None else 0,
        }
        for f in data.get("response", [])
        if needle in f["teams"]["home"]["name"].lower()
        or needle in f["teams"]["away"]["name"].lower()
    ]


async def get_fixture_state(fixture_id: int) -> dict:
    """Fetch a single fixture by ID and map it to a MatchState-compatible dict.

    Returns {status, home_score, away_score, goals: [{player, team, minute}]}.
    Raises HTTP 404 if the fixture_id is not found in the API response.
    Raises HTTP 503 on network errors or auth failures.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_BASE_URL}/fixtures",
                params={"id": fixture_id},
                headers=_auth_headers(),
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=503, detail="API-Football unreachable") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="API-Football unreachable") from exc

    if resp.status_code == 401:
        raise HTTPException(status_code=503, detail="API-Football authentication failed")

    data = resp.json()
    _raise_for_errors(data)

    fixtures = data.get("response", [])
    if not fixtures:
        raise HTTPException(status_code=404, detail="Fixture not found")

    fixture = fixtures[0]
    status_short = fixture["fixture"]["status"]["short"]
    home_score = fixture["goals"]["home"] if fixture["goals"]["home"] is not None else 0
    away_score = fixture["goals"]["away"] if fixture["goals"]["away"] is not None else 0

    _EXCLUDED_DETAILS = {"Missed Penalty", "Penalty Shootout Miss"}
    goals = [
        {
            "player": event["player"]["name"],
            "team": event["team"]["name"],
            "minute": event["time"]["elapsed"],
        }
        for event in fixture.get("events", [])
        if event.get("type") == "Goal"
        and event.get("detail") not in _EXCLUDED_DETAILS
    ]

    return {
        "status": _map_status(status_short),
        "home_score": home_score,
        "away_score": away_score,
        "goals": goals,
    }
