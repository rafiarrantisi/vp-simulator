# Phase 1 — Registry Hotfix

Fase: Phase 1
Status: PASS

## Kondisi aktual yang ditemukan

- Session TIDAK menyimpan full frozen snapshot — hanya `variant_id` +
  `variant_canonical_hash` + `persona` (JSON). §6.1a: yang ada adalah variant_id
  yang menunjuk content mutable → butuh cached resolution, bukan snapshot-direct.
- Dua `default_registry()` ternyata kode identik (`CaseRegistry.from_dir()`,
  root sama) — parity by construction; bedanya hanya memoization.
- Hot path memanggil full rebuild 8.2 dtk di: `_frozen_variant` (setiap turn,
  get_turns, judge), `library_cards` (setiap buka katalog), `start` (setiap
  mulai sesi V3).
- Tidak ada mutasi objek registry di hot path (engine/derive/read-only;
  `_strip_persona` copy-dulu). `canonical_hash()` deterministik.

## Perubahan dan alasan

Hotfix terkecil yang aman (§6.1b): 3 call-site di `v3_compat_service.py`
(`library_cards`, `start`, `_frozen_variant`) dialihkan ke SATU instance
`cached_registry()` yang sama dengan jalur progress/mentor existing.
Plus: double-checked `threading.Lock` anti-stampede, switch rollback
`QORA_REGISTRY_CACHE=0`, prewarm di lifespan (guarded, non-fatal).
Hash check `variant_canonical_hash` dipertahankan apa adanya.

## Files/modules yang benar-benar disentuh

- `backend/app/domains/sessions/progress_adapter.py` (lock + env switch)
- `backend/app/domains/sessions/v3_compat_service.py` (3 call-site → cache)
- `backend/app/main.py` (prewarm lifespan)
- (baru) `backend/tests/test_refactor_phase1_registry.py`

## Penyesuaian dari brief beserta buktinya

- Target §6.1d/g (precompiled snapshots, byte budget): DITUNDA dengan alasan —
  hotfix memoization menghapus ~8 dtk dengan diff minimal dan parity trivial;
  snapshot precompile tetap opsi bila profiling nanti menuntutnya. Budget 8 MiB:
  terukur 8.0 MiB peak-delta (ru_maxrss, peak-based; retained aktual ≤ itu).
- Prewarm +8 dtk startup/worker diterima (systemd timeout 90 dtk; guarded).

## Invariants yang relevan

- Disclosure/canonical truth: prompt bytes identik 264 varian × 2 bahasa.
- Frozen revision: hash check + determinisme dipertahankan; tidak ada re-freeze.
- Tenant: tidak ada override institusi pada registry (konten global, terverifikasi
  tidak ada cabang tenant di loader).

## Tests yang dijalankan beserta command/environment

- `pytest tests/test_refactor_phase1_registry.py` (worktree, venv, tanpa network):
  **6 passed** — zero rebuild, full-corpus parity, stabilitas objek, single build
  konkuren (8 thread), rollback switch, memory smoke.
- Suite existing pada kode refactor: hybrid_judge + phase_b_v3_compat +
  fase6_session_hardening + fase8_unified_progress + phase13_integration:
  **64 passed** (DB sqlite terisolasi + stub LLM via conftest).

## Test result dan evidence location

- `docs/refactor/phase0-report.md`, file ini, goldens `tests/fixtures/perf_phase0/`.

## Baseline vs after, sample count, dan workload

| Metrik | Sebelum | Sesudah | Sampel |
|---|---|---|---|
| Registry builds per V3 turn | 1 (8.2 dtk) | 0 (cache hit) | counter test |
| Prompt bytes 264 varian EN+ID | — | identik 100% | 528 pasang |
| Concurrent cold miss (8 thread) | 8× build | 1× build | 1 run |
| Retained peak-delta | — | 8.0 MiB | 1 run |
| Pre-LLM V3 (proyeksi) | ~7–8 dtk | ~0 | dihitung, bukan diukur E2E |

## Risiko/limit yang tersisa

- ru_maxrss peak-based, bukan retained accounting presisi (Phase 5).
- Cold build pertama/worker tetap ~8 dtk (prewarm di boot; lazy+lock bila prewarm gagal).
- E2E pre-LLM latency belum diukur ulang dengan timer instrumen (§11 milestone
  menyusul Phase 2).
- TIDAK di-deploy ke prod pada fase ini (otorisasi canary/deploy terpisah).

## Rollback dan hasil rehearsal bila berlaku

- `QORA_REGISTRY_CACHE=0` mengembalikan perilaku legacy per-call (diuji:
  tiap call rebuild, hash tetap sama). Prewarm failure non-fatal (try/except).
- Rollback = revert 3 file + restart; tidak ada migrasi/skema.

## Keputusan gate dan tahap berikutnya

- Gate Phase 1: **PASS**. Lanjut Phase 2 (async inference + streaming +
  cancellation) setelah milestone instrumentasi §11 dipasang.
