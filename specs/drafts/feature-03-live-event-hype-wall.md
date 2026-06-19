# Feature 03 — Live Event Screen & Hype Wall

**Flow steps:** 5–6 · **Risk hint:** MEDIUM · **Strategy:** PLAN_FIRST
**AI in product:** none (sets up data the recap consumes) · **Slice:** UI → API → DB + Drive

## Description

The in-match experience, shown after check-in. Two parts:

**Live screen** — match state and venue context:
- Live scoreboard + venue info.
- Countdown of match time.
- Goal count in a Google-summary style.
- On each goal, a **card of the scoring player**.
- Match state is **mocked / manually driven** (no live third-party feed).

**Hype Wall** — the shared live gallery:
- Any attendee can **upload a photo** to the wall during the event.
- Photos appear in a live gallery including contributions from **all attendees**.
- Each photo shows **which (registered) user uploaded it**.
- Photos are stored via **Google Drive** (backing store for the gallery).

When the system detects **end of match**, the UI flips to **Post-Event / Recap
mode** (Feature 04) and stops showing pre-event details.

## Acceptance Criteria

- [ ] Live screen shows scoreboard, venue info, match countdown, and goal count.
- [ ] A goal event renders a scoring-player card.
- [ ] Match state is driven by a mocked source the demo can advance (e.g. an admin/dev control or timed script).
- [ ] `POST /api/v1/events/{id}/photos` uploads a photo to the Hype Wall (stored in Google Drive).
- [ ] `GET /api/v1/events/{id}/photos` returns all attendees' photos with uploader identity.
- [ ] Hype Wall renders new photos live (poll or refresh acceptable for MVP).
- [ ] Uploads are rejected for users who are not checked in / not registered.
- [ ] On "match end", the UI transitions to Recap mode and hides pre-event detail.

## Notes

- Google Drive is the photo store; document the OAuth/credentials needs in `.env.example`.
- "Live" can be poll-based (no websockets needed for the demo).
- The photos and final score captured here are the **inputs to the AI recap**.
- Suggested files: `events.py` (photos, match-state), `photos_service.py` (Drive),
  frontend live-event view + Hype Wall grid.
