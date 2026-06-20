# FEST-07: Domain Entity Dataclasses and Local Seed Dataset

## 📋 User Story

**As a** backend developer working on FanFest
**I want** a well-defined Python dataclass for every core domain entity (Event, Fan, Registration, Match, Prediction, Photo) and a local seed dataset that instantiates them
**So that** the in-memory state layer has an explicit, type-checked schema that makes entity relationships clear and paves the way for future persistence

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | FanFest Backend | Initial request, requirements validation |
| Tech Lead | FanFest Backend | Architecture review, entity model approval |
| All feature teams | FEST-02 → FEST-06 | Consumers of the defined entities |

---

## 🎯 Success Criteria

1. A single module `fanfest/backend/app/models/entities.py` defines one `@dataclass` per entity; `python -c "from app.models.entities import *"` exits 0.
2. `fanfest/backend/app/data/seed.py` provides at least 2 sample instances per entity, all importable without errors.
3. `ruff check .` passes on all new and modified files.
4. `pytest` suite stays green (no regressions; no test changes required for this ticket unless the services are refactored to use the new models).

**Metrics**: Zero import errors on any of the new modules; dataclass fields match the shapes already used by the existing in-memory service dicts.

---

## ✅ Acceptance Criteria

### Scenario 1: All entity dataclasses import cleanly

```gherkin
Given the module fanfest/backend/app/models/entities.py exists
When a developer runs: python -c "from app.models.entities import Event, Fan, Registration, Match, Goal, Prediction, Photo"
Then the import succeeds with no TypeError or ImportError
```

### Scenario 2: Seed dataset loads and provides typed instances

```gherkin
Given the module fanfest/backend/app/data/seed.py exists
When a developer runs: python -c "from app.data.seed import EVENTS, FANS, REGISTRATIONS, MATCHES, PREDICTIONS, PHOTOS; print(len(EVENTS))"
Then the output is >= 2 for every collection
And each element is an instance of the corresponding dataclass
```

### Scenario 3: Fan entity is valid with required fields only

```gherkin
Given the Fan dataclass is defined with optional fields having defaults
When a Fan is constructed with only user_id and name
Then the instance is created without error
And fan.location defaults to None or an empty string
```

### Scenario 4: Registration links Fan to Event

```gherkin
Given a Fan with user_id "fan-001" and an Event with id "evt-001"
When a Registration is created with user_id="fan-001" and event_id="evt-001"
Then registration.user_id == "fan-001"
And registration.event_id == "evt-001"
And registration.checked_in is False by default
```

### Scenario 5: Match entity tracks goals as a typed list

```gherkin
Given a Match for event "evt-001" in status "pre"
When a Goal(player="Messi", team="Argentina", minute=23) is appended to match.goals
Then match.goals has length 1
And match.goals[0].player == "Messi"
```

### Scenario 6: Prediction holds clamped scores

```gherkin
Given a Prediction for user "fan-001" on event "evt-001"
When it is constructed with home_score=9 and away_score=0
Then the Prediction is created without error
And prediction.home_score == 9
And prediction.away_score == 0
```

### Scenario 7: Photo entity requires all identity fields

```gherkin
Given the Photo dataclass
When a Photo is constructed without uploader_id
Then a TypeError is raised (no default for required field uploader_id)
```

---

## 🔧 Technical Context

### Current State

- `fanfest/backend/app/models/` exists with an empty `__init__.py` — the intended slot for entity definitions.
- Domain state lives in module-level Python dicts in three services:
  - `events_service.py` — `_events`, `_predictions`, `_attendees` (raw dicts, no types)
  - `registry.py` — `_checked_in: dict[str, str]` (user_id → name mapping, no typed entity)
  - `photos_service.py` — in-memory photo list
  - `match_state.py` — dict-based match state per event
- Pydantic `BaseModel` classes in `schemas/events.py` define the **API response shapes** (e.g. `EventDetail`, `AttendeeOut`, `MatchState`, `Photo`). These are the API contract layer and must **not** be replaced — they stay as-is.
- No ORM, no database, no durable store. Persistence is in-process only.

### Proposed Changes

1. **`fanfest/backend/app/models/entities.py`** (new file) — one `@dataclass` per entity:

   | Dataclass | Key fields | Source of truth |
   |---|---|---|
   | `Event` | `id`, `home_team`, `home_flag`, `away_team`, `away_flag`, `venue_name`, `venue_address`, `organizer`, `kickoff_iso`, `match_start_time`, `invite_link`, `calendar_link`, `maps_link` | Mirrors `_events` dict in `events_service.py` |
   | `Fan` | `user_id`, `name`, `location: str \| None = None` | Mirrors `registry._checked_in`; adds optional location |
   | `Registration` | `user_id`, `event_id`, `registered_at`, `checked_in: bool = False`, `checked_in_at: datetime \| None = None` | Replaces the `_attendees` dict semantics |
   | `Match` | `event_id`, `home_team`, `away_team`, `home_score: int = 0`, `away_score: int = 0`, `status: str = "pre"`, `clock_seconds: int = 0`, `goals: list[Goal] = field(default_factory=list)` | Mirrors dict in `match_state.py` |
   | `Goal` | `player`, `team`, `minute: int` | Already in `schemas/events.py` as Pydantic; duplicated as a dataclass here for the model layer |
   | `Prediction` | `user_id`, `event_id`, `home_score: int`, `away_score: int`, `submitted_at: datetime` | Mirrors `_predictions` dict in `events_service.py` |
   | `Photo` | `id`, `event_id`, `url`, `uploader_id`, `uploader_name`, `uploaded_at: datetime` | Mirrors `Photo` Pydantic schema in `schemas/events.py` |

2. **`fanfest/backend/app/data/__init__.py`** (new) — empty package init.

3. **`fanfest/backend/app/data/seed.py`** (new) — 2–3 sample instances per entity, assigned to module-level constants (`EVENTS`, `FANS`, `REGISTRATIONS`, `MATCHES`, `PREDICTIONS`, `PHOTOS`). Seeds expand on the single `evt-001` already in `events_service.py`.

### Technical Constraints

- Use `dataclasses.dataclass` from the Python stdlib — not Pydantic — for entity model definitions. This cleanly separates the domain model layer (`models/`) from the API contract layer (`schemas/`).
- `field(default_factory=list)` is required for mutable defaults (e.g. `Match.goals`).
- `from __future__ import annotations` at the top of `entities.py` to support forward references without quoting.
- No `__post_init__` validation for score clamping — that belongs in the service layer (already enforced by Pydantic's `Field(ge=0, le=9)` on the API boundary).
- Do **not** refactor existing service dicts in this ticket (that migration is out of scope). The dataclasses define the schema; services continue to use their raw dicts until a dedicated migration ticket.
- `ruff check .` must pass; no line-length violations (88 chars).

### Integration Points

- Existing Pydantic schemas in `schemas/events.py` remain untouched — the dataclasses are a parallel model layer, not a replacement.
- Services (`events_service.py`, `registry.py`, etc.) are read-only for this ticket — no behavior changes.
- Seed data in `data/seed.py` is importable by future service tests as fixtures, replacing hand-rolled inline dicts.

### Architecture Decisions

- **`@dataclass` over Pydantic for models** — Pydantic's runtime validation cost is appropriate at the API boundary; pure dataclasses are lighter and more explicit for internal domain objects that don't need JSON serialisation.
- **Separate `models/` and `schemas/`** — conventional FastAPI layering: `schemas/` is the API contract; `models/` is the domain model. The empty `models/__init__.py` already signals this intent.
- **Seed data in `data/seed.py`, not embedded in services** — keeps service state reset logic (`_events = {}`) independent from the demo dataset, making it easier to swap in real persistence later.
- **No DB/ORM in this ticket** — the project has no persistent store declared (confirmed by wiki). Adding SQLAlchemy or similar is a separate infrastructure decision.

### Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirms no ORM/database; state lives in module-level Python dicts in `services/match_state.py` and `services/photos_service.py`; `models/` directory exists with empty `__init__.py`.

### Graph Evidence

- Codebase inspection of `app/models/__init__.py` — file is empty; directory is the intended slot for entity dataclasses.
- `app/schemas/events.py` — existing Pydantic models define the API contract shapes that the new dataclasses must align with (field names are the canonical reference).

---

## 🚫 Out of Scope

1. Replacing or modifying existing in-memory service dicts to use the new dataclasses (separate migration ticket).
2. Adding a database or ORM (separate infrastructure decision).
3. Score validation / clamping in `__post_init__` — that is the service and schema layer's responsibility.
4. Frontend data changes — this ticket is backend-only.
5. Pydantic schema changes in `schemas/events.py`.

**Future Considerations**: Once this ticket lands, a follow-up can migrate each service dict to use typed dataclass instances. After that, swapping the in-memory store for SQLite/Postgres becomes a single-layer change.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases

1. **`Match.goals` default** — must use `field(default_factory=list)`, not `goals: list = []` (mutable default causes shared state across instances).
2. **`datetime` fields** — must be timezone-aware (`datetime.now(timezone.utc)`) in seed data to match the convention already used in `events_service.py`.
3. **`Registration.checked_in_at`** — `None` when not yet checked in; must be `datetime | None`, not `Optional[datetime]` (Python 3.10+ union syntax is already used in the codebase, e.g. `user_id: str | None`).
4. **Forward reference in `Match`** — `goals: list[Goal]` requires `Goal` to be defined before `Match` in the same file (or use `from __future__ import annotations`).

### Error Scenarios

1. **Missing `field(default_factory=list)`** — Python raises `ValueError: mutable default <class 'list'> for field goals is not allowed` at class definition time. Fix: always use `dataclasses.field(default_factory=list)` for list fields.
2. **Circular import** — if `data/seed.py` imports from `services/` while `services/` imports from `data/seed.py`, a circular import occurs. Fix: `seed.py` imports only from `models/entities.py`, never from `services/`.

### Data Validation Rules

- `Prediction.home_score` and `away_score` are integers 0–9; validation is enforced at the Pydantic schema level on the API boundary, not in the dataclass.
- `Fan.user_id` is a non-empty string; no runtime check in the dataclass (keep it simple).
- `Photo.id` is a UUID string assigned by the service; the dataclass has no `default_factory` for it (caller must provide).

---

## 📦 Dependencies

### Blocking

- None — all stdlib; no new packages required.

### Related

- `FEST-02` — `events_service.py` will eventually be refactored to store `Event`, `Prediction`, and `Registration` instances.
- `FEST-03` — `photos_service.py` will eventually store `Photo` instances.
- `INFRA-01` — CI must stay green; this ticket only adds files and must not break the test suite.

---

## 🎓 Definition of Done

### Code Quality

- [ ] `fanfest/backend/app/models/entities.py` defines `Event`, `Fan`, `Registration`, `Match`, `Goal`, `Prediction`, `Photo` as `@dataclass` classes.
- [ ] `fanfest/backend/app/data/__init__.py` exists (empty).
- [ ] `fanfest/backend/app/data/seed.py` defines `EVENTS`, `FANS`, `REGISTRATIONS`, `MATCHES`, `PREDICTIONS`, `PHOTOS` with ≥ 2 instances each.
- [ ] `ruff check .` passes from `fanfest/backend/`.
- [ ] No mutable default values without `field(default_factory=...)`.
- [ ] All `datetime` values in seed data are timezone-aware.

### Testing

- [ ] `pytest` passes with no regressions (existing 17 tests stay green).
- [ ] Manual smoke test: `python -c "from app.models.entities import *; from app.data.seed import EVENTS, FANS; print(EVENTS[0])"` prints the first event without error.
- [ ] No circular imports (confirmed by running `python -c "from app.data.seed import *"` from `fanfest/backend/`).

### Documentation

- [ ] Docstring on `entities.py` module explaining the `models/` vs `schemas/` split.
- [ ] Inline comment in `seed.py` noting that seed data mirrors `events_service._events` for `evt-001`.

### Review & Deployment

- [ ] Code reviewed and approved.
- [ ] PR merged.

---

## 📝 Implementation Notes

- `entities.py` should open with:
  ```python
  """Domain entity dataclasses for FanFest.

  These are the canonical in-memory model layer. They live here (models/)
  rather than in schemas/ because schemas/ owns the API contract (Pydantic);
  models/ owns the domain shape (dataclasses, no runtime validation overhead).
  """
  from __future__ import annotations
  from dataclasses import dataclass, field
  from datetime import datetime
  ```
- Seed data in `seed.py` should re-use the `evt-001` / `event_001` IDs already present in `events_service.py` and `registry.py` so that the demo app stays consistent when services are later migrated.
- `Fan` users `user_001`, `user_002`, `user_003` already exist in `registry._checked_in`; the seed should include them so a future refactor can drop `registry.py` entirely.
- The `Photo.url` in seed data can be a placeholder string (`"https://picsum.photos/400/300?random=1"`) since no real storage exists.

---

## 🔗 References

- Existing Pydantic schemas: `fanfest/backend/app/schemas/events.py`
- Existing in-memory stores: `fanfest/backend/app/services/events_service.py`, `registry.py`, `match_state.py`, `photos_service.py`
- Empty models package: `fanfest/backend/app/models/__init__.py`
- Wiki: `docs/llm-wiki/wiki/services/backend.md` (data layer section)

---

**Created**: 2026-06-19
**Created By**: Claude (create-sdd-ticket skill)
**INVEST Validated**: ✅
**BDD Scenarios**: 7
**Priority**: Medium
**Labels**: sdd, backend, data-model, entities, seed-data

