"""Minimal SQLite database for user accounts and rate limiting."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "careeros_backend.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    action      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(_SCHEMA)
    conn.close()
