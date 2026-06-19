---
document_type: index
summary: >-
  Summary catalog for the ai-mast-challenge-promptazo LLM wiki — one line per
  page, frontmatter inline.
last_updated: '2026-06-19T16:01:37.120Z'
related:
  - ARCHITECTURE.md
  - SERVICES.md
---
# ai-mast-challenge-promptazo LLM Wiki

Summary catalog of every page in this wiki. Each line carries the page summary, document type, tags, and related pages — frontmatter inline so a single read of `index.md` serves Tier 1 retrieval.

## Architecture

- [ARCHITECTURE](ARCHITECTURE.md) — *architecture* — FanFest is a single-repository project (not a monorepo) containing two runtime components under a shared `fanfest/` directory. There is no workspace tool, no... **Tags:** architecture, topology, python, fastapi.

## Services catalog

- [SERVICES](SERVICES.md) — *services* — Catalog of services detected in this project with links to service docs. **Tags:** services, catalog. **Related:** [[ARCHITECTURE]].

## Per-service docs

- [backend](services/backend.md) — *service* — The backend is a Python FastAPI server (port 8000) that acts as the sole API layer for the FanFest platform. It is responsible for serving the REST API consu... **Tags:** service, python, backend, fastapi.

## How agents should use this

- Start with this index. Read the 1–3 page bodies whose summaries match your question.
- Follow `**Related:**` `[[wikilinks]]` only when the matched pages reference them.
- Stop wikilink traversal at depth 2.
- If the wiki does not answer your question, fall back to graph MCP tools — never re-read the wiki cover-to-cover.
