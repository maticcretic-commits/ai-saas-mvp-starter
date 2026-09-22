# AI SaaS MVP Starter

**Practice/demo starter for learning** — a minimal "AI-powered SaaS feature" template
showing the moving parts of a fixed-scope MVP build: a small front-end page, a
backend API with an **agentic lead-routing workflow**, SQLite for state, and Docker
for production-readiness basics.

Modeled on the *type of work* described in a real $500 fixed-scope Upwork posting
("Fixed-Scope MVP: AI-Powered SaaS Feature & Agentic Workflow Setup" — front-end +
agentic AI/RAG workflow + lightweight backend with a small DB + Docker/error logging).
**This is a learning exercise, not client work — no paid experience is claimed here.**

## What it does

The agentic workflow is **CRM lead routing**. `POST /api/leads/route` runs a 4-step
agent pipeline:

1. **Extract / normalize** — clean lead fields (trim, lowercase email)
2. **Score** — heuristic 0–100 fit score → `hot` / `warm` / `cold` tier
3. **Route** — assign an owner queue (`ae-north`, `sdr-general`, `nurture-drip`) with a written decision rationale
4. **Log decision** — persist the lead + decision trace to SQLite

The static front-end page (`frontend/index.html`, vanilla JS, no build step) has a lead
form and a routed-leads table; in a real build this page would be a Next.js/React page.

## Architecture

```
frontend/index.html (vanilla JS, fetch) 
        |
        v
backend/app.py  (FastAPI: routes, request logging, JSON error handler)
  +-- backend/db.py (SQLite: leads table, decision log)
tests/test_app.py (pytest, TestClient)
Dockerfile / docker-compose.yml (containerize API, expose :8000)
```

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
# open http://localhost:8000/docs for the API, or serve frontend/index.html
```

## Run with Docker

```bash
docker compose up --build
# API on http://localhost:8000 — point the front-end at it or copy
# frontend/index.html behind any static server on the same origin
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/leads/route` | Run the lead-routing agent (returns score, tier, owner, decision) |
| GET | `/api/leads` | List routed leads (newest first, `?limit=` up to 200) |

Example:

```bash
curl -X POST http://localhost:8000/api/leads/route \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ada Demo","email":"ada@example.com","company":"DemoCorp","source":"referral","message":"Need a demo and pricing for a pilot."}'
```

All errors return clean JSON (`{"error": ..., "detail": ...}`); every request is logged.

## Learning roadmap

- Swap `frontend/index.html` for a real **Next.js/React page** hitting the same API.
- Replace the heuristic scorer with a **real LLM call** (OpenAI/Anthropic API) — keep the decision log so routing stays explainable.
- Swap SQLite for **Postgres**; add Alembic migrations.
- Add **auth + multi-tenant scoping** and structured (JSON) error logging.
- Containerize the front-end too; add CI running `pytest` on every push.

## Practice notes (TODO for the learner)

- [ ] Try adding a 5th agent step: draft a personalized outreach note per tier.
- [ ] Add a `/api/stats` endpoint (counts per tier/owner).
- [ ] Harden scoring: turn signals into a config file instead of code constants.
