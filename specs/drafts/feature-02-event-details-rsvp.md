# Feature 02 — Event Detail, Invite, Prediction & Check-in

**Flow steps:** 3–4 · **Risk hint:** MEDIUM · **Strategy:** PLAN_FIRST
**AI in product:** none · **Slice:** UI → API → DB

## Description

The event detail screen and the actions a fan takes before the match: learn about
the event, bring friends, commit a prediction, and check in when they arrive.

From the detail view a user can:
- **Share** the event and **invite friends** (invite-by-link, à la Apple Invites / FB Events).
- **Predict the result** of the match (stored per user; revealed in the recap, Feature 04).
- **Save to Google Calendar** and **open navigation** to the venue via Google Maps (Resident Advisor takeaway).
- See the **attendee list** as social proof (Meetup takeaway).
- **Check in** with "Ya estoy acá", which unlocks the live experience (Feature 03).

## Acceptance Criteria

- [ ] `GET /api/v1/events/{id}` returns full event detail (teams, venue, time, organizer, attendees).
- [ ] Detail view shows event info, attendee list, and a shareable invite link.
- [ ] User can submit a **result prediction**; `POST /api/v1/events/{id}/predictions` persists it per user.
- [ ] A user cannot change their prediction after match start (mocked match-start time).
- [ ] "Add to Google Calendar" produces a working calendar link/event for the fest.
- [ ] "How to get there" opens Google Maps directions to the venue.
- [ ] "Ya estoy acá" check-in (`POST /api/v1/events/{id}/checkin`) marks the user present and routes to the live screen.
- [ ] Uploaders/predictors are identifiable — a lightweight registered user identity exists.

## Notes

- Identity can be lightweight (name + id) but **must be persistent** so predictions and photo uploads attribute to a user.
- Prediction model: at minimum home/away/draw or a scoreline; keep it simple for the demo.
- Suggested files: `events.py` endpoints (detail, predictions, checkin),
  `predictions_service.py`, frontend event-detail view + prediction widget.
