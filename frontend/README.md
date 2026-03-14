# Sustainability & SDG Reporting Hub — Frontend

React frontend for the **Sustainability & SDG Reporting Hub**: a complete app for login, dashboard, departments, reporting cycles, contributions, analytics, report sections with AI generation, and exports.

## Project status

All major modules are implemented:

- **Login** — Email/password auth, session restore
- **Dashboard** — Welcome, overview metrics cards (contributions, active cycle)
- **Departments** — List, create, edit (admin)
- **Reporting Cycles** — List, create, edit, open/close (admin)
- **Contributions** — List, filters, create, edit, detail, submit, approve/reject
- **Analytics** — Cycle selector, summary cards, charts (status, SDG, department, type)
- **Report Sections** — List, create, edit, AI generation, status updates
- **Exports** — CSV (contributions, metrics, evidence), Markdown report preview/download

## Prerequisites

- **Node.js** 18+ and **npm**
- **Backend** running and reachable (e.g. `http://localhost:8000`). Use backend seed/clean scripts for demo data (see backend README).

## Install

```bash
cd frontend
npm install
```

## Environment

Set the backend API base URL:

```bash
cp .env.example .env
```

Edit `.env`:

- **`VITE_API_BASE_URL`** — Backend API base URL with no trailing slash.
  - Local: `http://localhost:8000/api/v1`
  - Production: `https://your-api.example.com/api/v1`

If missing, the app falls back to `http://localhost:8000/api/v1`.

## Run

```bash
npm run dev
```

Open **http://localhost:5173** (or the port Vite reports).

## Production build

```bash
npm run build
```

Output is in `dist/`. Preview with:

```bash
npm run preview
```

For deployment (Vercel, Netlify, etc.), set `VITE_API_BASE_URL` to your production API URL and point the build output at `dist/`.

## Routes

| Path                  | Description                                             |
|-----------------------|---------------------------------------------------------|
| `/login`              | Login page                                              |
| `/`                   | Redirects to `/dashboard`                               |
| `/dashboard`          | Dashboard + metrics cards                               |
| `/departments`        | Departments list/create/edit (admin)                    |
| `/reporting-cycles`   | Reporting cycles list/create/edit/open/close (admin)    |
| `/contributions`      | Contributions list with filters                         |
| `/contributions/:id`  | Contribution detail, submit, approve/reject             |
| `/analytics`          | Analytics dashboard (charts, cycle selector)            |
| `/report-sections`    | Report sections, AI generation, Markdown preview        |
| `/exports`            | CSV and Markdown exports for selected cycle             |
| `*`                   | Not found page                                          |

## Backend dependency

The frontend uses:

- Auth: `POST /auth/login`, `GET /auth/me`
- Departments, reporting cycles, contributions, report sections
- Analytics: `GET /analytics/summary`
- AI: `POST /report-sections/generate`
- Exports: `GET /exports/contributions.csv`, `/metrics.csv`, `/evidence.csv`, `/report.md`

All requests use `Authorization: Bearer <token>` when logged in. The backend must allow CORS from the frontend origin when deployed.

## Role-based UI

- **Admin** — Create/edit departments, cycles, contributions, report sections; approve/reject; AI generation; exports
- **Department Coordinator** — Create/edit/submit contributions for their department; view report sections; exports
- **Viewer** — Read-only access; view contributions, analytics, report sections; exports

## Export functionality

- **CSV exports** — Contributions, metrics, and evidence for the selected reporting cycle. Download via authenticated API.
- **Markdown report** — Preview or download the compiled report draft. Reuses the report section preview modal with copy and download buttons.

## Deployment

- Set **`VITE_API_BASE_URL`** in your build environment to the production API URL (e.g. `https://api.example.com/api/v1`).
- Run **`npm run build`** — output goes to **`dist/`** (static HTML, JS, CSS).
- Deploy `dist/` to Vercel, Netlify, or any static host. Configure SPA fallback so `/login` and other routes resolve to `index.html`.
- Ensure the backend allows CORS from the frontend origin.
- The build script uses local TypeScript (`node ./node_modules/typescript/bin/tsc -b`); no global `tsc` required.

## Scripts

- `npm run dev` — Start dev server (Vite)
- `npm run build` — Production build (TypeScript + Vite). Output: `dist/`
- `npm run preview` — Serve production build locally
- `npm run lint` — Run ESLint
