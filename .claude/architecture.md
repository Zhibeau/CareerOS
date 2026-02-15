# Career Memory System — Architecture

## Core Insight

AI conversations are problem-solving sessions, not career narratives. Users say
"help me optimize this SQL query" — they don't say "I'm a Backend Engineer at
Stripe working on the payments team." This architecture is designed around that
reality:

- **Auto-extract** what's in the conversations: projects, skills, achievements
- **Manual-input** what's not: roles, companies, employment timeline
- **User links** extracted work to their career timeline

---

## Pipeline Overview

```
ChatGPT / Claude Export (JSON)
              │
              ▼
      ① Import & Parse
         Detect format, normalize to common model
              │
              ▼
      conversations table
              │
              ▼
      ② Extract & Classify (single LLM call)
         - Classify: is this work-relevant? (set is_work flag)
         - If yes, extract: projects, skills, achievements
         - If no, skip (is_work = 0, no entities)
              │
              ▼
      projects / skills / achievements tables
      + junction tables (provenance)
              │
              ▼
      ③ Dedup & Merge
         - Skills: exact match on normalized name
         - Projects: LLM similarity (merge related conversations)
         - Achievements: LLM dedup (semantic similarity)
              │
              ▼
      Same tables, deduplicated in-place
              │
              ▼
      ④ Manual Enrichment (CLI commands)
         - User adds roles (title, company, dates)
         - User links projects → roles
              │
              ▼
      roles table + project.role_id links
              │
              ▼
      ⑤ Resume Generator (post-MVP)
         - Input: job description + structured career data
         - Query relevant projects/skills/achievements per role
         - Generate tailored resume sections
```

---

## Components

### 1. Importers (`src/importers/`)
Normalize different export formats into a common internal representation.

- `chatgpt.py` — Parses ChatGPT `conversations.json` export format
- `claude.py` — Parses Claude JSON export format
- Each returns: `list[Conversation]` with unified schema (id, title, messages, timestamps)

**ChatGPT export format**: Single JSON array of conversation objects, each containing a `mapping` dict of message nodes.

**Claude export format**: JSON array of conversation objects with flat `chat_messages` arrays.

### 2. Extractor (`src/extractor.py`)
Takes normalized conversations and extracts structured career entities using an LLM. Classification and extraction happen in a **single LLM call** — no separate "work filter" step.

- Sends conversation text to Claude API with a structured extraction prompt
- Prompt instructs: "If this conversation is not work/technical, return `is_work: false` with no entities. Otherwise, extract projects, skills, and achievements."
- Returns structured JSON via `tool_use`
- Processes conversations in batches to manage token usage

**What's extractable from conversations (high confidence):**
- **Skills**: Users explicitly name technologies ("help me with React", "my PostgreSQL query")
- **Projects**: Inferred from context ("my e-commerce app", "the API I'm building", "our dashboard")
- **Achievements**: Inferred from problem resolution ("fixed the memory leak", "reduced latency by 80%")

**What's NOT extractable (requires manual input):**
- Job titles — users don't say "as a Senior Engineer..."
- Company names — users don't say "at Acme Corp..."
- Employment dates — no way to infer start/end dates
- Organizational context — team size, reporting structure, etc.

### 3. Database (`src/db.py`)
SQLite storage layer.

- `init_db()` — Creates tables from schema
- `upsert_*()` — Insert-or-update functions for each entity
- `query_*()` — Read functions for retrieval
- Deduplication: skills matched by normalized name, projects by name similarity

### 4. CLI (`src/cli.py`)
Command-line interface with two modes: automated extraction and manual enrichment.

**Automated (import & query):**
- `careeros import <file>` — Import, classify, extract, store
- `careeros show projects|skills|achievements` — Display extracted data
- `careeros export --json` — Dump DB as JSON

**Manual enrichment (roles & linking):**
- `careeros add role --title "Backend Engineer" --company "Acme" --start 2023-01 --end 2024-06`
- `careeros link project <project-id> --role <role-id>`
- `careeros show roles` — Display roles with linked projects

---

## Tech Stack

| Layer       | Choice     | Reason                                    |
|------------|------------|-------------------------------------------|
| Language   | Python 3.11+ | Fast prototyping, good LLM library support |
| Database   | SQLite     | Zero infrastructure, portable              |
| LLM        | Claude API | Structured extraction via tool_use         |
| CLI        | click      | Simple, well-documented                    |
| Models     | Pydantic   | Type-safe validation                       |
| Testing    | pytest     | Standard                                   |

---

## Data Flow

1. User runs `careeros import conversations.json`
2. Importer detects format (ChatGPT vs Claude), normalizes to `list[Conversation]`
3. Extractor batches conversations, sends to Claude API
4. For each conversation, Claude returns:
   - `is_work: false` → conversation stored with `is_work = 0`, no entities
   - `is_work: true` → entities extracted: `{projects: [], skills: [], achievements: []}`
5. DB layer upserts entities, deduplicates skills by name, links via junction tables
6. User manually adds roles: `careeros add role --title "..." --company "..."`
7. User links projects to roles: `careeros link project <id> --role <id>`
8. User queries with `careeros show skills` etc.

---

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

---

## Key Design Decisions

1. **LLM for extraction, not regex**: Conversations are unstructured natural language. Rule-based extraction would be brittle and incomplete. An LLM can understand context ("I built a React dashboard" → project: dashboard, skills: React).

2. **Single LLM call for classify + extract**: Combining work-relevance filtering and entity extraction into one API call halves cost and latency. Non-work conversations get `is_work = 0` with empty entities.

3. **No separate `work_conversations` table**: A boolean `is_work` column on `conversations` is simpler than duplicating rows into a second table.

4. **Roles are manual-input, not extracted**: Conversations almost never contain job titles or company names. Trying to extract them would produce hallucinated data. Better to have the user provide this explicitly and link projects to roles.

5. **Batch processing**: Send multiple conversations per LLM call to reduce costs. Each batch prompt includes 5-10 conversations.

6. **Idempotent imports**: Re-importing the same file skips already-imported conversations (tracked by conversation ID + source).

7. **No web UI for MVP**: CLI only. A web UI is a future concern.

8. **No real-time processing**: This is a batch tool. Import, extract, query. No streaming or webhooks.
