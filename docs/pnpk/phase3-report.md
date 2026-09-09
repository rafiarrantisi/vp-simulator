# PNPK Phase 3 — Pilot Mapping Draft (unapproved)

Fase: PNPK Phase 3
Status: DRAFT-STRUCTURALLY-CLEAN, publish gate **BLOCKED** menunggu clinician

## Kondisi aktual yang ditemukan

- Draft: 13 claims + 17 mappings + 1 template + 1 pack
  (`content/evidence/*/pilot_draft_001.json`), dari PDF resmi terverifikasi
  (UTI 2025, dengue dewasa 2020) dengan locator halaman + excerpt hash yang
  dapat dihitung ulang.
- Cakupan: uti_adult_002 (dx/inv/selected hx/safety), dengue_001_mild
  (warning signs, fluids, paracetamol, NS1/labs, safety). Gap jujur:
  dd x/comparison, referral, sebagian hx rutin, mg analgesia — tanpa mapping
  generik.
- Applicability ditegakkan: UTI-PREG-001 (hamil) TIDAK dipetakan ke
  uti_adult_002; compiler menolaknya bila dicoba.

## Perubahan dan alasan

- `pnpk_draft_pilot.py`: generator draft deterministik.
- Compiler: field `excerpt` authoring-only (dikeluarkan dari digest),
  cek applicability `sex`, mode `allow_draft` (hanya melaporkan gap
  approval; tidak publish; tidak melemahkan aturan lain).

## Files/modules yang benar-benar disentuh

- Lihat di atas + `tests/test_pnpk_pilot_draft.py`.

## Penyesuaian dari brief beserta buktinya

- Tanpa clinical review, tidak ada klaim/mapping/template approved — sesuai
  larangan self-approve (§10, §14). Reviewer: PENDING (clinician eksternal).

## Invariants yang relevan

- Draft tidak dapat mencapai runtime (strict gagal; tidak ada loader yang
  membaca status draft).

## Tests yang dijalankan beserta command/environment

- `test_pnpk_pilot_draft.py`: 3 passed (strict gagal, draft bersih
  struktural, excerpt terverifikasi). Compiler suite: 11 passed.

## Test result dan evidence location

- Semua hijau. 51 approval gaps tercatat (diharapkan).

## Baseline vs after, sample count, dan workload

- N/A (authoring; nol perubahan runtime).

## Risiko/limit yang tersisa

- **BLOCKER**: 51 approvals klinis (13 klaim + 17 mapping + 1 template +
  pack) menunggu clinician + second check untuk high-risk. Tanpa ini,
  Phase 4 tidak punya pack approved untuk di-compose.
- Transkripsi excerpt manusia (saya) bisa salah ketik — hash mengikat
  transkripsi saya, reviewer wajib cocokkan visual PDF.

## Rollback dan hasil rehearsal bila berlaku

- Hapus `content/evidence/*/pilot*` (draft, bukan artifacts).

## Keputusan gate dan tahap berikutnya

- Gate Phase 3: **BLOCKED (clinician review)** — sesuai desain brief.
  Pekerjaan independen Phase 4 (composer + DTO + persist + shadow tests
  dengan pack sintetis approved-di-fixture) dapat jalan paralel.
