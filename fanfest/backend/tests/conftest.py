import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import registry


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_event_id() -> str:
    return "event_001"


@pytest.fixture
def checked_in_user() -> dict[str, str]:
    return {"id": "user_001", "name": "Alice"}


@pytest.fixture
def non_checked_in_user() -> dict[str, str]:
    return {"id": "user_999", "name": "Stranger"}


@pytest.fixture(autouse=True)
def reset_services() -> None:
    """Reset mutable in-memory state between tests."""
    import app.services.match_state as ms
    import app.services.photos_service as ps
    import app.services.recap_service as rs
    from app.data.seed import FANS, MATCHES, RECAPS
    from app.schemas.events import Goal, MatchState, RecapHighlight, RecapResponse

    def _to_state(m) -> MatchState:
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

    ms._states = {m.event_id: _to_state(m) for m in MATCHES}
    ps._photos = {}
    registry._checked_in = {f.user_id: f.name for f in FANS}
    rs._store = {
        r.event_id: RecapResponse(
            event_id=r.event_id,
            narrative=r.narrative,
            highlights=[RecapHighlight(label=s.label, description=s.description) for s in r.slides],
            correct_predictors=r.correct_predictors,
            fallback=r.fallback,
            home_score=r.home_score,
            away_score=r.away_score,
            home_team=r.home_team,
            away_team=r.away_team,
            photo_count=r.photo_count,
        )
        for r in RECAPS
    }
