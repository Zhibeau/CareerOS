"""Tests for the SQLite storage layer."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.db import CareerDB
from src.models import (
    Achievement,
    Conversation,
    ExtractionResult,
    Message,
    Project,
    Role,
    Skill,
)


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    career_db = CareerDB(db_path)
    yield career_db
    career_db.close()


def _make_conversation(conv_id: str = "conv-1") -> Conversation:
    return Conversation(
        id=conv_id,
        source="chatgpt",
        title="Test Chat",
        messages=[Message(role="user", text="Hello")],
        started_at="2024-01-15T10:00:00Z",
    )


# ── Conversation tests ──


def test_insert_conversation(db: CareerDB):
    conv = _make_conversation()
    db.insert_conversation(conv, raw_path="/tmp/test.json")

    assert db.conversation_exists("conv-1", "chatgpt")
    assert not db.conversation_exists("conv-1", "claude")
    assert not db.conversation_exists("conv-999", "chatgpt")


def test_idempotent_import(db: CareerDB):
    conv = _make_conversation()
    db.insert_conversation(conv, raw_path="/tmp/test.json")
    # Second insert should be ignored (INSERT OR IGNORE)
    db.insert_conversation(conv, raw_path="/tmp/test.json")

    rows = db.conn.execute("SELECT COUNT(*) FROM conversations").fetchone()
    assert rows[0] == 1


def test_update_is_work(db: CareerDB):
    conv = _make_conversation()
    db.insert_conversation(conv, raw_path="/tmp/test.json")
    db.update_conversation_is_work("conv-1", True)

    row = db.conn.execute(
        "SELECT is_work FROM conversations WHERE id = ?", ("conv-1",)
    ).fetchone()
    assert row["is_work"] == 1


# ── Skill dedup tests ──


def test_skill_dedup_by_name(db: CareerDB):
    s1 = Skill(name="React", category="framework")
    s2 = Skill(name="react", category="framework")  # same name, different case

    id1 = db.upsert_skill(s1)
    id2 = db.upsert_skill(s2)

    assert id1 == id2  # Should return same ID

    skills = db.get_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "react"  # normalized to lowercase


def test_different_skills_not_deduped(db: CareerDB):
    db.upsert_skill(Skill(name="React", category="framework"))
    db.upsert_skill(Skill(name="Vue", category="framework"))

    skills = db.get_skills()
    assert len(skills) == 2


# ── Project tests ──


def test_project_dedup_by_name(db: CareerDB):
    p1 = Project(name="Dashboard", summary="Admin dashboard")
    p2 = Project(name="dashboard", summary="Same project")  # case-insensitive match

    id1 = db.upsert_project(p1)
    id2 = db.upsert_project(p2)

    assert id1 == id2
    projects = db.get_projects()
    assert len(projects) == 1


def test_different_projects_not_deduped(db: CareerDB):
    db.upsert_project(Project(name="Dashboard", summary="Admin dashboard"))
    db.upsert_project(Project(name="API", summary="REST API"))

    projects = db.get_projects()
    assert len(projects) == 2


# ── Role tests ──


def test_add_role(db: CareerDB):
    role = Role(title="Backend Engineer", company="Acme", started_at="2023-01", ended_at="2024-06")
    db.insert_role(role)

    roles = db.get_roles()
    assert len(roles) == 1
    assert roles[0]["title"] == "Backend Engineer"
    assert roles[0]["company"] == "Acme"


def test_link_project_to_role(db: CareerDB):
    role = Role(title="Backend Engineer", company="Acme")
    db.insert_role(role)

    project = Project(name="API Gateway", summary="Build API gateway")
    pid = db.upsert_project(project)

    db.link_project_to_role(pid, role.id)

    roles = db.get_roles()
    assert len(roles[0]["projects"]) == 1
    assert roles[0]["projects"][0]["name"] == "API Gateway"


# ── Store extraction result tests ──


def test_store_extraction_work(db: CareerDB):
    conv = _make_conversation()
    db.insert_conversation(conv, raw_path="/tmp/test.json")

    result = ExtractionResult(
        is_work=True,
        projects=[Project(name="My App", summary="A web app")],
        skills=[
            Skill(name="Python", category="language"),
            Skill(name="Flask", category="framework"),
        ],
        achievements=[
            Achievement(summary="Built REST API", impact="Serves 1k req/s")
        ],
        project_skills={"My App": ["Python", "Flask"]},
        project_achievements={"My App": ["Built REST API"]},
    )

    db.store_extraction("conv-1", result)

    # Check is_work flag
    row = db.conn.execute(
        "SELECT is_work FROM conversations WHERE id = ?", ("conv-1",)
    ).fetchone()
    assert row["is_work"] == 1

    assert len(db.get_projects()) == 1
    assert len(db.get_skills()) == 2
    assert len(db.get_achievements()) == 1

    # Check junction tables
    proj_skills = db.conn.execute(
        "SELECT COUNT(*) FROM project_skills"
    ).fetchone()[0]
    assert proj_skills == 2

    proj_achs = db.conn.execute(
        "SELECT COUNT(*) FROM project_achievements"
    ).fetchone()[0]
    assert proj_achs == 1

    conv_projs = db.conn.execute(
        "SELECT COUNT(*) FROM conversation_projects"
    ).fetchone()[0]
    assert conv_projs == 1


def test_store_extraction_non_work(db: CareerDB):
    conv = _make_conversation()
    db.insert_conversation(conv, raw_path="/tmp/test.json")

    result = ExtractionResult(is_work=False)
    db.store_extraction("conv-1", result)

    row = db.conn.execute(
        "SELECT is_work FROM conversations WHERE id = ?", ("conv-1",)
    ).fetchone()
    assert row["is_work"] == 0
    assert len(db.get_projects()) == 0
    assert len(db.get_skills()) == 0


# ── Export tests ──


def test_export_all(db: CareerDB):
    db.upsert_project(Project(name="P1", summary="Project 1"))
    db.upsert_skill(Skill(name="Python", category="language"))
    db.insert_achievement(Achievement(summary="Did something"))
    db.insert_role(Role(title="Engineer"))

    data = db.export_all()
    assert len(data["projects"]) == 1
    assert len(data["skills"]) == 1
    assert len(data["achievements"]) == 1
    assert len(data["roles"]) == 1
