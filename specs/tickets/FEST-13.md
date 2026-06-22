# FEST-13: Integrate API-Football for live match scores and goals

## 📋 User Story

**As a** FanFest organizer
**I want** the app to pull live scores, goals, and match status automatically from API-Football
**So that** I don't have to enter goals manually and the recap always reflects the real match result

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | FanFest Product | Initial request, scope validation |
| Tech Lead | FanFest Full-Stack | Architecture review, endpoint contract |
| Backend | FanFest API | API client, service extension, endpoints |

---

## 🎯 Success Criteria

1. `GET /api/v1/fixtures/search?team=belgrano&date=2026-06-22` returns a list of matching fixtures from API-Football with fixture ID, teams, date, status, and score.
2. `POST /api/v1/events/{event_id}/link-fixture` with `{"fixture_id": 12345}` links a real fixture to a FanFest event and performs an initial sync of score, goals, and status into `MatchState`.
3. `POST /api/v1/events/{event_id}/sync-fixture` re-fetches the fixture from API-Football and updates `MatchState`; a second call within 60 s returns the cached state without hitting the API (rate-limit guard).
4. After syncing a finished fixture, `GET /api/v1/events/{event_id}/match-state` returns `status="ended"`, correct `home_score`, `away_score`, and a `goals` list with `player`, `team`, and `minute` for each goal.
5. All existing tests (`pytest`) stay green; `ruff check .` passes.

---

## ✅ Acceptance Criteria

### Scenario 1: Search returns fixtures

```gherkin
Given API_FOOTBALL_KEY is set in the environment
When the organizer calls GET /api/v1/fixtures/search?team=belgrano&date=2026-06-22
Then the response is a JSON array of fixtures
And each fixture has: fixture_id, home_team, away_team, date, status, home_score, away_score
```

### Scenario 2: Link and initial sync

```gherkin
Given a FanFest event with id "abc123" exists
And the matching API-Football fixture_id is 67890
When the organizer POSTs {"fixture_id": 67890} to /api/v1/events/abc123/link-fixture
Then the server fetches the fixture from API-Football
And updates the event's MatchState with live score, goals, and status
And returns the updated MatchState
```

### Scenario 3: Manual sync refreshes state

```gherkin
Given event "abc123" is linked to fixture 67890
And more than 60 seconds have passed since the last sync
When the organizer POSTs to /api/v1/events/abc123/sync-fixture
Then the server fetches fresh data from API-Football
And the returned MatchState reflects the latest score and goals
```

### Scenario 4: Rate-limit guard prevents duplicate API calls

```gherkin
Given event "abc123" was just synced 10 seconds ago
When sync-fixture is called again
Then the server returns the cached MatchState without calling the API-Football API
```

### Scenario 5: No API key — graceful degradation

```gherkin
Given API_FOOTBALL_KEY is not set
When the organizer calls any /fixtures or /sync-fixture endpoint
Then the server returns HTTP 503 with a clear error message
And the manual match-state update endpoints continue to work normally
```

### Scenario 6: Status mapping

```gherkin
Given a fixture with API-Football status "FT"
When it is synced
Then MatchState.status == "ended"

Given a fixture with API-Football status "1H" or "HT" or "2H"
When it is synced
Then MatchState.status == "live"

Given a fixture with API-Football status "NS"
When it is synced
Then MatchState.status == "pre"
```

---

## 🔧 Technical Context

### Current State

- `fanfest/backend/app/services/match_state.py` — in-memory `_states` dict keyed by `event_id`; populated from seed data. `get_state()`, `score_goal()`, `end_match()`, `reset()`. No external API calls.
- `fanfest/backend/app/core/config.py` — `Settings` Pydantic model; no `api_football_key` field.
- `fanfest/backend/app/api/v1/endpoints/events.py` — router at `/api/v1/events`; `GET /{event_id}/match-state` and `POST /{event_id}/match-state` already exist.
- `requirements.txt` — `httpx>=0.27.0` already present; no new dependencies needed.

### Proposed Changes

#### New file: `fanfest/backend/app/services/football_api.py`

API-Football client. Base URL: `https://v3.football.api-sports.io`. Auth header: `x-apisports-key`.

**Functions:**

```python
async def search_fixtures(team: str, date: str) -> list[dict]:
    """Search fixtures by team name substring + date (YYYY-MM-DD).
    Calls GET /fixtures?date={date}&search={team} via httpx.
    Returns list of dicts: {fixture_id, home_team, away_team, date, status, home_score, away_score}.
    """

async def get_fixture_state(fixture_id: int) -> dict:
    """Fetch a single fixture and map to MatchState-compatible dict.
    Calls GET /fixtures?id={fixture_id}.
    Returns: {status, home_score, away_score, goals: [{player, team, minute}]}.
    """
```

**Status mapping** (`fixture.fixture.status.short`):

| API-Football | FanFest |
|---|---|
| `NS` | `pre` |
| `1H`, `HT`, `2H`, `ET`, `BT`, `P`, `LIVE` | `live` |
| `FT`, `AET`, `PEN` | `ended` |
| anything else | `pre` |

**Goal mapping** from `fixture.events[]`:
- Filter `type == "Goal"` (includes own goals, excludes penalties unless `detail == "Penalty"`)
- Map `{player: event.player.name, team: event.team.name, minute: event.time.elapsed}`

#### Updated: `fanfest/backend/app/core/config.py`

```python
api_football_key: str = ""
```

#### Updated: `fanfest/backend/app/services/match_state.py`

Add two in-memory dicts alongside `_states`:

```python
_fixture_links: dict[str, int] = {}      # event_id → fixture_id
_last_sync:     dict[str, float] = {}    # event_id → epoch seconds of last API sync
SYNC_THROTTLE_SECONDS = 60
```

New functions:

```python
def link_fixture(event_id: str, fixture_id: int) -> None:
    """Store the fixture_id link for an event."""

async def sync_from_api(event_id: str, force: bool = False) -> MatchState:
    """Fetch fresh state from API-Football and update _states.
    Respects SYNC_THROTTLE_SECONDS unless force=True.
    Raises HTTP 404 if event has no fixture linked.
    Raises HTTP 503 if API_FOOTBALL_KEY is not set.
    """
```

`sync_from_api` calls `football_api.get_fixture_state(fixture_id)` then builds an updated `MatchState` via `state.model_copy(update={...})` and stores it in `_states[event_id]`.

#### Updated: `fanfest/backend/app/api/v1/endpoints/events.py`

Add three new routes (add before the `/{event_id}/match-state` routes):

```python
# ── API-Football integration ──────────────────────────────────────────────────

@router.get("/fixtures/search")
async def search_fixtures(team: str = Query(...), date: str = Query(...)) -> list[dict]:
    """Search API-Football for fixtures matching team name + date."""

@router.post("/{event_id}/link-fixture", response_model=MatchState)
async def link_fixture(event_id: str, body: LinkFixtureRequest) -> MatchState:
    """Link an API-Football fixture to a FanFest event and perform initial sync."""

@router.post("/{event_id}/sync-fixture", response_model=MatchState)
async def sync_fixture(event_id: str) -> MatchState:
    """Force-refresh match state from API-Football (subject to 60 s throttle)."""
```

New request schema in `schemas/events.py`:

```python
class LinkFixtureRequest(BaseModel):
    fixture_id: int
```

#### Updated: `fanfest/backend/.env.example`

```
API_FOOTBALL_KEY=
```

### Technical Constraints

- **Free tier**: 100 requests/day. All sync calls are on-demand (no background polling). The 60 s throttle prevents accidental spam.
- **No background threads**: FastAPI lifespan / `asyncio` tasks are not needed. Sync happens only when an endpoint is explicitly called.
- **httpx async**: Use `httpx.AsyncClient` with `async with` context manager inside each function.
- **`ruff check .`** must pass; 88-char line limit.
- **No new Python dependencies** — `httpx` is already in `requirements.txt`.
- The `search_fixtures` endpoint on API-Football requires a team name search. API-Football v3 does not support free-text fixture search; instead the flow is: search teams by name → get team ID → search fixtures by team ID + date. Implement this two-step internally inside `football_api.search_fixtures`.

### Integration Points

- `app/core/config.py` — `settings.api_football_key` used by `football_api.py`.
- `app/services/match_state.py` — `_states`, `get_state()` used by all downstream callers (recap, video recap) — updating `_states` in `sync_from_api` means all of them automatically see fresh data.
- `app/api/v1/endpoints/events.py` — new routes must be placed **before** `/{event_id}/match-state` to avoid path conflicts.

### Architecture Decisions

| Decision | Rationale |
|---|---|
| On-demand sync, not background polling | Free tier is 100 req/day; background polling at 60 s over 90 min = 90 calls for one match. On-demand keeps control with the organizer. |
| 60 s throttle in `match_state.py` | Prevents accidental rate-limit exhaustion if someone hammers the sync endpoint. |
| Two-step team search (name → ID → fixtures) | API-Football v3 requires team IDs for fixture lookups; no free-text fixture search exists. |
| `fixture_links` in memory (not DB) | Demo scope — a fixture link is established per session. Adding a `fixture_id` column to `EventModel` is a follow-up. |
| Goals from `events[]`, not `goals{}` object | `fixture.goals` only gives totals; `fixture.events[]` gives per-goal detail (player, minute, team). |

---

## 🚫 Out of Scope

1. Background auto-polling during a live match.
2. Persisting the `fixture_id` link across server restarts (stored in-memory only).
3. Frontend UI for fixture search and linking (organizer uses the API endpoints directly or via a future admin panel).
4. Handling penalties / shootouts in goal detail.
5. Push notifications when a goal is detected.

**Future Considerations**: Add `fixture_id` column to `EventModel` + DB migration so the link survives restarts. Add a simple frontend "Link fixture" UI in event-detail for organizers.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases

1. **Team name has no results** — `search_fixtures` returns `[]`; endpoint returns empty array with HTTP 200.
2. **Fixture has no events yet** (pre-match) — `goals` is `[]`, scores are 0, status is `pre`. Valid state.
3. **Own goals** — `type == "Goal"` with `detail == "Own Goal"`: in API-Football, `team` is the team that **benefits** (the non-scoring team). Map as-is — the team attribution is already correct for FanFest's home/away goal logic.
4. **Fixture not found** (bad fixture_id) — API-Football returns `response: []`; raise HTTP 404.
5. **API key invalid or expired** — API-Football returns `{"errors": {"token": ...}}`; raise HTTP 503 with message `"API-Football authentication failed"`.
6. **Network timeout** — `httpx` raises `httpx.TimeoutException`; catch and raise HTTP 503 `"API-Football unreachable"`.
7. **Event has no fixture linked** — `sync_from_api` raises HTTP 404 `"No fixture linked to this event"`.

### Error Scenarios

| Scenario | Backend behavior |
|---|---|
| `API_FOOTBALL_KEY` not set | HTTP 503 `"API_FOOTBALL_KEY is not configured"` |
| Unknown fixture_id | HTTP 404 `"Fixture not found"` |
| Network error | HTTP 503 `"API-Football unreachable"` |
| Event not in `_states` | HTTP 404 (existing behavior from `get_state()`) |
| Sync called within throttle window | HTTP 200, returns cached state, no API call |

---

## 📦 Dependencies

### Blocking

- FEST-09 (SQLite migration) — **done**; `MatchState`, `match_state_service` are in place.
- API-Football account with a valid `API_FOOTBALL_KEY` — organizer must register at [api-sports.io](https://api-sports.io) (free tier).

### Related

- FEST-03 — `MatchState` schema and `match_state_service` that this ticket extends.
- FEST-04 — `recap_service` reads from `match_state_service.get_state()`; auto-sync means recap always uses real data.

---

## 🎓 Definition of Done

### Code Quality

- [ ] `fanfest/backend/app/services/football_api.py` created with `search_fixtures()` and `get_fixture_state()`.
- [ ] `API_FOOTBALL_KEY` added to `config.py` and `.env.example`.
- [ ] `match_state.py` extended with `_fixture_links`, `_last_sync`, `link_fixture()`, `sync_from_api()`.
- [ ] `LinkFixtureRequest` schema added to `schemas/events.py`.
- [ ] Three new endpoints added to `endpoints/events.py`: `GET /fixtures/search`, `POST /{event_id}/link-fixture`, `POST /{event_id}/sync-fixture`.
- [ ] `ruff check .` passes from `fanfest/backend/`.
- [ ] No new Python dependencies added to `requirements.txt`.

### Testing

- [ ] `pytest` passes with no regressions.
- [ ] Manual smoke test with a real `API_FOOTBALL_KEY`:
  - Search returns at least one fixture for a known team + date.
  - Link + sync updates `MatchState` with real score and goals.
  - Second sync within 60 s returns cached state (verify via log or response time).

### Review & Deployment

- [ ] Code reviewed and approved.
- [ ] PR merged to `feature/FEST-13-api-football` branched from `main`.

---

## 📝 Implementation Notes

- API-Football v3 team search: `GET /teams?search={name}` → pick `response[0].team.id`.
- API-Football v3 fixtures by team + date: `GET /fixtures?team={id}&date={YYYY-MM-DD}`.
- API-Football v3 single fixture: `GET /fixtures?id={fixture_id}`.
- All three calls use header `x-apisports-key: {API_FOOTBALL_KEY}`.
- Use `httpx.AsyncClient(timeout=10.0)` — the API is generally fast but set an explicit timeout.
- In `sync_from_api`, after updating `_states[event_id]`, also record `_last_sync[event_id] = time.monotonic()`.
- The `GET /fixtures/search` route must be declared **before** `GET /{event_id}/match-state` in `events.py` to avoid FastAPI treating `"fixtures"` as an `event_id` path parameter.

---

## 🔗 References

- API-Football v3 docs: [https://www.api-football.com/documentation-v3](https://www.api-football.com/documentation-v3)
- Free tier registration: [https://dashboard.api-football.com](https://dashboard.api-football.com)
- Match state service: `fanfest/backend/app/services/match_state.py`
- Config: `fanfest/backend/app/core/config.py`
- Schemas: `fanfest/backend/app/schemas/events.py`
- Endpoint router: `fanfest/backend/app/api/v1/endpoints/events.py`

---

**Created**: 2026-06-22
**Created By**: Claude (FEST-13)
**Priority**: Medium
**Labels**: backend, integration, live-data, api-football
