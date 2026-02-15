"""Tests for the service layer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.db import CareerDB
from src.models import Achievement, ExtractionResult, Project, Role, Skill
from src.service import (
    AmbiguousIDError,
    CareerService,
    NotFoundError,
    ServiceError,
)


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    career_db = CareerDB(db_path)
    yield career_db
    career_db.close()


@pytest.fixture
def svc(db):
    return CareerService(db)


def _write_json(data, suffix=".json") -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return Path(f.name)


def _chatgpt_conv(conv_id="conv-1", title="Test", messages=None):
    if messages is None:
        messages = [("user", "Hello"), ("assistant", "Hi")]
    mapping = {"root": {"id": "root", "parent": None, "message": None}}
    prev = "root"
    for i, (role, text) in enumerate(messages):
        nid = f"msg-{i}"
        mapping[nid] = {
            "id": nid,
            "parent": prev,
            "message": {"author": {"role": role}, "content": {"parts": [text]}},
        }
        prev = nid
    return {"id": conv_id, "title": title, "create_time": 1700000000.0, "mapping": mapping}


def _claude_conv(conv_id="uuid-1", title="Test", messages=None):
    if messages is None:
        messages = [("human", "Hello"), ("assistant", "Hi")]
    return {
        "uuid": conv_id,
        "name": title,
        "created_at": "2024-01-15T10:00:00Z",
        "chat_messages": [{"sender": s, "text": t} for s, t in messages],
    }


# ── Format detection ──


def test_detect_chatgpt_format(svc):
    path = _write_json([_chatgpt_conv()])
    assert svc.detect_format(path) == "chatgpt"


def test_detect_claude_format(svc):
    path = _write_json([_claude_conv()])
    assert svc.detect_format(path) == "claude"


def test_detect_unknown_format(svc):
    path = _write_json([{"unknown": "format"}])
    with pytest.raises(ServiceError, match="Could not detect"):
        svc.detect_format(path)


def test_detect_empty_array(svc):
    path = _write_json([])
    with pytest.raises(ServiceError, match="non-empty JSON array"):
        svc.detect_format(path)


# ── Import (skip extract to avoid needing API key) ──


def test_import_chatgpt_skip_extract(svc):
    path = _write_json([_chatgpt_conv(), _chatgpt_conv(conv_id="conv-2")])
    result = svc.import_file(path, skip_extract=True)

    assert result.source == "chatgpt"
    assert result.total_conversations == 2
    assert result.new_conversations == 2
    assert result.skipped_conversations == 0
    assert result.extracted is False


def test_import_claude_skip_extract(svc):
    path = _write_json([_claude_conv()])
    result = svc.import_file(path, skip_extract=True)

    assert result.source == "claude"
    assert result.new_conversations == 1


def test_import_idempotent(svc):
    path = _write_json([_chatgpt_conv()])
    svc.import_file(path, skip_extract=True)
    result = svc.import_file(path, skip_extract=True)

    assert result.new_conversations == 0
    assert result.skipped_conversations == 1


# ── Role management ──


def test_add_role(svc):
    role = svc.add_role(title="Backend Engineer", company="Acme", started_at="2023-01")
    assert role.title == "Backend Engineer"
    assert role.company == "Acme"
    assert role.id  # UUID was generated

    roles = svc.get_roles()
    assert len(roles) == 1
    assert roles[0]["title"] == "Backend Engineer"


# ── Linking ──


def test_link_project_to_role(svc, db):
    role = svc.add_role(title="Engineer")
    project = Project(name="Dashboard", summary="Admin dashboard")
    db.upsert_project(project)

    result = svc.link_project_to_role(project.id, role.id)
    assert result.project_name == "Dashboard"
    assert result.role_title == "Engineer"

    roles = svc.get_roles()
    assert len(roles[0]["projects"]) == 1


def test_link_project_prefix_match(svc, db):
    role = svc.add_role(title="Engineer")
    project = Project(name="Dashboard", summary="Admin dashboard")
    db.upsert_project(project)

    # Use first 8 chars as prefix
    result = svc.link_project_to_role(project.id[:8], role.id[:8])
    assert result.project_name == "Dashboard"


def test_link_project_not_found(svc):
    role = svc.add_role(title="Engineer")
    with pytest.raises(NotFoundError, match="not found"):
        svc.link_project_to_role("nonexistent", role.id)


def test_link_role_not_found(svc, db):
    project = Project(name="Dashboard", summary="Admin dashboard")
    db.upsert_project(project)
    with pytest.raises(NotFoundError, match="not found"):
        svc.link_project_to_role(project.id, "nonexistent")


# ── Queries ──


def test_get_projects_empty(svc):
    assert svc.get_projects() == []


def test_get_skills_empty(svc):
    assert svc.get_skills() == []


def test_get_achievements_empty(svc):
    assert svc.get_achievements() == []


def test_export_all(svc, db):
    db.upsert_project(Project(name="P1", summary="Proj"))
    db.upsert_skill(Skill(name="Python", category="language"))

    data = svc.export_all()
    assert len(data["projects"]) == 1
    assert len(data["skills"]) == 1
    assert "achievements" in data
    assert "roles" in data
