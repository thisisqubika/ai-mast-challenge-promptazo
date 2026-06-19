# FEST-03: Live Event Screen & Hype Wall

## User Story

**As an** event attendee who has checked in
**I want** to see the live match scoreboard, goal history, and a shared photo wall during the event
**So that** I can follow the game in real time and contribute to a shared group memory that feeds the post-event AI recap

## Stakeholders

- Product Owner / Event Organiser — acceptance and prioritization
- Demo operator / dev — advances match state via the mocked admin control
- Checked-in attendees — upload photos and view the live wall
- AI recap pipeline (Feature 04) — consumes the final score and photos produced here

## Success Criteria

1. A checked-in attendee can open the Live screen and see the current scoreboard, venue, clock, and goal-player cards within one poll cycle (≤ 3 s).
2. When a goal is recorded via the dev control, the scoring-player card appears on all connected browsers at the next poll.
3. A checked-in attendee can upload a photo; the photo appears in the Hype Wall grid for all viewers at the next poll.
4. An unchecked-in user's photo upload is rejected with HTTP 403.
5. When match status transitions to `ended`, the frontend stops showing the pre-event Hype Wall and renders the Recap banner instead.
6. All uploaded photo metadata (uploader identity, URL) is accessible to the AI recap pipeline via `GET /api/v1/events/{id}/photos`.

## Acceptance Criteria

### Scenario 1: View live scoreboard

```gherkin
Given a match is in status "live" for event_001
When an attendee opens the Live screen
Then the scoreboard shows the home team, away team, current scores, venue name, and match clock
And the goal-summary line reflects the current score (e.g. "River Plate 1 · Boca Juniors 0")
```

### Scenario 2: Goal card appears after dev control advances state

```gherkin
Given the match is in status "pre" or "live"
When the demo operator POSTs {"action":"goal","player":"Gallardo","team":"River Plate","minute":34} to POST /api/v1/events/event_001/match-state
Then GET /api/v1/events/event_001/match-state returns status "live", home_score 1, and a goals list containing {player:"Gallardo",team:"River Plate",minute:34}
And at the next poll cycle the frontend renders a goal card showing "Gallardo · River Plate · 34'"
```

### Scenario 3: Checked-in attendee uploads a photo

```gherkin
Given "user_001" (Alice) is in the check-in registry
When Alice POSTs a JPEG file with uploader_id "user_001" and uploader_name "Alice" to POST /api/v1/events/event_001/photos
Then the response is HTTP 201 with a Photo object containing id, url, uploader_name "Alice", and uploaded_at
And GET /api/v1/events/event_001/photos returns a list that includes Alice's photo with uploader_name "Alice"
```

### Scenario 4: Non-checked-in user is rejected

```gherkin
Given "user_999" is NOT in the check-in registry
When user_999 POSTs a photo to POST /api/v1/events/event_001/photos
Then the response is HTTP 403
And no photo is stored for event_001
```

### Scenario 5: Match-end transitions UI to Recap mode

```gherkin
Given the frontend is polling the live screen
When the demo operator POSTs {"action":"end"} to POST /api/v1/events/event_001/match-state
Then the next poll returns status "ended"
And the frontend hides the Hype Wall upload form and goal cards
And the frontend renders the Recap banner ("PARTIDO TERMINADO — Recapitulación disponible pronto")
```

### Scenario 6: Hype Wall shows empty state before any upload

```gherkin
Given no photos have been uploaded for event_001
When an attendee opens the Hype Wall section
Then the grid shows "Aún no hay fotos. Sé el primero en subir una."
```

## Technical Context

### Current State

- `fanfest/backend/app/api/v1/endpoints/events.py` — four routes: `GET /match-state`, `POST /match-state`, `POST /photos`, `GET /photos`
- `fanfest/backend/app/schemas/events.py` — Pydantic models: `MatchState`, `Goal`, `Photo`, `PhotoList`, `MatchStateUpdate`, `PhotoUploadForm`
- `fanfest/backend/app/services/match_state.py` — in-memory dict keyed by `event_id`; supports `score_goal`, `end_match`, `reset`; seeded with `event_001` (River Plate vs Boca Juniors, Estadio Monumental)
- `fanfest/backend/app/services/photos_service.py` — in-memory mock (default) + optional Google Drive backend gated by `settings.drive_enabled`
- `fanfest/backend/app/services/registry.py` — in-memory check-in dict seeded with `user_001` (Alice), `user_002` (Bob), `user_003` (Carlos)
- `fanfest/frontend/assets/js/live.js` — polls every 3 s; renders scoreboard, goal cards, Hype Wall grid, upload form; transitions to Recap banner on `status === "ended"`
- `fanfest/frontend/assets/js/api.js` — `fetchMatchState`, `fetchPhotos`, `uploadPhoto`, `advanceMatchState`; all routed through `API_BASE = 'http://localhost:8000/api/v1'`
- `fanfest/backend/tests/test_events.py` — 8 tests covering all four routes including 403 rejection
- `fanfest/backend/.env.example` — documents `GOOGLE_SERVICE_ACCOUNT_FILE` and `GOOGLE_DRIVE_FOLDER_ID`

### Proposed Changes

All implemented on branch `feature/FEST-03-live-event-hype-wall`. No further changes are required; this ticket documents the completed feature.

### Technical Constraints

- No WebSockets. Poll interval is 3 seconds (configurable via `POLL_INTERVAL` constant in `live.js`).
- Match state is entirely in-memory; state resets on server restart. No database or ORM.
- Google Drive integration is opt-in: set `GOOGLE_SERVICE_ACCOUNT_FILE` and `GOOGLE_DRIVE_FOLDER_ID` in `.env`; without them, the service falls back to in-memory storage.
- Photo uploads are multipart (`python-multipart` declared in `requirements.txt`).
- Frontend uses ES module imports — `live.js` imports from `api.js` via `import { ... } from './api.js'`.
- CORS is configured via `CORS_ORIGINS` env var (default `http://localhost:8080`).

### Integration Points

| Component | Role |
|-----------|------|
| `services/match_state.py` | Source of truth for scoreboard and goal history; advanced by dev control |
| `services/photos_service.py` | Stores photos in memory or Google Drive; queried by AI recap (Feature 04) |
| `services/registry.py` | Authorises photo uploads; seeded with demo users |
| Google Drive API | Optional durable photo store; activated by env vars |
| Feature 04 (Recap) | Reads final `MatchState.goals`, final score, and `PhotoList` to generate AI narrative |

### Architecture Decisions

- **Poll over WebSockets** — reduces infrastructure complexity for a demo context; 3-second latency is acceptable.
- **In-memory state with Google Drive fallback** — keeps the backend zero-dependency for local dev; Drive is wired for demo/production paths without code changes.
- **Uploader identity via form fields** — `uploader_id` and `uploader_name` are sent as `Form(...)` fields alongside the file, matching multipart form semantics. Identity is persisted in `localStorage` in the frontend.
- **`event_id` as a string** — originally typed as `int` in a prior draft; corrected to `str` to match the seeded key `"event_001"`.

## Out of Scope

- WebSocket / Server-Sent Events real-time push
- Persistent database (PostgreSQL, SQLite, etc.)
- Authentication / JWT tokens — identity is mock-based for the demo
- Photo moderation or deletion
- Clock advancement — `clock_seconds` is set by the dev control action, not auto-incremented by a timer
- Multiple concurrent events (only `event_001` is seeded)

## Edge Cases and Error Handling

| Case | Handling |
|------|----------|
| `goal` action missing `player`, `team`, or `minute` | HTTP 422 with detail message |
| Unknown `action` in `POST /match-state` | HTTP 422 "Unknown action" |
| `event_id` not in registry | HTTP 404 "Event not found" |
| Uploader not in check-in registry | HTTP 403 "User is not checked in" |
| No file selected before upload button clicked | Frontend shows "Seleccioná una foto primero." |
| Backend unreachable on first poll | Frontend shows "Conectando con el servidor..." |
| Photo upload returns non-403 error | Frontend shows "Error al subir la foto." |
| Photos URL is a mock path (`/mock-photos/…`) when Drive is disabled | Frontend renders `<img>` with broken URL — acceptable for demo; Drive must be enabled for real thumbnails |

## Validation Rules

- `MatchStateUpdate.action` must be one of `"goal"`, `"end"`, `"reset"` (Pydantic `Literal` enforced).
- `goal` action requires `player` (str), `team` (str), `minute` (int) — validated in the route handler with HTTP 422.
- Photo upload requires `file` (binary), `uploader_id` (str), `uploader_name` (str) — FastAPI `Form(...)` enforces presence.
- `uploader_id` must exist in `registry._checked_in` — enforced by `registry.is_checked_in()` before storage.

## Dependencies

- **Blocking:** FEST-02 (Check-in flow) — `registry.py` must be seeded with checked-in users before photo uploads can succeed.
- **Feeds into:** FEST-04 (AI Recap) — final `MatchState` (score, goals) and `PhotoList` are the primary inputs to the recap narrative.
- **Related:** FEST-01 (Pre-event screen) — shares the same `index.html` and `api.js`; Live screen is shown after check-in.

## Definition of Done

### Code Quality

- [x] `ruff check .` passes with zero errors (run from `fanfest/backend/`)
- [x] All new backend dependencies declared in `fanfest/backend/requirements.txt` before import
- [x] No inline styles; all CSS in `fanfest/frontend/assets/css/live.css`
- [x] All `fetch()` calls routed through `api.js`; none scattered in `live.js` directly

### Testing

- [x] `pytest` passes — 8 tests in `tests/test_events.py` cover all four routes
- [x] `test_get_match_state` — 200 response, correct initial state
- [x] `test_get_match_state_unknown_event` — 404 for unknown event
- [x] `test_score_goal_updates_state` — score and goals list updated, status `"live"`
- [x] `test_end_match_status` — status transitions to `"ended"`
- [x] `test_reset_match_state` — scores and goals cleared, status back to `"pre"`
- [x] `test_upload_photo_checked_in` — 201 with photo metadata
- [x] `test_upload_photo_not_checked_in_returns_403` — 403 rejection
- [x] `test_list_photos_returns_uploader` — photo list includes uploader name
- [x] `conftest.py` resets `match_state._states`, `photos_service._photos`, and `registry._checked_in` between every test via `autouse=True` fixture

### Documentation

- [x] `.env.example` documents `GOOGLE_SERVICE_ACCOUNT_FILE` and `GOOGLE_DRIVE_FOLDER_ID`
- [x] FastAPI auto-docs available at `/docs` and `/redoc`

### Review and Deployment

- [ ] Code reviewed and approved via pull request
- [ ] Branch `feature/FEST-03-live-event-hype-wall` merged to `main`
- [ ] Backend starts cleanly with `uvicorn app.main:app --reload` from `fanfest/backend/`
- [ ] Frontend loads at `http://localhost:8080` and polls successfully

## Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirmed route surface, service modules, data-layer design, testing conventions, and Google Drive integration pattern

## Graph Evidence

- Tool: `mcp__code_graph__get_impact_radius_tool` — params: `{"changed_files":["fanfest/backend/app/api/v1/endpoints/events.py","fanfest/backend/app/schemas/events.py","fanfest/backend/app/services/match_state.py","fanfest/backend/app/services/photos_service.py","fanfest/backend/app/services/registry.py","fanfest/frontend/assets/js/live.js","fanfest/frontend/assets/js/api.js"],"max_depth":2,"detail_level":"minimal"}` — finding: 7 impacted files, 1 service; key transitive dependents are `config.py/Settings`, `main.py`, `services/__init__.py`, `tests/conftest.py`; INVEST "Small" passes

## Implementation Notes

The feature is fully implemented on branch `feature/FEST-03-live-event-hype-wall`. Key implementation notes for reviewers:

- `event_id` is typed as `str` throughout (schemas, services, routes). An earlier draft used `int`; the mismatch was corrected in commit `b8e93a1`.
- Google Drive upload uses `service_account.Credentials` scoped to `drive.file` (least-privilege). The `_upload_to_drive` function imports `googleapiclient` lazily (inside the function) to avoid import-time failures when credentials are absent.
- The frontend stores uploader identity in `localStorage` under keys `live_uploader_name` / `live_uploader_id`. On first visit a `prompt()` captures the name; subsequent visits reuse the stored value.
- Photo thumbnails only render correctly when Google Drive is enabled and returns a `webViewLink`. In mock mode, URLs are `"/mock-photos/{event_id}/{filename}"` — these will be broken `<img>` tags in the browser, which is acceptable for local dev.
- The poll loop in `live.js` is optimised: full re-render only on status change; on subsequent ticks it patches only the `#hypeGrid` inner HTML and the clock element to avoid losing DOM event listeners on the upload button.

## References

- Draft spec: `specs/drafts/feature-03-live-event-hype-wall.md`
- Backend service doc: `docs/llm-wiki/wiki/services/backend.md`
- Implemented files:
  - `fanfest/backend/app/api/v1/endpoints/events.py`
  - `fanfest/backend/app/schemas/events.py`
  - `fanfest/backend/app/services/match_state.py`
  - `fanfest/backend/app/services/photos_service.py`
  - `fanfest/backend/app/services/registry.py`
  - `fanfest/backend/tests/test_events.py`
  - `fanfest/backend/tests/conftest.py`
  - `fanfest/frontend/assets/js/live.js`
  - `fanfest/frontend/assets/js/api.js`
  - `fanfest/frontend/assets/css/live.css`

---

**INVEST Validated**: yes
**BDD Scenarios**: 6
**Priority**: Medium
**Labels**: sdd, live-event, hype-wall, polling, google-drive
**Scope Impact**: 7 impacted files, 1 service (impact_radius max_depth=2, detail_level=minimal)
