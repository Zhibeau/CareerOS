"""Tests for auth endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import init_db, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    db_path = tmp_path / "test.db"
    import app.db as db_mod

    monkeypatch.setattr(db_mod, "_DB_PATH", db_path)
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_register_and_login(client):
    # Register
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Login with same credentials
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password456"},
    )
    assert resp.status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_refresh_token(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    refresh = resp.json()["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_endpoint(client):
    resp = client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_unauthorized(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
