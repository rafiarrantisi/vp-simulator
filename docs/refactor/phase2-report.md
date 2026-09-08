# Phase 2 — Async Inference, Streaming, Cancellation

Fase: Phase 2
Status: PASS (dengan NOT RUN eksplisit untuk load/proxy-path)

## Kondisi aktual yang ditemukan

- Rantai sync penuh: route `def` → generator `def` → engine sync →
  OpenAI sync SDK + `time.sleep` retry. Thread terpegang selama 5–120 dtk
  wait per stream (membuktikan urgensi, bukan mengukur load).
- OpenAI SDK 2.46.0: `AsyncOpenAI` tersedia; streaming via
  `await create(stream=True)` + `async for` + `aclose()` (terverifikasi di harness).
- Auth chain: `get_current_user(db=Depends(get_db))` — sesi auth terpisah dari
  sesi route; keduanya teardown-after-stream (temuan Phase 0).

## Perubahan dan alasan

- `llm.py`: `_is_transient` + `_with_retry_async` (budget identik, sleep nonblocking);
  `_chat_kwargs` builder tunggal sync/async (paritas by construction);
  `_openrouter_extra` shared; `AsyncStubLlmClient`; `_OAI_ASYNC`
  (kwarg/guard/retry identik + `aclose()` di finally); `get_async_llm_client`
  per-worker + `open_async_llm`/`close_async_llm` lifespan. Sync adapter UTUH
  sebagai fallback artifact + dipakai qa/tools.
- `engine_v2/v3`: `astream_respond` + `arespond` twins (assembly/params identik).
- Routes: `v2_turn_stream`, `v2_turn`, `v2_score` → async; `v3c.stream_turn`,
  `v3c.turn`, `v3c.score` → async. `db.close()` eksplisit setelah preflight
  commit (tidak ada koneksi route yang dipegang selama inference — dibuktikan
  test pool). Final persist via bounded thread unit (`db_limiter`).
- Admission (§7.1f/g): semaphore conversation 64 + judge 1 per worker
  (env override), acquire deadline 10 dtk → 503, idle antar-chunk 60 dtk,
  SDK total timeout dipertahankan. Judge semaphore di dalam twins.
- `test_phase_b_v3_compat` engine-failure test dialihkan ke async twin
  (assertion perilaku IDENTIK: error surface, tanpa fallback V2).
- Lifespan: pre-open async client + init admission + registry prewarm;
  shutdown menutup transport.

## Files/modules yang benar-benar disentuh

- `app/rag/llm.py`, `app/rag/engine_v2.py`, `app/rag/engine_v3.py`,
  `app/rag/judge_v2.py` (+aevaluate), `app/rag/judge_v3.py` (+aevaluate),
  `app/domains/sessions/v2_router.py`, `app/domains/sessions/v3_compat_service.py`,
  `app/main.py`, (baru) `app/shared/admission.py`, `app/shared/perf_marks.py`,
  tests + fixtures + `backend/.gitignore` (venv symlink).

## Penyesuaian dari brief beserta buktinya

- Preflight DB tetap inline sync (bukan thread unit): disengaja, interim —
  memindahkannya tanpa acceptance atomik (Phase 3) berisiko memecah batas
  transaksi. Hold ~0.2–0.5 dtk tercatat jujur sebagai residual.
- Sesi auth masih dipegang selama stream (milik dependency shared) — Phase 3
  (konsolidasi snapshot) menghilangkannya.
- Rollback = revert deploy (sync engines tetap ada & teruji), bukan runtime
  switch — diizinkan §7.5 (deployment rollback). Switch hanya untuk registry.
- Idle deadline diimplementasi (60 dtk); inter-content vs transport dibedakan
  di dokumentasi kode.

## Invariants yang relevan

- Wire contract: plain-text chunks, urutan, error string V3 / propagasi V2,
  status HTTP, dedup replay — semua dipertahankan, dibuktikan byte-identical
  pada stub replay + suite existing.
- Disclosure/prompts/params: golden sync vs async identik (shared builder).
- Scoring semantics: twins memakai normalize/fallback yang sama.

## Tests yang dijalankan beserta command/environment

- Baru: phase0 async parity (kwargs, stream replay, aclose), phase2
  instruments (3) + route behaviors (idle, pool-release, health-during-stream,
  score V2/V3, judge parity+release, cancel-release, lifespan).
- Diubah minimal: phase_b engine-failure (patch target async, assertion sama).
- Suite existing pada kode async: fase6 + phase_b (13), fase10 + fase12 +
  mentor + scoring_contract + scoring_v2 (60), fase8 + hybrid + phase13 (64
  sebelumnya), leakage/rag/medication (24).
- Semua: worktree venv, sqlite terisolasi + stub LLM via conftest, kecuali
  2 timing manual LLM di main tree (Phase 0).

## Test result dan evidence location

- Semua hijau. Evidence: goldens `tests/fixtures/perf_phase0/`, log milestone
  `qora.perf` (contoh padaaptured test), laporan ini.

## Baseline vs after, sample count, dan workload

- Thread menunggu LLM per stream: 1 → 0 (by construction; diuji via
  health-responsiveness + pool assertions, bukan load test).
- Pool checkout selama LLM wait: ≥1 (sesi route) → 0 (sesi auth tersisa 1;
  dibuktikan event listener).
- Perilaku single-request: identik (byte parity stub).
- Load/concurrency EyE: NOT RUN (Phase 5).

## Risiko/limit yang tersisa

- NOT RUN: Caddy/tunnel flush & disconnect propagation (§7.1s, §7.3) —
  butuh uji jalur proxy aktual (Phase 5 §10.1i).
- NOT RUN: load 1/10/25/50/100 streams, burst, mixed judge load, slow-reader
  leak, kill/restart recovery (Phase 5).
- NOT RUN: benchmark 1 vs 2 worker (§3.2).
- Preflight sync ±0.5 dtk block loop sesekali; sesi auth hold 1 koneksi —
  keduanya tutup di Phase 3.
- Env deadlines/limits adalah starting points, bukan hasil benchmark.

## Rollback dan hasil rehearsal bila berlaku

- Revert commit mengembalikan sync penuh (sync engines tidak dihapus, suite
  sync tetap hijau). Registry switch independen. Lifespan additions guarded.
- Belum rehearsal deploy (otorisasi terpisah).

## Keputusan gate dan tahap berikutnya

- Gate Phase 2: **PASS** untuk equivalence/async/cancellation/admission pada
  lingkup unit+integration terisolasi. Klaim kapasitas/load eksplisit
  ditunda ke Phase 5.
- Lanjut Phase 3 (konsolidasi DB + transaksi atomik + tutup H1 auth-session).
