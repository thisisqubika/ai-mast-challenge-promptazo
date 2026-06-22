"""Module-level in-memory match state store, dev-advanceable for demo purposes."""

import time

from fastapi import HTTPException

from app.core.config import settings
from app.data.seed import MATCHES
from app.schemas.events import Goal, MatchState


def _build_state(m) -> MatchState:
    return MatchState(
        event_id=m.event_id,
        home_team=m.home_team,
        away_team=m.away_team,
        home_score=m.home_score,
        away_score=m.away_score,
        status=m.status,
        clock_seconds=m.clock_seconds,
        venue=m.venue,
        goals=[Goal(player=g.player, team=g.team, minute=g.minute) for g in m.goals],
    )


_states: dict[str, MatchState] = {m.event_id: _build_state(m) for m in MATCHES}
_fixture_links: dict[str, int] = {}
_last_sync: dict[str, float] = {}
SYNC_THROTTLE_SECONDS = 60


def _init_from_db(event_id: str) -> MatchState | None:
    """Try to build a default pre-match state from the DB for a user-created event."""
    try:
        from app.services.events_service import get_event  # lazy to avoid circular import
        ev = get_event(event_id)
        match_status = "ended" if ev.get("status") == "past" else "pre"
        state = MatchState(
            event_id=event_id,
            home_team=ev["home_team"],
            away_team=ev["away_team"],
            home_score=ev.get("home_score") or 0,
            away_score=ev.get("away_score") or 0,
            status=match_status,
            clock_seconds=0,
            venue=ev.get("venue_name", ""),
            goals=[],
        )
        _states[event_id] = state
        return state
    except Exception:
        return None


def _persist(state: MatchState) -> None:
    """Best-effort write of current score to DB so it survives restarts."""
    try:
        from app.services.events_service import persist_score  # lazy to avoid circular import
        persist_score(state.event_id, state.home_score, state.away_score)
    except Exception:
        pass


def get_state(event_id: str) -> MatchState:
    state = _states.get(event_id)
    if state is None:
        state = _init_from_db(event_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return state


def score_goal(event_id: str, player: str, team: str, minute: int) -> MatchState:
    state = get_state(event_id)
    goal = Goal(player=player, team=team, minute=minute)
    updated_goals = list(state.goals) + [goal]
    home_score = state.home_score + (1 if team == state.home_team else 0)
    away_score = state.away_score + (1 if team == state.away_team else 0)
    updated = state.model_copy(
        update={
            "status": "live",
            "goals": updated_goals,
            "home_score": home_score,
            "away_score": away_score,
        }
    )
    _states[event_id] = updated
    _persist(updated)
    return updated


def end_match(event_id: str) -> MatchState:
    state = get_state(event_id)
    updated = state.model_copy(update={"status": "ended"})
    _states[event_id] = updated
    _persist(updated)
    return updated


def reset(event_id: str) -> MatchState:
    state = get_state(event_id)
    updated = state.model_copy(
        update={
            "home_score": 0,
            "away_score": 0,
            "status": "pre",
            "clock_seconds": 0,
            "goals": [],
        }
    )
    _states[event_id] = updated
    return updated


def link_fixture(event_id: str, fixture_id: int) -> None:
    """Store the API-Football fixture_id link for a FanFest event."""
    _fixture_links[event_id] = fixture_id


async def sync_from_api(event_id: str) -> MatchState:
    """Fetch fresh match state from API-Football and update the in-memory store.

    Respects SYNC_THROTTLE_SECONDS: returns cached state if called within the window.
    Raises HTTP 404 if the event has no fixture linked.
    Raises HTTP 503 if API_FOOTBALL_KEY is not configured.
    """
    if not settings.api_football_key:
        raise HTTPException(status_code=503, detail="API_FOOTBALL_KEY is not configured")

    if event_id not in _fixture_links:
        raise HTTPException(status_code=404, detail="No fixture linked to this event")

    last = _last_sync.get(event_id, 0.0)
    if time.monotonic() - last < SYNC_THROTTLE_SECONDS:
        return get_state(event_id)

    from app.services import football_api

    fixture_id = _fixture_links[event_id]
    api_state = await football_api.get_fixture_state(fixture_id)

    state = get_state(event_id)
    goals = [
        Goal(player=g["player"], team=g["team"], minute=g["minute"])
        for g in api_state["goals"]
    ]
    updated = state.model_copy(
        update={
            "status": api_state["status"],
            "home_score": api_state["home_score"],
            "away_score": api_state["away_score"],
            "goals": goals,
        }
    )
    _states[event_id] = updated
    _last_sync[event_id] = time.monotonic()
    return updated
