# CareerOS Flutter App — Implementation Plan

## Choices Made

| Decision           | Choice                      |
| ------------------ | --------------------------- |
| LLM Access         | Backend proxy with auth     |
| Platforms          | iOS + Android               |
| CV Output          | PDF + Word (.docx)          |
| UI Style           | Material Design 3           |

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Flutter App (Mobile)                │
│                                                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │  Import   │  │  Database  │  │  CV Generator    │ │
│  │  Screen   │  │  Viewer    │  │  Screen          │ │
│  └─────┬────┘  └─────┬─────┘  └────────┬─────────┘ │
│        │              │                  │           │
│        ▼              ▼                  ▼           │
│  ┌──────────────────────────────────────────────┐   │
│  │           Repository Layer (Riverpod)         │   │
│  └──────────┬───────────────────┬───────────────┘   │
│             │                   │                    │
│     ┌───────▼───────┐   ┌──────▼──────┐            │
│     │  Local SQLite  │   │ HTTP Client │            │
│     │  (sqflite)     │   │ (dio)       │            │
│     └───────────────┘   └──────┬──────┘            │
└─────────────────────────────────┼────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │     Backend (FastAPI)       │
                    │                            │
                    │  ┌────────┐  ┌──────────┐  │
                    │  │  Auth  │  │  Claude   │  │
                    │  │ (JWT)  │  │  Proxy    │  │
                    │  └────────┘  └──────────┘  │
                    │                            │
                    │  ┌────────────────────┐    │
                    │  │  CV Gen Endpoint   │    │
                    │  │  (PDF + DOCX)      │    │
                    │  └────────────────────┘    │
                    └────────────────────────────┘
```

---

## Backend (FastAPI)

### Why generate CV on the backend, not on-device?

PDF/DOCX generation on Flutter is limited. Server-side generation using
Python (`reportlab`/`python-docx`) is far more mature and produces
professional-quality output. It also keeps the app thin.

### Endpoints

```
POST   /auth/register          { email, password }
POST   /auth/login             { email, password } → { access_token }
POST   /auth/refresh           { refresh_token }   → { access_token }

POST   /extract                { conversations: [...] } → { results: [...] }
         - Auth required
         - Proxies to Claude API
         - Rate limited per user (e.g. 50 conversations/day)

POST   /cv/generate            { career_data, job_description, format: "pdf"|"docx" }
         - Auth required
         - Calls Claude to generate CV content
         - Renders to PDF or DOCX
         - Returns file bytes

GET    /health                 → { status: "ok" }
```

### Auth

- JWT-based (access token 15min + refresh token 7d)
- `bcrypt` for password hashing
- Stored in a small PostgreSQL (or SQLite for MVP)
- Optional: add Google/Apple social login later

### Tech Stack

| Layer      | Choice            | Reason                                 |
| ---------- | ----------------- | -------------------------------------- |
| Framework  | FastAPI           | Matches existing Python codebase       |
| Auth       | JWT (PyJWT)       | Simple, stateless                      |
| LLM        | Claude API        | Reuse existing extractor.py logic      |
| PDF        | reportlab         | Battle-tested Python PDF library       |
| DOCX       | python-docx       | Standard Word generation               |
| DB         | SQLite (MVP)      | User accounts + rate limits only       |
| Deploy     | Railway / Fly.io  | Simple container hosting               |

### Code Reuse

The backend directly reuses from the existing Python codebase:
- `src/extractor.py` → extraction logic (tool schema, parsing)
- `src/models.py` → Pydantic models
- `src/importers/` → format detection + parsing (server-side import option)

---

## Flutter App Structure

```
careeros_app/
├── lib/
│   ├── main.dart
│   ├── app.dart                          # MaterialApp, theme, router
│   │
│   ├── core/
│   │   ├── theme.dart                    # M3 theme, color scheme
│   │   ├── constants.dart                # API URLs, limits
│   │   └── router.dart                   # GoRouter config
│   │
│   ├── data/
│   │   ├── local/
│   │   │   ├── database.dart             # SQLite schema + helpers (drift)
│   │   │   └── tables.dart               # Table definitions
│   │   ├── remote/
│   │   │   ├── api_client.dart           # Dio HTTP client + interceptors
│   │   │   ├── auth_api.dart             # Login, register, refresh
│   │   │   └── extract_api.dart          # Extraction + CV endpoints
│   │   └── repositories/
│   │       ├── auth_repository.dart
│   │       ├── career_repository.dart    # Merges local DB + remote API
│   │       └── cv_repository.dart
│   │
│   ├── domain/
│   │   ├── models/                       # Dart equivalents of Python models
│   │   │   ├── conversation.dart
│   │   │   ├── project.dart
│   │   │   ├── skill.dart
│   │   │   ├── achievement.dart
│   │   │   ├── role.dart
│   │   │   └── extraction_result.dart
│   │   └── importers/                    # Client-side JSON parsing
│   │       ├── chatgpt_importer.dart
│   │       └── claude_importer.dart
│   │
│   ├── providers/                        # Riverpod providers
│   │   ├── auth_provider.dart
│   │   ├── career_provider.dart
│   │   ├── import_provider.dart
│   │   └── cv_provider.dart
│   │
│   └── ui/
│       ├── auth/
│       │   ├── login_screen.dart
│       │   └── register_screen.dart
│       ├── import/
│       │   ├── import_screen.dart        # File picker + progress
│       │   └── import_review_screen.dart # Preview before committing
│       ├── database/                     # Career data viewer/editor
│       │   ├── dashboard_screen.dart     # Overview: counts, recent
│       │   ├── projects_screen.dart      # List + detail + edit
│       │   ├── skills_screen.dart        # Grouped by category + edit
│       │   ├── achievements_screen.dart  # List + edit
│       │   ├── roles_screen.dart         # Timeline + link projects
│       │   └── widgets/
│       │       ├── entity_card.dart
│       │       ├── edit_dialog.dart
│       │       └── link_sheet.dart
│       ├── cv/
│       │   ├── cv_input_screen.dart      # Paste JD + select roles
│       │   ├── cv_preview_screen.dart    # Preview generated content
│       │   └── cv_export_screen.dart     # Download PDF/DOCX, share
│       ├── settings/
│       │   └── settings_screen.dart      # Account, about, logout
│       └── shared/
│           ├── loading_overlay.dart
│           └── empty_state.dart
│
├── test/
│   ├── importers/
│   │   ├── chatgpt_importer_test.dart
│   │   └── claude_importer_test.dart
│   ├── repositories/
│   └── ui/
│
├── pubspec.yaml
└── README.md
```

### Key Packages

```yaml
dependencies:
  # State management
  flutter_riverpod: ^2.5
  riverpod_annotation: ^2.3

  # Navigation
  go_router: ^14.0

  # Local database
  drift: ^2.15                  # Type-safe SQLite (better than raw sqflite)
  sqlite3_flutter_libs: ^0.5

  # HTTP
  dio: ^5.4

  # File picking (for JSON import)
  file_picker: ^8.0

  # Secure storage (for JWT tokens)
  flutter_secure_storage: ^9.0

  # Share / export
  share_plus: ^9.0
  open_filex: ^4.4

  # UI
  google_fonts: ^6.1
  flutter_animate: ^4.5         # Subtle transitions

dev_dependencies:
  drift_dev: ^2.15
  build_runner: ^2.4
  riverpod_generator: ^2.4
  mockito: ^5.4
```

---

## Screen-by-Screen Design

### 1. Auth (Login / Register)

```
┌──────────────────────────┐
│                          │
│       CareerOS logo      │
│                          │
│  ┌────────────────────┐  │
│  │  Email              │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │  Password           │  │
│  └────────────────────┘  │
│                          │
│  [ ━━━━ Log In ━━━━━ ]  │
│                          │
│  Don't have an account?  │
│  Register                │
└──────────────────────────┘
```

Simple email/password. No social login for MVP.

### 2. Dashboard (Home)

Bottom navigation: **Home** | **Import** | **CV** | **Settings**

```
┌──────────────────────────┐
│  CareerOS         [👤]   │
│──────────────────────────│
│                          │
│  ┌──────┐  ┌──────┐     │
│  │  12  │  │  34  │     │
│  │Proj. │  │Skills│     │
│  └──────┘  └──────┘     │
│  ┌──────┐  ┌──────┐     │
│  │   8  │  │   3  │     │
│  │Achiev│  │Roles │     │
│  └──────┘  └──────┘     │
│                          │
│  Recent Projects         │
│  ┌────────────────────┐  │
│  │ E-commerce API     │  │
│  │ Python, FastAPI     │  │
│  │ Sr. Eng @ Stripe   │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ Dashboard UI       │  │
│  │ React, TypeScript   │  │
│  │ Unlinked            │  │
│  └────────────────────┘  │
│                          │
│ ━━━━ ━━━━ ━━━━ ━━━━━━━ │
│ Home Import  CV  Settings│
└──────────────────────────┘
```

Tapping a stat card navigates to its list screen.

### 3. Import Screen

```
┌──────────────────────────┐
│  ← Import Chat History   │
│──────────────────────────│
│                          │
│    ┌──────────────────┐  │
│    │                  │  │
│    │   📁 Pick File   │  │
│    │                  │  │
│    │  Drop your       │  │
│    │  ChatGPT or      │  │
│    │  Claude export   │  │
│    │  (.json)         │  │
│    └──────────────────┘  │
│                          │
│  How to export:          │
│  ▸ ChatGPT: Settings →  │
│    Data Controls → Export│
│  ▸ Claude: Settings →   │
│    Account → Export Data │
│                          │
│──────────────────────────│
│  Previous Imports        │
│  ┌────────────────────┐  │
│  │ chatgpt_export.json│  │
│  │ 142 convos · Jan 15│  │
│  │ 89 work-relevant   │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

**Flow:**
1. User picks JSON file via system file picker
2. App parses locally (reuse importer logic in Dart)
3. Show preview: "Found 142 conversations. Extract career data?"
4. User confirms → conversations sent to backend `/extract` endpoint
5. Progress indicator during extraction
6. Results stored in local SQLite
7. Navigate to dashboard with updated counts

### 4. Database Viewer / Editor

**Projects list → detail:**

```
┌──────────────────────────┐
│  ← Projects          [+] │
│──────────────────────────│
│  🔍 Search...            │
│                          │
│  ┌────────────────────┐  │
│  │ E-commerce API      │  │
│  │ Built REST API with │  │
│  │ payment processing  │  │
│  │                     │  │
│  │ Python · FastAPI    │  │
│  │ Sr. Eng @ Stripe    │  │
│  │            [Edit ✎] │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ Dashboard UI        │  │
│  │ Real-time analytics │  │
│  │ dashboard           │  │
│  │                     │  │
│  │ React · TypeScript  │  │
│  │ ⚠ No role linked    │  │
│  │            [Edit ✎] │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

**Edit dialog (bottom sheet):**

```
┌──────────────────────────┐
│  Edit Project            │
│──────────────────────────│
│  Name                    │
│  ┌────────────────────┐  │
│  │ E-commerce API      │  │
│  └────────────────────┘  │
│  Summary                 │
│  ┌────────────────────┐  │
│  │ Built REST API with │  │
│  │ Stripe integration  │  │
│  └────────────────────┘  │
│  Status                  │
│  [Active ▾]              │
│                          │
│  Linked Role             │
│  [Sr. Engineer @ Stripe▾]│
│                          │
│  Skills                  │
│  [Python][FastAPI][+Add] │
│                          │
│  [Delete]      [Save]    │
└──────────────────────────┘
```

**Similar pattern for skills, achievements, roles.**

Roles screen has a timeline view:
```
  2023-01 ──── 2024-06
  │ Sr. Engineer @ Stripe
  │  └─ E-commerce API
  │  └─ Payment Dashboard
  │
  2024-07 ──── present
  │ Staff Engineer @ Meta
  │  └─ Feed Ranking
```

### 5. CV Generator

**Step 1: Input**
```
┌──────────────────────────┐
│  ← Generate CV           │
│──────────────────────────│
│                          │
│  Job Description         │
│  ┌────────────────────┐  │
│  │ Paste the job      │  │
│  │ description here...│  │
│  │                    │  │
│  │                    │  │
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  Include Roles           │
│  ☑ Sr. Eng @ Stripe      │
│  ☑ Staff Eng @ Meta      │
│  ☐ Intern @ Startup      │
│                          │
│  Format                  │
│  ◉ PDF  ○ Word (.docx)  │
│                          │
│  [ ━━ Generate CV ━━━ ]  │
└──────────────────────────┘
```

**Step 2: Preview**
```
┌──────────────────────────┐
│  ← CV Preview     [Edit] │
│──────────────────────────│
│                          │
│  EXPERIENCE              │
│  ──────────              │
│  Staff Engineer, Meta    │
│  Jul 2024 – Present     │
│  • Led feed ranking     │
│    optimization...      │
│  • Reduced latency by   │
│    40% through...       │
│                          │
│  Sr. Engineer, Stripe    │
│  Jan 2023 – Jun 2024    │
│  • Designed and built    │
│    payment processing...│
│  • Integrated Stripe    │
│    webhooks handling... │
│                          │
│  SKILLS                  │
│  ──────                  │
│  Python, React, ...     │
│                          │
│  [ Download ] [ Share ]  │
└──────────────────────────┘
```

The preview shows a rendered markdown version. "Edit" opens a text
editor where the user can tweak the LLM output before downloading.

Download calls the backend which returns the binary file (PDF or DOCX).

---

## Data Flow

### Import Flow

```
[User picks .json file]
        │
        ▼
[Flutter parses locally]          ← Dart importer (port of Python importers)
  - Detect format (ChatGPT/Claude)
  - Parse to List<Conversation>
  - Store raw conversations in local SQLite
        │
        ▼
[Send to backend /extract]        ← HTTP POST with JWT auth
  - Backend calls Claude API
  - Returns List<ExtractionResult>
        │
        ▼
[Store in local SQLite]           ← Projects, skills, achievements
  - Same schema as Python version
  - Dedup skills by name
  - Wire junction tables
```

### CV Generation Flow

```
[User pastes JD + selects roles]
        │
        ▼
[Flutter sends to /cv/generate]   ← POST { career_data, JD, format }
  career_data = {
    roles: [...],
    projects: [...] (filtered by selected roles),
    skills: [...],
    achievements: [...]
  }
        │
        ▼
[Backend: Claude generates CV text]
        │
        ▼
[Backend: Render to PDF/DOCX]
        │
        ▼
[Return binary file to app]
        │
        ▼
[Flutter: Preview + Share/Save]
```

---

## Local SQLite Schema (Drift)

Same as the Python version, ported to Drift table definitions:

```dart
class Conversations extends Table {
  TextColumn get id => text()();
  TextColumn get source => text()();
  TextColumn get title => text()();
  TextColumn get startedAt => text().nullable()();
  TextColumn get importedAt => text()();
  IntColumn get isWork => integer().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class Projects extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get summary => text().nullable()();
  TextColumn get status => text().withDefault(const Constant('active'))();
  TextColumn get startedAt => text().nullable()();
  TextColumn get endedAt => text().nullable()();
  TextColumn get roleId => text().nullable().references(Roles, #id)();

  @override
  Set<Column> get primaryKey => {id};
}

// Skills, Achievements, Roles, and junction tables follow same pattern
```

---

## Implementation Order

### Phase 1: Foundation (Week 1-2)
1. Flutter project setup + M3 theme
2. Backend skeleton (FastAPI + auth endpoints)
3. Local SQLite schema (Drift)
4. Dart model classes
5. Auth flow (register / login / token storage)

### Phase 2: Import Pipeline (Week 3)
6. Port ChatGPT importer to Dart
7. Port Claude importer to Dart
8. File picker integration
9. Backend `/extract` endpoint (reuse Python extractor)
10. Import screen + progress UI

### Phase 3: Database Viewer (Week 4)
11. Dashboard screen with stat cards
12. Projects list + detail + edit
13. Skills screen (grouped by category)
14. Achievements screen
15. Roles screen with timeline
16. Link projects to roles UI

### Phase 4: CV Generator (Week 5)
17. CV input screen (JD paste + role selection)
18. Backend CV generation endpoint (Claude + templates)
19. PDF generation (reportlab)
20. DOCX generation (python-docx)
21. CV preview screen
22. Download + share functionality

### Phase 5: Polish (Week 6)
23. Error handling + offline states
24. Loading skeletons
25. Empty states
26. Rate limit handling
27. Testing
28. App icon + splash screen

---

## Backend File Structure

```
backend/
├── app/
│   ├── main.py                # FastAPI app + CORS
│   ├── config.py              # Environment config
│   ├── auth/
│   │   ├── router.py          # /auth/* endpoints
│   │   ├── service.py         # JWT + bcrypt logic
│   │   ├── models.py          # User model
│   │   └── dependencies.py    # get_current_user dependency
│   ├── extract/
│   │   ├── router.py          # /extract endpoint
│   │   └── service.py         # Wraps existing extractor.py
│   ├── cv/
│   │   ├── router.py          # /cv/* endpoints
│   │   ├── generator.py       # Claude prompt for CV content
│   │   ├── pdf_renderer.py    # reportlab PDF output
│   │   └── docx_renderer.py   # python-docx Word output
│   └── db.py                  # User accounts DB
├── requirements.txt
├── Dockerfile
└── tests/
```
