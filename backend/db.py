"""Tiny SQLite helper for the AI SaaS MVP starter.

Keeps schema + CRUD in one small file so the app stays readable.
Database path is controlled by the LEADS_DB env var (defaults to leads.db).
"""

import os
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    company TEXT,
    source TEXT,
    message TEXT,
    score INTEGER NOT NULL,
    tier TEXT NOT NULL,
    owner TEXT NOT NULL,
    decision TEXT NOT NULL,
    received_at TEXT NOT NULL
);
"""


def db_path() -> str:
    return os.getenv("LEADS_DB", "leads.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def insert_lead(lead: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO leads
           (name, email, company, source, message, score, tier, owner, decision, received_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            lead["name"],
            lead["email"],
            lead.get("company", ""),
            lead.get("source", "web"),
            lead.get("message", ""),
            lead["score"],
            lead["tier"],
            lead["owner"],
            lead["decision"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    lead_id = cur.lastrowid
    conn.close()
    return lead_id


def list_leads(limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
