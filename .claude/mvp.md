# Career Memory System — MVP Scope

## What MVP Includes

### M1: Import & Parse
- [ ] ChatGPT JSON export importer
- [ ] Claude JSON export importer
- [ ] Normalize both to common `Conversation` model
- [ ] Track imported conversations in DB to prevent duplicates

### M2: Extract & Classify
- [ ] Single LLM call that classifies work-relevance AND extracts entities
- [ ] Claude API integration using `tool_use` for structured output
- [ ] Batch conversations (5-10 per API call)
- [ ] Extract 3 entity types: projects, skills, achievements
- [ ] Set `is_work` flag on conversations (skip non-work conversations)
- [ ] **Do NOT attempt to extract**: roles, job titles, companies, employment dates (these are almost never present in AI conversations)

### M3: Store
- [ ] SQLite database with full schema
- [ ] Auto-extracted tables: conversations, projects, skills, achievements
- [ ] Manual-input tables: roles
- [ ] Junction tables: conversation_projects, project_skills, project_achievements
- [ ] Upsert logic for all entities
- [ ] Skill deduplication by normalized name

### M4: Query & Manual Enrichment
- [ ] `careeros import <file>` — import + classify + extract + store
- [ ] `careeros show projects` — list all projects
- [ ] `careeros show skills` — list all skills with categories
- [ ] `careeros show achievements` — list achievements
- [ ] `careeros show roles` — list roles with linked projects
- [ ] `careeros export --json` — full DB dump as JSON
- [ ] `careeros add role --title "..." --company "..." --start YYYY-MM --end YYYY-MM` — manually add a role
- [ ] `careeros link project <project-id> --role <role-id>` — link a project to a role

## What MVP Excludes

- Web UI
- Semantic search / embeddings
- Automatic conversation export fetching (user provides files)
- Resume generation (post-MVP milestone)
- Multi-user support
- Conversation content storage (only extracted entities stored)
- Confidence scores on extractions
- Manual editing / correction of extracted entities
- Sync with LinkedIn or other platforms
- Analytics / visualization dashboards
- LLM-based project dedup/merge (use simple name matching for MVP)

## Success Criteria

MVP is done when:
1. You can drop a ChatGPT or Claude export file and run one command
2. The system classifies conversations as work-relevant or not
3. The system extracts projects, skills, and achievements from work conversations
4. You can manually add roles and link projects to them
5. You can query each entity type from the CLI
6. Re-importing the same file doesn't create duplicates

## Implementation Order

```
M1 (Import) → M3 (Store) → M2 (Extract) → M4 (Query & Enrich)
```

Build the data layer first (import + store), then add LLM extraction, then the
CLI query and manual enrichment commands. This lets you test import/storage with
fixtures before involving the LLM.

## Post-MVP: Resume Generation

Once the career data is structured (extracted projects/skills + manual roles),
resume generation becomes straightforward:

1. User provides a job description
2. System queries relevant projects, skills, achievements per role
3. LLM generates tailored resume sections
4. Output as Markdown, JSON, or PDF

This requires all prior milestones to be solid — especially the manual role
linking, since resumes are organized by role/position.
