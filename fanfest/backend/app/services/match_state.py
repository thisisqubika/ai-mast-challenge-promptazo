"""Module-level in-memory match state store, dev-advanceable for demo purposes."""

from fastapi import HTTPException

from app.schemas.events import Goal, MatchState

_states: dict[str, MatchState] = {
    "event_001": MatchState(
        event_id="event_001",
        home_team="River Plate",
        away_team="Boca Juniors",
        home_score=0,
        away_score=0,
        status="pre",
        clock_seconds=0,
        venue="Estadio Monumental",
        goals=[],
    )
}


def get_state(event_id: str) -> MatchState:
    state = _states.get(event_id)
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
    return updated


def end_match(event_id: str) -> MatchState:
    state = get_state(event_id)
    updated = state.model_copy(update={"status": "ended"})
    _states[event_id] = updated
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
