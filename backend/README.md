# Sustainability & SDG Reporting Hub — Backend

Backend API for **Sustainability & SDG Reporting Hub**, a university web platform to collect sustainability data from departments, map it to the UN Sustainable Development Goals (SDGs), analyse it, and support dashboards and AI-assisted sustainability report drafts.

This repository includes **Step 1: backend foundation**, **Step 2: core entities** (data layer), **Step 3: auth** (login, JWT, admin bootstrap, user creation), **Step 4: departments and reporting cycles** (CRUD and open/close workflow), **Step 5: contributions** (core CRUD and submit/approve/reject workflow), **Step 6: metrics, comments, and evidence metadata** (child records on contributions), **Step 7–8: analytics, report sections, and Markdown export**, **Step 9: real evidence file upload** (local storage and storage abstraction), **Step 10: CSV export** (contributions, metrics, evidence), **Step 11: AI draft generation** for report sections, and **Step 12: final hardening** (error handling, audit logging, pagination, demo seed, docs polish).

---

## Feature checklist / status

| Area | Status |
|------|--------|
| Auth (JWT, login, admin bootstrap, user CRUD) | ✅ |
| Departments CRUD | ✅ |
| Reporting cycles CRUD + open/close | ✅ |
| Contributions CRUD + submit/approve/reject | ✅ |
| Metrics, comments, evidence (metadata + file upload) | ✅ |
| Analytics summary | ✅ |
| Report section drafts + Markdown export | ✅ |
| CSV exports (contributions, metrics, evidence) | ✅ |
| AI report section generation (optional) | ✅ |
| Audit logging (write actions) | ✅ |
| Simple pagination (skip/limit on list endpoints) | ✅ |
| Demo seed script | ✅ |
| Health checks, Docker, migrations, tests | ✅ |

---

## Step 12: Final hardening (current)

- **Error handling:** Consistent human-readable API messages and status codes. Shared helpers in `app/core/http_errors.py` (`raise_404`, `raise_403`, `raise_400`). No tracebacks or raw internal errors in responses.
- **Audit logging:** `app/services/audit_service.py` provides `log_action(session, user_id, action, entity_type, entity_id, metadata_json=None)`. Important write actions (user/department/cycle/contribution/metric/evidence/report section create, update, submit, approve, reject, open, close, upload, delete, AI generate) are logged to the `AuditLog` model. Read-only operations are not logged.
- **Pagination:** List endpoints support optional query params **`skip`** (default 0, ≥ 0) and **`limit`** (default 100, 1–200). Validated in endpoints; defaults and max in `app/core/pagination.py`. **Endpoints with pagination:** `GET /api/v1/departments`, `GET /api/v1/reporting-cycles`, `GET /api/v1/contributions`, `GET /api/v1/report-sections` (with `reporting_cycle_id`).
- **Demo seed:** `app/db/seed_demo_data.py` creates a minimal demo dataset (departments, demo admin, reporting cycles, contributions, metrics, comments, evidence metadata, report sections). Idempotent; requires SDGs seeded first. Run:  
  `docker compose exec api poetry run python -m app.db.seed_demo_data`  
  Demo admin: `demo@example.com` / `DemoPassword1!` (dev only).
- **Startup/config:** Upload directory is created safely on startup. **AI configuration is optional:** the app starts successfully without `OPENAI_API_KEY`; only the AI report generation endpoint fails when invoked without a configured key.
- **Documentation:** README updated with project overview, architecture, features, run instructions, pagination, seeds, env vars, and tests.

**Enable "Generate with AI" (optional):**

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys) (or use an OpenAI-compatible endpoint).
2. In the **backend** folder, copy `.env.example` to `.env` if you don’t have one: `cp .env.example .env`
3. Edit `.env` and set: `OPENAI_API_KEY=sk-your-key-here`
4. If using Docker, restart the API so it picks up the new env: `docker compose restart api`
5. In the app, open **Report Sections**, choose a reporting cycle, and click **Generate with AI**. The modal will show a configuration message until the key is set and the API restarted.

---

- **Endpoint:** `POST /api/v1/report-sections/generate` (admin only). Request body: `reporting_cycle_id`, `scope_type` (SDG, DEPARTMENT, OVERALL), `scope_value`, optional `title`, `target_word_count` (100–1200), `overwrite_existing` (default true). Validates cycle and scope, gathers contributions and context by scope, builds a structured prompt, calls the configured LLM, and saves or updates a `ReportSectionDraft` with `generated_by=AI`, `status=DRAFT`, `last_generated_at`. Returns the section and optional `source_contribution_count`.  
- **Supported scope types:** SDG (scope_value = SDG id, e.g. `"4"`), DEPARTMENT (scope_value = department UUID), OVERALL (scope_value e.g. `"summary"`). THEME is not supported in this step.  
- **Human review workflow:** Generated drafts are saved as DRAFT for human review and editing via existing report section endpoints; final approval/editing remains human-controlled.  
- **Data basis:** AI drafts are based only on stored project data (contributions, departments, SDG metadata, analytics-style summary); the prompt instructs the model not to invent facts.  
- **Config:** `OPENAI_API_KEY` (required only when calling the generate endpoint; app starts without it), `LLM_MODEL` (default `gpt-4o-mini`), optional `LLM_BASE_URL`. See `.env.example`.  
- **Errors:** 404 if reporting cycle not found; 400 if scope not supported or no relevant data; 503 if generation fails or API key missing.  
- **Note:** Real async background job support (e.g. Celery) can be added later; this step runs generation synchronously.

---

## Step 10: CSV export

- **Endpoints:** `GET /api/v1/exports/contributions.csv`, `GET /api/v1/exports/metrics.csv`, `GET /api/v1/exports/evidence.csv`. All require query param **`reporting_cycle_id`** (UUID). Return downloadable CSV with `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="contributions_2025.csv"` (or `metrics_<year>.csv`, `evidence_<year>.csv`).  
- **Access:** Any authenticated user can download exports.  
- **Behaviour:** If the reporting cycle does not exist → **404** ("Reporting cycle not found."). If the cycle exists but has no data → valid CSV with **headers only** (no error).  
- **Columns:** Contributions export includes contribution_id, reporting_cycle_id, reporting_cycle_name, reporting_year, department_id, department_name, title, type, description, primary_sdg_id, **secondary_sdg_ids** (serialized as pipe-separated, e.g. `4|13|17`), start_date, end_date, status, created_by_user_id, approved_by_user_id, approval_notes, created_at, updated_at. Metrics export: one row per metric with metric_id, contribution_id, contribution_title, reporting_cycle_id, reporting_cycle_name, reporting_year, department_id, department_name, metric_name, value_number, value_text, unit, metric_year, created_at, updated_at. Evidence export: one row per evidence file with evidence_id, contribution_id, contribution_title, reporting_cycle_id, reporting_cycle_name, reporting_year, department_id, department_name, file_name, file_url, file_type, uploaded_by_user_id, uploaded_at.  
- **Use cases:** BI tools, audit review, spreadsheet analysis, reporting support.  
- **Implementation:** `app/services/export_service.py` uses Python’s built-in `csv` module; no extra dependencies.

---

## Step 9: Evidence file upload

- **Upload:** `POST /api/v1/contributions/{id}/evidence/upload` accepts a **multipart file upload**. Validates file type (allowlist from config), size (max `MAX_UPLOAD_SIZE_MB`), and non-empty file. Saves the file locally and creates an `EvidenceFile` record with `file_url` pointing to `/uploads/evidence/<generated-filename>`.  
- **List / delete:** `GET /api/v1/contributions/{id}/evidence` and `DELETE /api/v1/evidence/{id}` unchanged; delete also removes the local file when `file_url` is under `/uploads/`.  
- **Storage abstraction:** `app/services/storage_service.py` provides `save_upload`, `delete_file`, `build_public_url` so local storage can be swapped later for S3/R2/Supabase without changing endpoint logic.  
- **Local dev:** Upload directory is `UPLOAD_DIR` (default `/app/uploads`); `evidence` subdir is used. FastAPI mounts **StaticFiles** at `/uploads` so uploaded files are served at e.g. `GET /uploads/evidence/abc.pdf`. Directory is created on startup.  
- **Config:** `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_EVIDENCE_EXTENSIONS` (comma-separated, e.g. `pdf,xlsx,xls,csv,jpg,jpeg,png,doc,docx`). See `.env.example`.  
- **Permissions:** Same as Step 6: admin full; coordinator for own department when contribution is editable; viewer can list only, cannot upload or delete.  
- **Assumptions:** Production cloud storage (S3, presigned URLs, virus scanning) is not in this step; local upload is for dev-friendly flow.

---

## Step 8: Report Sections and Markdown Export

- **Report sections:** `GET /api/v1/report-sections?reporting_cycle_id=...`, `GET /api/v1/report-sections/{id}`, `POST /api/v1/report-sections` (admin), `PATCH /api/v1/report-sections/{id}` (admin). Sections are stored in `ReportSectionDraft` with `scope_type` (`OVERALL`, `SDG`, `DEPARTMENT`, `THEME`), `scope_value`, `title`, `content_markdown`, `status` (`DRAFT`, `REVIEWED`, `FINAL`), and `generated_by` (`HUMAN` for now).  
- **Export:** `GET /api/v1/exports/report.md?reporting_cycle_id=...` compiles a simple Markdown report: `# <cycle name>`, year, then each section as `## <title>` followed by its markdown body.  
- **Permissions:** Any authenticated user can read sections and export. Only **admins** can create and update report sections.  
- **Ordering:** Export orders sections deterministically: OVERALL, then SDG, then DEPARTMENT, then THEME, each group sorted by title. Empty cycles return a header-only (or minimal) Markdown report, not an error.  
- **Assumptions:** Drafts are manual in this step; AI generation and richer exports (DOCX/CSV) will be added later.

---

## Step 7: Analytics

- **Summary:** `GET /api/v1/analytics/summary?reporting_cycle_id=...` returns overall counts for a reporting cycle: total contributions, departments with contributions, SDGs covered (by primary SDG), totals by status and type, and simple metric summary counts.  
- **Breakdowns:** Includes SDG, department, type, and status breakdowns. SDG breakdown currently uses **primary_sdg_id only**; secondary SDGs are not counted yet.  
- **Metric summary:** Only counts metrics and distinguishes numeric/text metrics; it does **not** attempt to merge or sum metrics across units.  
- **Permissions:** Any authenticated user can read analytics.

---

## Step 6: Metrics, Comments, and Evidence

- **Metrics:** `GET /api/v1/contributions/{id}/metrics`, `POST /api/v1/contributions/{id}/metrics`, `DELETE /api/v1/metrics/{id}`. Name 2–120 chars; at least one of `value_number` or `value_text` required; year 2000–2100 if provided.  
- **Comments:** `GET /api/v1/contributions/{id}/comments`, `POST /api/v1/contributions/{id}/comments`. Text 3–2000 chars. Append-only; no edit/delete in this step.  
- **Evidence:** `GET /api/v1/contributions/{id}/evidence`, `POST /api/v1/contributions/{id}/evidence` (metadata-only), **`POST /api/v1/contributions/{id}/evidence/upload`** (real file upload — Step 9), `DELETE /api/v1/evidence/{id}`. Upload stores file under `UPLOAD_DIR/evidence/` and creates an `EvidenceFile` record; delete removes the record and the local file.  
- **Permissions:** Admin: full. Department coordinator: view/add/delete metrics and evidence for own department’s contributions when contribution is still editable; can add comments (and list) with access. Viewer: read-only (list metrics, comments, evidence); cannot create or delete. If a contribution is **APPROVED**, only admins can add/delete metrics or evidence; comments can still be added by admins and coordinators with access.  
- **Assumptions:** Evidence is metadata-only here. Approved contribution editability: non-admins cannot add/delete metrics or evidence for approved contributions.

---

## Step 5: Contributions

- **Endpoints:** `GET /api/v1/contributions`, `GET /api/v1/contributions/{id}`, `POST /api/v1/reporting-cycles/{id}/contributions`, `PATCH /api/v1/contributions/{id}`, `POST /api/v1/contributions/{id}/submit`, `POST /api/v1/contributions/{id}/approve` (admin), `POST /api/v1/contributions/{id}/reject` (admin).  
- **Workflow:** New contributions start as **DRAFT**. **DRAFT** or **REJECTED** → submit → **SUBMITTED**. **SUBMITTED** or **UNDER_REVIEW** → approve → **APPROVED**, or reject → **REJECTED**.  
- **Access:** List/get: admin and viewer see all; department coordinator sees only their department’s contributions. Create: coordinator creates for own department (department_id auto-filled); admin creates for any department (must send `department_id`). Update: coordinator can edit own department’s contribution only if not APPROVED and cycle is open; admin can edit any. Submit: coordinator (own dept) or admin. Approve/reject: admin only.  
- **Validation:** Title 3–250 chars, description min 10 chars, `primary_sdg_id` 1–17, `secondary_sdg_ids` optional list 1–17 (no duplicate of primary), `end_date` ≥ `start_date`.  
- **Assumptions:** Contributions belong to a reporting cycle. Contributions can only be created in an **OPEN** reporting cycle. Coordinators are limited to their own department. Only one reporting cycle is open at a time (Step 4).

---

## Step 4: Departments and Reporting Cycles

- **Department endpoints:** `GET /api/v1/departments`, `GET /api/v1/departments/{id}`, `POST /api/v1/departments` (admin), `PATCH /api/v1/departments/{id}` (admin).  
- **Reporting cycle endpoints:** `GET /api/v1/reporting-cycles`, `GET /api/v1/reporting-cycles/{id}`, `POST /api/v1/reporting-cycles` (admin), `PATCH /api/v1/reporting-cycles/{id}` (admin), `POST /api/v1/reporting-cycles/{id}/open` (admin), `POST /api/v1/reporting-cycles/{id}/close` (admin).  
- **Auth:** List/get require an authenticated user (Bearer token). Create, update, open, and close require **admin**.  
- **Validation:** Department: name 2–150 chars, code 2–20 chars (letters, numbers, underscores, hyphens), code unique, name unique. Reporting cycle: name required, year 2000–2100, `end_date` ≥ `start_date`, `in_scope_sdgs` non-empty list of SDG ids 1–17.  
- **Workflow:** New cycles are created as **DRAFT**. Only **one** reporting cycle may be **OPEN** at a time. **OPEN** → **close** → **CLOSED**.  
- **Assumption:** Only one reporting cycle can be open at a time; opening another returns 400 until the current open cycle is closed.

---

## Step 3: Auth

- **Security:** Password hashing (pwdlib/Argon2), JWT access tokens (python-jose), password strength validation.  
- **Endpoints:** `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/users` (admin-only).  
- **Dependencies:** `get_current_user`, `get_current_active_user`, `require_admin` in `app/api/deps.py`.  
- **Bootstrap:** `app/db/seed_admin.py` creates the first admin from `FIRST_ADMIN_*` env vars (idempotent).  
- **Password policy:** Min 8 characters; at least one uppercase, one lowercase, one digit, one special character.  
- **Limitation:** Refresh tokens are not implemented yet; use access token until expiry.

---

## Step 2: What was added (data layer only)

- **Models:** SDG, Department, User, ReportingCycle, Contribution, ContributionMetric, EvidenceFile, Comment, ReportSectionDraft, AuditLog  
- **Enums:** UserRole, DepartmentType, ReportingCycleStatus, ContributionType, ContributionStatus, ReportSectionScopeType, ReportSectionStatus, DraftGeneratedBy  
- **Shared:** `TimestampMixin` (created_at, updated_at in UTC), UUID primary keys (except SDG 1–17), relationships and indexes  
- **JSON fields:** `ReportingCycle.in_scope_sdgs` and `Contribution.secondary_sdg_ids` store lists of SDG ids (1–17) as JSON for portability and simple querying.  
- **AuditLog:** Python field `metadata_json` maps to DB column `metadata` (reserved name in SQLAlchemy).  
- **Migration:** `0002_step2_core_entities` creates tables and PostgreSQL ENUMs.  
- **SDG seed:** Idempotent script `app.db.seed_sdgs` inserts the 17 UN SDGs; run after migrations.

---

## Stack

- **Python** 3.12  
- **FastAPI** — API framework  
- **SQLModel** — ORM and models (SQLAlchemy + Pydantic)  
- **PostgreSQL** — database  
- **Alembic** — migrations  
- **Docker & docker-compose** — run API and DB locally  
- **Poetry** — dependency management  
- **pwdlib[argon2]** — password hashing (Argon2; 8–128 character limit)  
- **python-jose[cryptography]** — JWT (Step 3)  
- **email-validator** — Pydantic `EmailStr` validation (auth/user schemas)

---

## Folder structure

```
backend/
  app/
    api/
      deps.py            # Auth deps: get_current_user, require_admin
      v1/
        endpoints/
          auth.py        # POST login, GET me
          users.py       # POST users (admin)
          departments.py  # Departments CRUD (Step 4)
          reporting_cycles.py  # Reporting cycles CRUD + open/close (Step 4)
          contributions.py    # Contributions CRUD + submit/approve/reject (Step 5)
          metrics.py          # Contribution metrics (Step 6)
          comments.py         # Contribution comments (Step 6)
          evidence.py         # Evidence metadata + file upload (Step 6, 9)
          analytics.py        # Reporting cycle analytics (Step 7)
          report_sections.py  # Report section drafts (Step 8)
          exports.py          # Markdown report export (Step 8)
          health.py
        router.py
    core/
      config.py
      http_errors.py    # Shared 404/403/400 helpers (Step 12)
      pagination.py     # skip/limit constants and validation (Step 12)
      security.py        # Password hash/verify, JWT, password validation
    db/
      base.py
      session.py
      seed_sdgs.py
      seed_admin.py      # Bootstrap first admin
      seed_demo_data.py  # Demo dataset (Step 12; dev/demo)
    models/            # ORM models and enums
      base_mixins.py   # TimestampMixin (created_at, updated_at)
      enums.py         # UserRole, DepartmentType, etc.
      sdg.py, department.py, user.py, reporting_cycle.py
      contribution.py, contribution_metric.py, evidence_file.py
      comment.py, report_section_draft.py, audit_log.py
    schemas/           # auth, user, department, reporting_cycle, contribution, metric, comment, evidence, report_section, analytics
    services/         # auth, user, department, reporting_cycle, contribution, metric, comment, evidence, storage_service, export_service, analytics, report_section, audit_service (Step 12), llm_service, ai_report_service
    utils/             # Helpers (placeholder)
    main.py            # FastAPI app entry
  alembic/
    env.py             # Alembic env (uses app config)
    versions/          # Migration scripts
  tests/
    test_health.py
    test_auth.py       # Password validation, 401 for unauthenticated
    test_departments.py    # Departments 401, validation, service (Step 4)
    test_reporting_cycles.py  # Reporting cycles 401, validation, open/close (Step 4)
    test_contributions.py  # Contributions 401, validation, workflow (Step 5)
    test_metrics_comments_evidence.py  # Metrics, comments, evidence 401 and access (Step 6)
    test_evidence_upload.py           # Evidence file upload (Step 9)
    test_csv_exports.py               # CSV exports (Step 10)
    test_ai_report_generation.py      # AI report section generation (Step 11)
    test_report_sections.py  # Report sections and Markdown export (Step 8)
  scripts/
    verify_startup.py  # Import check after poetry install
  .dockerignore        # Excludes .env, cache, git from Docker build
  .env.example
  .gitignore
  Dockerfile
  docker-compose.yml
  pyproject.toml
  README.md
```

---

## Prerequisites

- **Docker** and **Docker Compose** (to run everything in containers), or  
- **Python 3.12**, **Poetry**, and **PostgreSQL** (to run locally without Docker).

---

## Run with Docker (recommended)

1. **Copy environment file**

   ```bash
   cd backend
   copy .env.example .env
   ```

   Edit `.env` and set at least `POSTGRES_PASSWORD` if you change it from the example.

2. **Start the stack**

   ```bash
   docker compose up --build
   ```

   First run will build the image and start the API and PostgreSQL. The API runs with **hot reload** (code changes are picked up automatically). The image includes dev dependencies so you can run `pytest` inside the container (see **Tests** below). A `.dockerignore` keeps `.env`, cache, and git out of the build context.

3. **Check that it’s up**

   - API: http://localhost:8000  
   - Docs: http://localhost:8000/docs  
   - Health: http://localhost:8000/health and http://localhost:8000/api/v1/health  

   **If the frontend shows "Cannot reach the server" on login:** The backend container must have **port 8000** published. Start the stack with this project's `docker-compose.yml` from the `backend` folder: `docker compose up -d --build`. If you have an existing "backend" container started without port mapping, recreate it: `docker compose down && docker compose up -d --build`.

4. **Run migrations (required for Step 2)**

   With the stack running, in another terminal:

   ```bash
   docker compose exec api poetry run alembic upgrade head
   ```

   This applies the schema (tables and ENUMs). Then seed the SDG reference table and **bootstrap the first admin** (Step 3):

   ```bash
   docker compose exec api poetry run python -m app.db.seed_sdgs
   docker compose exec api poetry run python -m app.db.seed_admin
   ```

   **(Optional) Demo data:** For a minimal demo dataset (departments, cycles, contributions, metrics, report sections, demo admin):

   ```bash
   docker compose exec api poetry run python -m app.db.seed_demo_data
   ```

   **Clean demo data (production polish):** To remove junk/test data and keep only a clean set, run clean then seed:

   ```bash
   docker compose exec api poetry run python -m app.db.clean_demo_data
   docker compose exec api poetry run python -m app.db.seed_demo_data
   ```

   Set `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` in `.env` before running `seed_admin`. The admin password must meet the password policy (see **Password policy** below).

---

## Run locally (without Docker)

1. **Python 3.12** and **Poetry** installed. Create and use the virtualenv:

   ```bash
   cd backend
   poetry install
   poetry shell
   ```

2. **PostgreSQL** running locally with a database and user matching `.env` (or use the same variable names as in `.env.example`).

3. **Copy and edit env**

   ```bash
   copy .env.example .env
   ```

   Set `POSTGRES_SERVER=localhost` (and port/user/password/db) to match your local Postgres.

4. **Run the API**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   To confirm no runtime import errors after install, run:  
   `poetry run python scripts/verify_startup.py`

5. **Migrations**

   ```bash
   alembic upgrade head
   ```

   Run from the `backend` directory so `app` is importable.

6. **Seed SDGs and first admin (after first migration)**

   ```bash
   poetry run python -m app.db.seed_sdgs
   poetry run python -m app.db.seed_admin
   ```

   **Important:** Change `SECRET_KEY`, `FIRST_ADMIN_EMAIL`, and `FIRST_ADMIN_PASSWORD` in `.env` for real deployments. Never commit real secrets.

   **(Optional) Demo data:**  
   `poetry run python -m app.db.seed_demo_data` — creates departments, demo admin, cycles, contributions, metrics, comments, evidence, report sections. Requires SDGs seeded first.

---

## Auth flow (Step 3)

1. **Bootstrap first admin** (once):  
   `poetry run python -m app.db.seed_admin` (or via Docker). Uses `FIRST_ADMIN_NAME`, `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD` from env. Idempotent.

2. **Login:**  
   `POST /api/v1/auth/login` with body `{"email": "admin@example.com", "password": "YourPassword"}`. Returns `access_token`, `token_type`, `expires_in`, and `user` (summary).

3. **Call protected endpoints:**  
   Add header: `Authorization: Bearer <access_token>`. Example: `GET /api/v1/auth/me` returns the current user.

4. **Create users (admin only):**  
   `POST /api/v1/users` with `Authorization: Bearer <admin_token>` and body matching `UserCreate` (name, email, password, role, optional department_id). Department coordinators must have `department_id` set.

**Env vars added in Step 3:**  
`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_ALGORITHM`, `FIRST_ADMIN_NAME`, `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD`. See `.env.example`. **Change secret values in production.**

**Env vars added in Step 9 (evidence upload):**  
`UPLOAD_DIR` (default `/app/uploads`), `MAX_UPLOAD_SIZE_MB` (default `10`), `ALLOWED_EVIDENCE_EXTENSIONS` (comma-separated, e.g. `pdf,xlsx,xls,csv,jpg,jpeg,png,doc,docx`). See `.env.example`.

**Env vars added in Step 11 (AI report generation — optional):**  
`OPENAI_API_KEY` (leave empty to run without AI; app starts fine, only the generate endpoint fails when called), `LLM_MODEL` (default `gpt-4o-mini`), optional `LLM_BASE_URL`. See `.env.example`.

**Password policy:** Between 8 and 128 characters; at least one uppercase letter, one lowercase letter, one digit, and one special character.

**Known limitations:** Refresh token not implemented; use access token until it expires.

---

## API docs

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

## Data model (Step 2)

| Table | Description |
|-------|-------------|
| **sdg** | UN SDG reference (id 1–17), seeded once |
| **department** | Organisational unit (e.g. Faculty of Science) |
| **user** | Platform user; role, optional department |
| **reporting_cycle** | Time-bounded reporting period; `in_scope_sdgs` = JSON list of SDG ids |
| **contribution** | Main record: title, type, primary_sdg, optional secondary_sdg_ids (JSON), status, approver |
| **contribution_metric** | Numeric or text metric for a contribution |
| **evidence_file** | File metadata linked to a contribution |
| **comment** | Comment on a contribution |
| **report_section_draft** | AI/human draft section (per SDG, department, theme, or overall) |
| **audit_log** | User action log; `metadata_json` in Python, column `metadata` in DB |

**Enums:** UserRole, DepartmentType, ReportingCycleStatus, ContributionType, ContributionStatus, ReportSectionScopeType, ReportSectionStatus, DraftGeneratedBy. Stored as PostgreSQL ENUMs.

**JSON fields:** `in_scope_sdgs` and `secondary_sdg_ids` are lists of integers (SDG ids 1–17). Using JSON keeps the schema portable and avoids PostgreSQL-specific array types.

---

## Endpoints

| Method | Path                 | Description                    |
|--------|----------------------|--------------------------------|
| GET    | /                    | Root message and links         |
| GET    | /health              | Health check                   |
| GET    | /api/v1/health       | Versioned health check         |
| POST   | /api/v1/auth/login   | Login; returns JWT and user    |
| GET    | /api/v1/auth/me      | Current user (Bearer token)    |
| POST   | /api/v1/users        | Create user (admin only)        |
| GET    | /api/v1/departments  | List departments (authenticated); **pagination:** `skip`, `limit` |
| GET    | /api/v1/departments/{id} | Get department (authenticated) |
| POST   | /api/v1/departments  | Create department (admin only)   |
| PATCH  | /api/v1/departments/{id} | Update department (admin only) |
| GET    | /api/v1/reporting-cycles | List reporting cycles (authenticated); optional ?status=OPEN; **pagination:** `skip`, `limit` |
| GET    | /api/v1/reporting-cycles/{id} | Get reporting cycle (authenticated) |
| POST   | /api/v1/reporting-cycles | Create reporting cycle (admin only); created as DRAFT |
| PATCH  | /api/v1/reporting-cycles/{id} | Update reporting cycle (admin only) |
| POST   | /api/v1/reporting-cycles/{id}/open | Open cycle (admin); only one open at a time |
| POST   | /api/v1/reporting-cycles/{id}/close | Close cycle (admin); OPEN → CLOSED |
| GET    | /api/v1/contributions | List contributions (authenticated); filters: reporting_cycle_id, department_id, sdg_id, status, type; **pagination:** `skip`, `limit` |
| GET    | /api/v1/contributions/{id} | Get contribution (authenticated; access by role) |
| POST   | /api/v1/reporting-cycles/{id}/contributions | Create contribution (cycle must be OPEN; coordinator own dept, admin any) |
| PATCH  | /api/v1/contributions/{id} | Update contribution (coordinator own + not approved, admin any) |
| POST   | /api/v1/contributions/{id}/submit | Submit contribution (DRAFT/REJECTED → SUBMITTED) |
| POST   | /api/v1/contributions/{id}/approve | Approve (admin only); body: `{"approval_notes": "..."}` optional |
| POST   | /api/v1/contributions/{id}/reject | Reject (admin only); body: `{"approval_notes": "..."}` encouraged |
| GET    | /api/v1/contributions/{id}/metrics | List metrics (authenticated; contribution access) |
| POST   | /api/v1/contributions/{id}/metrics | Create metric (coordinator/admin; at least one of value_number/value_text) |
| DELETE | /api/v1/metrics/{id} | Delete metric (coordinator for editable contribution, admin always) |
| GET    | /api/v1/contributions/{id}/comments | List comments (authenticated; contribution access) |
| POST   | /api/v1/contributions/{id}/comments | Create comment (admin/coordinator with access; viewers read-only) |
| GET    | /api/v1/contributions/{id}/evidence | List evidence metadata (authenticated; contribution access) |
| POST   | /api/v1/contributions/{id}/evidence | Create evidence metadata (metadata only; optional) |
| POST   | /api/v1/contributions/{id}/evidence/upload | **Upload evidence file** (multipart; validated type/size) |
| DELETE | /api/v1/evidence/{id} | Delete evidence (and local file when under /uploads) |
| GET    | /api/v1/exports/contributions.csv | CSV export of contributions; ?reporting_cycle_id= required (Step 10) |
| GET    | /api/v1/exports/metrics.csv | CSV export of metrics; ?reporting_cycle_id= required (Step 10) |
| GET    | /api/v1/exports/evidence.csv | CSV export of evidence; ?reporting_cycle_id= required (Step 10) |
| GET    | /api/v1/report-sections | List report sections; ?reporting_cycle_id= required; **pagination:** `skip`, `limit` |
| GET    | /api/v1/report-sections/{id} | Get report section (authenticated) |
| POST   | /api/v1/report-sections | Create report section (admin only) |
| PATCH  | /api/v1/report-sections/{id} | Update report section (admin only) |
| POST   | /api/v1/report-sections/generate | Generate report section draft (admin only; Step 11) |

Health responses look like:

```json
{
  "status": "ok",
  "project": "Sustainability & SDG Reporting Hub",
  "environment": "development"
}
```

**Example requests (Step 4):**

- Create department (admin, Bearer token):  
  `POST /api/v1/departments`  
  `{"name": "Faculty of Science", "code": "SCI", "type": "ACADEMIC"}`

- Create reporting cycle (admin):  
  `POST /api/v1/reporting-cycles`  
  `{"name": "Sustainability Report 2025", "year": 2025, "start_date": "2025-01-01", "end_date": "2025-12-31", "description": "Annual cycle.", "in_scope_sdgs": [4, 5, 9, 11, 12, 13, 17]}`

- Open a cycle (admin): `POST /api/v1/reporting-cycles/{id}/open`  
- Close a cycle (admin): `POST /api/v1/reporting-cycles/{id}/close`

**Example requests (Step 5 — contributions):**

- Create contribution (authenticated; reporting cycle must be OPEN):  
  `POST /api/v1/reporting-cycles/{cycle_id}/contributions`  
  `{"title": "Sustainability course 2025", "type": "TEACHING", "description": "A full course on sustainability and SDGs.", "primary_sdg_id": 4, "secondary_sdg_ids": [12, 13]}`  
  Coordinator: `department_id` is auto-filled from their profile. Admin: send `department_id`.

- Approve (admin): `POST /api/v1/contributions/{id}/approve` with body `{"approval_notes": "Well documented and aligned to SDG 4."}`  
- Reject (admin): `POST /api/v1/contributions/{id}/reject` with body `{"approval_notes": "Please provide clearer evidence."}`

**Example requests (Step 6 — metrics, comments, evidence):**

- Add metric: `POST /api/v1/contributions/{id}/metrics`  
  `{"name": "Students reached", "value_number": 1200, "unit": "students", "year": 2025}`

- Add comment: `POST /api/v1/contributions/{id}/comments`  
  `{"text": "Please add a clearer evidence link and update the metric source."}`

- Add evidence metadata (no file upload): `POST /api/v1/contributions/{id}/evidence`  
  `{"file_name": "sdg4-program-summary.pdf", "file_url": "https://example.com/files/sdg4-program-summary.pdf", "file_type": "pdf"}`

- **CSV exports (Step 10):** With Bearer token:  
  `GET /api/v1/exports/contributions.csv?reporting_cycle_id=<uuid>`  
  `GET /api/v1/exports/metrics.csv?reporting_cycle_id=<uuid>`  
  `GET /api/v1/exports/evidence.csv?reporting_cycle_id=<uuid>`  
  Response is `text/csv` with attachment filename e.g. `contributions_2025.csv`. Unknown cycle → 404; empty cycle → CSV with headers only.

- **Generate report section (Step 11):** Admin only.  
  `POST /api/v1/report-sections/generate`  
  Body: `{"reporting_cycle_id": "<uuid>", "scope_type": "SDG", "scope_value": "4", "title": "SDG 4 – Quality Education", "target_word_count": 500, "overwrite_existing": true}`  
  Returns the created or updated report section draft (`generated_by=AI`, `status=DRAFT`). Requires `OPENAI_API_KEY` to be set.

---

## Tests

From the `backend` directory:

```bash
poetry run pytest
```

Or with Docker (the image includes dev dependencies):

```bash
docker compose exec api poetry run pytest
```

At least the health endpoint tests in `tests/test_health.py`, auth tests in `tests/test_auth.py`, Step 4 tests in `tests/test_departments.py` and `tests/test_reporting_cycles.py`, Step 5 tests in `tests/test_contributions.py`, Step 6 tests in `tests/test_metrics_comments_evidence.py`, Step 8 tests in `tests/test_report_sections.py`, Step 9 tests in `tests/test_evidence_upload.py`, Step 10 tests in `tests/test_csv_exports.py`, Step 11 tests in `tests/test_ai_report_generation.py`, and Step 12 tests (pagination, audit, startup, demo seed) should pass.

---

## Manual steps

1. **Create `.env`** from `.env.example` and set `POSTGRES_PASSWORD` (and any other overrides).  
2. **First time with Docker:** run `docker compose up --build` and wait until the API and DB are healthy.  
3. **Step 2 & 3:** Run migrations, then seed SDGs and first admin:
   - `docker compose exec api poetry run alembic upgrade head`
   - `docker compose exec api poetry run python -m app.db.seed_sdgs`
   - `docker compose exec api poetry run python -m app.db.seed_admin`
4. **Without Docker:** from `backend`, run `alembic upgrade head`, then `poetry run python -m app.db.seed_sdgs` and `poetry run python -m app.db.seed_admin`.

---

## Next steps (later)

Possible future improvements:

- Refresh tokens for auth
- Background job system for long-running AI generation
- Cloud storage (S3/R2) for evidence files
- Rate limiting on sensitive endpoints
- Richer report exports (DOCX, PDF)
- Secondary SDG breakdown in analytics

No need to restructure the project; add new endpoints under `app/api/v1/endpoints/`, models in `app/models/`, and schemas in `app/schemas/`.

---

## Commands to run (after Step 2 & 3)

From the **backend** directory (or inside the `api` container):

1. **Apply migrations:**  
   `alembic upgrade head`  
   (or `docker compose exec api poetry run alembic upgrade head`)

2. **Seed the 17 SDGs:**  
   `python -m app.db.seed_sdgs`  
   (or `docker compose exec api poetry run python -m app.db.seed_sdgs`)

3. **Bootstrap first admin:**  
   `python -m app.db.seed_admin`  
   (or `docker compose exec api poetry run python -m app.db.seed_admin`)  
   Ensure `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` are set in `.env`; password must meet strength policy.

4. **(Optional) Demo data:**  
   `python -m app.db.seed_demo_data`  
   (or `docker compose exec api poetry run python -m app.db.seed_demo_data`)  
   Creates departments, demo admin (`demo@example.com` / `DemoPassword1!`), cycles, contributions, metrics, comments, evidence, report sections. Run after SDG seed.

5. **Run tests:**  
   `pytest`  
   (or `docker compose exec api poetry run pytest`)
