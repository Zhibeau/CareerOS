"""ChatGPT export parser.

ChatGPT exports are a JSON array of conversation objects. Each conversation has
a `mapping` dict of message nodes. The tree structure uses parent/children
pointers; we walk from the root to collect messages in order.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import Conversation, Message


def _timestamp_to_iso(ts: float | None) -> str:
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _walk_mapping(mapping: dict) -> list[Message]:
    """Walk the ChatGPT mapping tree and return messages in order."""
    # Build parent→children index
    children_map: dict[str | None, list[str]] = {}
    for node_id, node in mapping.items():
        parent = node.get("parent")
        children_map.setdefault(parent, []).append(node_id)

    # Find root nodes (parent is None)
    roots = children_map.get(None, [])

    # DFS to collect messages in conversation order
    messages: list[Message] = []
    stack = list(reversed(roots))
    while stack:
        node_id = stack.pop()
        node = mapping.get(node_id, {})
        msg_data = node.get("message")
        if msg_data:
            role = msg_data.get("author", {}).get("role", "")
            if role in ("user", "assistant"):
                parts = msg_data.get("content", {}).get("parts", [])
                text = "".join(str(p) for p in parts if isinstance(p, str))
                if text.strip():
                    messages.append(Message(role=role, text=text.strip()))
        # Add children in order
        node_children = children_map.get(node_id, [])
        stack.extend(reversed(node_children))

    return messages


def import_chatgpt(path: str | Path) -> list[Conversation]:
    """Parse a ChatGPT conversations.json export file."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    conversations: list[Conversation] = []
    for conv in data:
        conv_id = conv.get("id", "")
        title = conv.get("title", "Untitled")
        create_time = conv.get("create_time")
        mapping = conv.get("mapping", {})

        messages = _walk_mapping(mapping)
        if not messages:
            continue

        conversations.append(
            Conversation(
                id=conv_id,
                source="chatgpt",
                title=title,
                messages=messages,
                started_at=_timestamp_to_iso(create_time),
            )
        )

    return conversations
