# PNPK Phase 1 — Source Acquisition

Fase: PNPK Phase 1
Status: PASS

## Kondisi aktual yang ditemukan

- Toolkit diadaptasi ke `backend/tools/download_pnpk.py` + katalog +
  `backend/tools/tests/test_download_pnpk.py` (25 tests, tanpa ubahan logika).
- `pypdf==6.10.0` ditambahkan ke venv (sesuai requirements toolkit yang diuji).

## Perubahan dan alasan

- Download 3 PDF pilot dari URL resmi (Keslan): ISK 2025, hipertensi dewasa
  2026, dengue dewasa 2020. Layout `clinical_sources/<slug>/<year>/<edition>/<sha>.pdf`.
- PDF di-gitignore (3.1 MB binary); manifest + lock ter-commit. Reproduksi via
  URL resmi + pin SHA (bukan mengandalkan blob git).
- Halaman pertama terverifikasi: KMK 9845/2020 (64 hlm), 303/2026 (90 hlm),
  762/2025 (111 hlm) — cocok katalog + VALIDATION.md.
- Source hold dengue anak TIDAK diunduh (default set hanya 3 dewasa).

## Files/modules yang benar-benar disentuh

- (baru) `backend/tools/download_pnpk.py`, `pnpk_sources.json`,
  `pnpk_sources.lock.json`, `tools/tests/`
- (baru) `clinical_sources/manifest.json` (+ PDFs ignored)
- (baru) `docs/pnpk/phase1-report.md`
- venv: +pypdf==6.10.0

## Penyesuaian dari brief beserta buktinya

- Tidak ada: sesuai §14 (dry-run → download → verify → lock → tests).

## Invariants yang relevan

- Akuisisi tidak menyentuh scoring/latency/UI. Lock `clinical_approval: false`.

## Tests yang dijalankan beserta command/environment

- `tests/test_download_pnpk.py`: 25 passed (+3 subtests), offline/fake HTTP.
- CLI: dry-run (0 network), download (3/0/0/0), re-download (0/3/0/0),
  verify (3/0), lock OK. SHA cocok VALIDATION.md byte-per-byte.

## Test result dan evidence location

- Semua hijau. Manifest: `clinical_sources/manifest.json`.

## Baseline vs after, sample count, dan workload

- N/A (akuisisi; tidak ada perubahan runtime).

## Risiko/limit yang tersisa

- Bytes server resmi bisa berubah; manifest+backup lokal + lock mismatch
  fail-closed menanganinya. Backup off-machine PDF belum ada (disarankan).

## Rollback dan hasil rehearsal bila berlaku

- Hapus `clinical_sources/` + revert commit; tidak ada state runtime.

## Keputusan gate dan tahap berikutnya

- Gate Phase 1: **PASS**. Lanjut Phase 2 (contracts + compiler).
