# Career Memory System — MVP Scope

## What MVP Includes

### M1: Import & Parse
- [ ] ChatGPT JSON export importer
- [ ] Claude JSON export importer
- [ ] Normalize both to common `Conversation` model
- [ ] Track imported conversations in DB to prevent duplicates

### M2: Extract
- [ ] Single extraction prompt that pulls all 4 entity types at once
- [ ] Claude API integration using `tool_use` for structured output
- [ ] Batch conversations (5-10 per API call)
- [ ] Map extracted data to DB schema

### M3: Store
- [ ] SQLite database with full schema (6 entity tables + 4 junction tables)
- [ ] Upsert logic for all entities
- [ ] Skill deduplication by normalized name

### M4: Query
- [ ] `careeros import <file>` — import + extract + store
- [ ] `careeros show projects` — list all projects
- [ ] `careeros show skills` — list all skills with categories
- [ ] `careeros show achievements` — list achievements
- [ ] `careeros show roles` — list roles
- [ ] `careeros export --json` — full DB dump as JSON

## What MVP Excludes

- Web UI
- Semantic search / embeddings
- Automatic conversation export fetching (user provides files)
- Resume generation
- Multi-user support
- Conversation content storage (only extracted entities stored)
- Confidence scores on extractions
- Manual editing / correction UI
- Sync with LinkedIn or other platforms
- Analytics / visualization dashboards

## Success Criteria

MVP is done when:
1. You can drop a ChatGPT or Claude export file and run one command
2. The system extracts projects, skills, achievements, and roles
3. You can query each entity type from the CLI
4. Re-importing the same file doesn't create duplicates

## Implementation Order

```
M1 (Import) → M3 (Store) → M2 (Extract) → M4 (Query)
```

Build the data layer first (import + store), then add LLM extraction, then the CLI query commands. This lets you test import/storage with fixtures before involving the LLM.
