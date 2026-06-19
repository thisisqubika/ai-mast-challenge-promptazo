# FanFest

## Tech Stack

- **backend** (Python) — FastAPI
- **frontend** (JavaScript) — vanilla JS, no bundler

## File Placement Guide

| File Type | Location Pattern | Example |
|-----------|------------------|---------|
| **Backend** | | |
| FastAPI app entry | `fanfest/backend/app/main.py` | `fanfest/backend/app/main.py` |
| Core config module | `fanfest/backend/app/core/{module}.py` | `fanfest/backend/app/core/config.py` |
| API endpoints package | `fanfest/backend/app/api/v1/endpoints/__init__.py` | `fanfest/backend/app/api/v1/endpoints/__init__.py` |
| Pydantic schemas | `fanfest/backend/app/schemas/{domain}.py` | `fanfest/backend/app/schemas/events.py` |
| Service module | `fanfest/backend/app/services/{module}.py` | `fanfest/backend/app/services/events_service.py` |
| Python package init | `fanfest/backend/app/{module}/__init__.py` | `fanfest/backend/app/__init__.py` |
| Test package | `fanfest/backend/tests/__init__.py` | `fanfest/backend/tests/__init__.py` |
| **Frontend** | | |
| HTML entry point | `fanfest/frontend/index.html` | `fanfest/frontend/index.html` |
| JavaScript app module | `fanfest/frontend/assets/js/{module}.js` | `fanfest/frontend/assets/js/main.js` |
| API client | `fanfest/frontend/assets/js/api.js` | `fanfest/frontend/assets/js/api.js` |
| CSS stylesheet | `fanfest/frontend/assets/css/{module}.css` | `fanfest/frontend/assets/css/main.css` |

## Directory Structure

```
project/
└── fanfest/
    ├── backend/   FastAPI backend
    └── frontend/   frontend
```

## Services & Ports

| Service | Type | Port | Role |
| ------- | ---- | ---- | ---- |
| backend | backend | 8000 | FastAPI backend |
| frontend | frontend | 8080 | frontend |

## Essential Commands

| Command | Description |
| ------- | ----------- |
| `pip install -r requirements.txt` | Install backend dependencies (run from `fanfest/backend/`) |
| `ruff check .` | Lint backend Python (run from `fanfest/backend/`) |
| `pytest` | Run backend tests (run from `fanfest/backend/`) |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | AI recap feature |
| Google OAuth credentials | Calendar, Maps, Drive integrations (see `fanfest/backend/.env.example`) |

<!-- LLM_WIKI_START -->
## LLM Wiki
- Router (entry point): `docs/llm-wiki/CLAUDE.md` — decision table, tier discipline, available graph tools. **Read this first.**
- Index (summary catalog): `docs/llm-wiki/wiki/index.md` — one line per page; pick the 1–3 pages whose summaries match your question.
- Graph-backed docs: generated from .code-review-graph/graph.db with wiki-generator synthesis.
- Before broad code changes: load the router → match the index → read only the matched pages. Stop wikilink traversal at depth 2. Fall back to graph MCP tools only if the wiki does not answer.
<!-- LLM_WIKI_END -->

<!-- GRAPH_DISCIPLINE_START -->
## Graph navigation discipline

Top-down, never breadth-first. Graph MCP tools have strict per-result token caps; unbounded calls overflow silently. The full discipline (lean defaults, drill-in budgets, forbidden tools, spill-protocol HARD-FAILURE semantics) lives in the wiki router at `docs/llm-wiki/CLAUDE.md` (or `AGENTS.md` on Codex). Read it before issuing graph queries; do NOT improvise tool parameters from prior knowledge.
<!-- GRAPH_DISCIPLINE_END -->
