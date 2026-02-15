# Career Memory System — Architecture

## Overview

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Conversation    │     │   Parser /  │     │    SQLite        │
│  Exports         │────>│   Extractor │────>│    Career DB     │
│  (JSON files)    │     │             │     │                  │
└─────────────────┘     └─────────────┘     └─────────────────┘
     Input                  Processing            Output
```

## Components

### 1. Importers (`src/importers/`)
Normalize different export formats into a common internal representation.

- `chatgpt.py` — Parses ChatGPT `conversations.json` export format
- `claude.py` — Parses Claude JSON export format
- Each returns: `list[Conversation]` with unified schema (id, title, messages, timestamps)

**ChatGPT export format**: Single JSON array of conversation objects, each containing a `mapping` dict of message nodes.

**Claude export format**: JSON array of conversation objects with flat `chat_messages` arrays.

### 2. Extractor (`src/extractor.py`)
Takes normalized conversations and extracts structured career entities using an LLM.

- Sends conversation text to an LLM (Claude API) with a structured extraction prompt
- Prompt asks for: projects, skills, achievements, roles
- Returns structured JSON matching our schema
- Processes conversations in batches to manage token usage
- Uses a single extraction prompt (not per-entity) to minimize API calls

### 3. Database (`src/db.py`)
SQLite storage layer.

- `init_db()` — Creates tables from schema
- `upsert_*()` — Insert-or-update functions for each entity
- `query_*()` — Read functions for retrieval
- Deduplication: skills matched by normalized name, projects by name similarity

### 4. CLI (`src/cli.py`)
Minimal command-line interface.

- `careeros import <file>` — Import a conversation export
- `careeros show projects|skills|achievements|roles` — Display extracted data
- `careeros export` — Dump DB as JSON

## Tech Stack

| Layer       | Choice     | Reason                                    |
|------------|------------|-------------------------------------------|
| Language   | Python 3.11+ | Fast prototyping, good LLM library support |
| Database   | SQLite     | Zero infrastructure, portable              |
| LLM        | Claude API | Structured extraction via tool_use         |
| CLI        | click      | Simple, well-documented                    |
| Testing    | pytest     | Standard                                   |

## Data Flow

1. User runs `careeros import conversations.json`
2. Importer detects format (ChatGPT vs Claude), normalizes to `list[Conversation]`
3. Extractor batches conversations, sends to Claude API with extraction prompt
4. Claude returns structured JSON per batch: `{projects: [], skills: [], achievements: [], roles: []}`
5. DB layer upserts entities, deduplicates skills by name, links via junction tables
6. User queries with `careeros show skills` etc.

## File Structure

```
CareerOS/
├── .claude/              # Design docs (this file)
├── src/
│   ├── __init__.py
│   ├── cli.py            # Click CLI entry point
│   ├── db.py             # SQLite schema + queries
│   ├── extractor.py      # LLM-based entity extraction
│   ├── models.py         # Pydantic models for all entities
│   └── importers/
│       ├── __init__.py
│       ├── base.py        # Common Conversation model
│       ├── chatgpt.py     # ChatGPT export parser
│       └── claude.py      # Claude export parser
├── tests/
│   ├── test_importers.py
│   ├── test_extractor.py
│   └── test_db.py
├── pyproject.toml
└── README.md
```

## Key Design Decisions

1. **LLM for extraction, not regex**: Conversations are unstructured natural language. Rule-based extraction would be brittle and incomplete. An LLM can understand context ("I built a React dashboard" → project: dashboard, skills: React).

2. **Batch processing**: Send multiple conversations per LLM call to reduce costs. Each batch prompt includes 5-10 conversations.

3. **Idempotent imports**: Re-importing the same file skips already-imported conversations (tracked by conversation ID + source).

4. **No web UI for MVP**: CLI only. A web UI is a future concern.

5. **No real-time processing**: This is a batch tool. Import, extract, query. No streaming or webhooks.
