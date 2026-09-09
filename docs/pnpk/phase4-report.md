# PNPK Phase 4 — Composer, DTO, Persist, Shadow Validation

Fase: PNPK Phase 4
Status: PASS (flag default OFF; tanpa pack approved, perilaku identik)

## Kondisi aktual yang ditemukan

- Report live V2-shaped; per_item tanpa ID stabil (teks bebas LLM).
- Merge `_merge_per_item` hanya manipukas teks answer-key: linkage kanonis
  tidak tersedia. Solusi: lampirkan `rubric_ids` saat merge via normalisasi
  eksak (strip prefiks imperatif) — mekanisme kesetaraan yang sama, tanpa fuzzy.
- Hanya item hx_* rutin yang ter-link hari ini (matriks terverifikasi);
  inv/mg/dx/safety-derived tidak punya pasangan answer-key.

## Perubahan dan alasan

- `evidence_loader.py`: load by digest + verifikasi ulang tiap load, cache
  bounded (8), binding resolution tanpa latest, QORA_EVIDENCE_DIR override.
- `feedback_composer.py`: murni deterministik; status via rubric_ids lalu
  fallback teks; satu rationale per target (prioritas); sitasi dedup +
  numbering; substitusi allowlisted; fail-closed (None + reason).
- `evidence_integration.maybe_enrich_report`: flag `QORA_EVIDENCE_ENRICH`
  (default off), metrik counts, tidak pernah raise.
- Hook V2 (rubric kosong → unavailable jujur) + V3 (rubrik live) sebelum
  persist; namespace atomik bersama report.
- Pilot mappings di-target ulang ke hx yang ter-link; inv/mg/dx jadi gap
  tercatat (bukan citation generik).

## Files/modules yang benar-benar disentuh

- Lihat di atas + `_merge_per_item` (+rubric_ids), `_normalize_rubric_text`.

## Penyesuaian dari brief beserta buktinya

- Tidak ada perubahan prompt/judge/panggilannya (terbukti 1 call).
- Tidak ada compaction/decomposition.

## Invariants yang relevan

- Score-critical deep-equal off/on (diuji eksplisit).
- Tidak ada mutasi objek skor (diuji deep snapshot).
- Stored retry identik; tenant/single-flight tidak regresi (suite existing).

## Tests yang dijalankan beserta command/environment

- `test_pnpk_composer.py`: 9 passed (loader, happy, no-mutasi, unavailable,
  flag-off, e2e attach, off/on invariansi, stub-tanpa-namespace, cache bound).
- Regresi: scoring_contract + scoring_v2 + fase12 + fase10 (40 passed).

## Test result dan evidence location

- Semua hijau. Overhead: komposisi pilot tionskala ms (bagian dari respons
  score; angka route-level tercatat pada run invariansi).

## Baseline vs after, sample count, dan workload

- Flag off: byte-identik (suite + invariansi). Flag on tanpa binding: identik.

## Risiko/limit yang tersisa

- Hanya item hx ter-link; klaim bernilai tinggi (NSAID, kultur) menunggu
  bentuk report yang membawa ID kanonis atau review mapping answer-key.
- Cross-worker duplicate judge (diketahui, idempotent via stored).

## Rollback dan hasil rehearsal bila berlaku

- Flag off (default) = perilaku lama bit-identik. Revert commit bersih.

## Keputusan gate dan tahap berikutnya

- Gate Phase 4: **PASS**. Lanjut Phase 5 (UI minor, sudah di-mount).
