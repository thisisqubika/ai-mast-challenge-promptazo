# Feature 01 — Event Discovery (Home Feed)

**Flow steps:** 1–2 · **Risk hint:** LOW · **Strategy:** DIRECT
**AI in product:** none (pure UI + data) · **Slice:** UI → API → mocked data

## Description

The entry point of the app. When a user opens Fan Fest, they land on a home feed
showing fan fests happening **near them** (mocked location/data for the MVP).
Inspired by Fever's visual-first, location-aware discovery — cards, not a list.

Each event card shows: match (teams), venue name, date/time, distance, attendee
count, and a cover image. Tapping a card opens the event detail (Feature 02).

## Acceptance Criteria

- [ ] `GET /api/v1/events` returns a list of nearby fan fests (mocked dataset).
- [ ] Home page renders events as visual cards (image, teams, venue, time, distance, attendee count).
- [ ] Cards are ordered by proximity (mocked distance) then start time.
- [ ] Tapping a card navigates to the event detail view with the event id.
- [ ] Empty state renders gracefully if no events are returned.
- [ ] Mocked dataset has at least 6 World-Cup-themed events to make the demo feel alive.

## Notes

- Mocked data only — no geolocation API required; assume a fixed demo location.
- Seed events should be World Cup themed (teams, venues) for the challenge.
- Suggested files: `fanfest/backend/app/api/v1/endpoints/events.py`,
  `fanfest/backend/app/services/events_service.py` (mock store),
  `fanfest/frontend` home view + event-card component.
