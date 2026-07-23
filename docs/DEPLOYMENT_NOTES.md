# Qora — Deployment & Review Notes (this iteration)

What was built this iteration, how to configure/deploy it, and the findings from
the UX / performance / security / infra reviews (instruksi §3, §10–§12; Tambahan §5).

---

## 1. What changed (frontend `sistemnya/` + backend `backend/`)

- **Frontend build restored** — the "Qora-only" cleanup had deleted the bundler,
  the Vite entry, and the `ApiDataStore` seam while `package.json`/`vite.config.js`
  still referenced them. Rebuilt: `engine/data-store.js` (lean, self-contained),
  `build/bundle-legacy.mjs`, `index.html`. Design is byte-identical
  (CSS hash `index-Bj97HpXF.css` preserved on every build).
- **Auth robustness** — silent access-token refresh on 401 (`_qoraRefreshToken`),
  so an expired token transparently refreshes instead of dumping the user out.
- **Dashboard** personalized ("Welcome back, {name}"), **Profile** screen (view/edit).
- **Cases** — difficulty filter; removed the "only answers what you ask" line.
- **Session flow** — mode select (Practice vs OSCE) + prep screen (mic/STT/privacy)
  → session with a desktop **task panel**, **countdown timer**, **time-up penalty**
  choice, **streaming** replies, **voice input**.
- **Assess** — tabbed (Conversation / Investigations / Diagnosis / Therapy) with
  searchable, capped **investigation** + **therapy** pickers (`qora-catalog.js`).
- **Gamification** — real daily **streak**, **daily goal**, **badges** (12).
- **Evaluator** reworked into an evidence-based senior-examiner prompt.
- **Google Sign-In** (`/api/auth/google`) and **Xendit** payments
  (`/api/billing/xendit/*`) — both env-driven and off until keys are set.

## 2. Environment variables

### Backend (`backend/.env` — never commit; `.gitignore` covers it)

```
ENV=prod
JWT_SECRET=<64-hex; generate with: python -c "import secrets;print(secrets.token_hex(32))">
DATABASE_URL=postgresql://postgres.<ref>:<url-encoded-pw>@aws-0-<region>.pooler.supabase.com:5432/postgres
CORS_ORIGINS=["https://<your-vercel-domain>"]
LLM_API_KEY=<OpenRouter key>            # patient + judge models
# Voice: STT now uses the browser (Web Speech API) by default — no key needed.
# The server STT fallback (Firefox etc.) uses Groq; set these only for that path:
STT_BASE_URL=https://api.groq.com/openai/v1
STT_API_KEY=<Groq key>
STT_LANGUAGE=en                         # English product; the STT prompt is now language-aware
# TTS is NOT used (replies are text) — leave TTS_API_KEY empty.
GOOGLE_CLIENT_ID=<Google OAuth Web client id>     # enables /api/auth/google
XENDIT_API_KEY=<Xendit secret key>                # enables Xendit checkout/webhook
XENDIT_WEBHOOK_TOKEN=<Xendit callback verification token>
XENDIT_CURRENCY=USD
XENDIT_SUCCESS_URL=https://<domain>/billing/success
XENDIT_FAILURE_URL=https://<domain>/billing/failed
# BILLING_ENFORCED=true                 # flip ON only after a pricing/upgrade UI exists
```

> **Supabase password MUST be URL-encoded** in `DATABASE_URL`
> (`urllib.parse.quote_plus`) — the password contains `@`/`#`/`!` which otherwise
> break parsing (Tambahan §1).

### Frontend (`sistemnya/.env`)

```
VITE_API_BASE=            # empty when FastAPI serves the built SPA (same origin);
                          # or https://<backend> for a split deployment
VITE_GOOGLE_CLIENT_ID=<same Google OAuth Web client id>   # enables the Google button
```

## 3. Google Sign-In setup (owner console step)

1. Google Cloud Console → APIs & Services → Credentials → **OAuth client ID** → *Web*.
2. Authorised JavaScript origins: your Vercel domain (+ `http://localhost:5173` for dev).
3. Copy the client id into `GOOGLE_CLIENT_ID` (backend) and `VITE_GOOGLE_CLIENT_ID`
   (frontend). The button stays a disabled placeholder until both are set.
4. Flow: the frontend gets a Google ID token → `POST /api/auth/google` verifies it
   (Google tokeninfo + audience check) → finds/creates the user → issues our JWT.

## 4. Xendit setup (owner console step)

1. Xendit dashboard → API keys → copy the **secret** key → `XENDIT_API_KEY`.
2. Settings → Webhooks/Callbacks → set the invoice callback URL to
   `https://<backend>/api/billing/webhooks/xendit`; copy the **callback token** →
   `XENDIT_WEBHOOK_TOKEN`.
3. Flow: `POST /api/billing/xendit/checkout/{plan}` creates a hosted invoice and
   returns `checkout_url`; on payment Xendit calls the webhook (token-verified),
   which sets the user's entitlement. No card data ever touches our servers.
4. **Still to build for a full paywall:** a pricing/upgrade page in the UI, then
   flip `BILLING_ENFORCED=true`. The server-side freemium wall already exists
   (`billing.can_start_session`).

## 5. Database / infra review (Supabase + Vercel free tier)

- **Migrations:** use Alembic in prod — `alembic upgrade head`. Do **not** rely on
  `Base.metadata.create_all()`; note that `app/main.py` `lifespan()` calls
  `init_db()` (which runs `create_all`) on startup — it is idempotent, but for a
  managed Postgres the source of truth should be Alembic. *Recommendation:* gate
  `init_db()`'s `create_all` to dev only (skip when `ENV` is prod) and run Alembic
  in the deploy step. (Left unchanged here to avoid touching live startup — flag
  for a deliberate migration.)
- **Indexes:** already present on hot columns — `users.email` (unique), `*.user_id`,
  `usage_events.created_at`/`kind`, `session_costs.created_at`. Adequate for the
  freemium metering queries.
- **RLS:** the backend connects with a single service role and enforces access in
  FastAPI (JWT + `_owned` ownership checks), so RLS is not the enforcement layer.
  *Recommendation:* enable RLS on the app tables as defense-in-depth (deny-all +
  service-role bypass) so a leaked anon key can't read rows directly.
- **Free-tier care:** keep the LLM `max_tokens` caps (persona 220 / judge 1200);
  the per-session cost guardrail (`SessionCost`) is already logged.

## 6. Security review

| Item | Status / action |
|------|-----------------|
| **JWT_SECRET** | Was the dev default. Generate a 64-hex secret and set `JWT_SECRET` in prod env; the prod-guard already refuses to start prod with a weak secret. |
| Password hashing | bcrypt ✓ |
| Auth on all data routes | `get_current_user` + `_owned` ownership checks ✓ |
| Server-side gating | freemium wall + entitlement only via verified webhook ✓ |
| Security headers / CORS / rate-limit | middleware present; set `CORS_ORIGINS` to the exact prod domain (no `*`) ✓ |
| Google token | verified via Google (tokeninfo) + audience check ✓ |
| Xendit webhook | `x-callback-token` verified before any state change ✓ |
| Secrets | all via env; `.env` gitignored; **never commit** the credential docs ✓ |
| **Note** | the v2 streaming/turns endpoints sit on the `sessions` router which has no per-user rate-limit dependency (the `ai` router does). Consider adding the rate limiter to v2 session turns to cap abuse/cost. |

## 7. UX / performance review (highlights)

- **UX:** expired-session dead-end fixed (silent refresh); answer-restraint is
  explained in onboarding; catalogue is filterable (specialty + difficulty);
  session flow is linear and signposted (setup → session → assess → debrief).
- **Performance:** replies **stream** token-by-token (perceived latency ↓); the
  static catalogue is a single fetch; case load is O(1) per session; JS bundle
  ~70 kB gzip (within the app-page budget). Images/media lazy-load in the viewer.
- **Next perf wins (optional):** cache `/api/v2/cases` response; precompute the
  catalogue on the server; add HTTP caching headers for static media.

## 8. Deploy checklist

- [ ] Backend `.env` complete (esp. `JWT_SECRET`, `DATABASE_URL` url-encoded, `LLM_API_KEY`, `CORS_ORIGINS`).
- [ ] `alembic upgrade head` against Supabase.
- [ ] `cd sistemnya && npm ci && npm run build` → deploy `dist/` (Vercel) **or** let FastAPI serve it.
- [ ] Set `VITE_API_BASE` (empty for same-origin) + `VITE_GOOGLE_CLIENT_ID` at build time.
- [ ] Google + Xendit console steps (§3, §4) if enabling those.
- [ ] Smoke: signup/login, Google (if on), run a case (streaming), assess, debrief, progress.
