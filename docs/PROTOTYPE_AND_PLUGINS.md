# Qora prototype — external-key plug points

The prototype runs **fully locally with no external accounts** except the LLM,
which is already plugged in (DeepSeek via OpenRouter). Everything else — payments,
email, OAuth, voice — is a clean seam you "plug" later by setting env vars. Nothing
is gated: with no payment/email/OAuth keys, the whole Qora experience works.

Run it: see [`RUN_LOCAL.md`](RUN_LOCAL.md) (`scripts/dev.ps1`, login `demo@qora.app / demo1234`).

## Plug-point table

| Service | What it powers | State now | Plug it in by setting (in `backend/.env`) |
|---|---|---|---|
| **LLM** | Patient persona + calibrated judge (the core AI) | ✅ **Plugged** | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` (currently OpenRouter + `deepseek/deepseek-v4-flash`). Optional `LLM_JUDGE_MODEL`, `LLM_AUTHOR_MODEL`. |
| **Payments (Merchant of Record — Lemon Squeezy)** | Subscriptions, the freemium wall, entitlement | ⛔ **Off** (`BILLING_ENFORCED=false` → everything unlocked) | `BILLING_ENFORCED=true` + `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_WEBHOOK_SECRET`, `LEMONSQUEEZY_CHECKOUT_MONTHLY/ANNUAL/EXAM_PASS`, `LEMONSQUEEZY_PORTAL_URL`. Webhook + entitlement mapping already built (`app/domains/billing/`). |
| **Email (transactional)** | Verification / password-reset links | 📋 **Console mode** (links logged to the server console) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. Seam: `app/shared/mailer.py` (works with Resend/SES/Postmark/any SMTP). Verification flow itself is not wired yet (signup works without it). |
| **Google OAuth** | "Continue with Google" | ⛔ **Deferred** (button shows "coming soon") | Build the OAuth callback + `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`. Email/password auth works locally today. |
| **Voice (STT / TTS)** | Spoken interviews (optional beta) | ⛔ **Off** (degrades cleanly; transcript is source of truth) | `STT_API_KEY` (e.g. Groq Whisper) and/or `TTS_API_KEY` (e.g. ElevenLabs). |

## What "plugging" looks like in practice
1. Drop the key(s) into `backend/.env`.
2. Restart the backend (`uvicorn ...`). No code change for LLM / payments / email / voice — they read env at startup.
3. For payments, also flip `BILLING_ENFORCED=true` when you want the free wall active.
4. For Google OAuth, the only one needing new code is the callback handler (small, isolated).

## Prototype guarantees
- **No external key required to use it** (the LLM key is the only one needed, and it's set).
- **Design is byte-identical** to the original — the production CSS hash stays `index-Bj97HpXF.css`.
- **Legacy ophthalmology app preserved** ("Classic" edition), reachable from the Qora landing.
- Secrets live only in `backend/.env` (gitignored) — never committed.

> See also: [`AUDIT.md`](../AUDIT.md), [`SCHEMA_v2.md`](SCHEMA_v2.md), [`SCORING.md`](SCORING.md), [`REBRAND.md`](REBRAND.md), and the legal drafts in `docs/legal/`.
