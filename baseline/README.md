# FASE 0 — Visual Baseline (V2-first, regression reference)

Tanggal: 2026-09-04. Backend baseline: isolated sqlite `/tmp/qora_baseline.db`
(BUKAN prod), `CASE_CONTENT_ENGINE=v2`, `V3_COMPAT_TEST_EMAILS=""`,
`LLM_API_KEY=""` (StubLLM). Frontend: vite dev `:5173` →
`VITE_API_BASE=http://127.0.0.1:8001`. Port 8000 prod TIDAK disentuh.

## Isi (desktop 1440x900 + mobile 390x844)

| File | Hash/route | Akun |
|---|---|---|
| 01-dashboard.png | `#/dashboard` | intake fresh (no journey) |
| 02-cases-library.png | `#/cases` (92 V2 cases) | intake fresh |
| 03-session-setup.png | `#/cases/derm_eczema_001` | intake fresh |
| 04-conversation.png | `#/session/<anamnesis>` + 1 stub turn | intake fresh |
| 05-physical-examination.png | `#/session/<osce>` + 1 stub turn (tahap chat pre-PF) | intake fresh |
| 06-assessment-result.png | `#/result` via `qora_last_report` (stub judge → overall 0) | intake fresh |
| 07-mentor-intake.png | `#/mentor` tanpa journey | intake fresh |
| 08-mentor-journey-active.png | `#/mentor` dengan journey active Day 1/7 | demo@qora.app (active journey) |

## Batasan yang diketahui (bukan bug)

- Stub LLM: balasan pasien berbahasa Indonesia `[STUB LLM]...`, skor debrief 0
  di semua dimensi. Real LLM hanya di prod/canary.
- 05 adalah sesi OSCE pada tahap chat (pre-PF). UI chips PF (`QV2PhysicalExam`)
  muncul setelah interaksi lanjutan di sesi OSCE — belum di-automasi di baseline.
- 03 menampilkan banner "Free session limit reached" untuk akun intake karena
  akun itu dipakai membuat 3 sesi setup via API (limit free 5/30 hari).
  Ini state billing `billing_enforced=false` + metering, bukan error visual.
- 06 answer-key tetap tampil lengkap (model answer) meski skor 0 — expected
  untuk stub judge.
- Setiap perubahan frontend WAJIB di-diff ke baseline ini (pelajaran rollback V3:
  fungsi jalan tapi visually terasa aplikasi lain).

## Cara reproduce

```bash
rm -f /tmp/qora_baseline.db
cd backend && DATABASE_URL=sqlite:////tmp/qora_baseline.db LLM_API_KEY= ENV=dev \
  CASE_CONTENT_ENGINE=v2 V3_COMPAT_TEST_EMAILS= ./.venv/bin/python -m scripts.seed_dev_user
# terminal 1
cd backend && DATABASE_URL=sqlite:////tmp/qora_baseline.db LLM_API_KEY= ENV=dev \
  CASE_CONTENT_ENGINE=v2 V3_COMPAT_TEST_EMAILS= ./.venv/bin/python -m uvicorn app.main:app --port 8001
# terminal 2
cd sistemnya && VITE_API_BASE=http://127.0.0.1:8001 ./node_modules/.bin/vite --port 5173
# screenshots: node /tmp/qora_fase0/baseline_shots.mjs (butuh playwright chromium)
```
