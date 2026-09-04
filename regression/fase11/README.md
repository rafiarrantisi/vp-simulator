# FASE 11 — Guideline Watcher & Clinical Surveillance Pipeline

Qora tetap aware terhadap guideline baru TANPA live scoring browsing.
Judge tidak pernah membuka internet: session hari ini dan besok dinilai
identik. Yang berjalan berkala hanyalah source registry + watcher offline;
yang berubah hanya antrean review manusia — bukan konten live.

## Arsitektur (`backend/pipeline/surveillance/`, stdlib-only)

- `registry.py` — 10 sumber otoritatif tier 0–3 (KKI/SKD, Kemenkes PNPK,
  PAPDI/IDAI/PERKI, Farmalkes e-Fornas, WHO/NICE/GINA) + kind
  (guideline/formulary/competency/international/society). Validasi:
  non-empty, id unik, field identitas, vocab tier/kind, versi terlacak,
  tanggal ISO, claim area bervocab, **isolasi Fornas** (formulary dilarang
  klaim `management` — juga di level registry).
- `check.py` — scheduled check: `fetch_fn` opsional memasok observasi,
  lalu **metadata/hash/version dulu** (superseded > new_version >
  focused_update > effective_date_change > no_change). `semantic_fn`
  hanya dipanggil saat metadata tak konklusif — tak pernah untuk
  menghemat/menimpa vonis metadata. Judge live tak tersentuh.
- `diff.py` — diff klaim human-readable + severity
  (informational < minor < clinically_meaningful < safety_critical):
  sinyal safety ID/EN menang atas segalanya (termasuk proposal semantik);
  formulary di-cap minor dan tak bisa menjadi kebenaran manajemen;
  wording-only → informational; superseded naik satu tingkat;
  internasional divergen → flag `differs_from_local_guidance` + alasan
  Tier 1 (alternatif yang diterima, BUKAN override — reviewer memutuskan
  applicability Indonesia, resource, scope dokter umum, relevansi ujian).
- `impact.py` — mapping konservatif (over-approximate) ke
  (family, variant, area): V3 families + V2-compatible; formulary hanya
  medications; family tak dikenal → warning, bukan crash; entri
  internasional membawa penanda divergensi. Registry diakses duck-typed
  (hanya `families` + `variants_for_family`), jadi stub unit maupun
  `CaseRegistry` asli sama-sama jalan.
- `queue.py` — `ReviewerQueue` + gerbang manusia: approve/reject wajib
  **named human**; safety-critical wajib role klinis; approve mengusulkan
  bump versi minor (`v3.0` → `v3.1`) + flag `needs_update` untuk safety;
  reject membersihkan usulan (old truth utuh); keputusan ganda ditolak.
  Export JSONL **menolak** tree `content/` secara struktural.
- `service.py` — `run_surveillance_cycle` → (result, queue): temuan →
  diff → impact → task. `live_truth_changed` selalu False — tidak ada
  jalur kode yang menulis konten, mempublish, atau men-scoring.

## Simulasi diprove (stub deterministik, tanpa network/LLM)

- Fornas baru → 1 task, severity ≤ minor, area medications-only.
- PNPK DBD 2026 → `clinically_meaningful`, kedua varian dengue terpetakan.
- NICE vs PNPK → divergen, Tier-1 reason, tanpa override.
- Wording minor → `informational`.
- Safety-critical (kontraindikasi cairan) → task `needs_update`,
  status pending, tanpa auto-publish.
- No-change → 0 task. Full-cycle di `content/v3` asli: byte-identical.

## Bukti

- `backend/tests/test_fase11_surveillance.py`: **37 passed**.
- `network/sample_review_task.jsonl`: 1 task safety (6 entri impact dengue).
- Regresi backend lain tak tersentuh (modul pipeline murni; tanpa impor
  app/DB; tanpa migrasi; tanpa file generated).

## STOP

Watcher hanya flag/review. Jalur manusia → versi konten baru → lint → QA →
regresi → promotion tetap manual; sesi aktif pinned versi lama. Live-LLM
trial (deepseek-v4-flash via kredensial owner) tetap gated + approval.
