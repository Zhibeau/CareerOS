# Career Memory System — Data Schema

## Core Entities

### conversations
Source conversation records (raw import tracking).

| Column       | Type     | Description                          |
|-------------|----------|--------------------------------------|
| id          | TEXT PK  | UUID                                 |
| source      | TEXT     | "chatgpt" or "claude"                |
| title       | TEXT     | Original conversation title          |
| started_at  | TEXT     | ISO 8601 timestamp                   |
| raw_path    | TEXT     | Path to source export file           |
| imported_at | TEXT     | When this record was created         |

### projects
Distinct projects extracted from conversations.

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| name       | TEXT     | Project name                         |
| summary    | TEXT     | One-line description                 |
| status     | TEXT     | "active", "completed", "abandoned"   |
| started_at | TEXT     | Earliest mention date                |
| ended_at   | TEXT     | Latest mention date (nullable)       |

### skills
Skills demonstrated or discussed across conversations.

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| name       | TEXT     | Skill name (normalized, lowercase)   |
| category   | TEXT     | "language", "framework", "tool", "concept", "soft_skill" |

### achievements
Concrete accomplishments extracted from conversations.

| Column          | Type     | Description                      |
|----------------|----------|----------------------------------|
| id             | TEXT PK  | UUID                             |
| summary        | TEXT     | What was achieved                |
| impact         | TEXT     | Quantified impact if available   |
| achieved_at    | TEXT     | Approximate date                 |

### roles
Professional roles/positions mentioned or implied.

| Column      | Type     | Description                          |
|------------|----------|--------------------------------------|
| id         | TEXT PK  | UUID                                 |
| title      | TEXT     | Role title                           |
| company    | TEXT     | Company/org name (nullable)          |
| started_at | TEXT     | Start date (nullable)                |
| ended_at   | TEXT     | End date (nullable)                  |

## Junction Tables

### conversation_projects
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

### role_projects
| Column     | Type    |
|-----------|---------|
| role_id    | TEXT FK |
| project_id | TEXT FK |

## Design Rationale

- **SQLite**: Zero-infrastructure, portable, single-file database. Perfect for a personal tool.
- **UUIDs over autoincrement**: Stable references across imports, merge-friendly.
- **TEXT dates**: ISO 8601 strings. SQLite has no native date type; text sorts correctly.
- **Junction tables**: Many-to-many relationships between all core entities. A skill can appear in multiple projects; a project can have multiple achievements.
- **No conversation content stored**: We store extracted entities only. Raw exports stay as files on disk. This keeps the DB small and privacy-friendly.
