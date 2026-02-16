"""Claude export parser.

Claude exports are a JSON array of conversation objects with flat
`chat_messages` arrays. Each message has a `sender` field ("human" or
"assistant") and a `text` field (or `content` array).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import Conversation, Message


def _parse_timestamp(ts: str | None) -> str:
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    # Claude timestamps are ISO 8601 already
    return ts


def _extract_text(msg: dict) -> str:
    """Extract text content from a Claude message object."""
    # Try `text` field first (older exports)
    if "text" in msg and isinstance(msg["text"], str):
        return msg["text"].strip()

    # Try `content` array (newer exports)
    content = msg.get("content", [])
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts).strip()

    if isinstance(content, str):
        return content.strip()

    return ""


def import_claude(path: str | Path) -> list[Conversation]:
    """Parse a Claude JSON export file."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    conversations: list[Conversation] = []
    for conv in data:
        conv_id = conv.get("uuid", conv.get("id", ""))
        title = conv.get("name", conv.get("title", "Untitled"))
        created_at = conv.get("created_at", conv.get("create_time"))

        chat_messages = conv.get("chat_messages", [])

        messages: list[Message] = []
        for msg in chat_messages:
            sender = msg.get("sender", "")
            role_map = {"human": "user", "user": "user", "assistant": "assistant"}
            role = role_map.get(sender, "")
            if not role:
                continue

            text = _extract_text(msg)
            if text:
                messages.append(Message(role=role, text=text))

        if not messages:
            continue

        conversations.append(
            Conversation(
                id=conv_id,
                source="claude",
                title=title,
                messages=messages,
                started_at=_parse_timestamp(created_at),
            )
        )

    return conversations
