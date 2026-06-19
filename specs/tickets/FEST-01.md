# FEST-01: Event Discovery Home Feed

## User Story

**As a** FanFest fan who has just opened the app
**I want** to land on a visual home feed showing fan fest events happening near me
**So that** I can quickly discover which watch-parties are closest, see which match is being shown, and tap through to the event I want to attend.

---

## Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | Product (FanFest) | Initial request, requirements validation |
| Product Owner | FanFest PO | Acceptance, prioritization |
| Tech Lead | Frontend/Full-stack lead | Architecture review, technical approval |
| End Users | FanFest fans | Primary beneficiaries |

---

## Success Criteria

1. The home feed renders event cards drawn from a mocked dataset of at least 6 World-Cup-themed events without any backend call being required.
2. Cards are ordered by proximity (mocked distance) and then by start time, matching the sort order the mock data provides.
3. An empty state renders gracefully when the data source returns zero events.
4. Tapping a card passes the event id to the event-detail view (Feature 02).

**Metrics**: All six acceptance criteria pass; the home feed is fully functional with mocked inline data; navigation to the event-detail view works correctly.

---

## Acceptance Criteria

### Scenario 1: Happy Path — home feed loads and displays event cards

```gherkin
Given a user opens the FanFest app
When the home screen initialises
Then the event card grid renders at least 6 World-Cup-themed event cards
And each card displays: match teams (with flags), venue name, date/time, distance, and amenity tags
And cards are ordered by distance ascending, then by start time ascending
```

### Scenario 2: Card navigation — tapping a card opens event detail

```gherkin
Given the home feed is showing a list of event cards
When the user taps on an event card
Then the app navigates to the event-detail view (Feature 02)
And the event id of the tapped card is passed as the navigation parameter
```

### Scenario 3: Empty state — no events available

```gherkin
Given the events data source returns an empty list
When the home screen initialises
Then an empty-state message is displayed to the user
And no broken or missing card elements are visible
```

### Scenario 4: Category filter — switching tabs updates the card list

```gherkin
Given the home feed is displaying FIFA 26 events
When the user taps a different category tab (e.g. Fútbol)
Then the card list updates to show only events in the selected category
And the active tab indicator moves to the selected tab
```

### Scenario 5: Live badge — live events are visually distinguished

```gherkin
Given the home feed is loaded and at least one event has status "live"
When the user views the card for that event
Then a LIVE badge and the current score are displayed on the card
And a pulsing indicator or colour cue distinguishes it from upcoming events
```

### Scenario 6: Layout — card grid is responsive within the phone frame

```gherkin
Given the app is rendered in the phone-frame viewport
When the home screen is displayed
Then all event cards are fully visible without horizontal overflow
And the card layout respects the design's padding and gap tokens
```

---

## Technical Context

### Current State

- The feature is fully implemented as of commit `a617de2` ("Implement Tribuna Home discovery screen").
- Implementation lives entirely in the frontend: `fanfest/frontend/index.html`, `fanfest/frontend/assets/js/main.js`, `fanfest/frontend/assets/css/main.css`.
- No `GET /api/v1/events` backend endpoint exists; this was a deliberate MVP choice — mock data is inlined in `main.js`.
- The backend's `events.py` router currently covers only `/{event_id}/match-state` and `/{event_id}/photos`.

### Proposed Changes (implemented)

- `fanfest/frontend/index.html` — full HTML skeleton: status bar, greeting, pill row (location + search), category tabs, three horizontally-scrollable card rows (Selección, World Cards, Upcoming), bottom navigation.
- `fanfest/frontend/assets/js/main.js` — inline mock data arrays (`worldCards`, `seleccionVenues`, `upcomingCards`, `recapCards`) plus renderers (`renderCategories`, `renderSeleccion`, `renderWorldCards`, `renderUpcoming`, `renderRecap`) and event delegation for card click-through.
- `fanfest/frontend/assets/css/main.css` — full design system: colour tokens, phone-frame layout, card components, category tabs, bottom-nav, LIVE badge, avatar stack, tag pills.

### Constraints

- MVP only: mocked data — no geolocation API, no backend list endpoint required for this ticket.
- No frontend test framework is established; manual verification only (per testing-conventions skill).
- All CSS must live in `fanfest/frontend/assets/css/`; no inline styles (per code-conventions).
- All `fetch()` calls, when introduced, must go through `fanfest/frontend/assets/js/api.js` (per multi-file-workflows gotcha).

### Integration Points

- Card tap navigation feeds into Feature 02 (Event Detail); the event id must be passed correctly.
- Bottom navigation tabs hook into the routing logic that Feature 03 (Live Screen) also uses.

### Architecture Decisions

- **Mock data inline in `main.js` (not a backend call)**: chosen to keep the discovery feed self-contained for the demo with zero backend dependency for Feature 01.
- **Vanilla JS, no bundler**: consistent with the project-wide frontend stack.

### Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — confirms no list-events endpoint exists; clarifies service boundaries and the frontend-only nature of the mock.
- `docs/llm-wiki/wiki/ARCHITECTURE.md` — confirms single-repo layout, port assignments, and stack constraints.

### Graph Evidence

- Tool: `mcp__code_graph__get_impact_radius_tool` — params: `{"changed_files": ["fanfest/frontend/assets/js/main.js", "fanfest/frontend/index.html", "fanfest/frontend/assets/css/main.css"], "max_depth": 2, "detail_level": "minimal"}` — finding: 9 nodes changed, 1 additional file impacted, risk: low. Confirms the ticket is scoped to the frontend only.

---

## Out Of Scope

- Real geolocation (GPS or IP-based); a fixed demo location (Córdoba, AR) is assumed.
- A `GET /api/v1/events` backend endpoint; the data is mocked inline for the MVP. This endpoint may be added in a future ticket when a real data store is introduced.
- User authentication or personalisation of the home feed.
- Pull-to-refresh or pagination.
- Search functionality (the search pill is present in the UI but not wired up in Feature 01).

---

## Edge Cases And Error Handling

| Case | Handling |
|------|----------|
| Zero events in mock data | Render the empty-state message; no broken card shells |
| Event card with missing cover image | Card renders with a fallback colour/gradient, no broken `<img>` |
| Long venue name | CSS truncation (`text-overflow: ellipsis`) prevents layout overflow |
| Card tap with no event id | Navigation is a no-op; console warning logged |

### Validation Rules

- Mock dataset must contain at least 6 events (spec requirement for a demo-ready feel).
- Each event object must carry: `home`, `away`, `homeFlag`, `awayFlag`, `venue`, `distance`, `kickoff` or `date`, and at least one `amenities` entry.

---

## Dependencies

- **Blocking none**
- **Depends on none** for Feature 01 itself
- **Related**: Feature 02 (FEST-02) — event-detail view that card navigation routes to; the event id format used in `main.js` must match what `FEST-02` expects on the detail screen.

---

## Definition Of Done

### Code Quality

- [ ] `ruff check .` passes with zero errors on any backend changes (no backend changes in this ticket).
- [ ] No inline styles introduced — all CSS in `fanfest/frontend/assets/css/main.css` or a peer CSS file.
- [ ] No `fetch()` calls scattered in `main.js`; all API calls go through `api.js`.

### Testing

- [ ] All 6 BDD scenarios manually verified in the browser (no automated frontend test framework exists yet).
- [ ] Empty-state path manually verified by temporarily setting the mock data array to `[]`.
- [ ] Card tap navigation verified to pass the correct event id to the detail view.

### Documentation

- [ ] LLM wiki updated if new patterns are introduced (run `/wiki-refresh`).

### Review And Deployment

- [ ] Code reviewed and approved.
- [ ] Feature works in the phone-frame viewport without horizontal scroll on the `<body>`.

---

## Implementation Notes

The implementation in commit `a617de2` uses three horizontally-scrollable card rows rather than a single vertical list:

1. **Selección row** (`renderSeleccion`) — watch-party venues for the Argentina national-team match.
2. **World Cards row** (`renderWorldCards`) — the main FIFA 26 event cards (live + upcoming matches).
3. **Upcoming row** (`renderUpcoming`) — future events with countdown labels.

This multi-section layout matches the Fever-inspired design brief and provides a richer demo experience than a flat list. The category tab bar at the top (`renderCategories`) filters the active section but is partially scaffolded in Feature 01 — full filtering logic may be completed in a follow-up.

The `api.js` file is not yet used by the home feed (all data is inline mock); when Feature 02 introduces `fetch()` calls it must follow the multi-file-workflows pattern: add the function to `api.js`, not inline in `main.js`.

---

## References

- Draft spec: `specs/drafts/feature-01-event-discovery.md`
- Implementation commit: `a617de2` — "Implement Tribuna Home discovery screen"
- Related ticket: `specs/tickets/FEST-02.md`

---

**INVEST Validated**: yes
**BDD Scenarios**: 6
**Scope Impact**: impacted_services=1, impacted_files=1, max_depth=2 (tool: `mcp__code_graph__get_impact_radius_tool`) — risk: low, Small criterion passes
**Implementation Status**: DONE (commit `a617de2`)
