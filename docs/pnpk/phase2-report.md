# PNPK Phase 2 — Contracts & Compiler

Fase: PNPK Phase 2
Status: PASS (no live enrichment — sesuai mandat)

## Kondisi aktual yang ditemukan

- `EVIDENCE_PACK_VERSION` ganda makna: "1.0.0" (contract scoring output) vs
  "1.0" (family authoring bundle `case_v3/evidence.py`). KEPUTUSAN: tipe baru
  `ClinicalEvidencePack`, tidak reuse, tidak bump constant global.
- Rubric live posisional (`inv_1`, `mg_*`, `sf_avoid_{len}`); mapping key =
  (variant_id, canonical_hash, item_id) + cross-check kind/expected.

## Perubahan dan alasan

- (baru) `pipeline/clinical_contracts/evidence_clinical.py`: Source→Citation
  models + `PACK_SCHEMA_VERSION="1.0"`, vocab tertutup, validate() eksplisit.
- (baru) `pipeline/evidence/compiler.py`: validasi semua aturan §12
  (unknown IDs, non-PNPK, locator/halaman vs PDF lokal, unapproved, source
  hold, digest mismatch, applicability umur/kehamilan, substitusi template,
  orphan citation, condition allowlist, banned patient-route keys,
  placeholders, versi), ekspansi family-defaults → binding eksplisit per
  variant, digest pack stabil, emit pack+index deterministik, reverse index.
- Skeleton `content/evidence/` + `build/evidence/` (kosong; Phase 3 mengisi).

## Files/modules yang benar-benar disentuh

- Lihat di atas. Tanpa perubahan runtime/scoring/UI.

## Penyesuaian dari brief beserta buktinya

- Tidak ada; sesuai §5/§12/§13.

## Invariants yang relevan

- Tidak ada perilaku produk berubah (compiler offline, build-time only).

## Tests yang dijalankan beserta command/environment

- `tests/test_pnpk_compiler.py`: 11 passed (happy deterministik +
  10 aturan rejection + rubric mismatch + source hold + patient payload).

## Test result dan evidence location

- Semua hijau (venv, tanpa network/PDF hidup kecuali page-count lokal).

## Baseline vs after, sample count, dan workload

- N/A (belum ada konten klinis; compiler diuji dengan fixture sintetis).

## Risiko/limit yang tersisa

- Page validation butuh PDF lokal; tanpanya tercatat unverifiable.
- `sf_avoid`/positional IDs rapuh — mitigasi triple key.

## Rollback dan hasil rehearsal bila berlaku

- Hapus file baru; tidak ada state runtime.

## Keputusan gate dan tahap berikutnya

- Gate Phase 2: **PASS**. Lanjut Phase 3 (mapping pilot + templates draft).
