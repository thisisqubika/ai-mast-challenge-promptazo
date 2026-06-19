# Fan Fest Search

## What is Fan Fest?

Fan Fest is a web platform for discovering and participating in fan events tied to sports and similar experiences. Users can create public or private Fan Fests — from large gatherings in parks and public spaces to small watch parties with friends.

The core differentiator is combining visual discovery, community RSVP, navigation, photo sharing, and AI-powered recaps — an end-to-end fan journey that no single competitor currently offers.

---

## Full Feature Vision

- Create public or private Fan Fests
- Explore Fan Fests near you
- RSVP and event registration
- Invite friends and build communities
- Interactive maps and navigation
- Event amenities (food trucks, pet-friendly spaces, chair rentals, etc.)
- Photo and video sharing
- AI-powered event recaps and highlights

---

## MVP Scope (Demo)

For the demo build, the MVP features are:

- Explore Fan Fests near you
- Event registration
- Event sharing on social media and direct invitation
- Fan Fest details: description, amenities, sponsors, cost, location
- Content sharing during and after the event
- AI-powered event recaps and highlights

---

## Competitive Reference Platforms

| Platform | Key Takeaway for Fan Fest |
|---|---|
| **Eventbrite** | Benchmark for event creation and registration flow. Clean, minimal steps from "create" to "publish." |
| **Fever** | Visual-first discovery (photo-heavy cards). Closest to Fan Fest's desired feel. Urgency mechanics (selling fast, waitlist). |
| **Meetup** | Community/group model. Attendee list visibility drives RSVP conversion. Action-oriented discovery. |
| **Resident Advisor (RA)** | Geolocation-powered discovery. Maps + Uber navigation integration. Rich event pages with amenities and embedded media. |
| **Facebook Events / Apple Invites** | Private event model. Share by link, no app required to RSVP. Shared photo wall tied to the event. |

### Feature Matrix

| Feature | Eventbrite | Fever | Meetup | RA | FB Events |
|---|---|---|---|---|---|
| Event creation (public/private) | ✅ | ❌ | ✅ | ✅ | ✅ |
| Location-based discovery | ✅ | ✅ | ✅ | ✅ | ✅ |
| RSVP / Registration | ✅ | ✅ | ✅ | ✅ | ✅ |
| Social sharing | ✅ | ✅ | ✅ | ❌ | ✅ |
| Interactive map / navigation | ❌ | ❌ | ❌ | ✅ | ✅ |
| Photo/content sharing | ❌ | ❌ | ❌ | ❌ | ✅ |
| Rich event details / amenities | ✅ | ✅ | ❌ | ✅ | ❌ |
| AI / personalization | ❌ | ❌ | ✅ | ✅ | ❌ |

**Fan Fest sits at the intersection of Fever's visual discovery, Meetup's community RSVP, RA's map + navigation, and Facebook Events' photo sharing. The AI recap is the differentiator none of them have.**

---

## Demo Strategy

### Build context: 8 hours total (design + development)

Since this is a **demo**, the goal is storytelling impact, not production completeness.

### Recommended focus: After the event (combined during + after)

The AI recap is the hero moment. Steps 1–4 exist to earn that moment — they should be fast and confident in the demo so the recap has room to land.

---

## Demo Story Map

| Step | User action | Google integration touchpoint | Demo moment |
|---|---|---|---|
| **1. RSVP / Registration** | User finds and registers to a Fan Fest of interest | — | Event card + RSVP confirmation screen |
| **2. Social sharing** | She shares the event with friends and saves the date | **Google Calendar** — event date added automatically | Calendar invite appears with Fan Fest details |
| **3. Navigation** | They all gather at the location | **Google Maps** — deep link from event page | Maps opens with the Fan Fest location pinned |
| **4. Content sharing** | During the event, they take photos and upload them | **Google Drive** — upload to shared event folder | Photos appear on a live event gallery wall inside Fan Fest |
| **5. AI recap** | After the match, they see the recap of the Fan Fest | Fan Fest web — "Recap" tab on event detail page | AI-generated summary + photo highlights + football match moments |

### Key design decisions

- **Step 2:** Social sharing via link/WhatsApp/Instagram is the primary mechanic. Google Calendar is a secondary "add to calendar" action — not the main share method.
- **Step 4:** Drive is the backend; the frontend must show a visible gallery wall for the moment to land in demo context.
- **Step 5:** Align early on whether match highlights are mocked or pulled from an API. Mocked is fine for demo.

### The hero moment

The AI recap (Step 5) is what makes audiences feel something. Everything before it is setup. It should feel personal — e.g., *"Here's your Fan Fest at Estadio Kempes, June 18, with 47 fans and 3 goals."*

---

## Google Integrations

Three integrations thread through the full journey as connective tissue:

| Integration | Role in Fan Fest | Step |
|---|---|---|
| **Google Calendar** | Confirmation + date saving after RSVP | Step 2 |
| **Google Maps** | Navigation to the venue from event page | Step 3 |
| **Google Drive** | Photo/video upload + storage during event | Step 4 |

These add demo credibility by leveraging familiar, trusted infrastructure rather than requiring custom builds.

---

## Name Options

Ten name directions explored:

| Name | Angle | Notes |
|---|---|---|
| **Fanzone** | Community feeling | Direct, lives in sports vocabulary |
| **Stands** | Community feeling | Stadium stands, short and evocative |
| **Terrace** | Community feeling | European football authenticity |
| **Kickoff** | Event/gathering | Action-oriented, works beyond football |
| **Matchday** | Event/gathering | Sports ritual, immediately understood |
| **Fanfield** | Event/gathering | Friendly, open, community-oriented |
| **Rewind** | Experience/memory | Nods to AI recap as hero feature |
| **Fandom** | Experience/memory | Bold, culturally established word |
| **Tifo** | Original/brandable | Insider sports term, strong visual identity potential |
| **Fanfest** | Original/brandable | Clear, zero explanation needed, risk of genericness |

### Top 3 recommendations

| Name | Reason |
|---|---|
| **Stands** | Short, memorable, emotionally resonant, works as a brand |
| **Tifo** | Distinctive, sports-authentic, great visual identity potential |
| **Matchday** | Instantly communicates the sports ritual without needing explanation |

---

## Key Principles

- **Demo framing changes everything.** Scope and narrative decisions should optimize for storytelling impact, not production completeness.
- **The AI recap needs narrative buildup.** The first four steps exist to earn that moment.
- **Google integrations add credibility.** Leverage familiar infrastructure rather than building custom.
- **Steps 1–4 should be fast in the demo.** Speed through setup so the recap has room to breathe.
- **Drive needs a visible frontend.** A gallery wall, not just a folder link, for the photo moment to land.

---

## Tech Stack

- **Backend:** Python / FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **Integrations:** Google Calendar, Google Maps, Google Drive
