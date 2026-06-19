# FEST-05: Event Detail Screen (Previa)

## 📋 User Story

**As a** fan browsing the Tribuna app
**I want** to open an event from the Home feed and see the pre-match (Previa) detail screen with match info, a prediction tool, and a hype feed
**So that** I can learn about the fan fest, commit a score prediction, and engage with other attendees before kickoff

---

## 👥 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Requester | FanFest Product | Initial request, requirements validation |
| Product Owner | FanFest Product | Acceptance, prioritization |
| Tech Lead | FanFest Frontend | Architecture review, technical approval |
| End Users | Fans attending fan fests | Primary beneficiaries |

---

## 🎯 Success Criteria

1. The Event Detail (Previa) screen renders every section from the design faithfully, reusing the existing CSS design tokens in `assets/css/main.css`.
2. Tapping a Home event card navigates to the Event Detail screen for that event.
3. The prediction flow works end to end: toggle panel → adjust clamped score steppers → confirm → collapse to confirmed state.
4. `node --check` passes on the new JS, and the page serves with no console errors using inline mock data.

**Metrics**: Screen renders all documented sections with zero console errors; prediction interaction completes without page reload; visual parity with the `Tribuna Event Detail.dc.html` design.

---

## ✅ Acceptance Criteria

### Scenario 1: Screen renders faithfully from a Home card
```gherkin
Given the Tribuna Home feed is showing event cards
When the user taps an event card
Then the Event Detail (Previa) screen is shown for that event
And it renders the back row, match header, event info, action buttons, hype feed, empty state, and floating CTA
And it reuses the existing design tokens from assets/css/main.css
```

### Scenario 2: Match header shows the Previa state
```gherkin
Given the user is on the Event Detail screen in the Previa state
When the screen renders the match header
Then both teams show a flag avatar and name
And the score shows the empty placeholder "– : –"
And a glowing "PREVIA" status pill is visible
And an animated countdown ("Comienza en 10 min") is shown
And the competition label ("FIFA World Cup 2026 · Grupo C · Jornada 2") is shown
```

### Scenario 3: Prediction panel toggles and steppers clamp (happy path)
```gherkin
Given the user is on the Event Detail screen
When the user taps "Predecir"
Then the prediction panel expands inline showing ARG and MEX score steppers
When the user taps the "+" stepper for ARG nine times then once more
Then the ARG score is clamped at 9 and does not increase further
When the user taps the "–" stepper for MEX while the MEX score is 0
Then the MEX score is clamped at 0 and does not go negative
```

### Scenario 4: Confirming a prediction collapses to the confirmed state
```gherkin
Given the prediction panel is open with ARG set to 2 and MEX set to 1
When the user taps "Confirmar predicción →"
Then the panel collapses into the confirmed state
And it shows "Predicción enviada · Argentina 2 – 1 México"
```

### Scenario 5: Upload action is disabled before kickoff
```gherkin
Given the user is on the Event Detail screen in the Previa state
When the screen renders the action buttons
Then the "Subir foto" action button is disabled
And the floating "Subir foto / video" CTA is visible over its gradient
```

### Scenario 6: Hype feed renders all post variants
```gherkin
Given the Event Detail screen has inline mock hype-feed posts
When the hype feed renders under the "Previa" divider
Then photo, video, and text-only posts are shown
And each post shows an avatar, @handle, and time-ago
And video posts show a duration badge on the placeholder
And each post shows react, comment, and share actions
And some posts show like and comment counts
```

### Scenario 7: Empty state when there are no match events
```gherkin
Given the match has not started and there are no match events yet
When the Event Detail screen renders the match-events section
Then the empty state is shown
And it reads "Los eventos del partido aparecerán aquí · Inicio · Goles · Entretiempo · Fin"
```

---

## 🔧 Technical Context

### Current State
- `fanfest/frontend/` is a vanilla JS app with no bundler. `index.html` loads `assets/css/main.css` and `assets/js/main.js`.
- `main.js` already implements the Tribuna Home screen with inline mock data, a `$` DOM helper, `renderX()` functions, and event-delegation listeners called at the bottom of the file.
- `assets/css/main.css` defines the design tokens (`--bg`, `--card`, `--accent`, `--live`, etc.) and component styles.
- `assets/js/api.js` exists but is empty — there is no API client and no backend client wiring yet.
- The feature-02 (`POST /api/v1/events/{id}/predictions`) and feature-03 (photo upload) backends do not exist yet; this ticket consumes them only via mocks.

### Proposed Changes
- Add Event Detail (Previa) markup to `fanfest/frontend/index.html` (a new screen container alongside the Home screen).
- Add screen logic — sections, prediction state, steppers, and renderers — to `fanfest/frontend/assets/js/main.js` or a new `fanfest/frontend/assets/js/event-detail.js`, following the existing renderer + event-delegation pattern.
- Add any new styles to `fanfest/frontend/assets/css/main.css` (or a peer `event-detail.css`), reusing existing tokens; no inline styles.
- Wire Home event-card taps to navigate to the Event Detail screen for the tapped event.
- Keep all data inline as mock data (match, venue, amenities, hype-feed posts), mirroring the Home screen approach.

### Technical Constraints
- Framework-free vanilla JS only — match the existing `fanfest/frontend` style; no new build tooling.
- No inline styles; all CSS lives under `assets/css/`.
- Any browser API call must go through `api.js` only (not scattered `fetch()` in `main.js`) — relevant when the prediction/upload calls are later un-mocked.
- Score steppers clamp to the range 0–9.

### Integration Points
- Reached from a Home event card (feature-01).
- Prediction submit is intended to call feature-02's `POST /api/v1/events/{id}/predictions`; mock the call until that backend exists.
- The floating "Subir foto / video" CTA is intended to call feature-03's photo endpoint; mock the call until that backend exists, and the "Subir foto" action button stays disabled in the Previa state.

### Architecture Decisions
- **Mock data inline, no live feeds in MVP** — rationale: matches the Home screen approach and keeps the screen self-contained while the backends are not yet built.
- **Reuse existing design tokens and the renderer/event-delegation pattern** — rationale: visual and structural consistency with the Home screen, no duplicated styling system.
- **Route prediction/upload calls through `api.js` when un-mocked** — rationale: project convention that all browser API calls are centralized in `api.js`.

---

## 🚫 Out of Scope

The following are explicitly NOT part of this ticket:
1. Building the feature-02 prediction backend or the feature-03 photo/upload backend (the calls are mocked here).
2. Live/real-time hype-feed updates, websockets, or polling (no live feeds in MVP).
3. The in-match Live screen and Hype Wall behavior, and the post-match Recap mode (feature-03 / feature-04 / feature-06).
4. Persistent user identity, real photo/video upload, and storage (Google Drive).

**Future Considerations**: Un-mock the prediction submit against feature-02's `POST /api/v1/events/{id}/predictions` and the upload CTA against feature-03's photo endpoint once those backends land; enable the "Subir foto" action once the match starts.

---

## ⚠️ Edge Cases & Error Handling

### Edge Cases
1. **Score stepper at bounds**: `+` at 9 must not exceed 9; `–` at 0 must not go below 0 (clamp 0–9 for both ARG and MEX).
2. **No match events yet**: render the empty state copy rather than an empty container.
3. **Hype-feed post without media**: text-only posts render without a photo/video placeholder; video posts render a duration badge, photo posts do not.
4. **Re-confirming a prediction**: once confirmed, the panel shows the collapsed confirmed state with the chosen scoreline (no duplicate panels).

### Error Scenarios
1. **Mocked prediction submit fails (future, once un-mocked)**: surface a non-blocking message and keep the entered scoreline; do not crash the screen.
2. **Mocked upload invoked while disabled in Previa**: the "Subir foto" action button is disabled, so the action is not triggerable before kickoff.

### Data Validation Rules
- ARG and MEX prediction scores are integers clamped to 0–9.
- Confirmed-state copy must reflect the exact chosen scoreline ("Argentina X – Y México").

---

## 📦 Dependencies

### Blocking
- [ ] None for the UI itself (the screen ships with mock data).

### Related
- `feature-01-event-discovery` - Home feed; the Event Detail screen is reached from a Home event card.
- `feature-02-event-details-rsvp` - Provides the prediction/check-in backend this screen will later call (mocked for now).
- `feature-03-live-event-hype-wall` - Provides the hype-feed/photo backend this screen will later call (mocked for now).

---

## 🎓 Definition of Done

### Code Quality
- [ ] All acceptance criteria scenarios implemented.
- [ ] `node --check` passes on the new/changed JS.
- [ ] No inline styles; all CSS in `assets/css/`.
- [ ] Browser API calls (when un-mocked) routed through `api.js` only.
- [ ] Code matches the existing vanilla-JS renderer + event-delegation style in `main.js`.

### Testing
- [ ] Manual verification: page serves (`python -m http.server 8080`) and renders with no console errors using inline mock data.
- [ ] Manual verification of prediction toggle, stepper clamping (0–9), and confirmed-state collapse.
- [ ] Manual verification that "Subir foto" is disabled in Previa and the floating CTA is visible.
- [ ] Manual verification of photo/video/text hype-feed post variants and the empty state.
- [ ] Note: no frontend test framework is established in this project (per `testing-conventions`); verification is manual.

### Documentation
- [ ] README updated only if the run/verify steps change (they do not for this screen).
- [ ] Any new prescriptive frontend rule added to the relevant convention skill if a new pattern is introduced.

### Review & Deployment
- [ ] Code reviewed and approved.
- [ ] PR merged.
- [ ] Stakeholders validated the screen against the design.

---

## 🎨 UI Testing (if applicable)

### Test Levels
| Level | Required | Tool | Status |
|-------|----------|------|--------|
| Unit | No | n/a (no frontend test framework) | - |
| Component | No | n/a | - |
| E2E | No | n/a | - |
| Visual | No | Manual visual comparison against design | - |

No automated visual-testing configuration exists in this project, and `testing-conventions` states the frontend has no test framework. Verification for this screen is manual: `node --check` plus visual parity with the design and a clean console.

### Figma Reference (if visual level)
- claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Event Detail.dc.html`

---

## 📝 Implementation Notes

- This is a vanilla port of the Event Detail `.dc.html` into `fanfest/frontend`, the same approach used for the Tribuna Home screen: replace the claude.ai/design runtime (`sc-for` / `sc-if` / `DCLogic` / `support.js`) with plain data-driven HTML/CSS/JS.
- This is the pre-match ("Previa") state of a fan fest.
- Sections top → bottom: back row (arrow + venue, returns to Home) · match header (teams, `– : –` placeholder, glowing PREVIA pill, animated countdown, competition label) · event info (venue + distance, "47 van" attendees pill, scrolling amenity chips) · action buttons ("Subir foto" disabled, "Predecir" toggles the panel) · prediction panel (ARG/MEX steppers clamp 0–9, "Confirmar predicción →") · hype feed under a "Previa" divider (avatar, @handle, time-ago, optional photo/video placeholder with duration badge, caption, react/comment/share, some with like/comment counts) · empty state · floating "Subir foto / video" CTA over a gradient.
- State / interactions from the design: `showPredict` toggle, `homeScore` / `awayScore` steppers (clamped 0–9), `submitPredict` → `predictSent` confirmed state.
- Apply QAF frontend conventions in `code-conventions`; keep it framework-free to match the existing `fanfest/frontend`.

---

## 🔗 References

- Design: claude.ai/design → "Tribuna Fan Fests Discovery" → `Tribuna Event Detail.dc.html`
- Draft: `specs/drafts/feature-05-event-detail-screen.md`
- Implements UI for: `specs/drafts/feature-02-event-details-rsvp.md`, `specs/drafts/feature-03-live-event-hype-wall.md`
- Existing pattern: `fanfest/frontend/assets/js/main.js` (Tribuna Home screen)

---

**Created**: 2026-06-19
**Created By**: Claude (create-sdd-ticket skill)
**INVEST Validated**: ✅
**BDD Scenarios**: 7
**Priority**: Medium
**Labels**: sdd, frontend, ui, event-detail, previa
