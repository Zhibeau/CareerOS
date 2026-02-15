# Career Memory System — Data Schema

## Design Principle: Extractable vs. Manual

Real AI conversations are problem-solving oriented. A user asks "help me fix this
CORS error in my Express API" — not "as a Senior Engineer at Acme Corp, I need..."

This schema separates entities into two categories:

- **Auto-extracted** (from conversations): projects, skills, achievements
- **Manual-input** (user provides): roles, companies, date ranges

The system extracts what it can, then the user links extracted work to their
career timeline manually.

---

## Auto-Extracted Entities

These are reliably extractable from AI conversations because users explicitly
discuss them while problem-solving.

### conversations
Source conversation records (raw import tracking).

| Column         | Type     | Description                          |
|---------------|----------|--------------------------------------|
| id            | TEXT PK  | UUID                                 |
| source        | TEXT     | "chatgpt" or "claude"                |
| title         | TEXT     | Original conversation title          |
| started_at    | TEXT     | ISO 8601 timestamp                   |
| raw_path      | TEXT     | Path to source export file           |
| imported_at   | TEXT     | When this record was created         |
| is_work       | INTEGER  | 1 = work-relevant, 0 = not, NULL = unclassified |

### projects
Distinct projects or work efforts extracted from conversations.

A "project" is any coherent body of work: building a feature, debugging a system,
designing an architecture, setting up infrastructure. Extracted from contextual
clues like "my app", "our API", "the dashboard I'm building".

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| name       | TEXT     | Inferred project name                |
| summary    | TEXT     | What was being built/solved          |
| status     | TEXT     | "active", "completed", "abandoned"   |
| started_at | TEXT     | Earliest mention date                |
| ended_at   | TEXT     | Latest mention date (nullable)       |
| role_id    | TEXT FK  | Linked role (nullable, user-assigned)|

### skills
Technologies and techniques demonstrated across conversations.

These are the most reliably extractable entity — users explicitly name
the technologies they're using ("React", "PostgreSQL", "Docker").

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| name       | TEXT     | Skill name (normalized, lowercase)   |
| category   | TEXT     | "language", "framework", "tool", "platform", "concept", "soft_skill" |

### achievements
Concrete accomplishments inferred from problem-solving conversations.

Extracted when a user solves a meaningful problem: "reduced query time from 5s
to 200ms", "migrated 10k users to the new auth system", "shipped the v2 API".

| Column          | Type     | Description                      |
|----------------|----------|----------------------------------|
| id             | TEXT PK  | UUID                             |
| summary        | TEXT     | What was achieved                |
| impact         | TEXT     | Quantified impact if available   |
| achieved_at    | TEXT     | Approximate date                 |

---

## Manual-Input Entities

These are NOT reliably extractable from conversations. Users rarely mention
their job title, company, or employment dates while asking for coding help.

### roles
Professional roles/positions. **User-provided, not extracted.**

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| title      | TEXT     | Role title                           |
| company    | TEXT     | Company/org name (nullable)          |
| started_at | TEXT     | Start date (nullable)                |
| ended_at   | TEXT     | End date (nullable)                  |

---

## Junction Tables

### conversation_projects
Links conversations to the projects they relate to (provenance tracking).

| Column          | Type    |
|----------------|---------|
| conversation_id | TEXT FK |
| project_id      | TEXT FK |

### project_skills
| Column     | Type    |
|-----------|---------|
| project_id | TEXT FK |
| skill_id   | TEXT FK |

### project_achievements
| Column         | Type    |
|---------------|---------|
| project_id     | TEXT FK |
| achievement_id | TEXT FK |

---

## Design Rationale

- **SQLite**: Zero-infrastructure, portable, single-file database. Perfect for a personal tool.
- **UUIDs over autoincrement**: Stable references across imports, merge-friendly.
- **TEXT dates**: ISO 8601 strings. SQLite has no native date type; text sorts correctly.
- **Junction tables**: Many-to-many relationships between extracted entities. A skill can appear in multiple projects; a project can have multiple achievements.
- **No conversation content stored**: We store extracted entities only. Raw exports stay as files on disk. This keeps the DB small and privacy-friendly.
- **`is_work` on conversations**: Avoids a separate `work_conversations` table. The LLM classifies during extraction — non-work conversations simply get `is_work = 0` and no entities extracted.
- **`role_id` on projects**: Simple FK instead of a junction table. A project typically belongs to one role/job. Users manually link projects to roles after extraction.
- **No `role_projects` junction table**: Replaced by `projects.role_id` FK. Simpler for the common case (1 project → 1 role). If needed later, can migrate to a junction table.
