# Fan Fest — Project Write-Up

## What problem we tried to solve

Every weekend, football fans across Latin America gather in parks, bars, and living rooms to watch matches together. These gatherings are real, spontaneous, and deeply social — but they're invisible. There's no place to find out where people are meeting, no way to coordinate across friend groups, and nothing that captures the experience afterward. The match ends and the memory dissolves.

We saw a gap that no single platform fills: the full arc from *"where should I watch this?"* to *"I was there."*

## What we built

Fan Fest is a web platform that follows fans through the complete journey of a watch party:

1. **Discover** — Browse fan events near you with a visual-first event feed.
2. **RSVP** — Register in one tap and get a Google Calendar invite with the event details.
3. **Navigate** — Open Google Maps directly from the event page to find the venue.
4. **Share** — Upload photos during the event to a live gallery wall backed by Google Drive, visible to all attendees in real time.
5. **Relive** — After the final whistle, an AI-generated recap turns the event into a personal story: *"Here's your Fan Fest at Estadio Kempes, June 18, with 47 fans and 3 goals."*

The AI recap is the moment the whole flow is building toward. The first four steps exist to earn it.

## How we used AI to build it

**Claude Code CLI** was the primary development tool. Rather than writing code from scratch, we described what we needed — API endpoints, frontend components, data flows — and iterated from Claude's output. This compressed the scaffolding phase from hours to minutes and let the team focus on product decisions instead of boilerplate.

**QAF (Qubika Agentic Framework)**, our internal multi-agent system built on LangGraph and Claude, handled two key tasks: the `initialize-project` workflow analyzed the repo and generated the project configuration automatically, and the `implement-ticket` skill delegated feature work to Claude Code agents running in sequence. We were essentially using an agent to coordinate other agents on our own codebase — a pattern that paid off in the compressed timeline.

**In the product itself**, Claude (Anthropic) generates the post-event recap. We pass it the event location, date, attendance count, and match context, and it returns a narrative that feels personal rather than generated. The first version surprised us — we expected to spend significant time tuning the prompt, but the initial output was close enough to ship. The lesson: Claude handles narrative well with light guidance, especially when the input is structured.

The full demo was designed and built in approximately 8 hours across the team. We moved fast by treating AI as a collaborator at every layer — design decisions, code generation, and the core product feature — rather than as a single tool applied to one step.

## What we'd do next

- **Real-time gallery updates** — WebSocket push so photos appear on the wall as they're uploaded, without a page reload.
- **Event creation flow** — Let any fan host their own Fan Fest, not just discover existing ones.
- **Live match data integration** — Connect to a football data API to pull real-time scores and match moments into the recap automatically instead of using manual input.
- **Private events** — Friend-group watch parties with invite-only access, shared only via link.
- **Multi-sport support** — The core flow works for any live sport; the branding and discovery layer would adapt to basketball, rugby, tennis.
- **Push notifications** — Alert fans to events near them on match day before they think to look.

The infrastructure is Google-native by design. With more time, we'd lean further into that — using Google Photos API for richer media management, and Google Wallet for event tickets.
