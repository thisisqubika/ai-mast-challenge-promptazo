---
name: code-conventions
description: Project-specific coding conventions for FanFest — Python/FastAPI backend and vanilla JS frontend
disable-model-invocation: false
version: 1.0
---

# Code Conventions

## Naming Conventions

**Python (backend)**
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Route handlers: verb prefix — `get_`, `create_`, `update_`, `delete_`

**JavaScript (frontend)**
- Files: match existing style (`main.js`, `api.js` — `camelCase`)
- Functions: `camelCase`
- DOM IDs/classes: `kebab-case`

## API Design Rules

Route handlers live in `fanfest/backend/app/api/v1/endpoints/`. Each domain gets its own module. Response models are Pydantic classes defined alongside or in a peer `schemas/` file.

```python
# fanfest/backend/app/api/v1/endpoints/events.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/{event_id}")
async def get_event(event_id: int):
    event = db.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
```

## Error Handling

- Raise `HTTPException` for expected client errors (4xx).
- Let unhandled exceptions propagate to FastAPI's default 500 handler; do not swallow them.
- Never encode error state in a 200 response body.

```python
# WRONG — hides failure mode from callers
def get_event(event_id: int):
    try:
        return db.get(event_id)
    except Exception:
        return {"error": "not found"}

# CORRECT
def get_event(event_id: int):
    event = db.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
```

## Code-Style Conventions

- Python: PEP 8, line length 88; linter is `ruff` (`ruff check .` from `fanfest/backend/`).
- Import order: stdlib → third-party → local (isort-compatible).
- Frontend: no inline styles; all CSS in `fanfest/frontend/assets/css/`.
- All API calls from the browser go through `api.js` — no `fetch()` calls scattered in `main.js`.

## Gotchas

### Declare in requirements.txt Before Importing

Any new backend dependency must be added to `fanfest/backend/requirements.txt` before importing. CI installs from this file; missing entries cause import errors in GitHub Actions even if locally installed.

```python
# WRONG — import will fail in CI (not in requirements.txt)
from anthropic import Anthropic
client = Anthropic()

# CORRECT — add to requirements.txt first, then import
# fanfest/backend/requirements.txt: anthropic>=0.25.0
from anthropic import Anthropic
client = Anthropic()
```