# Qora — Deployment & Integration Plan v1
> **Author:** Ker (Quakeran) — co-founder / tech lead  
> **Date:** 21 July 2026  
> **Status:** Waiting for Arran's review & approval  
> **Repo:** `rafiarrantisi/vp-simulator`, branch `feature/pivot-v4`

---

## 0. Executive Summary

Deploy Qora (English multi-specialty anamnesis trainer) with 38 cases across 10 specialties to a production environment at minimal cost. Frontend goes to Vercel (free), database migrates to Supabase PostgreSQL (free tier), backend stays on this VPS (already running). Zero visual changes to the frontend design.

**Total estimated cost: $0/mo** (Vercel free + Supabase free + existing VPS).

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────┐
│          Vercel (Free Tier)                       │
│  Static hosting: Vite build output                │
│  Domain: qora.vercel.app / custom domain          │
│  CDN edge cached, HTTPS auto                      │
└──────────────────┬───────────────────────────────┘
                   │  API calls
                   │  /api/v2/*  /api/auth/*
                   ▼
┌──────────────────────────────────────────────────┐
│          VPS (Existing — ubuntu)                  │
│  FastAPI backend (:8000)                          │
│  • /api/v2/cases — catalogue                      │
│  • /api/v2/sessions — OSCE flow                   │
│  • /api/auth/* — signup/login                     │
│  • WebSocket WS streaming                         │
│  • LLM orchestration (OpenRouter deepseek)        │
│  • Static files (exam media, eye photos)          │
│  Nginx reverse proxy + Let's Encrypt              │
└──────────────────┬───────────────────────────────┘
                   │  SQLAlchemy
                   ▼
┌──────────────────────────────────────────────────┐
│          Supabase (Free Tier)                     │
│  PostgreSQL 15                                    │
│  • users, user_profiles, sessions, session_turns  │
│  • scoring_reports, user_badges, billing          │
│  • admin_audit_log, eye_photos                    │
│  500MB storage, auto-backups                      │
└──────────────────────────────────────────────────┘
```

**Why this split:**

| Concern | Where | Why |
|---------|-------|-----|
| Static files | Vercel | Free CDN, auto HTTPS, no server management |
| LLM + WebSocket | VPS | 10-30s calls, persistent connections — impossible on serverless |
| Database | Supabase | Free managed PostgreSQL, auto-backups, no DBA overhead |
| Case files | VPS | Filesystem needed for markdown parsing + uploads |

---

## 2. Phase 1: Database Migration — SQLite → PostgreSQL

### 2.1 Create Supabase Project
- Sign up / login at [supabase.com](https://supabase.com)
- Create new project → get `DATABASE_URL` (connection string)
- Free tier: 500MB, 2 projects, auto-backups

### 2.2 Update Backend Config
```bash
# backend/.env changes
DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
```
- Switch from `sqlite:///./ophtha_dev.db` to PostgreSQL connection string
- Install `psycopg2-binary` (already in requirements.txt)

### 2.3 Run Alembic Migrations
```bash
cd backend
.venv/bin/alembic upgrade head
```
Creates all tables: `users`, `user_profiles`, `user_badges`, `sessions`, `session_turns`, `scoring_reports`, `cases`, `eye_photos`, `admin_audit_log`

### 2.4 Seed Admin User
```bash
.venv/bin/python -m scripts.seed_dev_user  # creates demo@qora.app (dev only)
```

### 2.5 Verify
```bash
.venv/bin/pytest -q  # confirm all tests pass with PostgreSQL
```

**Files changed:** `backend/.env` only (1 line), plus `backend/app/database.py` if any SQLite-specific code needs updating.

---

## 3. Phase 2: Case Integration — 38 Cases → Frontend

### 3.1 Assessment: Cases Already Integrated ✅

The generated cases are already in `content/cases/`. The backend catalog:

```python
# backend/app/domains/cases/v2_catalog.py
def list_v2_cases():
    for fp in sorted(_dir().glob("*.md")):  # <- reads ALL .md files
        c = parse_case_v2(fp)
        if lint(c).ok:                       # <- only serves valid cases
            out.append(c)
```

**The frontend already calls `GET /api/v2/cases`** → returns all 38 cases automatically.  
**The Qora catalogue UI** (`qora-v2.jsx`) already renders them with specialty filters.  
**No code changes needed.** When the backend restarts with the new cases in `content/cases/`, they appear.

### 3.2 Cleanup: Legacy Ophthalmology Cases

The old ophthalmology cases live in `data-kasus/` — a **different directory** from `content/cases/`. The Qora catalog only reads from `content/cases/`. Legacy cases are **already excluded** from Qora.

**Action needed:** None. Legacy cases stay accessible only via the "Classic" eye app (separate screen).

### 3.3 Update Status for New Cases

Currently all 27 new cases have `status: in_review`. To show them in the catalogue, either:
- **Option A:** Set `status: published` on cases after review (linter allows `in_review` too — `list_v2_cases` doesn't filter by `published_only` by default)
- **Option B:** No change needed — the catalog already shows `in_review` cases

**Status quo works.** Cases are visible immediately. Review can happen later.

---

## 4. Phase 3: Frontend Deployment — Vercel

### 4.1 Build

```bash
cd sistemnya
npm install
npm run build
# → dist/ contains static files + index-Bj97HpXF.css
```

### 4.2 Configure Vercel

**Option A: Vercel CLI (recommended)**
```bash
npm i -g vercel
vercel --prod
```
- Root directory: `sistemnya/`
- Build command: `npm run build`
- Output directory: `dist`
- Framework: Vite

**Option B: Vercel Git Integration**
- Connect GitHub repo → Vercel dashboard
- Set root to `sistemnya/`
- Auto-deploy on push to `main`/`feature/pivot-v4`

### 4.3 Environment Variables (Vercel)
```
VITE_API_BASE=https://api.qora.example.com   # points to VPS backend
```

### 4.4 Domain
- Vercel auto-assigns `qora-<hash>.vercel.app`
- Custom domain (e.g., `qora.app`, `getqora.com`) later

### 4.5 CORS Update
Backend `.env`:
```bash
CORS_ORIGINS=["https://qora-xxx.vercel.app","https://qora.app"]
```

### 4.6 Verify
- Visit Vercel URL → Qora landing page loads
- Sign up → catalogue shows 38 cases
- Start OSCE session → chat works (WebSocket to VPS backend)
- Score + answer key reveal works

---

## 5. Phase 4: Backend Production Hardening

### 5.1 Security
```bash
# Generate proper secrets
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD_HASH=$(python -c "import bcrypt; print(bcrypt.hashpw(b'<password>', bcrypt.gensalt()).decode())")
```

### 5.2 Nginx + HTTPS on VPS
- New domain (e.g., `api.qora.app`) → A record to VPS IP
- Nginx config with WebSocket support
- Let's Encrypt via certbot

### 5.3 Systemd Service
```bash
sudo cp deploy/ophtha-backend.service /etc/systemd/system/qora-backend.service
sudo systemctl enable --now qora-backend
```

### 5.4 Health Check
```bash
curl https://api.qora.app/health
# → {"success":true,"data":{"status":"up","env":"prod"}}
```

---

## 6. What Does NOT Change (Design Invariant)

| Component | Status |
|-----------|--------|
| `design.css` | **NEVER edited** |
| CSS hash `index-Bj97HpXF.css` | **MUST stay identical** |
| `src/main.jsx` | Generated file, never hand-edit |
| `Virtual Patient Simulator.html` | Kept for legacy compatibility |
| Qora screen components (`qora-v2.jsx`, `qora-landing.jsx`) | Already built, no changes |
| Legacy eye app (Classic) | Preserved, reachable from nav |

The 38 new cases populate the catalogue automatically — the frontend doesn't need any code changes to display them.

---

## 7. Files Modified Summary

| File | Change | Why |
|------|--------|-----|
| `backend/.env` | `DATABASE_URL` → Postgres, new `JWT_SECRET`, `CORS_ORIGINS` → Vercel URL | DB migration + security |
| `backend/app/database.py` | Possibly update SQLite-specific code | Postgres compatibility |
| Vercel config | `vercel.json` or dashboard settings | Deployment |
| Nginx config | New server block for `api.qora.app` | Reverse proxy to FastAPI |
| `content/cases/*.md` | 27 new files already generated | Cases |

**Zero frontend code changes. Zero design changes.** ✅

---

## 8. Risk & Rollback

| Risk | Mitigation |
|------|-----------|
| Supabase free tier limit (500MB) | Monitor DB size; upgrade if needed |
| VPS IP blocked by Vercel | Not an issue — Vercel frontend talks to VPS backend via public API |
| LLM latency on VPS | Same as current — no change |
| PostgreSQL migration breaks tests | Run full test suite before deploy; keep SQLite `.env` backup |
| Vercel cold start | Only affects frontend static files — CDN cached, negligible |

**Rollback:** Keep old SQLite `.env` file as `.env.sqlite.bak`. To revert, restore `DATABASE_URL` and restart backend.

---

## 9. Deployment Order (Sequential)

```
Step 1: Supabase project created → DATABASE_URL obtained
Step 2: backend/.env updated → DATABASE_URL to Postgres
Step 3: Alembic upgrade head → tables created
Step 4: Seed admin user → demo@qora.app working
Step 5: Run test suite → all green
Step 6: Restart backend → /health confirms up
Step 7: Build frontend → npm run build green
Step 8: Deploy to Vercel → vercel --prod
Step 9: Update CORS origins → Vercel domain
Step 10: Smoke test → signup → catalogue → OSCE → score
```

---

## 10. What's Deferred (Post-Launch)

- Payments (Lemon Squeezy) — seam exists, keys deferred
- Email (SMTP/Resend) — console mode works for dev
- OAuth Google — "coming soon" disabled button
- Voice (STT/TTS) — endpoints exist, labelled beta
- Scoring calibration (20 human trials)
- Custom domain for Qora frontend
- Analytics / error monitoring

---

**Approved by Arran:** ☐ Yes / ☐ No / ☐ With changes  
**Changes requested:**
