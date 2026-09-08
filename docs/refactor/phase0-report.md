# Phase 0 — Inventaris, Baseline, Contract Freeze

Fase: Phase 0
Status: PASS (dengan catatan NOT MEASURED eksplisit di bawah)

## Kondisi aktual yang ditemukan

- Branch kerja terisolasi: `refactor/backend-perf` (worktree `/home/ubuntu/vp-simulator-refactor`),
  base HEAD 2387a14. Tidak ada AGENTS.md di repo; instruksi berlaku = brief refactor + source of truth.
- Worktree BARU tanpa `.env` (prod creds tidak ikut); bukti DB memakai engine scratch read-only.
- Versi terpasang (venv, Python 3.11.15): FastAPI 0.139.2, Starlette 1.3.1, AnyIO 4.14.2,
  Uvicorn 0.51.0, SQLAlchemy 2.0.51, OpenAI SDK 2.46.0, Pydantic 2.13.4, httpx 0.28.1,
  psycopg2-binary 2.9.12, greenlet 3.5.3, pytest 9.1.1. Tidak ada asyncpg/psycopg3.
- Call graph terverifikasi:
  - `POST /api/v2/sessions/{id}/turns/stream` → `v2_router.v2_turn_stream` (def sync).
    V2: preflight di request `db`, commit user turn, lalu `gen()` sync streaming
    `engine_v2.stream_respond` → `get_llm_client().stream` → OpenAI sync SDK.
    Finalisasi di `SessionLocal()` fresh dalam generator. `s.language` dibaca di
    dalam `gen()` pada ORM object request-scoped (aman dari lazy-load karena
    `expire_on_commit=False`, terverifikasi di `database.py:37`).
  - V3 (`content_schema == "new"`): `v3c.stream_turn` — `_frozen_variant()` memanggil
    `default_registry()` (full `CaseRegistry.from_dir()`) **setiap turn**, juga di
    `turn()`, `get_turns()`, dan 3 call-site lain.
  - `get_db()` = yield dependency tanpa scope khusus; pool
    pool_size=10/max_overflow=10/pre_ping/recycle=300/timeout=10.
  - LLM adapter: OpenAI sync client, `timeout=120.0`, retry 3x `time.sleep`
    (blocking), guard `reasoning:{enabled:False}` untuk OpenRouter, meaningful-content
    guard me-retry pesan "overload".
- Caddy: `reverse_proxy` polos, tanpa `flush_interval` (default berlaku; perilaku
  cancellation/flush عبر proxy BELUM diuji — dicatat untuk Phase 2 §7.1s).

## Perubahan dan alasan

- Hanya file BARU (nol modifikasi tracked): `backend/tests/test_refactor_phase0_baseline.py`
  (deterministic replay harness + golden fixtures di `tests/fixtures/perf_phase0/`)
  dan dokumen ini. Aman terhadap pekerjaan lain.

## Files/modules yang benar-benar disentuh

- (baru) `backend/tests/test_refactor_phase0_baseline.py`
- (baru) `backend/tests/fixtures/perf_phase0/{v2_outbound,v3_outbound,v2_stream,dependency_lifecycle}.json`
- (baru) `docs/refactor/phase0-report.md`

## Penyesuaian dari brief beserta buktinya

- §5.1a (AGENTS.md): tidak ada di repo → diganti source of truth + brief. Non-blocking.
- §2.5/H1 (koneksi tertahan selama stream): DIBUKTIKAN, bukan asumsi. Test
  `test_yield_dependency_teardown_after_stream_body` pada FastAPI/Starlette
  terpasang membuktikan urutan setup → first_chunk → second_chunk → teardown.
  Artinya klaim docstring `v2_turn_stream` ("db is closed by the time the
  streaming body runs") SALAH pada versi ini: request Session (dan koneksi pool
  yang sudah checkout) dipegang selama seluruh LLM stream. Ini temuan utama
  yang memotivasi Phase 3.
- Angka audit dipakai sebagai konteks, bukan baseline resmi; semua baseline di
  bawah diukur ulang di sini.

## Invariants yang relevan

- Disclosure/canonical truth, tenant isolation, API/stream contract, scoring
  semantics: tidak disentuh fase ini; dijaga oleh suite existing yang lolos
  (lihat Tests).

## Tests yang dijalankan beserta command/environment

- `pytest tests/test_refactor_phase0_baseline.py` (worktree, venv, stub transport,
  tanpa network/paid call): **6 passed**. Mencakup golden outbound V2/V3
  (model deepseek/deepseek-v4-flash, temperature 0.5, max_tokens 1024,
  extra_body reasoning-disabled, system-first role order), stream replay
  equivalence (chunks join == generate), empty-content guard, lifecycle bukti.
- Suite existing: `test_leakage_p1 + test_rag + test_fase6_session_hardening +
  test_medication_contract`: **24 passed**.

## Test result dan evidence location

- Goldens: `backend/tests/fixtures/perf_phase0/*.json` (di worktree).
- Lifecycle proof: `dependency_lifecycle.json` (`teardown_after_body: true`).

## Baseline vs after, sample count, dan workload

Belum ada perubahan perilaku (fase inventaris). Baseline terukur:

| Metrik | Hasil | Sampel |
|---|---|---|
| Registry build (`default_registry()`) | 8.2–8.4 dtk, 122 fam / 264 var | 2x, venv lokal |
| V2 case load | 20 ms cold / 12 ms warm | 2x |
| DB SELECT 1 cold (fresh engine, connect+checkout, no pre-ping) | 1.26 dtk + exec 145 ms | 1x |
| DB SELECT 1 warm (pooled reuse) | ~217 ms | 3x |
| LLM 600-token call (real key, main tree, manual) | 2.2 dtk | 1x (preliminer) |
| LLM 1600-token call (real key, main tree, manual) | 3.3 dtk | 1x (preliminer) |

## Risiko/limit yang tersisa

- NOT MEASURED: concurrent baseline, browser TTFT, provider p99, judge duration,
  memory PSS/eviction, Caddy/tunnel flush & disconnect propagation, pooler
  prepared-statement behavior (belum relevan — driver sync).
- Warm SELECT 217 ms menunjukkan latency pooler/jaringan mendominasi, bukan query —
  konsolidasi preflight (Phase 3) bernilai lebih dari kelihatannya.
- Registry 8.2 dtk > angka audit 6 dtk (mesin sama, waktu berbeda) — target Phase 1 tetap:
  nol rebuild di hot path.

## Rollback dan hasil rehearsal bila berlaku

- Tidak ada perubahan perilaku → tidak perlu rollback. Baseline evidence dipertahankan.

## Keputusan gate dan tahap berikutnya

- Gate Phase 0: **PASS**. Call graph + versi terverifikasi, kontrak executable,
  baseline reproduksibel, unknowns eksplisit.
- Lanjut Phase 1: hilangkan registry rebuild per-turn. Kandidat utama = pakai
  frozen snapshot session bila lengkap, atau `cached_registry()` existing sebagai
  hotfix bila parity/immutability/memory lolos — diputuskan setelah uji §6.1a–c.
