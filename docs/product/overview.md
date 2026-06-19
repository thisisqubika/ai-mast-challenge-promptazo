# Fan Fest — Overview

## What we're building

Fan Fest is a community-driven web platform for football fans to **discover**,
**join**, and **relive** watch parties ("fan fests") around live matches. The
hero moment is a personalized, AI-generated **post-event recap** that closes the
loop from discovery to shared memory.

## Challenge context

| Item | Value |
|---|---|
| Event | Qubika AI Mastery Challenge, World Cup Edition 2026 |
| Track | Fan Experience |
| Build week | Jun 16–23, 2026 |
| Submission deadline | **Jun 23, 11:59 PM (UYT)** |
| Demo day | Jun 25, 5:00 PM (UYT) — top 10 finalists, 10 min each |
| Mandatory foundation | **QAF (Qubika Agentic Framework)** |

### Scoring pillars (plan for all three)
1. Cross-studio / cross-country team composition.
2. **Use of QAF** — judged on how well its patterns are applied, not just used.
3. Idea quality and execution (creativity, usefulness, polish of the demo).

## What matters for the demo

The jury evaluates a **10-minute demo**, not the code. Priorities:
- One user story that works end-to-end: **discover a fest → join it → live experience → AI recap**.
- The role of AI must be **visible and explainable** ("the AI does X because Y").
- Nothing breaks live. Mocked data is acceptable where it keeps the demo solid.

## MVP scope — IN

- Home feed of nearby fan fests (mocked event data is fine).
- Event detail: share, invite friends, **predict the result**.
- Check-in ("Ya estoy acá") to enter the live experience.
- Live event screen: live scoreboard, countdown, goal cards, venue info.
- **Hype Wall**: attendees upload photos to a live shared gallery.
- Post-event **Recap mode**: AI highlights, final result, event wrap-up, photo carousel, prediction results, next-event suggestions.

## MVP scope — OUT (explicitly not building)

- Real-time third-party match data feeds (scores/goals are mocked or manually driven).
- Native mobile apps (web only).
- Payments / paid ticketing.
- Full auth provider integration beyond what the demo needs (lightweight registration only; uploaders must be identifiable).
- Real push-notification infrastructure.

## Tech stack (current)

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI | Claude API (Anthropic) — recap + highlight generation |
| Integrations | Google Calendar, Google Maps, Google Drive |
| Build tooling | Claude Code CLI, QAF |

## Build approach

Vertical slices (UI → API → DB) per feature, not horizontal layers. Each slice
is one spec in `/specs` and is demo-able on its own. See `user-flow.md` for how
the slices connect.
