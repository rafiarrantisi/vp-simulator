# Handoff → Hermes

**From:** the owner's other assistant (Claude Code), working on branch `feature/pivot-v4`.
**Date:** 2026-07-24. **Full env/setup detail:** see [`DEPLOYMENT_NOTES.md`](./DEPLOYMENT_NOTES.md).

Hermes — I did a large iteration on Qora and pushed it. A few things are done and
live; a few need the VPS / a domain / TLS, which are your territory. Everything you
need is below.

---

## What I changed (all pushed to `feature/pivot-v4`)

- **Frontend build restored** (the cleanup commit had deleted the bundler + Vite
  entry + the `ApiDataStore` seam). Rebuilt `sistemnya/build/bundle-legacy.mjs`,
  `sistemnya/index.html`, `sistemnya/engine/data-store.js`. Design byte-identical
  (CSS hash `index-Bj97HpXF.css` preserved).
- **New UX/features** (frontend): personalized dashboard + Profile screen,
  difficulty filter, Practice/OSCE mode select + prep screen + task panel + timer
  + time-up penalty, **streaming** replies, **browser-native STT** (Web Speech API;
  no TTS — replies are text), tabbed Assess with searchable investigation/therapy
  pickers, gamification (streak/daily-goal/badges), pricing/upgrade page, silent
  401 token-refresh, Google Sign-In button.
- **New backend**: v2 streaming turns endpoint, UI-mode→rubric mapping + overtime
  penalty, evidence-based senior-examiner judge prompt, gamification fields in
  `/api/v2/progress`, `/api/auth/google`, Xendit (`/api/billing/xendit/*`),
  `/api/ai/voice-status`, language-aware STT prompt, rate-limit on LLM endpoints.
- All env-driven; no new DB schema, **no new Alembic migration**, no new Python deps.

## What I did NOT touch (stayed yours)

- The **P1 answer-restraint** parser / case schema (`pipeline/case_v2.py`) and the
  82 case files — untouched. Leakage stays structural.
- **LLM model/provider config** (`backend/.env` model routing, temperature) — yours.
- The **VPS** (systemd, processes) — I did not SSH in.

## Already done & live (by me)

- **GitHub:** pushed; all 29 commits reattributed to `rafiarrantisi <arrantisi.online@gmail.com>`.
- **Vercel:** was broken by **mixed content** (HTTPS site calling `http://43.156.79.53:8000`
  directly). Fixed with `sistemnya/vercel.json` that proxies `/api/*` + `/health`
  to the backend **server-side**, and removed the `VITE_API_BASE` env var so the
  browser makes same-origin calls. Verified live: `/health`, `/api/v2/cases`, and a
  real demo **login all work** through `https://vp-simulator.vercel.app`.
- **Supabase:** verified healthy (PG 17.6, migrations at HEAD `f1a2b3c4d5e6`, indexed,
  19 users). **Enabled RLS on all 11 app tables** — they were all RLS-off while the
  `anon`/`authenticated` PostgREST roles exist, i.e. the public anon key could read
  every row (emails, hashed passwords) via `/rest/v1/...`. Backend role has
  `BYPASSRLS`, so the app is unaffected. Rollback: `ALTER TABLE public.<t> DISABLE ROW LEVEL SECURITY;`

---

## ⚠️ YOUR TASKS (in order)

### 0. PRE-FLIGHT — check before restarting (or the backend won't start)
The new code's prod-guard **refuses to start** when `ENV=prod` and `JWT_SECRET`
is the placeholder (`dev-only-change-me`), or `DATABASE_URL` is sqlite, or
`CORS_ORIGINS` has `*`, or `LLM_API_KEY` is empty. Verify `backend/.env`:
```bash
grep -E '^(ENV|JWT_SECRET|DATABASE_URL|CORS_ORIGINS|LLM_API_KEY)=' backend/.env
```
If `JWT_SECRET` is still the placeholder, generate one **on the server**:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
and set it in `backend/.env`.

### 1. Update the backend code (activates all new endpoints)
```bash
cd <REPO_DIR>
git fetch origin && git checkout feature/pivot-v4 && git pull origin feature/pivot-v4
# in the backend venv:
pip install -r backend/requirements.txt      # no new deps — safe/no-op
# no Alembic migration needed (schema unchanged; already at HEAD f1a2b3c4d5e6)
sudo systemctl restart <SERVICE_NAME>         # e.g. qora-backend
```
Verify (405 = still old code; 401/"not configured" = new code live ✅):
```bash
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/auth/google -H "Content-Type: application/json" -d '{"credential":"x"}'
```
> As of this handoff the prod backend is still running the OLD code
> (`/api/auth/google` → 405, `/api/billing/plans` has no `provider` field,
> `/api/v2/progress` has no `badges`/`streak`). The Vercel frontend degrades
> gracefully against it, but the new features need this step.

### 2. TLS for the backend (remove the plaintext Vercel→backend hop)
The Vercel proxy currently targets `http://43.156.79.53:8000` (works, but that hop
is unencrypted — login passwords included). Let's Encrypt needs a **domain** (not an IP):
1. Point a domain/subdomain (e.g. a free DuckDNS `qora-api.duckdns.org`) → A record `43.156.79.53`.
2. Open **port 80** in the Tencent Cloud firewall (for the ACME HTTP-01 challenge), or use a DNS-01 challenge.
3. Caddy is already installed — switch the `Caddyfile` to the domain (Caddy auto-provisions Let's Encrypt):
   ```
   qora-api.duckdns.org {
       reverse_proxy localhost:8000
   }
   ```
   `sudo systemctl reload caddy`
4. Verify: `curl -s https://qora-api.duckdns.org/health` (200, valid cert, no `-k`).

### 3. Point the Vercel proxy at HTTPS (after step 2)
Edit `sistemnya/vercel.json` — replace both `http://43.156.79.53:8000` with
`https://qora-api.duckdns.org`, then commit + push (Vercel auto-redeploys):
```bash
git add sistemnya/vercel.json
git commit -m "chore(vercel): proxy to HTTPS backend"
git push origin feature/pivot-v4
```

### 4. Optional — enable Google / Xendit (owner supplies keys)
In `backend/.env`, then restart: `GOOGLE_CLIENT_ID`, `XENDIT_API_KEY`,
`XENDIT_WEBHOOK_TOKEN` (point the Xendit webhook to `/api/billing/webhooks/xendit`),
optional `STT_LANGUAGE=en`. Flip `BILLING_ENFORCED=true` only once pricing is final.

### 5. Rotate exposed credentials
These appeared in a shared chat and should be rotated: the **Supabase DB password**
(then update `backend/.env` `DATABASE_URL`) and the **GitHub PAT** used for the push.
