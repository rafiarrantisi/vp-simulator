# FASE 10 — Adaptive Mentor V1 (Guided Learning System)

Mentor Phase-1 (chatbot list-case) menjadi guided journey adaptif. Prinsip:
**LLM understands and explains, Qora planning engine decides.** Tidak ada
migrasi (alembic tetap 10 revisi), tidak ada kolom/atribut model baru
(`JourneyCase`/`LearningJourney` tanpa `mission`/`slot_type`), tidak ada
rewrite laporan mentah — semua adaptasi dibaca dari judge + plan JSON.

## Backend

- `journey_builder.py` — ekstraksi deterministik (stub-safe): `goal`
  (`osce` kini termasuk `ujian|exam`), `target_specialty` (= weakness
  pertama), `confidence_score` (beginner-cue → 20),
  `available_minutes_per_day` (ID/EN: "2 jam sehari" → 120, default 45).
  Baru: `needs_clarification(ctx)` → 0–2 pertanyaan prioritas
  (goal → specialty → deadline); intake tetap free text.
- `mentor/planning_policy.py` (baru, murni, tanpa input LLM — saran model
  struktural tidak bisa override eksklusi): `eligible_v3_families`
  (human-reviewed ∩ stage-fit ∩ punya varian; `fam_hypertension` draft
  out, `fam_dengue` in), `rank_candidates` (skor deterministik:
  specialty/weakness, review rank, difficulty fit, fase hari, budget,
  novelty; sort stabil `(-score, ref)`), eksklusi keras (ref kosong,
  difficulty ∉ 1..5, review_rank < 0, family tak dikenal/belum review).
- `case_selector.select_journey_cases(ctx, cases)` (baru): pool V3 eligible
  + V2, peringkat satu engine, cap hari, workload dari menit/hari
  (1 encounter/hari, estimated = budget), progresi Foundation → mock
  (mock = osce_full terberat, selalu hari terakhir). Tiap baris:
  `slot_type: core` + `selection_reason` deterministik (dipakai misi "why").
- `mentor/service.py`:
  - Slot metadata (`slot_type/selection_reason/mandatory`) di plan JSON
    (`final_plan`/`proposed_plan`), merge by day — tanpa kolom baru.
  - `create_journey` → planner unified + `clarifications` di respons.
  - `complete_case` → **ingest-gated**: sesi harus completed + ber-report
    (409 jika belum); skor/evidence/safety dari SERVER (klaim klien
    diabaikan, `score_source: server`). Remediasi eksplisit: safety →
    `remediate` (slot remediation mandatory di hari+1, same-case varian
    beda saat start); skor <60 → `reinforce`; sisanya `advance`. Feedback
    selalu mengutip evidence nyata. `coach_insight` persist di plan JSON.
  - Baru: `GET .../mission` (state/focus/expected/encounters/why/cta),
    `POST .../rebalance` (incomplete +missed_days, DESC per-row flush agar
    UNIQUE aman; slot plan ikut geser), `GET .../report` (verdict
    `ready` hanya skor ≥75 + confidence medium+; else `completed` jujur +
    rekomendasi konkret), `GET .../recap` (cases/time/next_focus/tomorrow).
  - Progress (%) = penyelesaian workload; readiness = engine evidence
    Phase 8. Keduanya tak lagi dicampur.
- `v3_compat_service.start` — novelty: repeat family → varian eligible
  pertama yang belum ditemui user (fresh user: deterministik, tak berubah).

## Frontend (`qora-mentor.jsx`, GDV sama, tanpa desain baru)

- Active journey: Header (lentera + goal/date, TANPA target %) → Today's
  Mission (focus/waktu/encounters/why/CTA) → Coach Insight → Timeline
  (carousel, kartu 220px) → actions sekunder (report ghost, abandon =
  quiet underline, bukan tombol merah) → verdict card saat completed.
- Mobile: hero seni cropped sendiri (band aspect-locked memotong teks) +
  tanpa overlap; daycard responsif; safe-area.
- Proposal: chip Target % dihapus. Readiness report: + strengths/needs-work
  + evidence coverage. i18n en+id (12 kunci mentor.* baru).
- Insiden forensik: satu kartu overlap misterius tak ter-style —
  akar: pola `Object.assign({}, _mtCard, …)` di satu call-site (penyebab
  pasti tak terisolasi); diperbaiki via inline literal terverifikasi DOM.
  Pelajaran: transform HMR vite lambat — screenshot hanya sah setelah bundle
  tersaji terverifikasi (di-poll), bukan setelah sleep tetap.

## Bukti

- `backend/tests/test_fase10_adaptive_mentor.py`: 10 passed — ekstraksi
  IM/budget ID, klarifikasi 1–2 vs [], gate V3, rank deterministik,
  plan 7-hari (slot/reason/45/mode), e2e mission→ingest server (72,
  client 5 diabaikan), 409 sesi aktif, remediate mandatory + insight
  safety, reinforce + rebalance geser +2, varian repeat beda, report
  completed-vs-ready + recap, no-schema + legacy stabil.
- `test_mentor.py` 20 passed (e2e lama dijadikan ingestion jujur: turn →
  score stub → ingest 0 server-side). Regresi: v2/phaseB/scoring 39,
  presentation/analytics/fase6 11, fase8 22 + fase9 6 hijau.
- `network/`: mission.json, report.json, cases-slots.json (kanonis).
- `desktop|mobile/mentor-journey.png`: header/mission/timeline/actions,
  nol pageerror, overflow-x 0. (Tab-bar pada shot full-page = artefak
  fixed-element.)

## STOP / catatan rilis

- Model stabil, kontrak V2 utuh, FE lain tak tersentuh. Broad release
  menunggu keputusan produk; judge production (FASE 7) tetap gate terpisah.
- Live-LLM trial (conversation/judge/mentor, deepseek-v4-flash via kredensial
  yang ditunjuk owner) bersifat gated + approval per run — belum dipakai di
  fase ini (semua stub, nol biaya).
