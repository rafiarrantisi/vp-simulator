# Phase 5 — Load, Failure, Release Hardening

Fase: Phase 5
Status: PASS (dengan NOT RUN eksplisit: provider capacity, tunnel-disconnect propagation)

## Kondisi aktual yang ditemukan

- Jalur prod: Cloudflare Tunnel → uvicorn :8000 langsung. Caddy TIDAK di
  jalur qora (hanya `/qora/*` legacy) → §7.1s flush_interval Caddy NOT
  APPLICABLE, dengan bukti (Caddyfile + tunnel ingress config).
- TestClient portal tidak mempropagasikan disconnect ke server (server
  menyelesaikan stream) — disconnect driving diuji langsung pada generator
  (valid) bukan via close() portal.

## Perubahan dan alasan

- Outcome `cancelled` eksplisit pada kedua generator stream.
- Explicit child-`aclose()` di SELURUH rantai bridge (route wrapper → route
  gen → engine twin → SDK stream): investigasi membuktikan `async for`
  TIDAK menutup child generator saat parent di-cancel (bug real, kini
  diperbaiki + diuji sampai ke socket provider).
- (baru) `backend/loadtest/smoke.py`: uvicorn 1/2 worker, sqlite + stub,
  waves berulang, RSS/threads/first-chunk.

## Files/modules yang benar-benar disentuh

- `v2_router.py`, `v3_compat_service.py`, `engine_v2/v3.py` (cleanup Close)
- (baru) `tests/test_refactor_phase5_load.py`, `backend/loadtest/smoke.py`
- (baru) `docs/refactor/phase5-report.md` (file ini)

## Penyesuaian dari brief beserta buktinya

- Kapasitas provider TIDAK diklaim (stub only, §10.1b ditaati).
- 100-stream/50/25: dijalankan 10–25 konkuren (bukti), bukan 100 — ресурсов
  sesi ini tidak untuk 100-way; angka 100 dinyatakan NOT RUN, bukan PASS.
- Kill/restart recovery process: NOT RUN (butuh orkestrasi proses di luar
  lingkup sesi ini); desain recovery (durable acceptance + fencing +
  superseded) diuji logikanya.

## Invariants yang relevan

- Semua failure test mempertahankan kontrak error existing (422/409/404/503).

## Tests yang dijalankan beserta command/environment

- Baru phase5 (7): konkuren 10×2 waves, burst 25, cancel-midstream (+slot
  reuse + upstream close), missing variant 422, stale hash 409, mixed judge.
- Smoke uvicorn: 1 worker (10×2 waves, 0 err, first-chunk p50 ~0.3 dtk,
  threads plateau 16, RSS +3MB lalu datar) dan 2 worker (0 err, tree RSS
  255MB datar).
- Rollback rehearsal: suite stream/score hijau dengan QORA_REGISTRY_CACHE=0.
- Regresi terkonsolidasi akhir: 45 passed + 1 skipped (pg-only).

## Test result dan evidence location

- Semua hijau. Evidence: file ini + `backend/loadtest/smoke.py` + logs
  `qora.perf` pada captured tests.

## Baseline vs after, sample count, dan workload

| Uji | Hasil |
|---|---|
| 10 konkuren × 2 waves, stub instan | 0 err; threads 7→16 lalu plateau; RSS +3MB datar |
| Burst 25 submit | 0 err |
| Mixed judge + chat | 0 err; score 200 |
| Cancel mid-stream | outcome=cancelled; slot reuse OK; upstream closed |
| Missing/stale artifact | 422 / 409 eksplisit |
| Uvicorn 1 vs 2 worker | fungsional identik; tree RSS datar |

## Risiko/limit yang tersisa

- NOT RUN: provider-backed capacity/latency, 50–100 streams, tunnel
  disconnect propagation, kill/restart, 1-vs-2 worker benchmark formal.
- Sync engine path (fallback/tools) tidak menutup SDK stream se-eksplisit
  async (perilaku lama dipertahankan).

## Rollback dan hasil rehearsal bila berlaku

- Switch registry rehearsed hijau. Revert commit = rollback penuh (tanpa
  migrasi di semua fase). Laporan per fase mendokumentasikan tiap switch.

## Keputusan gate dan tahap berikutnya

- Gate Phase 5: **PASS** pada lingkup teruji. Paket rilis: branch
  `refactor/backend-perf` (commits Phase 0–5 + reports), siap review.
- Deployment/canary: MENUNGGU otorisasi eksplisit (sesuai kesepakatan).
