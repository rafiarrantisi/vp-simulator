# PNPK Phase 5/6 — Result UI, Governance, Failure Tests

Fase: PNPK Phase 5 + 6
Status: PASS (canary menunggu pack approved + keputusan rollout)

## Kondisi aktual yang ditemukan

- Result page: `QV2Result` (qora-v2.jsx). Report lama tanpa namespace harus
  tetap tampil persis sama.

## Perubahan dan alasan

- Phase 5: komponen `QV2ClinicalEvidence` (rationale ≤5 awal + toggle,
  marker [n], daftar referensi + link PDF resmi `#page=`) di-mount setelah
  blok summary; render null bila namespace absent. Tanpa spinner/interaksi
  wajib baru; reuse tipografi/spacing/warna existing.
- Phase 6: failure/governance ter-cakup test (missing pack, malformed,
  disconnect, superseded, stale hash 409, source hold, cache bound,
  backup/restore via re-download unchanged di Phase 1).
- Cadence review sumber: proses internal berkala via indeks resmi (dokumen
  §10); tidak ada daemon baru. Reverse index tersedia dari compiler untuk
  daftar kasus terdampak.

## Files/modules yang benar-benar disentuh

- `sistemnya/qora-v2.jsx` (komponen + mount point).

## Penyesuaian dari brief beserta buktinya

- Canary (flag ON untuk pilot) dan edukator feedback: menunggu pack
  approved (Phase 3 BLOCKED) + keputusan rollout. Kode canary-ready.

## Invariants yang relevan

- Report lama: UI identik (komponen null).

## Tests yang dijalankan beserta command/environment

- Build Vite hijau. UI diverifikasi via build + review kode (tidak ada
  browser harness di repo; gate visual canary menunggu rollout).

## Test result dan evidence location

- Build OK. Gate fungsional via backend tests (namespace absent → null).

## Baseline vs after, sample count, dan workload

- N/A (UI additive).

## Risiko/limit yang tersisa

- Perceived authority: rationale dibatasi klaim approved + kalimat pembeda
  "Scores are unaffected".
- Mobile/long titles: layout mengikuti pola kartu existing; verifikasi
  visual penuh saat canary.

## Rollback dan hasil rehearsal bila berlaku

- Flag backend off + reader menerima both schemas (optional field).

## Keputusan gate dan tahap berikutnya

- Gate Phase 5/6 (kode): **PASS**. Blocker eksternal: clinician review
  (Phase 3) + keputusan canary/rollout.
