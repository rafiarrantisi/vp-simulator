# FASE 6 — Conversation / Voice / PF / Investigation / Session Hardening

Constraint: keep the approved Qora V2 session experience (bubbles, typed input,
mic interaction, timer, Exam CTA, PF, assess). No new chat, no new mic.
V3 engine receives transcript/text only and never knows the mic implementation.
UI changes limited to hardening/spacing/error-state.

## What was hardened

Backend (`app/domains/sessions/hardening.py`, wired into `v2_router` + `v3_compat_service`):
- completed-session guard: turns/stream/pf → 409 once `status=completed`
  (reopen via stored report; score stays idempotent).
- duplicate-send idempotency: identical user-text retry returns the stored
  patient reply, no new rows (covers double-Enter, interrupted-stream retry,
  stream→fallback double-persist).
- canonical vitals: single `format_vitals_canonical`/`general_with_vitals`
  formatter from the persisted variant; PF fallback can never diverge from
  answer key / judge ground truth / scorer truth.
- PF stays request-based / revealed-area only; investigations stay same-variant
  (answer key names == variant names == judge ground truth names).
- refresh/resume keeps exact patient/variant/persona/content version
  (frozen variant + canonical hash, existing rule, now pinned by test).

Frontend (`sistemnya/qora-v2.jsx`, bundle regen → `src/main.jsx`):
- duplicate-send race guard (`sendInflightRef`) + completed read-only banner.
- sticky input dock with `env(safe-area-inset-bottom)` (bottom-nav safe),
  `100dvh` retained, scroll anchor `scrollMarginTop: 72` for sticky header.
- long-message wrapping (`overflowWrap/wordBreak: break-word`), wider mobile
  bubble cap (86%), `aria-live` streaming status ("Patient is replying…"),
  `role=alert` errors, input `aria-label`.
- stream failure keeps the typed/voice text in the input for retry and shows
  the backend error; fallback POST passes `input_type` so voice-vs-text
  metering stays correct; Exam/Assess stays disabled while `busy`.
- mic path unchanged: existing `QV2MicButton` (browser STT) + auto-send text;
  no new recorder, no V3-mic coupling. Server MediaRecorder path remains
  unused dead code (not resurrected — avoids a second mic).

## Evidence

- `backend/tests/test_fase6_session_hardening.py`: 2 passed (isolated sqlite,
  stub LLM) — completed-guard + dedupe + vitals canonical + investigation
  consistency + frozen-variant resume.
- `tests/test_phase_b_v3_compat.py`: 11 passed (no regression on V2 contract).
- `regression/fase6/network/frontend_hardening.json`: static markers for all
  8 frontend hardening items present in source + regenerated bundle.
- Real-browser desktop/mobile + real-mic speech→transcript→auto-send:
  NOT reproducible headless here (no browser/mic in this env) — required
  manual smoke before prod cutover: refresh/resume live session, OSCE full,
  blind no-leak, mic permission denied + STT-fail recovery, interrupted
  stream retry, duplicate send, completed reopen, PF state, bottom-nav overlap,
  keyboard-open input visibility.
