# Phase 3 — Konsolidasi Database dan Transaksi Atomik

Fase: Phase 3
Status: PASS (dengan residual eksplisit: sesi auth + legacy writers + pg-only concurrency)

## Kondisi aktual yang ditemukan

- Preflight per turn: `_owned` GET + `_history` SELECT + `_next_turn_no` COUNT +
  INSERT + commit (≈5 exchanges) + sesi route dipegang sampai teardown.
- Tidak ada unique constraint (session_id, turn_number) → race numbering
  hanya dicegah secara struktural (lihat di bawah).
- `get_current_user` mengembalikan ORM yang juga dipakai writers
  (`user.profile.total_sessions += 1` lalu `db.commit()` di sesi route).
  Mengubah lifecycle sesi auth akan mengubah perilaku writers tersebut —
  DILARANG oleh prioritas correctness (§0). Sesi auth tetap dipegang.
- Legacy V1 (`sessions/router.py`), native `v3_service`, websocket-stub punya
  semantics error/status berbeda (mis. legacy tanpa `ensure_turnable`) →
  tidak dimigrasi; koeksistensi didokumentasikan sebagai residual.
- `FOR UPDATE` di-drop diam-diam oleh dialek sqlite (terverifikasi via
  compile) — serialisasi adalah properti PostgreSQL.

## Perubahan dan alasan

- (baru) `turn_acceptance.accept_turn`: SATU transaksi — SELECT session
  FOR UPDATE → revalidasi ownership/status (error/messages identik) →
  history (fungsi existing) → dup check (fungsi existing) → numbering
  MAX+1 dalam lock (tanpa COUNT ekstra) → INSERT user turn → commit.
  Mengembalikan TurnSnapshot DTO beku (termasuk persona + canonical hash).
- (baru) `turn_acceptance.finalize_patient_turn`: fencing — advisory xact
  lock per session (PostgreSQL; diskip di dialek lain) → lewati insert bila
  turn >= turn_no sudah ada (`superseded`) → insert + commit (+ billing
  opsional). Tidak pernah regenerate LLM.
- 4 penulis hot-path (V2/V3 stream + fallback) dialihkan; V3 service
  sekarang murni snapshot-in (tidak menyentuh request db sama sekali).
- Sequencing/billing dipertahankan: 2 commit terpisah dengan semantics
  durability identik (turn tetap tersimpan bila billing gagal).
- Pool knobs env (`QORA_POOL_SIZE/OVERFLOW`, default 10/10 identik) —
  tunability tanpa klaim tuning.
- Mikro-deviasi terdokumentasi: dup-check mendahului validasi frozen
  variant (replay tanpa inference; validasi tetap di setiap turn baru).

## Files/modules yang benar-benar disentuh

- (baru) `app/domains/sessions/turn_acceptance.py`
- `app/domains/sessions/v2_router.py` (4 call-site → accept/finalize)
- `app/domains/sessions/v3_compat_service.py` (snapshot-in)
- `app/database.py` (pool knobs, default identik)
- (baru) `backend/tests/test_refactor_phase3_acceptance.py`

## Penyesuaian dari brief beserta buktinya

- Tanpa single-statement snapshot (raw SQL agregat beda dialek sqlite/pg) —
  2 statement dalam 1 txn (§8.1h: solusi sederhana dipertahankan bila
  perubahan besar unjustified). Round-trip dihitung jujur di bawah.
- Tanpa migrasi/fungsi SQL (§8.1d/u: alembic heads sedang blocked; advisory
  lock + row lock tanpa DDL mencapai fencing yang dibutuhkan).
- Tanpa driver async (§8.1m: psycopg2 dipertahankan; thread units bounded
  untuk finalisasi; alasan + evidence kompatibilitas tercatat — tidak ada
  perubahan driver = tidak ada risiko pooler baru).

## Invariants yang relevan

- Tenant/ownership: 404 identik termasuk forged IDs (diuji).
- Ordering: turn numbers naik ketat dalam lock; history order dipertahankan.
- Idempotency: retry teks identik → `_deduped` tanpa insert ganda (diuji).
- Stored report:Idempotency score path tidak disentuh.
- Billing sequencing: identik (diuji via guarded cost path existing).

## Tests yang dijalankan beserta command/environment

- Baru `test_refactor_phase3_acceptance.py`: 5 passed + 1 skipped
  (pg-only concurrency, alasan eksplisit).
- Regresi pada kode baru: phase0/1/2 refactor + fase6: 31 passed + 1 skipped.
- Sebelumnya: fase8/10/mentor/scoring/hybrid/phase13/leakage (laporan Phase 1–2).

## Test result dan evidence location

- Semua hijau (worktree venv, sqlite terisolasi + stub LLM).

## Baseline vs after, sample count, dan workload

| Metrik | Sebelum | Sesudah |
|---|---|---|
| Statement preflight (excl. protocol) | GET + SELECT turns + COUNT + INSERT | SELECT FOR UPDATE + SELECT turns (+MAX) + INSERT |
| Nomor turn | COUNT terpisah (race) | MAX dalam lock (atomik di pg) |
| Koneksi route selama LLM | 0 (Phase 2) | 0 (dipertahankan) |
| Koneksi auth selama LLM | 1 | 1 (residual, lihat risiko) |
| Fencing finalisasi | tidak ada | advisory lock + skip-if-newer |

## Risiko/limit yang tersisa

- Sesi auth masih hold 1 koneksi selama stream ( mengubahnya merusak writers;
  desain migrasi DTO terpisah butuh gate sendiri).
- Legacy V1/native-v3/websocket writers tidak ikut lock (mixed-path race
  residual; frontend memakai jalur V2).
- Serialisasi konkuren hanya terbukti di PostgreSQL (test pg-only NOT RUN di
  sini — tidak ada PG lokal; butuh runbook pg sebelum klaim penuh).
- Advisory lock path belum dieksekusi di PG (cabang dialek; logika Python-nya
  diuji di sqlite).

## Rollback dan hasil rehearsal bila berlaku

- Revert commit (tidak ada migrasi/skema). QORA_REGISTRY_CACHE independen.

## Keputusan gate dan tahap berikutnya

- Gate Phase 3: **PASS** untuk konsolidasi/acceptance/fencing pada lingkup
  teruji. Item pg-only eksplisit NOT RUN.
- Lanjut Phase 4 (scoring: fast path stored report, single-flight, tanpa
  ubah report).
