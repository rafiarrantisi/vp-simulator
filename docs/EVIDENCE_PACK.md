# FASE 2 — Clinical Evidence Foundation & Data Contracts

## 1. Hierarki sumber (mengikat untuk semua authoring/review)

```
SKD 2026 ............ otoritas tunggal competency scope + kategori
                      (Tuntas | Tatalaksana awal dan rujuk). Tier 0.
PNPK / guideline ..... kebenaran manajemen PRIMER bila tersedia
nasional & societas     (Tier 1 Kemenkes/PNPK, Tier 2 PAPDI/PERKI/IDAI/…).
Indonesia
Fornas / JKN ........ konteks formularium/obat SAJA. Tidak pernah menjadi
                      guideline penyakit dan tidak pernah menimpa Tier 0-2.
Internasional ........ WHO/NICE/ESC/GINA/GOLD/KDIGO/ADA/IDSA/… — tambahan
(WHO, NICE, …)         yang sah atau pemicu update. Tidak auto-override
                      Indonesia. Basis manajemen Tier-3-only WAJIB flag
                      `intl_primary_interim` + rasional manusia.
SKDI 2012 3A/3B/4A .. legacy crosswalk SAJA bila terverifikasi
                      (`legacy_mapping_confirmed`). Tidak pernah di-infer.
```

Implementasi: `pipeline/case_v3/vocab.py` (`SourceTier`, `SourceKind`,
`SKD2026_*`, registry SKDI legacy), `pipeline/case_v3/governance.py`
(`SourceRecord`, `HIERARCHY_DOC`, `has_clinical_guidance_source`,
`validate_governance`, anti-self-promote), `pipeline/case_v3/evidence.py`
(`EvidencePack`, `infer_tier`, `validate_evidence_pack`).

## 2. Approved Clinical Evidence Pack

Satu pack per family = `build_evidence_pack(family, variants)`:
otoritas kompetensi, guideline primer nasional, guideline societas,
referensi internasional, konteks formularium, sumber epidemiologi,
kategori SKD 2026 (LIST — satu family boleh menjangkau dua kategori,
mis. dengue ringan=tuntas vs syok=rujuk), crosswalk legacy, tanggal
(publication/effective/review), `clinical_content_version`, `review_status`,
reviewers. Validasi: `validate_evidence_pack` (error menghalangi
publishability; warning ditutup reviewer manusia), `lint_evidence_family`
(plus kontrak obat + konsistensi `active_variant_ids`).

Status konten saat ini (report-only, tanpa perubahan konten):
5 family / 12 variant — dengue + UTI lolos error; fever_child in_review;
hypertension + pyelonephritis draft tanpa variant terlink (gap
terdokumentasi di `test_evidence_pack.py`, bukan disembunyikan).

## 3. Kontrak konsep obat (normalized medication concept)

`MedicationConcept`: generic, class, preferred local agent, alternatif,
dose range, route, frequency, duration, kontraindikasi, monitoring,
referral restriction, source refs, formulary status
(in_stock|limited|non_formulary|unknown). Aturan: preferred agent wajib
punya sumber; formularium tidak pernah menggantikan guideline.
Belum ada variant yang mengisi — diisi hanya via authoring yang
direview manusia (Fase 4).

## 4. Kontrak output scoring (satu bahasa data)

`app/domains/scoring/contracts.py`, `CONTRACT_VERSION = "1.0"`:
`NormalizedScore` menampung overall 0–100, 7 core OSCE domains
(`None` = tidak dinilai, bukan 0), dimensi belajar penuh, rubric items
hit/partial/miss + evidence, safety gates, global rating opsional,
feedback, flag answer-key, metadata sumber + versi, engine/model.
Adapter murni (`from_v2_report`, `from_v3_native`) menerjemahkan report
TERSIMPAN saat dibaca — live judge tidak diubah, histori
`SessionRow.report` tidak pernah ditulis ulang (skor lama tidak bergeser
saat guideline/judge update).

## 5. Versioning & keputusan DB

Versi di tiga lapis: `clinical_content_version` (konten),
`pack_version`/`contract_version` (kontrak), `variant_canonical_hash`
(resume guard — stabil untuk 12 variant existing; field obat baru hanya
masuk hash bila terisi). **Tidak ada perubahan skema DB di Fase 2**:
report JSON + file konten + versioning kontrak sudah cukup. Bila kelak
perlu kolom (mis. index queryable), implikasinya: reconcile 2-heads
Alembic dulu (P0 Fase 0), migrasi aditif + backfill, runtime ALTER tetap
sebagai net — dilaporkan dulu, tidak dikerjakan diam-diam.
