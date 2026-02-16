from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid4())


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ── Conversation (common model for all importers) ──


class Message(BaseModel):
    role: str  # "user" or "assistant"
    text: str


class Conversation(BaseModel):
    id: str
    source: str  # "chatgpt" or "claude"
    title: str
    messages: list[Message]
    started_at: str  # ISO 8601


# ── Extracted entities ──


class Project(BaseModel):
    id: str = Field(default_factory=_uuid)
    name: str
    summary: str
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    role_id: str | None = None


class Skill(BaseModel):
    id: str = Field(default_factory=_uuid)
    name: str
    category: str  # language, framework, tool, platform, concept, soft_skill


class Achievement(BaseModel):
    id: str = Field(default_factory=_uuid)
    summary: str
    impact: str | None = None
    achieved_at: str | None = None


# ── Manual-input entities ──


class Role(BaseModel):
    id: str = Field(default_factory=_uuid)
    title: str
    company: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


# ── Extraction result (returned by LLM) ──


class ExtractionResult(BaseModel):
    is_work: bool
    projects: list[Project] = []
    skills: list[Skill] = []
    achievements: list[Achievement] = []
    # skill names linked to each project (by project name)
    project_skills: dict[str, list[str]] = {}
    # achievement summaries linked to each project (by project name)
    project_achievements: dict[str, list[str]] = {}
