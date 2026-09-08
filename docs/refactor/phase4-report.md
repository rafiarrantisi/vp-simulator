# Phase 4 — Optimasi Scoring Tanpa Mengubah Report

Fase: Phase 4
Status: PASS (tanpa prompt/output compaction — tidak justified)

## Kondisi aktual yang ditemukan

- Stored-report fast path SUDAH ada (`completed + report` → return, XP aman).
  Celah nyata: request score konkuren ganda lolos fast path bersamaan →
  judge ganda + XP ganda (dbling progress).
- Satu judge call per scoring (dipertahankan; tidak didekomposisi).
- Tidak ada compaction/decomposition yang lolos gate evaluasi → TIDAK
  diaktifkan, sesuai §9.4 (yang gagal tetap nonaktif).

## Perubahan dan alasan

- (baru) `scoring/singleflight.py`: in-worker single-flight keyed
  `score:{session_id}` — request pertama jalan, sisanya berbagi hasil;
  progress/XP tercatat tepat sekali. Tanpa hang di semua path (future selalu
  settle; waiter-cancel hanya bunuh waiter). Cross-worker residual
  didokumentasikan (fast path stored menutupi retry).
- `v2_score`: fast path di luar flight; judge+persist+progress di dalam;
  milestone TurnClock (stored_hit / judge_call / shared counts).
- Tidak ada perubahan prompt, format output, rubric, atau normalize.

## Files/modules yang benar-benar disentuh

- (baru) `app/domains/scoring/singleflight.py`
- `app/domains/sessions/v2_router.py` (score path saja)
- tests (stored fast path, concurrent single-judge, isolation hygiene)

## Penyesuaian dari brief beserta buktinya

- Output compaction/decomposition/score-first/polling: DITOLAK (butuh paired
  evaluation + clinical gate yang di luar scope mekanis; manfaat tak terbukti).
- Single-flight in-worker saja (bukan DB claim): race lintas worker sempit
  (jendela skor pertama) dan idempotent via stored report; klaim atomik DB
  unjustified untuk jendela ini (§8.1h: jangan framework besar tanpa alasan).

## Invariants yang relevan

- Report bytes identik; XP sekali; retry semantics; judge fallback stub.

## Tests yang dijalankan beserta command/environment

- Baru: stored-skips-judge, concurrent-duplicate → 1 judge + identical 200s.
- Regresi: instruments + scoring_contract + scoring_v2 + fase12 (42 passed).
- Isolation: singleton settings/client + event-loop hygiene fixtures (menemukan
  + memperbaiki interferensi `asyncio.run` vs legacy `get_event_loop`).

## Test result dan evidence location

- Semua hijau (worktree venv, sqlite + stub).

## Baseline vs after, sample count, dan workload

| Metrik | Sebelum | Sesudah |
|---|---|---|
| Judge calls untuk 2 skor konkuren | 2 (+XP ganda) | 1 (+XP sekali) |
| Retry setelah complete | 0 calls (ada) | 0 calls (dipertahankan, diuji) |
| Prompt/output/normalize | — | byte-identik (tidak disentuh) |

## Risiko/limit yang tersisa

- Cross-worker duplicate judge (sempit; idempotent via stored).
- Owner-disonnect → waiters gagal cepat (terdokumentasi; retry aman).
- Durasi judge provider (47–86 dtk per audit) TIDAK berkurang — hanya
  duplikasi yang hilang; klaim perceived-fast DITOLAK (§9.4).

## Rollback dan hasil rehearsal bila berlaku

- Revert commit; tidak ada migrasi. Stored reports utuh.

## Keputusan gate dan tahap berikutnya

- Gate Phase 4: **PASS**. Lanjut Phase 5 (load, failure matrix, proxy path,
  rollback rehearsal, paket rilis).
