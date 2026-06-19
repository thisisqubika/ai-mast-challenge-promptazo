---
name: multi-file-workflows
description: Ordered checklists for cross-cutting changes in FanFest — new endpoint, new frontend feature, new dependency
disable-model-invocation: false
version: 1.0
---

# Multi-File Workflows

## Adding a New API Endpoint

1. Create `fanfest/backend/app/services/{domain}_service.py` with business logic and in-process state
2. Create (or extend) `fanfest/backend/app/api/v1/endpoints/{domain}.py` with the route handler; import from the service
3. Declare Pydantic request/response models in `fanfest/backend/app/schemas/{domain}.py`
4. Register the router in `fanfest/backend/app/main.py` via `app.include_router(router, prefix="/api/v1")`
5. Add tests in `fanfest/backend/tests/test_{domain}.py`

```python
# fanfest/backend/app/api/v1/endpoints/{domain}.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/{domain}", tags=["{domain}"])

@router.get("/")
async def list_{domain}():
    return []

@router.get("/{item_id}")
async def get_{domain}(item_id: int):
    raise HTTPException(status_code=404, detail="Not found")
```

> **Gotcha**: The router must be included in the app — adding only the file has no effect. Wire it in `main.py` via `app.include_router(router)`.

## Adding a New Frontend Feature

1. Add markup to `fanfest/frontend/index.html`
2. Add API call function to `fanfest/frontend/assets/js/api.js`
3. Add UI logic to `fanfest/frontend/assets/js/main.js` (or a new `{feature}.js` file)
4. Add styles to `fanfest/frontend/assets/css/main.css` (or a new `{feature}.css`)

```javascript
// fanfest/frontend/assets/js/api.js
async function fetch{Feature}() {
  const res = await fetch('http://localhost:8000/api/v1/{domain}/');
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}
```

> **Gotcha**: Backend base URL (`http://localhost:8000`) must be defined in `api.js` only — not repeated across `main.js` or HTML.

## Adding a New Backend Dependency

1. Add the package and version pin to `fanfest/backend/requirements.txt`
2. Run `pip install -r requirements.txt` in the `fanfest/backend/` directory
3. Import the library in the relevant module

```text
# fanfest/backend/requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
anthropic>=0.25.0
google-auth>=2.29.0
```