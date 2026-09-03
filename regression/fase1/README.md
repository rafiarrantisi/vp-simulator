# Regression — FASE 1 (after)

Perbandingan terhadap `baseline/` (FASE 0, before). Kondisi capture identik:
isolated sqlite, `CASE_CONTENT_ENGINE=v2`, StubLLM, vite `:5173` → API `:8001`.

## Hasil smoke (14 layar, desktop 1440 + mobile 390)

- `overflow-x=0px` di semua layar. Tidak ada `pageerror`.
- CTA selalu dalam jangkauan: `Assess →` (session), `Continue to assessment`
  (exam/PF), `Start Case` (mentor-active).
- Top collision (Fase 0: chat header `libTop=-22` tertutup sticky header)
  → kini `libTop=66–70` vs `headerBottom=68` (toleransi glass 2px).
- File: `dashboard, cases, session, exam (PF UI asli via klik Exam →),
  result, mentor (intake), mentor-active` per viewport.

## Yang berubah dari before

- Session mobile: tidak ada lagi inner scroller fixed `100dvh-140px`;
  halaman yang scroll, input dock + CTA selalu tercapai.
- Timer memakai tabular-nums; viewport `viewport-fit=cover`; root `100dvh`;
  input mobile 16px (anti iOS zoom); glass fallback solid <768px (GDV §13).
- Desktop tidak berubah secara visual kecuali perbaikan di atas
  (diff diverifikasi via build + screenshot).
