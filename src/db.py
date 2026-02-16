"""SQLite storage layer.

All tables follow the schema defined in .claude/schema.md.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models import Achievement, Conversation, ExtractionResult, Project, Role, Skill

DEFAULT_DB_PATH = Path.home() / ".careeros" / "career.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    title       TEXT NOT NULL,
    started_at  TEXT,
    raw_path    TEXT,
    imported_at TEXT NOT NULL,
    is_work     INTEGER
);

CREATE TABLE IF NOT EXISTS projects (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    summary    TEXT,
    status     TEXT DEFAULT 'active',
    started_at TEXT,
    ended_at   TEXT,
    role_id    TEXT REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS skills (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    category TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_skills_name ON skills(name);

CREATE TABLE IF NOT EXISTS achievements (
    id          TEXT PRIMARY KEY,
    summary     TEXT NOT NULL,
    impact      TEXT,
    achieved_at TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    company    TEXT,
    started_at TEXT,
    ended_at   TEXT
);

CREATE TABLE IF NOT EXISTS conversation_projects (
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    project_id      TEXT NOT NULL REFERENCES projects(id),
    PRIMARY KEY (conversation_id, project_id)
);

CREATE TABLE IF NOT EXISTS project_skills (
    project_id TEXT NOT NULL REFERENCES projects(id),
    skill_id   TEXT NOT NULL REFERENCES skills(id),
    PRIMARY KEY (project_id, skill_id)
);

CREATE TABLE IF NOT EXISTS project_achievements (
    project_id     TEXT NOT NULL REFERENCES projects(id),
    achievement_id TEXT NOT NULL REFERENCES achievements(id),
    PRIMARY KEY (project_id, achievement_id)
);
"""


class CareerDB:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ── Conversations ──

    def conversation_exists(self, conv_id: str, source: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND source = ?",
            (conv_id, source),
        ).fetchone()
        return row is not None

    def insert_conversation(
        self,
        conv: Conversation,
        raw_path: str,
        is_work: bool | None = None,
    ) -> None:
        is_work_val = None if is_work is None else (1 if is_work else 0)
        self.conn.execute(
            """INSERT OR IGNORE INTO conversations
               (id, source, title, started_at, raw_path, imported_at, is_work)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                conv.id,
                conv.source,
                conv.title,
                conv.started_at,
                raw_path,
                datetime.now(timezone.utc).isoformat(),
                is_work_val,
            ),
        )
        self.conn.commit()

    def update_conversation_is_work(self, conv_id: str, is_work: bool) -> None:
        self.conn.execute(
            "UPDATE conversations SET is_work = ? WHERE id = ?",
            (1 if is_work else 0, conv_id),
        )
        self.conn.commit()

    # ── Skills (dedup by normalized name) ──

    def upsert_skill(self, skill: Skill) -> str:
        """Insert skill or return existing ID if name matches."""
        normalized = skill.name.strip().lower()
        row = self.conn.execute(
            "SELECT id FROM skills WHERE name = ?", (normalized,)
        ).fetchone()
        if row:
            return row["id"]
        self.conn.execute(
            "INSERT INTO skills (id, name, category) VALUES (?, ?, ?)",
            (skill.id, normalized, skill.category),
        )
        self.conn.commit()
        return skill.id

    # ── Projects ──

    def upsert_project(self, project: Project) -> str:
        """Insert project. Simple name-based dedup for MVP."""
        normalized = project.name.strip().lower()
        row = self.conn.execute(
            "SELECT id FROM projects WHERE LOWER(name) = ?", (normalized,)
        ).fetchone()
        if row:
            return row["id"]
        self.conn.execute(
            """INSERT INTO projects (id, name, summary, status, started_at, ended_at, role_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                project.id,
                project.name,
                project.summary,
                project.status,
                project.started_at,
                project.ended_at,
                project.role_id,
            ),
        )
        self.conn.commit()
        return project.id

    # ── Achievements ──

    def insert_achievement(self, achievement: Achievement) -> str:
        self.conn.execute(
            """INSERT INTO achievements (id, summary, impact, achieved_at)
               VALUES (?, ?, ?, ?)""",
            (
                achievement.id,
                achievement.summary,
                achievement.impact,
                achievement.achieved_at,
            ),
        )
        self.conn.commit()
        return achievement.id

    # ── Roles (manual input) ──

    def insert_role(self, role: Role) -> str:
        self.conn.execute(
            """INSERT INTO roles (id, title, company, started_at, ended_at)
               VALUES (?, ?, ?, ?, ?)""",
            (role.id, role.title, role.company, role.started_at, role.ended_at),
        )
        self.conn.commit()
        return role.id

    def link_project_to_role(self, project_id: str, role_id: str) -> None:
        self.conn.execute(
            "UPDATE projects SET role_id = ? WHERE id = ?",
            (role_id, project_id),
        )
        self.conn.commit()

    # ── Junction tables ──

    def link_conversation_project(self, conv_id: str, project_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO conversation_projects VALUES (?, ?)",
            (conv_id, project_id),
        )
        self.conn.commit()

    def link_project_skill(self, project_id: str, skill_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO project_skills VALUES (?, ?)",
            (project_id, skill_id),
        )
        self.conn.commit()

    def link_project_achievement(self, project_id: str, achievement_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO project_achievements VALUES (?, ?)",
            (project_id, achievement_id),
        )
        self.conn.commit()

    # ── Store full extraction result ──

    def store_extraction(
        self, conv_id: str, result: ExtractionResult
    ) -> None:
        """Store all entities from an extraction result and wire up junctions."""
        self.update_conversation_is_work(conv_id, result.is_work)

        if not result.is_work:
            return

        # Build lookup maps for linking
        project_id_by_name: dict[str, str] = {}
        skill_id_by_name: dict[str, str] = {}
        achievement_id_by_summary: dict[str, str] = {}

        for project in result.projects:
            pid = self.upsert_project(project)
            project_id_by_name[project.name] = pid
            self.link_conversation_project(conv_id, pid)

        for skill in result.skills:
            sid = self.upsert_skill(skill)
            skill_id_by_name[skill.name.strip().lower()] = sid

        for achievement in result.achievements:
            aid = self.insert_achievement(achievement)
            achievement_id_by_summary[achievement.summary] = aid

        # Wire project→skill links
        for proj_name, skill_names in result.project_skills.items():
            pid = project_id_by_name.get(proj_name)
            if not pid:
                continue
            for sname in skill_names:
                sid = skill_id_by_name.get(sname.strip().lower())
                if sid:
                    self.link_project_skill(pid, sid)

        # Wire project→achievement links
        for proj_name, ach_summaries in result.project_achievements.items():
            pid = project_id_by_name.get(proj_name)
            if not pid:
                continue
            for asummary in ach_summaries:
                aid = achievement_id_by_summary.get(asummary)
                if aid:
                    self.link_project_achievement(pid, aid)

    # ── Query functions ──

    def get_projects(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT p.id, p.name, p.summary, p.status, p.started_at, p.ended_at,
                      r.title AS role_title, r.company AS role_company
               FROM projects p
               LEFT JOIN roles r ON p.role_id = r.id
               ORDER BY p.started_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def get_skills(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, name, category FROM skills ORDER BY category, name"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_achievements(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, summary, impact, achieved_at FROM achievements ORDER BY achieved_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_roles(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, company, started_at, ended_at FROM roles ORDER BY started_at DESC"
        ).fetchall()
        results = []
        for r in rows:
            role = dict(r)
            # Attach linked projects
            projects = self.conn.execute(
                "SELECT id, name, summary FROM projects WHERE role_id = ?",
                (role["id"],),
            ).fetchall()
            role["projects"] = [dict(p) for p in projects]
            results.append(role)
        return results

    def get_project_by_id(self, project_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_role_by_id(self, role_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM roles WHERE id = ?", (role_id,)
        ).fetchone()
        return dict(row) if row else None

    def find_by_id_prefix(self, table: str, prefix: str) -> list[dict]:
        """Find rows in a table whose ID starts with the given prefix."""
        allowed_tables = {"projects", "skills", "achievements", "roles", "conversations"}
        if table not in allowed_tables:
            raise ValueError(f"Invalid table: {table}")
        rows = self.conn.execute(
            f"SELECT * FROM {table} WHERE id LIKE ?",
            (f"{prefix}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    def export_all(self) -> dict:
        return {
            "projects": self.get_projects(),
            "skills": self.get_skills(),
            "achievements": self.get_achievements(),
            "roles": self.get_roles(),
        }
