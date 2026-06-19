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
    from app.schemas.events import MatchState

    ms._states = {
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
    ps._photos = {}
    registry._checked_in = {
        "user_001": "Alice",
        "user_002": "Bob",
        "user_003": "Carlos",
    }
