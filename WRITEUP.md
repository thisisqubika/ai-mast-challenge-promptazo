# Tribuna — Project Writeup
Qubika AI Mastery Challenge · World Cup Edition 2026 · Track: Fan Experience


## What Problem We Tried to Solve

Watching events with other fans is one of the best parts of the experience, especially when the World Cup begins — but the infrastructure around it is completely scattered. Every week across Latin America, fans improvise: a WhatsApp group to coordinate, a Facebook event nobody updates, a bar everyone defaults to out of habit. There is no single place to find these gatherings, decide they're worth going to, get there with ease, connect with other fans in the moment, and keep the memory of the experience afterward.

Existing platforms solve one slice of this. Eventbrite handles registration. Fever does visual discovery. Facebook Events covers photo sharing. But none of them were built for the specific rhythm of a football match — the buildup, the live intensity, the emotional release at the final whistle. And every single one of them stops when the match ends.

Tribuna was our answer to that gap.

## What We Built

With a week of production time, we made a deliberate decision: rather than build a shallow end-to-end product, we would go deep on the parts of the journey that no one has built well before — the experience during the match, and what happens after it.

The journey we shipped looks like this:

A fan arrives at a Fan Fest and checks in with a single "I’m here" tap. That action unlocks the live match screen — a real-time view of the event showing the current score, a countdown, and a live photo wall where every attendee can upload photos that appear instantly in a shared gallery. The energy of the room becomes visible inside the app.

When the final whistle blows, Tribuna detects it automatically. No button press, no manual action. The interface transitions into Recap Mode — a post-match experience that weaves together the fan photos uploaded during the event, the key moments of the match, and an AI-generated narrative summary. The recap identifies emotional beats — "Pre-match," "Event starts," "First goal", etc. — and presents them as a highlight reel that feels personal and shareable. Fans can react, leave comments, and share the recap directly to social media.

The result is a closed loop: you lived it together, and now you have something to remember it by.


## How We Used AI to Build It

Claude (Anthropic) is at the center of the product's hero moment. After a match ends, a call to the Claude API generates the recap narrative from structured event context — venue, date, teams, final score, goal timeline, photo count. The output is shaped as a JSON object with two keys: highlights (an array of labeled moment objects) and narrative (a short paragraph in Spanish, in a selectable tone: exciting, inspiring, humorous, or nostalgic).

On the development side, Claude Code CLI was used end-to-end from the terminal — scaffolding the FastAPI backend, generating API routes, writing frontend components, and iterating on bugs through natural-language prompts. QAF (Qubika Agentic Framework), our internal multi-agent framework built on LangGraph and Claude, ran the initialize-project workflow to analyze the repository and auto-generate project configuration, and powered the implement-ticket skill to delegate feature development tasks to Claude Code agents following spec-driven tickets.

## What We'd Do Next With Another Week

Everything we built lives in the middle and end of the fan journey. The natural next chapter is the beginning: helping fans find their people before the match even starts. The "before the experience" arc we'd build next:

- Smart event discovery. A location-aware explore feed where fans can browse upcoming Fan Fests near them — visual-first cards showing the event, the team, the venue vibe, and who's already going. 

- Event details and registration. A rich event page covering everything a fan needs to commit: description, location, amenities (food trucks, seating, pet-friendly areas, sponsors), cost, and a one-tap RSVP. From that confirmation screen, fans can share the event directly to WhatsApp or Instagram Stories.

- Connected invitations. Direct invite-by-link for private Fan Fests (small watch parties at home or a friend's bar), with no account required to RSVP.

- Push notifications for the moments that matter: kickoff, goals, and "your recap is ready" when the AI finishes generating after the final whistle.

The vision is a complete fan journey in a single product — from the first scroll through nearby events, to the last share of the recap. We got the hardest part right. The rest is a matter of time.

