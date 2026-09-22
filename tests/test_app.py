"""Tests for the AI SaaS MVP starter backend (no live server needed)."""

import os
import sys
import tempfile

# Isolated temp DB per test run so tests never touch a real leads.db
_tmp = tempfile.mkdtemp()
os.environ["LEADS_DB"] = os.path.join(_tmp, "test_leads.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_route_hot_lead():
    r = client.post("/api/leads/route", json={
        "name": "Ada Demo",
        "email": "ADA@Example.com",
        "company": "DemoCorp",
        "source": "referral",
        "message": "We want a demo and pricing for a pilot.",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["tier"] == "hot"
    assert data["owner"] == "ae-north"
    assert data["score"] >= 70
    assert data["email"] == "ada@example.com"  # normalized
    assert "id" in data
    assert "decision" in data


def test_route_cold_lead():
    r = client.post("/api/leads/route", json={
        "name": "Quiet Person",
        "email": "quiet@example.com",
        "source": "ads",
        "message": "just browsing",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["tier"] == "cold"
    assert data["owner"] == "nurture-drip"


def test_route_warm_lead():
    r = client.post("/api/leads/route", json={
        "name": "Mid Funnel",
        "email": "mid@example.com",
        "company": "MidCo",
        "source": "web",
        "message": "hello",
    })
    assert r.status_code == 201
    assert r.json()["tier"] == "warm"


def test_validation_errors():
    # missing name, bad email, bad source
    r = client.post("/api/leads/route", json={"email": "not-an-email"})
    assert r.status_code == 422
    r = client.post("/api/leads/route", json={
        "name": "X", "email": "x@y.com", "source": "spammy",
    })
    assert r.status_code == 422


def test_list_leads():
    client.post("/api/leads/route", json={"name": "List Me", "email": "list@example.com"})
    r = client.get("/api/leads")
    assert r.status_code == 200
    leads = r.json()["leads"]
    assert any(l["email"] == "list@example.com" for l in leads)


def test_error_handler_returns_json():
    # unknown route -> handled, not an HTML stack trace
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_internal_error_json():
    # force an unhandled exception via a patched dependency-free route path
    from fastapi import Request
    from backend import app as app_module

    async def boom(request: Request):
        raise RuntimeError("boom")

    app_module.app.routes.append(
        __import__("fastapi").routing.APIRoute("/api/boom", boom, methods=["GET"])
    )
    r = client.get("/api/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["error"] == "internal_error"
