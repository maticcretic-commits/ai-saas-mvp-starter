"""AI SaaS MVP starter — FastAPI backend with an agentic lead-routing workflow.

Practice/demo starter for learning: a lightweight SaaS MVP shape
(front-end page + REST API + SQLite state + agentic workflow + Docker),
modeled on the type of deliverables described in fixed-scope MVP postings.
Not client work — the "agent" below is a small heuristic pipeline so the
MVP runs with zero API keys; real LLM scoring is a documented roadmap step.

The lead-routing agent runs 4 steps on every POST /api/leads/route:
  1. extract/normalize  -> clean & standardize lead fields
  2. score             -> heuristic 0-100 fit score -> tier (hot/warm/cold)
  3. route             -> assign an owner queue from tier + source
  4. log decision      -> persist lead + decision trace to SQLite
"""

import logging
import time
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, ValidationError

from backend.db import init_db, insert_lead, list_leads

# ---------------------------------------------------------------- logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("saas-mvp")

app = FastAPI(title="AI SaaS MVP Starter", version="0.1.0")

init_db()

# ---------------------------------------------------------------- models


class LeadIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    company: str = Field(default="", max_length=160)
    source: Literal["web", "ads", "referral", "partner"] = "web"
    message: str = Field(default="", max_length=2000)


# ---------------------------------------------------------------- agent

OWNER_QUEUES = {
    "hot": "ae-north",       # account executives, priority queue
    "warm": "sdr-general",   # sales dev reps
    "cold": "nurture-drip",  # automated nurture, no human owner
}

BUDGET_SIGNALS = ("budget", "pricing", "quote", "cost", "poc", "pilot", "demo", "trial")


def extract_lead(payload: LeadIn) -> dict:
    """Step 1: normalize raw input into a clean lead dict."""
    return {
        "name": payload.name.strip(),
        "email": payload.email.strip().lower(),
        "company": payload.company.strip(),
        "source": payload.source,
        "message": payload.message.strip(),
    }


def score_lead(lead: dict) -> tuple[int, str]:
    """Step 2: heuristic 0-100 fit score -> tier.

    Placeholder for a real LLM/regression scorer; transparent on purpose
    so the decision log stays explainable in the demo.
    """
    score = 20  # base: submitted a lead
    if lead["company"]:
        score += 20
    msg = lead["message"].lower()
    if any(sig in msg for sig in BUDGET_SIGNALS):
        score += 25
    if lead["source"] in ("referral", "partner"):
        score += 20
    if lead["source"] == "ads":
        score += 5
    score = min(score, 100)
    tier = "hot" if score >= 70 else "warm" if score >= 40 else "cold"
    return score, tier


def route_lead(score: int, tier: str, lead: dict) -> tuple[str, str]:
    """Step 3: pick an owner queue and write the decision rationale."""
    owner = OWNER_QUEUES[tier]
    decision = (
        f"tier={tier} score={score} -> owner={owner}; "
        f"source={lead['source']}"
        + ("; buying-signal keywords in message" if tier == "hot" else "")
    )
    return owner, decision


def run_routing_agent(payload: LeadIn) -> dict:
    """Run the full 4-step agent pipeline; returns the enriched lead record."""
    lead = extract_lead(payload)                    # 1. extract
    score, tier = score_lead(lead)                   # 2. score
    owner, decision = route_lead(score, tier, lead)  # 3. route
    lead.update(score=score, tier=tier, owner=owner, decision=decision)
    lead["id"] = insert_lead(lead)                   # 4. log
    return lead


# ---------------------------------------------------------------- middleware

@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000
    log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path,
             response.status_code, elapsed_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_errors(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "Something went wrong. Try again."},
    )


@app.exception_handler(ValidationError)
async def validation_errors(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()},
    )


# ---------------------------------------------------------------- routes

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-saas-mvp-starter"}


@app.post("/api/leads/route", status_code=201)
def route_lead_endpoint(payload: LeadIn):
    log.info("routing lead from %s (%s)", payload.email, payload.source)
    return run_routing_agent(payload)


@app.get("/api/leads")
def get_leads(limit: int = 50):
    return {"leads": list_leads(limit=min(limit, 200))}
