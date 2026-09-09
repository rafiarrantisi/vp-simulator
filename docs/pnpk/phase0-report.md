# PNPK Phase 0 — Audit Repo Aktual & Baseline Invariants

Fase: PNPK Phase 0
Status: PASS (lanjut Phase 1)

## Kondisi aktual yang ditemukan

- Branch: `feature/pivot-v4` @ 0076394 (post refactor-merge). Registry aktual:
  122 families / 264 variants (terverifikasi via loader, bukan angka audit).
- Pilot mapping ke exact IDs:
  - `fam_uti` (clinically_reviewed) → `uti_adult_002` (34 th, cystitis, koas),
    `uti_child_001`, `uti_male_003`. Hash `1f15ee0ae4c8415e`.
  - `fam_dengue` (clinically_reviewed) → `dengue_001_mild` (24 th, adult,
    preclinical+koas, hash `4c4c4df1d0dfb5f1`), `dengue_002_warning` (38 th),
    `dengue_003_severe`.
  - `fam_hypertension` (DRAFT) → `htn_001_typical` (48 th) dkk. Mapping boleh
    draft; publish terkunci sampai family reviewed.
  - `fam_pyelonephritis` (DRAFT) → `pyelo_*` termasuk `pyelo_preg_001`
    (scope kehamilan — tidak untuk variant nonhamil).
  - `fam_tb` (in_review), `fam_fever_child` (in_review, 0 variants).
- Score-critical fields (tidak boleh berubah): overall, score, per_dimension,
  per_item (+evidence), safety_gates, summary, answer_key, debrief,
  overtime_penalty, schema, variantId, familyId, envelope `ok()`, HTTP status.
- Urutan assembly V3: aevaluate → score_encounter → build_debrief → adapter →
  overtime → persist. V2: aevaluate → overtime → persist + progress.
- Transcript: full history tanpa cap jumlah turn; truncasi 500 char per
  evidence text di judge; `_empty_report` skor 0 pada failure (ada).
- Stable rubric IDs (live): `hx_{n}`, `rf_{n}`, `dx_1`, `ddx_{n}`, `inv_{n}`,
  `mg_{bucket}_{n}`, `sf_avoid_{len}` — posisional per variant. Deterministik
  untuk konten sama, rapuh terhadap filtering (inv appropriateness) dan
  `sf_avoid` berbasis len(items). Mapping key = (variant_id, canonical_hash,
  item_id) + cross-check kind/expected.
- EVIDENCE_PACK_VERSION ganda makna (temuan §13):
  - `clinical_contracts/versions.py` = "1.0.0" → contract scoring output.
  - `case_v3/evidence.py::EvidencePack` (pack_version "1.0") → bundel sumber
    family untuk authoring. KEPUTUSAN: tipe baru `ClinicalEvidencePack`,
    tidak reuse, tidak bump constant global per konten.
- `canonical_hash` = sha256 variant minus id/title (medications kondisional).
  Binding evidence TIDAK BOLEH jadi field canonical (picu 409) → sidecar
  release binding. Diverifikasi di models.py:530.
- Serialisasi: tanpa `response_model` di route score → namespace additive lolos.
  sessionStorage (`qora_last_report`, `qora_session_meta`) menyimpan JSON penuh
  → additive field survive. Result page: `QV2Result` (qora-v2.jsx:1156).
- Consumers EVIDENCE_PACK_VERSION: response header + ops version + judge
  pipeline stamp. Tidak diubah.

## Perubahan dan alasan

- Hanya dokumen ini (read-only). Tidak ada perubahan produk.

## Files/modules yang benar-benar disentuh

- (baru) `docs/pnpk/phase0-report.md`

## Penyesuaian dari brief beserta buktinya

- Brief §2 berasumsi fam_uti/fam_hypertension dsb. dari audit: DIVERIFIKASI
  live, dengan koreksi status (hypertension/pyelo = DRAFT, bukan reviewed).
- Brief §3.4 (cap 40 turns): TIDAK DITEMUKAN di HEAD (history penuh).
  Absence-evidence concern tetap dipegang via wording aman di composer nanti.
- Brief §11 pilot dengue: variant dewasa terkonfirmasi (`dengue_001_mild`,
  24 th). Source hold dengue anak tetap berlaku (tidak dipakai).

## Invariants yang relevan

- Disclosure/canonical truth, tenant isolation, API/stream contract, scoring
  semantics: baseline, dijaga suite existing.

## Tests yang dijalankan beserta command/environment

- Belum ada test baru fase ini (audit). Suite existing relevan terakhir hijau
  pada sesi sebelumnya (569 passed, 5 pre-existing).

## Test result dan evidence location

- N/A (read-only). Evidence = file ini + hash di atas.

## Baseline vs after, sample count, dan workload

- N/A. Baseline perilaku = kode HEAD saat ini.

## Risiko/limit yang tersisa

- Mapping key posisional rapuh → mitigasi via (variant, hash, kind) triple.
- Clinical review manusia (Phase 3) adalah gate eksternal — di luar kendali kode.

## Rollback dan hasil rehearsal bila berlaku

- N/A (tanpa perubahan).

## Keputusan gate dan tahap berikutnya

- Gate Phase 0: **PASS**. Lanjut Phase 1 (toolkit + acquisition 3 PDF pilot).
