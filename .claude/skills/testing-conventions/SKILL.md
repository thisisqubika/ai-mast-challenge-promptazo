---
name: testing-conventions
description: Testing conventions for FanFest — pytest for the Python backend; no frontend test framework established
disable-model-invocation: false
version: 1.0
---

# Testing Conventions

## Testing Philosophy

- Backend: test route behavior and business logic with pytest and FastAPI's `TestClient`.
- Frontend: no test framework is set up; manual verification only until one is chosen.
- Do not test FastAPI's own routing or dependency injection machinery — test your logic.
- Mock external third-party APIs (Anthropic, Google) to avoid billing and flakiness.

## Unit Test Patterns

Test files live in `fanfest/backend/tests/`. Name them `test_{module}.py`.

```python
# fanfest/backend/tests/test_events.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_event_returns_404_when_missing():
    response = client.get("/api/v1/events/9999")
    assert response.status_code == 404

def test_create_event_returns_created():
    payload = {"name": "Test Fest", "date": "2026-07-01"}
    response = client.post("/api/v1/events/", json=payload)
    assert response.status_code == 201
```

## What NOT to Mock

- Do not mock `TestClient` request/response — use real route handlers.
- Mock only external services: `anthropic.Anthropic`, Google API clients.

## Fixture Conventions

Shared fixtures go in `fanfest/backend/tests/conftest.py`. Name fixtures after the object they produce.

```python
# fanfest/backend/tests/conftest.py
import pytest

@pytest.fixture
def sample_event():
    return {"name": "Test Fest", "date": "2026-07-01", "location": "Buenos Aires"}
```

For services with mutable in-memory state, add an `autouse=True` fixture that resets module-level dicts before each test. This prevents state leaking between tests without needing explicit teardown.

```python
# fanfest/backend/tests/conftest.py
@pytest.fixture(autouse=True)
def reset_services() -> None:
    import app.services.some_service as svc
    svc._store = {}  # reset to baseline before every test
```

## Coverage Expectations

No formal threshold. Cover all route handlers and any non-trivial business logic before merging. External API integration paths should have at least one test with a mocked client.