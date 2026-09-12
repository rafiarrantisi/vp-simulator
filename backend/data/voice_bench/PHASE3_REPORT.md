# Phase-3 Honest Old-vs-New Voice Benchmark (SAME provider, SMALL sample)

Date (UTC): 2026-09-12. Host: same Tencent host as 12-Sep baseline.
Provider frozen throughout: OpenCode zen `deepseek-v4-flash`
(base contains `opencode.ai`), temp 0.5, max_tokens 350, TTFT guard 7.0s,
total guard 20.0s, SDK retries 0 on patient (judge untouched), patient
overrides empty (inherit). Flag `qora.voice.adaptive` default OFF
(baseline 1200/3000 applies to all measured turns).

Sample: N=10 per flow (existing 10-turn harness precedent).
n=10 is INSUFFICIENT for p95 — p50/p90 (nearest-rank) only, no p95 claims.

Re-run (one command, from repo root):
`backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode transport`
`backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode segments --allow-paid`
`backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode all --allow-paid`
`backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode analyze`

Results JSONL (timings/lengths only, never content/keys):
`backend/data/voice_bench/phase3_transport_*.jsonl`,
`phase3_segments_old_*.jsonl`, `phase3_segments_new_*.jsonl`.
This report + script + JSONL are the ONLY files committed for Phase-3.

## 1. Old vs new architecture

OLD (frontend-coordinated, 2 round trips):
mic/endpoint (baseline 3000 interim / 1200 final) -> POST
`/api/v2/sessions/{id}/turns/stream` (Phase-1 adapter, guarded stream,
collect full text in browser) -> POST `/api/ai/tts/stream`
{text, session_id} (server resolves voice, framed PCM 4B-BE + int16 24kHz,
zero-len = EOF) -> progressive playback. Two HTTP round trips, client holds
full text between them.

NEW (server-orchestrated, 1 round trip, Phase-2):
mic/endpoint (same baseline constants, flag OFF) -> single POST
`/api/v2/sessions/{id}/turns/voice-stream`
{client_turn_id, transcript} (idempotency key + body hash, untrusted telemetry
sanitized) -> atomic accept (ledger UNIQUE fence) -> ONE full reply via the
SAME Phase-1 adapter/guards (no pipelining) -> fenced winner commit (durable
BEFORE any PCM) -> ONE server-side `stream_pcm` -> ONE typed framed stream
(`app/voice/frames.py` v1: metadata -> final-text -> pcm* -> done; error
frames terminal, no done on truncation). Disconnect before commit cancels
(no patient row, same key adopts); after commit recovery replays stored
winner with no new inference. Text-chat (`/turns`, `/turns/stream`) and
scoring (`/score`) contracts untouched.

## 2. Exact files changed across all 3 phases (vs 851117b)

Phase-1 (19ebb93, foundation, no provider change):
`backend/.env.example`, `backend/app/config.py` (PATIENT_LLM_* scope,
inherit by default), `backend/app/domains/ai/router.py` (TTS audit note),
`backend/app/domains/sessions/v2_router.py`, `v3_compat_service.py`,
`backend/app/main.py` (lifespan prewarm), `backend/app/rag/engine_v2.py`,
`engine_v3.py` (patient seam), `backend/app/rag/llm.py` (retry map + attempt
timeline, guards 7/20 unchanged, SDK destack patient-only),
`backend/app/rag/patient_provider.py` (NEW seam),
`backend/app/shared/admission.py` (named patient limiter, same 64 bound),
`observability.py`, `perf_marks.py`, `perf_sink.py` (NEW sink),
`backend/scripts/perf_summary.py` (NEW CLI), `backend/tests/conftest.py`,
`test_refactor_phase0_baseline.py`, `test_refactor_phase2_instruments.py`,
`test_refactor_phase5_load.py`, `test_voice_phase1_foundation.py` (NEW).

Phase-2 (aec67ad, server orchestration, flag OFF):
`backend/app/domains/sessions/models.py` (VoiceTurnLedger),
`turn_acceptance.py` (accept_voice_turn/commit/read fences),
`v2_router.py` (POST turns/voice-stream), `voice_stream.py` (NEW service),
`backend/app/voice/frames.py` (NEW protocol),
`backend/tests/test_voice_phase2_server_orch.py` (NEW),
`sistemnya/qora-v2.jsx`, `sistemnya/qora-voice.jsx` (single-flight sender,
framed parser, adaptive state machine behind flag, baseline 3000/1200
unchanged when OFF).

Phase-3 (this benchmark, no prod code changes):
`backend/scripts/voice_bench_phase3.py` (NEW harness),
`backend/data/voice_bench/phase3_*.jsonl` (NEW results),
`backend/data/voice_bench/PHASE3_REPORT.md` (this file).

Guard/timeout value drift vs 851117b: ZERO. persona_max_tokens 350, judge
8000, models unchanged, TTFT 7.0 / total 20.0, SDK timeout 120.0, admission
64/1/8 + 10s wait + 60s idle, temperature 0.5 — all identical; diff shows
only additive scope/seam/instrument/fence code.

## 3. Latency tables (N and method)

Method transport (FREE): stub LLM (AsyncStubLlmClient) + deterministic stub
PCM for BOTH flows (injected in an isolated /tmp uvicorn on an ephemeral
localhost port, isolated sqlite file, rate limiter disabled on that server
only), one unmeasured warmup per flow, then N=10 measured turns per flow in
one session each (same 10 synthetic ID inputs, distinct per turn to avoid
dedup). Metrics: submit->first-byte and total over real HTTP. Cleanup:
DELETE sessions/turns/ledger/users from the isolated file, verify zero,
remove file. Prod rows touched: 0.

Transport (stub, localhost HTTP, N=10 each, warm):
| metric | old 2-RTT p50 | old p90 | new 1-RTT p50 | new p90 |
|---|---|---|---|---|
| submit->first-audio (old) / first-byte (new) | 56.5 ms | 64.3 ms | 53.4 ms | 57.5 ms |
| total (old = LLM stream + TTS stream; new = single framed stream) | 57.9 ms | 65.7 ms | 55.8 ms | 59.7 ms |
Raw totals old: 56-66 ms (one 159 ms outlier, turn 2); new: 54-60 ms.
Saving: ~2 ms p50, ~6 ms p90 localhost. PLAINLY: no measurable improvement
at localhost stub scale beyond one extra HTTP round trip (~2 ms); the ADR
0.1-0.4 s browser<->backend RTT estimate for real/mobile networks is NOT
proven here.

Method segments (PAID, capped): in-process (TestClient setup only for
auth/session; timed spans are direct service calls in an isolated sqlite
file, never prod), same 10 inputs + frozen case `em_anaphylaxis_001`/lang
`id`, sequential turns per flow (histories diverge after turn 1 due to
sampling, documented). Old: accept_turn -> `engine_v2.astream_respond`
(route v2_turn_stream, TTFT+full timed) -> finalize -> `stream_pcm` on the
ACTUAL reply (TTFA = first yielded PCM chunk in worker thread, full =
synthesis end, one billed call per reply). New: accept_voice_turn ->
identical streaming primitive with route voice_stream (same adapter/guards
as `run_voice_llm`/arespond, TTFT preserved without a second billed call)
-> commit_voice_winner -> same `stream_pcm`. Transition gap =
full-text-ready -> TTS-RPC-start (server-local handoff; THE eliminated-RTT
metric in-process). Endpointing constant recorded per turn:
baseline_1200_3000_flagOFF. Timings + lengths only.

Segments — LLM (real OpenCode zen deepseek-v4-flash):
| flow | N attempted | N ok | TTFT p50 | TTFT p90 | full p50 | full p90 | failures |
|---|---|---|---|---|---|---|---|
| old | 10 | 9 | 4244 ms | 9880 ms | 5653 ms | 9938 ms | 1 TimeoutError |
| new | 10 | 8 | 2281 ms | 6117 ms | 2335 ms | 6562 ms | 2 TimeoutError |
Prior 12-Sep in-process baseline (same host): TTFT p50 ~4600 ms p90 ~12100
ms. Current old (4244/9880) reproduces it within small-sample noise.
PLAINLY: new median appears lower but distributions overlap heavily, N
differs (9 vs 8 ok), failure counts differ (1 vs 2), and the provider/guards
are identical by construction — NO measurable LLM improvement proven or
claimed. Apparent gap is small-sample noise.

Segments — TTS (real Gemini `stream_pcm`, one call per actual reply):
| flow | N ok | TTFA p50 | TTFA p90 | full p50 | full p90 |
|---|---|---|---|---|---|
| old | 9 | 840 ms | 1609 ms | 3302 ms | 7547 ms |
| new | 8 | 899 ms | 1440 ms | 2000 ms | 4020 ms |
Prior baseline TTFA p50 ~900 ms. Reproduced (840/899). PLAINLY: no TTS win;
same synthesis path, overlapping tails, small N.

Segments — transition gap (full-ready -> TTS-start, in-process):
old p50 15.8 ms p90 18.2 ms (n=9); new p50 14.9 ms p90 19.3 ms (n=8).
PLAINLY: identical server-local handoff (~15 ms); the eliminated
browser<->backend round trip is a TRANSPORT effect (see above, ~2 ms
localhost), not an inference effect.

Endpointing (ANALYTIC ONLY, no device measurement):
baseline (flag OFF): interim 3000 ms / final 1200 ms. Adaptive (flag logic,
JS `qvEndpointNext` + python mirror, identical thresholds): final-quiet
500 ms + stable 100 ms; interim-quiet 800 ms + stable 400 ms + stop grace
250 ms; hesitation hold 1200 ms; manual flush <=250 ms. Derived timer deltas
(ADR §3 rank 2): final-mature path ~0.6-0.9 s, interim-stable path ~1.5-2.0
s vs baseline. HONESTLY: mic-level savings need device QA (STT finalization,
acoustic silence vs recognition-event timers, capture compat, clipping
rates with 200/500/800/1200/2000 ms pause fixtures, Android cohorts). NO
measured endpointing wins are claimed.

Statistics honesty: N=10 attempted per flow (transport 10/10 ok both flows;
segments 9/10 and 8/10 ok for LLM/TTS). Nearest-rank p50/p90 only. n=10 is
INSUFFICIENT for p95 — no p95 values are reported or implied. Failures are
counted (not hidden): 15% LLM TimeoutError overall (3/20), consistent with
the known ~12 s tail + 7 s guard x2-attempt policy.

## 4. Regressions found

- `test_voice_phase1_foundation.py` + `test_voice_phase2_server_orch.py`:
33 passed.
- Touched-module suites: `test_refactor_phase0_baseline`,
`test_refactor_phase2_instruments`, `test_refactor_phase3_acceptance`,
`test_v2_runtime`, `test_scoring_contract`: 44 passed, 1 skipped, 3 failed.
The 3 failures (`test_v2_outbound_request_shape`,
`test_v3_outbound_request_shape`, `test_async_outbound_matches_sync_golden`)
are PRE-EXISTING stale goldens expecting max_tokens 1024 while config has
been 350 since 7441999 (ancestor of 851117b, before voice phases); test file
diff since 851117b is only singleton-cleanup lines. Not regressions.
- `test_scoring_v2`, `test_fase6_session_hardening`,
`test_refactor_phase5_load`: 20 passed.
- Text-chat and scoring contracts: untouched (separate routes; suites green
above). No new regressions from Phase-1/2/3.

## 5. Paid-call count actually used

Transport: 0 paid (stub LLM + stub PCM, localhost).
Segments: 10 logical LLM turns per flow (cap 12/flow) = 20 logical LLM;
TTS only for actual replies: old 9, new 8 (3 turns failed at LLM with
TimeoutError before any TTS). Failed LLM turns each consumed the frozen
2-attempt guarded policy (7 s TTFT x fresh-lane retry); billed attempts on
cancelled tries are provider-side and reported as unknown (not zero).
Total billed logical calls: 20 LLM + 17 TTS. No other paid calls were made.

## 6. ADR recommendations DELIBERATELY not implemented (with one-line reason each)

- Provider migration (OpenRouter pinned Wafer / DeepSeek direct / Gemini
fallback as patient primary): requires full §7 gates (200-1000+ req/route,
multi-day/peak coverage, quality/adversarial suites); this phase is a
SAME-provider orchestration comparison only.
- Sentence pipelining (partial-response -> early TTS): median LLM
first-to-full gap bound ~118 ms on prior data — too small for v1
complexity/prosody/commit-gating risk.
- Hedge/circuit-breaker (1.2 s trigger, 2.8 s group deadline, 5-fail/30 s
breaker): tail-control for a NEW route only after its attempt distribution
is measured; would confound the old-vs-new comparison here.
- Audio guard (getUserMedia AudioWorklet energy gate): needs device-cohort
capture-compat QA (dual-stream mic, CPU/battery, worklet availability);
ships as null plugin slot with recognition-events-only v1.
- Admission changes (100 ms voice wait, 4 logical/8 outbound per worker):
capacity tuning needs offered-load evidence; kept at 64/10 s to isolate the
orchestration effect.

Also not done (same rationale class): STT streaming rewrite, prompt/history
compression, semantic endpoint model, Redis/Kafka/GPU/websocket infra, Judge
or rubric changes, client-held secrets — all out of scope for the
orchestration comparison and gated on future evidence.
