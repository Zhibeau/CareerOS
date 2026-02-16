"""Tests for ChatGPT and Claude importers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.importers.chatgpt import import_chatgpt
from src.importers.claude import import_claude


# ── ChatGPT importer tests ──


def _write_json(data: list, suffix: str = ".json") -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return Path(f.name)


def _make_chatgpt_conversation(
    conv_id: str = "conv-1",
    title: str = "Test Chat",
    messages: list[tuple[str, str]] | None = None,
) -> dict:
    """Build a minimal ChatGPT conversation export object."""
    if messages is None:
        messages = [("user", "Hello"), ("assistant", "Hi there!")]

    # Build mapping tree: root → msg1 → msg2 → ...
    mapping = {}
    root_id = "root"
    mapping[root_id] = {"id": root_id, "parent": None, "message": None}

    prev_id = root_id
    for i, (role, text) in enumerate(messages):
        node_id = f"msg-{i}"
        mapping[node_id] = {
            "id": node_id,
            "parent": prev_id,
            "message": {
                "author": {"role": role},
                "content": {"parts": [text]},
            },
        }
        prev_id = node_id

    return {
        "id": conv_id,
        "title": title,
        "create_time": 1700000000.0,
        "mapping": mapping,
    }


def test_chatgpt_basic_import():
    conv = _make_chatgpt_conversation(
        messages=[
            ("user", "How do I use React hooks?"),
            ("assistant", "React hooks let you use state in functional components."),
        ]
    )
    path = _write_json([conv])
    result = import_chatgpt(path)

    assert len(result) == 1
    assert result[0].id == "conv-1"
    assert result[0].source == "chatgpt"
    assert result[0].title == "Test Chat"
    assert len(result[0].messages) == 2
    assert result[0].messages[0].role == "user"
    assert "React hooks" in result[0].messages[0].text


def test_chatgpt_skips_empty_conversations():
    conv = {
        "id": "conv-empty",
        "title": "Empty",
        "create_time": 1700000000.0,
        "mapping": {
            "root": {"id": "root", "parent": None, "message": None},
        },
    }
    path = _write_json([conv])
    result = import_chatgpt(path)
    assert len(result) == 0


def test_chatgpt_skips_system_messages():
    mapping = {
        "root": {"id": "root", "parent": None, "message": None},
        "sys": {
            "id": "sys",
            "parent": "root",
            "message": {
                "author": {"role": "system"},
                "content": {"parts": ["You are a helpful assistant."]},
            },
        },
        "user1": {
            "id": "user1",
            "parent": "sys",
            "message": {
                "author": {"role": "user"},
                "content": {"parts": ["Hello"]},
            },
        },
    }
    conv = {
        "id": "conv-sys",
        "title": "System Test",
        "create_time": 1700000000.0,
        "mapping": mapping,
    }
    path = _write_json([conv])
    result = import_chatgpt(path)

    assert len(result) == 1
    # System message should be excluded
    assert len(result[0].messages) == 1
    assert result[0].messages[0].role == "user"


def test_chatgpt_multiple_conversations():
    convs = [
        _make_chatgpt_conversation(conv_id=f"conv-{i}", title=f"Chat {i}")
        for i in range(3)
    ]
    path = _write_json(convs)
    result = import_chatgpt(path)
    assert len(result) == 3


def test_chatgpt_invalid_format():
    path = _write_json({"not": "a list"})
    with pytest.raises(ValueError, match="Expected JSON array"):
        import_chatgpt(path)


# ── Claude importer tests ──


def _make_claude_conversation(
    conv_id: str = "uuid-1",
    title: str = "Test Chat",
    messages: list[tuple[str, str]] | None = None,
) -> dict:
    """Build a minimal Claude conversation export object."""
    if messages is None:
        messages = [("human", "Hello"), ("assistant", "Hi there!")]

    chat_messages = []
    for sender, text in messages:
        chat_messages.append({"sender": sender, "text": text})

    return {
        "uuid": conv_id,
        "name": title,
        "created_at": "2024-01-15T10:00:00Z",
        "chat_messages": chat_messages,
    }


def test_claude_basic_import():
    conv = _make_claude_conversation(
        messages=[
            ("human", "Help me optimize this SQL query"),
            ("assistant", "Here's an optimized version with an index."),
        ]
    )
    path = _write_json([conv])
    result = import_claude(path)

    assert len(result) == 1
    assert result[0].id == "uuid-1"
    assert result[0].source == "claude"
    assert result[0].title == "Test Chat"
    assert len(result[0].messages) == 2
    assert result[0].messages[0].role == "user"  # "human" → "user"


def test_claude_content_array_format():
    """Claude newer exports use content arrays instead of text field."""
    conv = {
        "uuid": "uuid-content",
        "name": "Content Array Test",
        "created_at": "2024-01-15T10:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [{"type": "text", "text": "Hello from content array"}],
            },
            {
                "sender": "assistant",
                "content": [{"type": "text", "text": "Hi back!"}],
            },
        ],
    }
    path = _write_json([conv])
    result = import_claude(path)

    assert len(result) == 1
    assert result[0].messages[0].text == "Hello from content array"


def test_claude_skips_empty_conversations():
    conv = {
        "uuid": "uuid-empty",
        "name": "Empty",
        "created_at": "2024-01-15T10:00:00Z",
        "chat_messages": [],
    }
    path = _write_json([conv])
    result = import_claude(path)
    assert len(result) == 0


def test_claude_multiple_conversations():
    convs = [
        _make_claude_conversation(conv_id=f"uuid-{i}", title=f"Chat {i}")
        for i in range(3)
    ]
    path = _write_json(convs)
    result = import_claude(path)
    assert len(result) == 3


def test_claude_invalid_format():
    path = _write_json({"not": "a list"})
    with pytest.raises(ValueError, match="Expected JSON array"):
        import_claude(path)
