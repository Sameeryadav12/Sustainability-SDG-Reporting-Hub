# Deployment checklist

Use this list when deploying Sustainability & SDG Reporting Hub for demo or portfolio.

## Frontend

- [ ] `VITE_API_BASE_URL` set to deployed backend API base URL (e.g. `https://your-api.onrender.com/api/v1`) at **build time**
- [ ] Production build tested locally: `npm run build` (from `frontend/`)
- [ ] No hardcoded `localhost` in production build

## Backend

- [ ] `DATABASE_URL` or Postgres env vars set (e.g. from Render Postgres or Supabase)
- [ ] `SECRET_KEY` set to a long random value (not the default)
- [ ] `CORS_ORIGINS` set to deployed frontend URL(s), comma-separated (e.g. `https://your-app.vercel.app`)
- [ ] `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` set if using `seed_admin` (use a strong password)
- [ ] Migrations run: `alembic upgrade head`
- [ ] SDGs seeded: `python -m app.db.seed_sdgs`
- [ ] Admin/demo user created: `python -m app.db.seed_admin` and/or `python -m app.db.seed_demo_data`
- [ ] Optional: `OPENAI_API_KEY` set if using AI report generation
- [ ] Optional: `UPLOAD_DIR` or storage configured for evidence files

## General

- [ ] No `.env` or secrets committed; use hosting provider env/config
- [ ] Health check URL works (e.g. `/health` or `/api/v1/health`)
- [ ] Frontend can reach backend (CORS and network allow it)
