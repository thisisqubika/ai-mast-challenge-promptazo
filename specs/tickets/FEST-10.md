# FEST-10: Create New Event

## 📋 User Story

**As an** event organizer using FanFest
**I want** to create a new fan fest event from the home feed by tapping the "+" button
**So that** the event appears immediately in the upcoming events feed and fans can start registering

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | FanFest Product | Initial request, scope validation |
| Tech Lead | FanFest Full-Stack | Architecture review, endpoint contract |
| Frontend | FanFest UI | Form UX, FAB placement, screen transitions |
| Backend | FanFest API | Schema, service, endpoint, tests |

---

## 🎯 Success Criteria

1. `POST /api/v1/events` accepts a valid `EventCreate` payload and returns an `EventDetail` with `status="future"` and HTTP 201.
2. The newly created event appears in the home feed's "Próximos fan fests" section on the next `GET /api/v1/events?status=future` call.
3. Tapping the "+" FAB on the home screen opens a create-event form styled with the existing FanFest dark theme; tapping "×" or "Cancelar" returns to the home feed without side effects.
4. Submitting the form with valid data calls `POST /api/v1/events`, shows a success state, then navigates back to the home feed and refreshes the events list.
5. `ruff check .` passes from `fanfest/backend/`.
6. `pytest` suite stays green (no regressions).

**Metrics**: New event is visible in the feed within the same browser session after creation. `status` is always `"future"` regardless of any client-supplied value.

---

## ✅ Acceptance Criteria

### Scenario 1: Organizer creates a complete event

```gherkin
Given the organizer is on the home feed
When they tap the "+" floating action button
Then a "Crear Fan Fest" form screen slides in
And the form contains fields for home team, home flag, away team, away flag,
    competition, kickoff date/time, venue name, venue address, and organizer name
And optional fields for invite link, calendar link, and maps link
```

### Scenario 2: Successful event creation navigates back to home

```gherkin
Given the organizer has filled all required fields with valid data
When they tap "Crear Evento"
Then the browser POSTs to /api/v1/events with status 201
And the form shows a brief success indicator
And the home feed is visible again with the new event in "Próximos fan fests"
```

### Scenario 3: Status is always "future" server-side

```gherkin
Given a POST /api/v1/events request body that includes status="live"
When the server processes the request
Then the created event has status="future" in the response
And the "live" value sent by the client is silently ignored
```

### Scenario 4: Validation — required fields missing

```gherkin
Given the organizer submits the form with "Venue Name" left empty
When the form validation runs (client-side)
Then the form does NOT submit to the API
And the empty field is highlighted with an error indicator
And the organizer is prompted to fill in the missing field
```

### Scenario 5: API validation — invalid kickoff_iso

```gherkin
Given a POST /api/v1/events request with kickoff_iso="not-a-date"
When the server processes the request
Then the server returns HTTP 422
And the response body contains a validation error referencing the "kickoff_iso" field
```

### Scenario 6: Cancellation has no side effects

```gherkin
Given the organizer has opened the "Crear Fan Fest" form
When they tap "×" or "Cancelar" without submitting
Then the form screen is dismissed
And no POST request was sent to the API
And the home feed is shown unchanged
```

### Scenario 7: Duplicate-safe ID generation

```gherkin
Given two concurrent POST /api/v1/events requests with identical payload
When both requests are processed
Then each response contains a distinct event id (UUID)
And both events are independently stored in the database
```

---

## 🔧 Technical Context

### Current State

- `fanfest/backend/app/db/models.py` — `EventModel` SQLAlchemy ORM class with all event columns; `status` defaults to `"future"`. No creation endpoint exists.
- `fanfest/backend/app/services/events_service.py` — has `list_events()`, `get_event()`, `_event_to_dict()`. No `create_event()` function.
- `fanfest/backend/app/schemas/events.py` — has `EventDetail`, `EventSummary`. No `EventCreate` input schema.
- `fanfest/backend/app/api/v1/endpoints/events.py` — router at prefix `/api/v1/events`; already registered in `main.py` (line 38). No `POST ""` route.
- `fanfest/frontend/index.html` — home feed screen, `#eventDetailView`, `#recapView`, bottom nav. No "+" FAB, no `#createEventView`.
- `fanfest/frontend/assets/js/api.js` — all API calls go through this file. No `createEvent()` function.

### Proposed Changes

#### Backend (3 files)

| File | Change |
|------|--------|
| `fanfest/backend/app/schemas/events.py` | Add `EventCreate` Pydantic model (see below) |
| `fanfest/backend/app/services/events_service.py` | Add `create_event(data: EventCreate) -> dict` function |
| `fanfest/backend/app/api/v1/endpoints/events.py` | Add `POST ""` route handler `create_event_handler` returning `EventDetail` with HTTP 201 |

**`EventCreate` schema** — add to `schemas/events.py`:

```python
class EventCreate(BaseModel):
    home_team: str
    home_flag: str
    away_team: str
    away_flag: str
    venue_name: str
    venue_address: str
    organizer: str
    kickoff_iso: str          # ISO 8601; server derives match_start_time from this
    invite_link: str = ""
    calendar_link: str = ""
    maps_link: str = ""
    competition: str = ""
    venue_distance: str = ""
    amenities: list[list[str]] = []
```

`status` is intentionally absent — server always sets `"future"`.

**`create_event()` service** — add to `events_service.py`:

```python
import json, uuid
from datetime import datetime, timezone
from app.db.database import get_session
from app.db.models import EventModel
from app.schemas.events import EventCreate

def create_event(data: EventCreate) -> dict:
    event_id = str(uuid.uuid4())
    match_start = datetime.fromisoformat(data.kickoff_iso).replace(tzinfo=timezone.utc)
    with get_session() as db:
        event = EventModel(
            id=event_id,
            home_team=data.home_team,
            home_flag=data.home_flag,
            away_team=data.away_team,
            away_flag=data.away_flag,
            venue_name=data.venue_name,
            venue_address=data.venue_address,
            organizer=data.organizer,
            kickoff_iso=data.kickoff_iso,
            match_start_time=match_start,
            invite_link=data.invite_link,
            calendar_link=data.calendar_link,
            maps_link=data.maps_link,
            status="future",
            competition=data.competition,
            venue_distance=data.venue_distance,
            amenities=json.dumps(data.amenities),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
    return _event_to_dict(event)
```

If `kickoff_iso` cannot be parsed, `datetime.fromisoformat()` raises `ValueError` — let FastAPI's 422 handler surface this (do not swallow).

**Route handler** — add to `endpoints/events.py` (before `/{event_id}` to avoid path-param capture):

```python
@router.post("", response_model=EventDetail, status_code=201)
def create_event_handler(body: EventCreate) -> EventDetail:
    event = events_service.create_event(body)
    return EventDetail(
        **event,
        attendees=[],
        attendee_count=0,
    )
```

`main.py` requires **no changes** — the router is already registered at `/api/v1`.

#### Frontend (4 files)

| File | Change |
|------|--------|
| `fanfest/frontend/index.html` | Add "+" FAB button (home view only) + `#createEventView` hidden scroll screen |
| `fanfest/frontend/assets/js/api.js` | Add `createEvent(data)` async function |
| `fanfest/frontend/assets/js/create-event.js` | New module: form rendering, validation, submit logic, navigation |
| `fanfest/frontend/assets/css/create-event.css` | New stylesheet: FAB, form screen, field styles, error states |

**"+" FAB placement** in `index.html` — add inside `.phone` div, after the home `#scroll` area and before `#eventDetailView`:

```html
<!-- FAB — only visible on home screen -->
<button id="fabCreateEvent" class="fab" type="button" aria-label="Crear Fan Fest">
  <i class="ti ti-plus"></i>
</button>

<!-- CREATE EVENT SCREEN -->
<div id="createEventView" class="scroll" hidden></div>
```

**CSS design tokens** (from `main.css`): `--accent: #10b981`, `--screen: #0f172a`, `--card: #1e293b`, `--ink: #f1f5f9`, `--muted: #64748b`, font: `Inter`. FAB: 48 × 48 px circle, `background: var(--accent)`, positioned `fixed` bottom-right above nav; uses Tabler icon `ti-plus`.

**Form fields** (all labels in Spanish):

| Field | Type | Required | Placeholder |
|-------|------|----------|-------------|
| Local (`home_team`) | text | ✅ | Ej: Argentina |
| Bandera local (`home_flag`) | text | ✅ | 🇦🇷 |
| Visitante (`away_team`) | text | ✅ | Ej: México |
| Bandera visitante (`away_flag`) | text | ✅ | 🇲🇽 |
| Competición (`competition`) | text | ✗ | Ej: Copa América |
| Fecha y hora (`kickoff_iso`) | datetime-local | ✅ | — |
| Estadio (`venue_name`) | text | ✅ | Ej: Monumental |
| Dirección (`venue_address`) | text | ✅ | Ej: Av. Figueroa Alcorta 7597 |
| Organizador (`organizer`) | text | ✅ | Ej: FanFest BA |
| Link invitación | url | ✗ | https://... |
| Link calendario | url | ✗ | https://... |
| Link mapa | url | ✗ | https://... |

**Navigation pattern**: same as existing screens — `hidden` attribute toggled. FAB is hidden when `#createEventView` is visible, shown when home feed is active.

### Technical Constraints

- `status` is always `"future"` server-side; `EventCreate` schema must NOT include a `status` field.
- `match_start_time` is derived server-side from `kickoff_iso` via `datetime.fromisoformat()`.
- `id` is generated server-side with `uuid.uuid4()` — client never supplies it.
- `ruff check .` must pass; 88-char line limit.
- No new Python dependencies required (`uuid` is stdlib).
- All browser `fetch()` calls must go through `api.js` — not scattered in `create-event.js` directly.
- New CSS in `create-event.css`; no inline styles.
- `create-event.css` must be linked in `index.html`.
- `create-event.js` must be loaded as `<script type="module">` in `index.html`.

### Integration Points

- `fanfest/backend/app/db/database.py` — `get_session()` context manager (already used by all service functions).
- `fanfest/backend/app/db/models.py` — `EventModel`; all required columns are already defined.
- `fanfest/frontend/assets/js/main.js` — home feed refresh function must be exposed or re-callable after event creation.
- `fanfest/frontend/index.html` — FAB visibility toggle tied to active screen state.

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| `status` hardcoded server-side | Enforces domain invariant: only the system (not clients) can set "live" or "past" |
| `match_start_time` derived from `kickoff_iso` | Single source of truth; avoids client/server drift on time zones |
| `id` as UUID generated server-side | Avoids collisions; matches existing event IDs in `EventModel` |
| `EventCreate` schema separate from `EventDetail` | Input and output shapes differ (no `id`, `status`, `attendees`, `attendee_count` on input); standard FastAPI pattern |
| New `create-event.js` module (not inline in `main.js`) | Screen logic is self-contained; keeps `main.js` focused on home feed |
| New `create-event.css` file | Avoids bloating `main.css`; follows existing pattern (`event-detail.css`, `recap.css`) |

### Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirms `GET /api/v1/events/{id}` shape, SQLAlchemy + `get_session()` data layer, no existing create-event endpoint, `EventModel` is the persistence layer as of FEST-09.

### Graph Evidence

- `mcp__code_graph__semantic_search_nodes_tool` — `EventModel` found in `fanfest/backend/app/db/models.py`; all required columns (including `status="future"` default) already defined — no schema migration needed.
- `mcp__code_graph__query_graph_tool` (callers_of `_event_to_dict`) — called by `list_events()` and `get_event()` in `events_service.py`; new `create_event()` should also call it for consistency.
- Codebase inspection of `events.py` endpoint file — `@router.post("")` slot is unused; the `GET ""` list endpoint comment explicitly says it must precede `/{event_id}` to avoid capture — the new `POST ""` is safe to add before `GET /{event_id}`.

---

## 🚫 Out of Scope

1. Authentication / authorization — any caller can create an event (no auth layer in the current app).
2. Event editing or deletion — separate tickets.
3. Image upload for event cover art.
4. Amenities UI on the create form — `amenities` defaults to `[]` on creation; editing them is a future feature.
5. `venue_distance` calculation — left as empty string on creation; geolocation is a future concern.
6. Frontend test automation — no JS test framework is set up (testing-conventions confirms this).

**Future Considerations**: Once auth is added, restrict event creation to organizer-role users. A follow-up ticket should add event editing (`PATCH /api/v1/events/{id}`) and deletion.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases

1. **`kickoff_iso` without timezone offset** — `datetime.fromisoformat()` succeeds but returns a naive datetime; service must call `.replace(tzinfo=timezone.utc)` to match the timezone-aware convention used by `match_start_time` in the DB.
2. **`datetime-local` browser input** — yields `"2026-07-15T21:00"` (no seconds, no `Z`); `fromisoformat()` handles this in Python 3.11+; the service should append `:00` if needed or document the exact expected format.
3. **Home feed not refreshing** — the `create-event.js` submit handler must explicitly call the home feed refresh function after navigation; leaving it uncalled results in stale data shown.
4. **FAB visible on wrong screen** — FAB must be hidden whenever `#createEventView`, `#eventDetailView`, or `#recapView` is active; it must reappear when returning to the home feed.
5. **Double-submit on slow network** — disable the submit button on first click; re-enable on error so the user can retry.

### Error Scenarios

| Scenario | Backend behavior | Frontend behavior |
|----------|-----------------|-------------------|
| Invalid `kickoff_iso` | HTTP 422 with Pydantic validation error | Show "Fecha inválida" near the kickoff field |
| Missing required field (caught server-side) | HTTP 422 | Show field-level error message |
| Network error / 5xx | HTTP 500 | Show a toast: "Error al crear el evento. Intenta de nuevo." |
| Duplicate event ID (probabilistically impossible with UUID4) | N/A — no unique constraint on content fields | N/A |

### Data Validation Rules

- `home_team`, `away_team`, `venue_name`, `venue_address`, `organizer` — non-empty string; validated client-side (HTML `required`); no server-side length cap defined (use Pydantic default, which accepts any non-null string).
- `kickoff_iso` — must be parseable by `datetime.fromisoformat()`; validated server-side; a future date is not enforced by the server in this ticket.
- `home_flag`, `away_flag` — should be emoji flag strings (e.g. `"🇦🇷"`); no server validation — treated as opaque strings.

---

## 📦 Dependencies

### Blocking

- FEST-09 (SQLite migration) — **done**; `EventModel`, `get_session()`, and the SQLAlchemy data layer are in place.

### Related

- FEST-07 — `Event` dataclass shape; new `EventCreate` schema must match its field names.
- FEST-02 — `EventDetail` is the response schema for the new endpoint; already defined.

---

## 🎓 Definition of Done

### Code Quality

- [ ] `EventCreate` Pydantic schema added to `fanfest/backend/app/schemas/events.py`; no `status` field.
- [ ] `create_event(data: EventCreate) -> dict` added to `fanfest/backend/app/services/events_service.py`; uses `get_session()`, sets `status="future"`, derives `match_start_time` from `kickoff_iso`.
- [ ] `POST ""` route handler added to `fanfest/backend/app/api/v1/endpoints/events.py`; returns `EventDetail` with HTTP 201.
- [ ] `ruff check .` passes from `fanfest/backend/`.
- [ ] `main.py` unchanged.
- [ ] "+" FAB button added to `fanfest/frontend/index.html`.
- [ ] `#createEventView` hidden screen added to `fanfest/frontend/index.html`.
- [ ] `create-event.css` linked in `index.html`.
- [ ] `create-event.js` loaded as `<script type="module">` in `index.html`.
- [ ] `createEvent(data)` function added to `fanfest/frontend/assets/js/api.js`.
- [ ] New `fanfest/frontend/assets/js/create-event.js` module for form logic.
- [ ] New `fanfest/frontend/assets/css/create-event.css` for FAB + form styles.
- [ ] No inline styles; no `fetch()` calls outside `api.js`.

### Testing

- [ ] `pytest` passes with no regressions (existing test suite stays green).
- [ ] New test in `fanfest/backend/tests/test_events.py`:
  - `test_create_event_returns_201` — POST valid payload, assert 201 + `status == "future"` + non-empty `id`.
  - `test_create_event_status_always_future` — POST payload with `status="live"`, assert response `status == "future"`.
  - `test_create_event_missing_required_field` — POST payload missing `venue_name`, assert 422.
  - `test_create_event_invalid_kickoff_iso` — POST payload with `kickoff_iso="garbage"`, assert 422.
  - `test_create_event_appears_in_list` — POST event, then GET `/api/v1/events`, assert new event id present.
- [ ] Manual smoke test: form opens, submits, and new event card appears in the home feed.

### Documentation

- [ ] `POST /api/v1/events` entry added to `docs/llm-wiki/wiki/services/backend.md` Public API table (run `/wiki-refresh` after merge).

### Review & Deployment

- [ ] Code reviewed and approved.
- [ ] PR merged.

---

## 📝 Implementation Notes

- The `POST ""` route handler must be declared **before** `GET "/{event_id}"` in `events.py` to avoid FastAPI path ambiguity. The existing `GET ""` list route is already first; add `POST ""` immediately after it.
- `datetime.fromisoformat()` in Python 3.11+ accepts the `datetime-local` format `"2026-07-15T21:00"` without seconds. In Python 3.10, it requires seconds. Use `data.kickoff_iso.rstrip('Z')` + `.replace(tzinfo=timezone.utc)` for safety, or document that `kickoff_iso` must include seconds.
- The FAB's `z-index` must exceed the bottom nav's `z-index` to render above it. Inspect `.bottomnav` in `main.css` for the current value.
- Existing hidden screens (`#eventDetailView`, `#recapView`) are shown/hidden via the `hidden` HTML attribute — follow the same pattern in `create-event.js` for `#createEventView`.
- State reset: `create_event()` uses SQLAlchemy and commits to SQLite; no in-memory dict to reset between tests. Use `conftest.py`'s existing DB reset fixture (or a new one) to isolate test state.
- `amenities` is stored as a JSON string in `EventModel.amenities`; `json.dumps([])` = `"[]"`. On read, `_event_to_dict()` already calls `json.loads()`.

---

## 🔗 References

- ORM model: `fanfest/backend/app/db/models.py` — `EventModel`
- Existing schemas: `fanfest/backend/app/schemas/events.py` — `EventDetail`, `EventSummary`
- Service: `fanfest/backend/app/services/events_service.py`
- Endpoint: `fanfest/backend/app/api/v1/endpoints/events.py`
- DB session: `fanfest/backend/app/db/database.py` — `get_session()`
- Home feed: `fanfest/frontend/index.html`
- API client: `fanfest/frontend/assets/js/api.js`
- Design tokens: `fanfest/frontend/assets/css/main.css` (`:root` block)
- Icon font: Tabler Icons webfont (`@tabler/icons-webfont`) — use `ti-plus` for FAB, `ti-x` for close

---

**Created**: 2026-06-21
**Created By**: Claude (create-sdd-ticket skill)
**INVEST Validated**: ✅
**BDD Scenarios**: 7
**Priority**: Medium
**Labels**: sdd, full-stack, events, create-event, frontend, backend
