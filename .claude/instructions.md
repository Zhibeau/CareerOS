# CareerOS — Project Instructions

## What This Is
A CLI tool that extracts structured career data (projects, skills, achievements, roles) from ChatGPT and Claude conversation exports, storing them in a local SQLite database.

## Design Docs
- [Data Schema](.claude/schema.md) — All tables and relationships
- [Architecture](.claude/architecture.md) — Components, data flow, tech stack
- [MVP Scope](.claude/mvp.md) — What's in and out of scope

## Conventions
- Python 3.11+, type hints everywhere
- Pydantic for data models
- Click for CLI
- pytest for tests
- SQLite via stdlib `sqlite3` (no ORM)
- All dates as ISO 8601 strings
- UUIDs as TEXT primary keys (generated via `uuid4()`)

## Running
```bash
pip install -e .
careeros import <path-to-export.json>
careeros show projects|skills|achievements|roles
careeros export --json
```

## Testing
```bash
pytest tests/
```

## Key Principles
- Keep it simple. This is a personal tool, not a SaaS product.
- No web UI in MVP. CLI only.
- Idempotent imports. Running the same import twice should be safe.
- Privacy-first. Raw conversation content is never stored in the DB.
