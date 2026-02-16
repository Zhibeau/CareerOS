"""Service layer — framework-agnostic business logic.

Both CLI and future web API call this layer. No Click, no Flask, no FastAPI
dependencies here — just pure business logic operating on models and the DB.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.db import CareerDB
from src.extractor import extract_from_conversations
from src.importers.chatgpt import import_chatgpt
from src.importers.claude import import_claude
from src.models import Conversation, Role


# ── Result types ──


@dataclass
class ImportResult:
    source: str
    total_conversations: int
    new_conversations: int
    skipped_conversations: int
    extracted: bool
    work_conversations: int
    projects_extracted: int
    skills_extracted: int
    achievements_extracted: int


@dataclass
class LinkResult:
    project_id: str
    project_name: str
    role_id: str
    role_title: str


class ServiceError(Exception):
    """Raised when a service operation fails."""


class NotFoundError(ServiceError):
    """Entity not found."""


class AmbiguousIDError(ServiceError):
    """Short ID matches multiple entities."""

    def __init__(self, message: str, matches: list[dict]):
        super().__init__(message)
        self.matches = matches


# ── Service ──


class CareerService:
    def __init__(self, db: CareerDB):
        self.db = db

    # ── Import & Extract ──

    def detect_format(self, path: Path) -> str:
        """Detect whether a file is a ChatGPT or Claude export.

        Returns "chatgpt" or "claude".
        Raises ServiceError if format is unrecognized.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            raise ServiceError(f"Expected non-empty JSON array in {path}")

        first = data[0]

        if "mapping" in first:
            return "chatgpt"
        if "chat_messages" in first or "uuid" in first:
            return "claude"

        raise ServiceError(
            "Could not detect export format. Expected ChatGPT or Claude export."
        )

    def parse_file(self, path: Path, source: str) -> list[Conversation]:
        """Parse conversations from an export file of known format."""
        if source == "chatgpt":
            return import_chatgpt(path)
        elif source == "claude":
            return import_claude(path)
        else:
            raise ServiceError(f"Unknown source format: {source}")

    def import_file(
        self, path: str | Path, skip_extract: bool = False
    ) -> ImportResult:
        """Full import pipeline: detect → parse → dedup → store → extract.

        This is the main entry point for importing conversation exports.
        """
        path = Path(path)
        source = self.detect_format(path)
        conversations = self.parse_file(path, source)

        # Filter already-imported
        new_convs = []
        skipped = 0
        for conv in conversations:
            if self.db.conversation_exists(conv.id, conv.source):
                skipped += 1
            else:
                new_convs.append(conv)

        # Store conversations
        for conv in new_convs:
            self.db.insert_conversation(conv, raw_path=str(path.resolve()))

        result = ImportResult(
            source=source,
            total_conversations=len(conversations),
            new_conversations=len(new_convs),
            skipped_conversations=skipped,
            extracted=False,
            work_conversations=0,
            projects_extracted=0,
            skills_extracted=0,
            achievements_extracted=0,
        )

        if skip_extract or not new_convs:
            return result

        # Extract career data
        extractions = extract_from_conversations(new_convs)

        for conv_id, extraction in extractions:
            self.db.store_extraction(conv_id, extraction)
            if extraction.is_work:
                result.work_conversations += 1
                result.projects_extracted += len(extraction.projects)
                result.skills_extracted += len(extraction.skills)
                result.achievements_extracted += len(extraction.achievements)

        result.extracted = True
        return result

    # ── Roles (manual input) ──

    def add_role(
        self,
        title: str,
        company: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> Role:
        """Create a new role and store it."""
        role = Role(
            title=title, company=company, started_at=started_at, ended_at=ended_at
        )
        self.db.insert_role(role)
        return role

    # ── Linking ──

    def link_project_to_role(self, project_id: str, role_id: str) -> LinkResult:
        """Link a project to a role. Supports short ID prefixes.

        Raises NotFoundError or AmbiguousIDError for bad IDs.
        """
        project_id, project = self._resolve_project(project_id)
        role_id, role = self._resolve_role(role_id)

        self.db.link_project_to_role(project_id, role_id)

        return LinkResult(
            project_id=project_id,
            project_name=project["name"],
            role_id=role_id,
            role_title=role["title"],
        )

    def _resolve_project(self, project_id: str) -> tuple[str, dict]:
        """Resolve a full or prefix project ID to (full_id, project_dict)."""
        project = self.db.get_project_by_id(project_id)
        if project:
            return project_id, project

        matches = self.db.find_by_id_prefix("projects", project_id)
        if len(matches) == 1:
            return matches[0]["id"], matches[0]
        elif len(matches) > 1:
            raise AmbiguousIDError(
                f"Ambiguous project ID '{project_id}'",
                matches=[{"id": m["id"], "name": m["name"]} for m in matches],
            )
        else:
            raise NotFoundError(f"Project '{project_id}' not found")

    def _resolve_role(self, role_id: str) -> tuple[str, dict]:
        """Resolve a full or prefix role ID to (full_id, role_dict)."""
        role = self.db.get_role_by_id(role_id)
        if role:
            return role_id, role

        matches = self.db.find_by_id_prefix("roles", role_id)
        if len(matches) == 1:
            return matches[0]["id"], matches[0]
        elif len(matches) > 1:
            raise AmbiguousIDError(
                f"Ambiguous role ID '{role_id}'",
                matches=[{"id": m["id"], "title": m["title"]} for m in matches],
            )
        else:
            raise NotFoundError(f"Role '{role_id}' not found")

    # ── Queries (thin pass-through to DB) ──

    def get_projects(self) -> list[dict]:
        return self.db.get_projects()

    def get_skills(self) -> list[dict]:
        return self.db.get_skills()

    def get_achievements(self) -> list[dict]:
        return self.db.get_achievements()

    def get_roles(self) -> list[dict]:
        return self.db.get_roles()

    def export_all(self) -> dict:
        return self.db.export_all()
