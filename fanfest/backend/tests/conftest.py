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
    from app.data.seed import FANS, MATCHES
    from app.schemas.events import Goal, MatchState

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
