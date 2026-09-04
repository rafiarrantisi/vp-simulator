# FASE 9 — Dashboard Product Refinement (di atas data Phase 8 yang trustworthy)

Glass hero dipertahankan — bukan dashboard generic solid. Semua angka membaca
canonical backend (`GET /api/v2/progress`, longitudinal Phase 8); tidak ada
hardcode/dummy/recompute di frontend.

## Yang diubah (frontend saja + 1 fallback backend aditif)

- `sistemnya/qora-v2.jsx` — `QoraDashboard` ditulis ulang + atom `QD9*`:
  - Hero: pita `fajar` + panel kaca Level tetap (desktop). Panel disembunyikan
    di layar sempit (GDV §9); CTA tidak lagi lari ke bawah panel (`maxWidth`
    guard desktop). Mobile: hero seni cropped 200px + scrim (judul selalu
    muat, tidak terpotong), CTA full-width di permukaan halaman.
  - Stats overlap `-72` desktop; mobile tanpa overlap (hero pendek) + grid
    2 kolom kompak, margin horizontal 16px konsisten, bottom safe-area.
  - Skill bars menjadi visualisasi UTAMA (sort terlemah-dulu, evidence count,
    pill Developing <60 dengan skor tetap ditampilkan — framing tanpa
    menyembunyikan fakta). Radar didemosi ke disclosure "Skill detail" di
    kartu Readiness (GDV: radar hanya untuk analitik dalam + data cukup).
  - Angka kanonis: `avgScore`, `strongest/weakestSkill`, `dimensionDetail`,
    `coverage`, `readiness{score,state,confidence,drivers,evidence}`,
    `badges`, `sessions` — semua dari `/progress`. Rata-rata FE yang salah
    (mean of dimension avgs) dihapus.
  - Ikon GDV: semua emoji dihapus (👋📋📊🏅🎯 + emoji spesialisasi +
    emoji badge backend + ▶). Section pakai `QIcon` garis; badge backend
    dipetakan ke ring produk Qora (`QD9Ring`: dot/ring/dash/plum/amb) +
    locked terlihat 30%. Skor pill netral ungu (hijau/merah hanya di result).
  - Kokpit: kartu Next focus (weakest + driver + evidence + Find a case),
    kartu Readiness (skor/state/confidence/drivers), kartu Continue Journey
    (journey aktif → Mentor), recent dikelompokkan per hari tanpa ikon baris,
    sesi incomplete → tombol Lanjutkan real (`#/session/<id>`), bukan dead-end.
  - New user: onboarding state ("Build your clinical profile…"), avg `–`
    (bukan vonis 0%), kartu achievements/readiness disembunyikan jujur.
- `sistemnya/translations.js` — 20 kunci dashboard baru (en+id).
- `sistemnya/design.css` (tema saja) — `:focus-visible` ungu + matikan
  `backdrop-filter` ≤768px (GDV §13, ponsel menengah).
- `backend/app/domains/sessions/v2_router.py` — `/sessions` list fallback ke
  family card untuk baris V3 (judul + spesialisasi, bukan `fam_*` mentah).
- `backend/app/domains/sessions/progress_adapter.py` — `cached_registry()`
  (386 YAML tidak lagi di-parse per baris; kontrak cache = deploy+restart,
  sama seperti katalog V2).

## Bukti (`network/`, `desktop/`, `mobile/`)

- `network/progress-rich.json` — respons kanonis 5 sesi (V2+V3, avg 70.2,
  readiness 56/medium/safety-capped, weakest management).
- `test_fase9_dashboard_contract.py`: 6 passed — empty jujur, angka kanonis
  rich (total 3/avg 75.0/WeakSkill n≥2/drivers/engines v3_compat),
  paritas readiness progress↔mentor, shape history V3, shape journey.
- Playwright (chromium, stub backend :8001 + vite :5173): 4 shots OK —
  desktop+mobile × new+rich. Verifikasi DOM-vs-API: totalSessions, avgScore,
  readiness score, weakest/strongest label, blok kokpit; sapuan emoji;
  overflow-x 0; nol pageerror. (Tab-bar pada shot full-page adalah artefak
  fixed-element, bukan bug — padding safe-area nyata 96px.)
- Regresi backend: fase8 22 + fase9 6 + mentor 20 + v2/phaseB/presentation/
  scoring/analytics/fase6 hijau (kontrak V2 tak berubah).

## Catatan jujur (bukan blocker Fase 9)

- Specialty registry V3 (`fam_uti`→paediatrics, `fam_dengue`→
  internal_medicine) adalah canonical content — kalau kurasi ingin beda,
  itu kerjaan konten, bukan dashboard.
- Copy interpretasi readiness dari backend tetap EN (data, bukan chrome UI).
- Radar `QSkillRadar` tidak dihapus — tetap dipakai di disclosure.

## STOP

Dashboard kini study cockpit di atas data tepercaya. FE lain tak tersentuh;
tidak ada migrasi; tidak ada file generated yang di-commit.
