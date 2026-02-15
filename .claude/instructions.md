# CareerOS — Project Instructions

## What This Is
A CLI tool that extracts structured career data (projects, skills, achievements) from ChatGPT and Claude conversation exports, storing them in a local SQLite database. Users manually add roles and link extracted work to their career timeline.

## Core Insight
AI conversations contain rich technical work evidence (what you built, what tech you used, what problems you solved) but almost never contain career metadata (job titles, companies, dates). The system auto-extracts what it can, and the user provides the rest.

## Design Docs
- [Data Schema](.claude/schema.md) — All tables and relationships (auto-extracted vs manual)
- [Architecture](.claude/architecture.md) — Components, pipeline, tech stack
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
careeros show projects|skills|achievements
careeros add role --title "..." --company "..." --start YYYY-MM --end YYYY-MM
careeros link project <project-id> --role <role-id>
careeros show roles
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
- Extract what's extractable (projects, skills, achievements). Don't hallucinate what's not (roles, companies).
- Manual enrichment is a feature, not a limitation. Users know their career better than an LLM can guess.
