# FASE 12 — Release Hardening (CI · Observability · Security · Ops)

Tujuan: perubahan clinical engine bukan black box saat gagal. Semua aditif;
tidak ada migrasi, tidak ada rewrite keamanan, tidak ada ganti platform.

## CI (`.github/workflows/ci.yml`)

- Backend: pip install + pytest terkurasi dalam sqlite terisolasi + stub
  LLM (compat V3, scoring/judge fixtures + kontrak, pipeline unit, mentor,
  hardening suites, analytics). Live/paid LLM tak pernah jalan di CI
  (gated `QORA_LIVE_TURNS`/`RUN_LLM_QA`, default skip).
- Konten: `lint_v3` + QA battery sebagai **informasional**
  (`continue-on-error`) — bank legacy punya debt human-review records
  (12 error yang diketahui), jadi gate-nya pytest, bukan lint.
- Frontend: `npm ci` + `npm run build` (termasuk prebundle legacy).
- Smoke: boot uvicorn terisolasi → `/health` + header `X-Request-ID` +
  `/api/ops/version` + `/api/ops/readiness`.

## Observability (korelasi tanpa bocor isi)

- `X-Request-ID` (echo/generate) + `X-Qora-Scoring-Version` /
  `X-Qora-Evidence-Pack` / `X-Qora-Content-Version` di **setiap** respons
  (termasuk 401/500) → error chat/judge/Mentor traceable end-to-end.
- `GET /api/ops/version` (publik): versi kontrak + snapshot flag, tanpa secret
  (dipindai: api_key/secret/password/midtrans/xendit/token/@/bearer/hash).
- `GET /api/ops/readiness` (publik): `{ready, checks:{db,uploads,catalog,llm,
  ok}}` — boolean membosankan, tanpa secret (dipindai terpisah).
- `POST /api/ops/client-errors` (auth): intake error layar kritis —
  validasi batas (screen 80, message 1000 → 422), URL di-strip query/
  fragment SEBELUM log, log hanya user_id (tanpa email/transkrip).
- `app/shared/observability.py`: `log_llm_event` / `log_judge_event`
  metadata-only — garansi level-signature tak ada parameter konten
  (prompt/completion/transcript/rubric/dll dilarang di signature).
  Judge `error`/`ok` di-wire di path scoring (guarded, tak ubah perilaku);
  persona failures terlacak via envelope + client-errors.
- Envelope 500: `{success:false, error, ref}` — tanpa traceback, pesan
  disanitasi dari token secret-like, ref = request id.

## Rate limiting (review + hardening)

- Temuan lama: in-memory per-worker (bypass multi-instance), tanpa eviksi
  (tumbuh tanpa batas), start/pf tak ter-cover. Perbaikan: `_MAX_BUCKETS`
  + eviksi expiry-driven per check + cap live entries; start/pf V2+V3
  (termasuk cabang compat) kini memakai bucket AI — diverifikasi di level
  route agar refactor tak bisa diam-diam melepasnya.
- Batasan jujur: tetap per-proses (Redis ditunda, tercatat); `_client_ip`
  percaya `cf-connecting-ip` (sah di belakang Tunnel).

## Feature flags (rollout/rollback tanpa revert besar)

- `content_engine` (v2|v3_compat, live), `judge_engine` (v2|hybrid —
  **observasional**: hybrid FASE 7 STOP, tak di-wire ke scoring),
  `judge_live` (cerminan), `mentor_v1_enabled` (kill-switch write-path
  Mentor → 503, reads tetap buka). Nilai asing → fallback aman;
  snapshot tak pernah berisi secret. V2 fallback selalu satu flip.

## Frontend: no more silent blank

- `qora-boundary.jsx` (terdaftar di LOAD_ORDER): `QoraErrorBoundary`
  GDV — kartu tenang, retry primer + back quiet, lapor bounded ke
  `/api/ops/client-errors`. Dipasang: root `QoraV2Screen` (per-view key)
  + dashboard journey Mentor. Terverifikasi client-side: fallback tampil,
  teks error tak bocor, retry reset state (`regression/fase12/`).

## Security audit (fokus, 2026-09-04 — tanpa P0/P1 baru)

- Auth custom JWT + refresh; admin dari role DB real-time; upload
  (ext+MIME+8MB, UUID filename, route ber-auth); CORS localhost default +
  guard tolak `*` di prod; input principal ber-cap (turn 4000, ddx/mgmt
  12K, story 2000, client-errors 80/1000); batas prompt Part-A tak masuk
  konteks pasien; blind via candidate-safe-view; ownership `_owned` di
  semua path sesi; nol logging transkrip/konten di app; secret env-only.
- **Risiko dikenal, tak diubah di fase ini**: rate limiter per-proses;
  `/docs`+`/openapi.json` aktif (P2 lama); foto eye-photo readable semua
  user login (P2 lama); uploads = disk lokal VPS (lihat bawah).

## Upload storage & backup (risiko + recovery, tanpa ganti platform)

- Fakta: `UPLOAD_DIR` lokal (`./uploads` dev, `/opt/ophtha/uploads` prod),
  tanpa backup di kode, tanpa object storage. Disk VPS mati = foto +
  `backend.log` hilang (kasus/kode aman di git; data klinis di Postgres).
- Recovery plan (operasional, belum diotomasi — owners setuju dulu):
  nightly `rsync -a` upload dir ke host backup + retensi 14 hari, restore =
  rsync balik + restart; migrasi R2/S3 hanya bila ukuran/akses butuh.
- `/api/ops/readiness.checks.uploads` memantau keberadaan direktori.

## Rollback runbook (cepat, tanpa revert besar)

- Frontend: re-promote deploy Pages sebelumnya (dashboard CF) ATAU
  `git checkout <baik> -- sistemnya && deploy.sh`; edge cache lag wajar.
- Backend: `git checkout <baik> -- backend && restart qora-backend`;
  JANGAN auto-downgrade Alembic (2 heads, reconcile dulu).
- Cepat tanpa revert: flip `CASE_CONTENT_ENGINE=v2` (matikan V3),
  `MENTOR_V1_ENABLED=false` (matikan tulis Mentor),
  `BILLING_ENFORCED` tetap false sampai cutover. Judge tetap v2
  (flag hybrid observasional).

## Bukti

- `test_fase12_hardening.py`: 14 passed. Regresi penuh hijau (lihat commit).
- Boundary fallback ter-render client-side (`mobile/boundary-fallback.png`).
