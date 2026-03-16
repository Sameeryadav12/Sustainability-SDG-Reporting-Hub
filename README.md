# Sustainability & SDG Reporting Hub

A web platform for universities and institutions to collect sustainability data from departments, map it to the UN Sustainable Development Goals (SDGs), analyse it, and produce dashboards and AI-assisted sustainability report drafts.

---

## Project overview

**Sustainability & SDG Reporting Hub** helps organisations:

- **Collect** sustainability contributions from departments in structured reporting cycles.
- **Map** contributions to SDGs (primary and secondary) and track metrics, comments, and evidence.
- **Analyse** data via an analytics dashboard (counts by SDG, department, status, type).
- **Report** with human- and AI-generated report sections and export to Markdown and CSV.

It is aimed at **sustainability officers**, **department coordinators**, and **admins** who need a single place to manage university sustainability reporting, SDG mapping, data collection, dashboards, and exports. The optional **AI-generated report sections** help draft narrative content from existing contribution data.

---

## Features

- **Authentication** — JWT-based login; admin, coordinator, and viewer roles.
- **Departments** — CRUD for organisational units (e.g. faculties) with types.
- **Reporting cycles** — Create and manage cycles (DRAFT / OPEN / CLOSED); only one open at a time.
- **Contributions** — Create, edit, submit, approve, or reject contributions per cycle and department.
- **Metrics, comments, evidence** — Attach metrics, comments, and evidence (including file uploads) to contributions.
- **Analytics dashboard** — Summary and breakdowns by SDG, department, type, and status.
- **Report sections** — Draft sections per scope (overall, SDG, department); human or AI-generated.
- **AI generation** — Optional “Generate with AI” for report sections (OpenAI or compatible API).
- **Exports** — Markdown report and CSV (contributions, metrics, evidence) per reporting cycle.

---

## Tech stack

| Layer    | Technologies |
|----------|--------------|
| **Frontend** | React, TypeScript, Vite |
| **Backend**  | FastAPI, PostgreSQL, SQLModel / SQLAlchemy, Alembic |
| **Other**    | Docker, JWT auth, file uploads (local or configurable), optional AI (OpenAI-compatible) |

---

## Project structure

```
Sustainability & SDG Reporting Hub/
├── frontend/          # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── api/        # API client, auth
│   │   ├── features/   # Auth, departments, cycles, contributions, analytics, report sections, exports
│   │   └── ...
│   └── package.json
├── backend/            # FastAPI API and workers
│   ├── app/
│   │   ├── api/        # Routes, deps (auth)
│   │   ├── core/       # Config, security, pagination
│   │   ├── db/         # Migrations, seeds (SDGs, admin, demo)
│   │   ├── models/     # SQLModel entities
│   │   ├── schemas/    # Pydantic request/response
│   │   └── services/   # Business logic, storage, exports, AI
│   ├── alembic/        # Database migrations
│   ├── docker-compose.yml
│   └── Dockerfile
├── README.md           # This file
└── DEPLOYMENT_CHECKLIST.md
```

The **frontend** talks to the **backend** via `VITE_API_BASE_URL`. The **backend** uses PostgreSQL (or a compatible database) and optional file storage for evidence uploads.

---

## Local setup

Copy-paste friendly steps. Run from the repo root unless stated otherwise.

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd "Sustainability & SDG Reporting Hub"
```

### 2. Backend: env and Docker

```bash
cd backend
copy .env.example .env
```

Edit `.env` and set at least `POSTGRES_PASSWORD` (and `SECRET_KEY`, `FIRST_ADMIN_*` for production). Then start the stack:

```bash
docker compose up -d --build
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

### 3. Backend: migrations and seed

With the stack running:

```bash
docker compose exec api poetry run alembic upgrade head
docker compose exec api poetry run python -m app.db.seed_sdgs
docker compose exec api poetry run python -m app.db.seed_admin
```

Optional — demo data (departments, cycles, contributions, report sections, demo admin):

```bash
docker compose exec api poetry run python -m app.db.seed_demo_data
```

To reset to a clean demo set:

```bash
docker compose exec api poetry run python -m app.db.clean_demo_data
docker compose exec api poetry run python -m app.db.seed_demo_data
```

### 4. Frontend: install and run

From repo root:

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 (or the port Vite prints). The default `.env` points the app at `http://localhost:8000/api/v1`.

---

## Environment variables

### Backend (`.env` in `backend/`)

| Variable | Description |
|----------|-------------|
| `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | PostgreSQL connection (used when `DATABASE_URL` is not set). |
| `DATABASE_URL` | Optional full DB URL (overrides postgres_*). Use `postgresql://...` for SQLModel. |
| `SECRET_KEY` | JWT signing secret; **must change in production**. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_ALGORITHM` | Token expiry and algorithm. |
| `FIRST_ADMIN_NAME`, `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD` | Used by `seed_admin` to create the first admin. |
| `UPLOAD_DIR` | Directory for evidence uploads (e.g. `/app/uploads`). |
| `MAX_UPLOAD_SIZE_MB`, `ALLOWED_EVIDENCE_EXTENSIONS` | Upload limits and allowed file types. |
| `OPENAI_API_KEY` | Optional; set to enable “Generate with AI” for report sections. |
| `LLM_MODEL`, `LLM_BASE_URL` | Optional LLM overrides (default: gpt-4o-mini). |
| `CORS_ORIGINS` | Optional; comma-separated allowed origins (e.g. for deployed frontend). If not set, localhost origins are used. |

### Frontend (`.env` in `frontend/`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base URL (no trailing slash), e.g. `http://localhost:8000/api/v1`. For production, set to your deployed API URL. |

---

## Demo credentials

Admin account for testing the system with the seeded development database (after running `seed_demo_data`).

| Field    | Value            |
|----------|------------------|
| **Email**    | `demo@example.com` |
| **Password** | `DemoPassword1!`   |

These credentials are for **development/demo purposes only**. Change or disable the demo admin in production.

---

## Demo / test data

- **`seed_demo_data`** creates a demo admin (see [Demo credentials](#demo-credentials)), departments, reporting cycles, contributions, metrics, comments, evidence metadata, and report sections. Idempotent; run after `seed_sdgs`.
- **`seed_admin`** creates the first admin from `FIRST_ADMIN_*` env vars; use for a real first user.
- **`clean_demo_data`** removes test/junk data and leaves only a whitelist of departments and cycles; then run **`seed_demo_data`** again for a fresh demo set.
- Do not commit real secrets; use strong passwords and unique `SECRET_KEY` in production.

---

## Screenshots

Add screenshots here for a stronger GitHub presence. Suggested captures:

- **Dashboard** — Home or overview after login.
- **Contributions** — List or detail of contributions.
- **Analytics** — Analytics summary and charts.
- **Report sections** — List and “Generate with AI” flow.
- **Exports** — Markdown preview or CSV download.

Example: place images in `docs/screenshots/` and link them in this section.

---

## Deployment

For a **portfolio or demo** deployment:

- **Frontend**: Deploy the Vite build (e.g. to **Vercel**). Set `VITE_API_BASE_URL` to your backend API URL at build time.
- **Backend**: Run as a web service (e.g. **Render**, Railway, Fly.io). Set `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS` (see below), and optional `OPENAI_API_KEY`.
- **Database**: Use **Render Postgres**, **Supabase**, or any PostgreSQL provider.
- **Storage**: For evidence uploads, use **Cloudflare R2**, S3, or Supabase Storage; configure `UPLOAD_DIR` or a storage abstraction accordingly.

**CORS**: Set `CORS_ORIGINS` to your frontend origin(s), e.g. `https://your-app.vercel.app`. Multiple origins: comma-separated, no spaces.

See [Free deployment plan](#free-deployment-plan) for a fully free-tier setup.

---

## Free deployment plan

Suitable for **demo/portfolio** use on free tiers.

| Component   | Suggested service        | Notes |
|------------|--------------------------|--------|
| **Frontend** | Vercel                   | Connect repo; set `VITE_API_BASE_URL` to backend URL. |
| **Backend API** | Render Web Service    | Build: Docker or `pip install` + run; set env vars. |
| **Database** | Render Postgres or Supabase | Create a free project; use connection string as `DATABASE_URL`. |
| **Evidence storage** | Cloudflare R2 (free tier) or same server disk | Optional; for production-like file storage. |

Required steps:

1. Create backend and DB; run migrations (`alembic upgrade head`), then `seed_sdgs`, `seed_admin`, and optionally `seed_demo_data`.
2. Set backend env: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS=https://your-frontend.vercel.app`, and optionally `OPENAI_API_KEY`.
3. Deploy frontend with `VITE_API_BASE_URL=https://your-backend.onrender.com/api/v1` (or your API base URL).
4. No secrets in the repo; configure all secrets in the hosting dashboard.

This setup is **not** intended for high-scale or sensitive production without paid plans and hardening.

---

## Known limitations

- **Free-tier hosting**: Cold starts, rate limits, and resource caps may apply; not ideal for high traffic.
- **Production scale**: For serious production use, consider paid DB, compute, and storage; harden auth, CORS, and file handling.
- **AI generation**: Depends on a configured provider (e.g. OpenAI); optional and can be disabled by not setting `OPENAI_API_KEY`.
- **File storage**: Default local uploads are fine for dev; production may require cloud storage and stricter permissions.

---

## License

For educational and portfolio use unless otherwise specified. Add a `LICENSE` file in the repo if you adopt a specific license (e.g. MIT).

---

## Quick links

- **Backend API docs**: http://localhost:8000/docs (when running locally).
- **Backend README**: [backend/README.md](backend/README.md) for detailed API, auth, and step-by-step feature notes.
- **Deployment checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md).
