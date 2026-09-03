# Phase A — Audit Contract V2 (sebelum coding)

Dokumen ini adalah **hasil audit exact contract frontend/backend V2** yang harus
dipertahankan sebagai invariant. Tidak ada komponen yang diubah — murni inventori
"apa yang V2 butuh dari backend" agar phase B+ (v3 compatibility facade) bisa
memenuhi kontrak itu tanpa menyentuh UI.

> Dokumen untuk keputusan: **V2 UI = production shell (invariant). V3 = content +
> clinical engine di belakangnya.**

---

## 0. Prinsip umum tentang bagaimana V2 berkomunikasi dengan backend

Semua panggilan backend dari frontend V2 lewat satu helper:

- **`qv2Fetch(path, opts)`** (`qora-v2.jsx:22`)
  - Base URL: `window.OPHTHA_API_BASE` (umumnya `''` → same-origin `/api`).
  - Header: `Content-Type: application/json` + `Authorization: Bearer <token>`.
  - Token diambil dari `localStorage.ophtha_api_auth.token`.
  - 401 → auto-refresh via `window._qoraRefreshToken()` lalu retry sekali.
  - Timeout default 30 s (dapat di-override `opts.timeout`).
  - **Response shape yang diharapkan**: `{ "data": <payload> }` — `qv2Fetch`
    mengembalikan **hanya `<payload>`** (unwrap `json.data`).
  - Error: `{ "error": msg }` atau `{ "detail": { message } }` → dilempar sebagai `Error`.
- Nama field di frontend pakai **camelCase** (`sessionId`, `caseId`, `openingLine`).
  Backend V2 memakai camelCase di JSON output. Facade v3-compat WAJIB meniru ini.

### Data user / auth
- `GET /api/users/me` → `{ id, name, ... preferred_language }`
- `PATCH /api/users/me` (profile edit)
- `GET /api/billing/me` → `{ usage: { sessions }, free_session_limit, unlimited }`

---

## 1. `QV2Catalogue` (daftar kasus / case library)

| Aspek | Nilai |
|------|-------|
| Komponen | `QV2Catalogue` — `qora-v2.jsx:152` |
| Endpoint | `GET /api/v2/cases` |
| Response | `{ cases: [CaseCard...], specialties: [..], total }` |
| Card fields (yang dipakai render) | `id`, `specialty`, `mode` (`osce_full`→pill OSCE, else Anamnesis), `difficulty`, `estimated_minutes`, `first_impression_id`/`first_impression`/`chief_complaint`, title via `_qv2Title(c)` |
| Filter | lokal di client: `specialty`, `difficulty` |
| Action | `onPick(c)` → set `picked=c`, `view=setup`, hash `#/cases/<id>` |

CaseCard `id` dipakai langsung sebagai `case_id` ke session.

---

## 2. `QV2SessionSetup` (modal/cover sebelum sesi)

| Aspek | Nilai |
|------|-------|
| Komponen | `QV2SessionSetup` — `qora-v2.jsx:515` |
| Props | `caseSummary`, `onStart(opts)`, `onBack` |
| Yang dipakai dari `caseSummary` | `mode` (`osce_full`→ default OSCE, else practice), `first_impression_id`/`first_impression`/`presentation_id`/`presentation`, `estimated_minutes` (untuk timer; dibaca juga di QV2Session) |
| Fetch internal | `GET /api/users/me` (preferensi bahasa), `GET /api/billing/me` (limit) |
| UI | pilih Practice/OSCE, bahasa, mic permission (`getUserMedia`), STT availability, billing upsell |
| **onStart signature** | `onStart({ mode, micReady, sttReady, language })` — `mode` ∈ `practice`/`osce`, `language` ∈ `en/id/ms/tl/vi/th` |

> Catatan penting: **setup TIDAK membuat sesi**. Ia cuma mengumpulkan mode/bahasa/mic.
> Sesi dibuat saat masuk QV2Session.

---

## 3. `QV2Session` (inti: chat, mic, timer, physical, assess, submit)

| Aspek | Nilai |
|------|-------|
| Komponen | `QV2Session` — `qora-v2.jsx:741` |
| Props | `caseSummary`, `mode`, `language`, `onScored(report)`, `onExit`, `initialSessionId`, `onSessionReady(sessionId)` |
| Internal state | `sessionId`, `messages: [{role,text}]`, `busy`, `err`, `stage` (`brief`/`chat`/`pf`/`assess`), `pf {notes,areas}`, timer (`secs`, `timerOn`, `timeUp`, `overtime`), mic control |

### 3.a Membuat sesi baru (start)
- **`POST /api/v2/sessions`** body `{ case_id, language }`
- Response `{ sessionId, caseId, mode, language, openingLine }`
- Frontend: `setMessages([{role:'patient', text: d.openingLine}])`, simpan meta di
  `sessionStorage.qora_session_meta` `{sessionId, caseId, mode, language}`, panggil `onSessionReady(sessionId)`.

### 3.b Resume (refresh / deep-link `#/session/<sid>`)
- **`GET /api/v2/sessions/{id}/turns`**
- Response `{ turns: [{role, content}], case_id, language, status, opening_line }`
- Frontend: map `turns` → `{role, text}`; jika kosong pakai `opening_line`.
- Hash router (`QoraV2Screen`) juga fetch `GET /api/v2/cases/{case_id}` untuk dapat `picked`.

### 3.c Kirim pertanyaan (chat) — STREAM utk UX suara/kata-per-kata
- **`POST /api/v2/sessions/{id}/turns/stream`** body `{ text, input_type: 'text'|'voice' }`
- Response: **body raw text/plain stream** (token chunks), dibaca via `fetch` + `reader`.
- Frontend `send()`: append user bubble + empty patient bubble (streaming) → patch teks per chunk → final trim.
- Fallback bila stream gagal: **`POST /api/v2/sessions/{id}/turns`** body `{ text }` → `{ reply, audioUrl }`.

### 3.d Mic / voice
- **BUKAN browser STT.** Pakai server transcription:
  - `POST /api/ai/transcribe` (multipart `audio`, webm) → `{ transcript }`
  - lalu hasilnya di-auto-send lewat turns/stream dengan `input_type:'voice'`.
- `QV2MicButton` (`qora-v2.jsx:641`) = tombol UI mic; logika recorder/silence ada di dalam `QV2Session`.

### 3.e Physical examination step (`stage='pf'`)
- `QV2PhysicalExam` → **`POST /api/v2/sessions/{id}/pf`** body `{ notes, areas: [..] }`
- Response `{ findings: {area:text}, examined: [..], available_areas: [..] }`
- Reveals HANYA area yang di-examined (isolation rule).

### 3.f Assessment & submit — **`POST /api/v2/sessions/{id}/score`**
- Body: `{ ddx: dict, management: dict, mode: 'practice'|'osce', overtime: bool, pf_notes, pf_areas }`
- Response: **`report`** (lihat §5). Idempotent: jika `status==='completed'` & punya `report`, endpoint balikin report tersimpan (tidak rekomen award ulang).
- Frontend: simpan `qora_last_report` di sessionStorage → `onScored(report)` → `view=result`, hash `#/result`.

### 3.g Explicit completion / autopsy (asal eligible)
- `GET /api/v2/mentor/sessions/{id}/autopsy` → `{ autopsy }` atau 404 → `POST` generate.

---

## 4. `QV2Result` (debrief) — view model yang harus compatible

| Aspek | Nilai |
|------|-------|
| Komponen | `QV2Result` — `qora-v2.jsx:1110` |
| Props | `report`, `caseSummary`, `onAgain`, `onLibrary`, `sessionId` |
| Field `report` yang dipakai | `answer_key` (reveal), `per_dimension` (dims), `safety_gates` (label khusus), `overall` (skor + confetti >=80), `summary`, `badges`, `xp`, plus `overtime_penalty` |
| Answer-card | `QV2AnswerCard`, `QV2ItemRow`, `QV2SkillBar`, `QV2Stat`, `QV2Badges` |

**Wajib**: v3 debrief harus diserahkan sebagai `report` dengan shape yang sama
(`answer_key`, `per_dimension`, `safety_gates`, `overall`, `summary`, …)
agar render di `QV2Result` tanpa perubahan UI. Endpoint score V2 sudah idempotent
(return stored report) — pola ini bisa ditiru v3.

---

## 5. Shape `report` (hasil evaluate_v2 → ditampilkan QV2Result)

Dibuat oleh `app/rag/judge_v2.py:evaluate_v2`. Field kunci (yang digunakan UI):
- `overall` (int, 0–100) — dipakai confetti threshold ≥80
- `summary` (str) — ringkasan
- `per_dimension`: `{ dimName: { score, max, label?, ... } }` — dipakai QV2SkillBar/dims
- `safety_gates`: list objek, label via map di QV2Result
- `answer_key`: reveal post-session (ddx/management/expected)
- optional `badges`, `xp`, `overtime_penalty`

---

## 6. `QV2Progress` / Dashboard (tidak di-touch, tapi contract)

- `GET /api/v2/progress` → `{ xp, totalSessions, completedCases, streak, dailyGoal, weeklyCount, sessions, dimensionAverages, specialtyCounts, badges }`
- `QoraDashboard` → `GET /api/v2/progress`, `GET /api/v2/sessions?limit=5`, `GET /api/users/me`

---

## 7. Ringkasan endpoint contract V2 (mustahap dipenuhi facade v3)

| # | Endpoint | Method | Body | Response key |
|---|----------|--------|------|--------------|
| 1 | `/api/users/me` | GET/PATCH | — | profile (preferred_language) |
| 2 | `/api/billing/me` | GET | — | usage, free_session_limit, unlimited |
| 3 | `/api/v2/cases` | GET | — | `cases[]`, `specialties` |
| 4 | `/api/v2/cases/{id}` | GET | — | `summary(c)` (CaseCard) |
| 5 | `/api/v2/cases/{id}/media` | GET | — | `media[]` |
| 6 | `/api/v2/sessions` | POST | `case_id, language` | `sessionId, openingLine, caseId, mode, language` |
| 7 | `/api/v2/sessions/{id}/turns` | GET | — | `turns[], case_id, language, opening_line` |
| 8 | `/api/v2/sessions/{id}/turns` | POST | `text` | `reply, audioUrl` |
| 9 | `/api/v2/sessions/{id}/turns/stream` | POST | `text, input_type` | raw text stream |
| 10 | `/api/v2/sessions/{id}/pf` | POST | `notes, areas` | `findings, examined, available_areas` |
| 11 | `/api/v2/sessions/{id}/score` | POST | `ddx, management, mode, overtime, pf_notes, pf_areas` | `report` |
| 12 | `/api/v2/mentor/sessions/{id}/autopsy` | GET/POST | — | `autopsy` |
| 13 | `/api/v2/sessions?limit=` | GET | — | `sessions[]` |
| 14 | `/api/v2/progress` | GET | — | gamification payload |
| 15 | `/api/ai/transcribe` | POST | multipart audio | `transcript` |
| 16 | `/api/v2/pilot/events` | POST | fire-and-forget | — |

---

## 8. Component ternak backend V2 yang dipanggil

- `app/domains/sessions/v2_router.py` (all endpoints above)
- `app/domains/cases/v2_catalog.py` → `list_v2_cases`, `load_v2_case`, `summary`, `parse_pf_findings`
- `app/rag/engine_v2.py` → `respond(case_id, history, user_message, language)`, `stream_respond(...)`
- `app/rag/judge_v2.py` → `evaluate_v2(case, transcript, mode, student_ddx, student_management, student_pf)`
- Billing gate: `billing.can_start_session`, `record_usage`, `record_session_cost`
- Envelope: `app.shared.envelope.ok` → `{success, data}`

---

## 9. Engine V3 (yang akan dipakai di dalam facade) — sudah siap

- `app/rag/engine_v3.py` → live patient engine v3 (canonical truth + persona constrained).
- `app/pipeline/case_v3/` → loader, models (ClinicalVariant), derive, lint, qa, semantic, redteam, sourceqa, governance, runtime, persona, vocab.
- `app/rag/judge_v2.py` **tidak dipakai utk score v3**; v3 pakai scoring-nya sendiri (`case_v3/qa.py` / `semantic`).
- Content murni v3: `content/v3/families/*.yaml`, `content/v3/variants/*.yaml`, `content/v3/catalog/`.

Facade v3-compat (`v3_compat_*`) akan **menerjemahkan** internal v3 ke shape
external §7 di atas, mengikuti pola §0 (camelCase + `{success,data}`), tanpa
membuat UI baru, tanpa route `#/v3`, tanpa mount React kedua.

---

## 10. Yang TIDAK Akan Diubah (hard freeze § f)

- `sistemnya/Virtual Patient Simulator.html` (app shell routing, `/cases` → `QoraV2Screen`)
- `sistemnya/build/bundle-legacy.mjs` (load order)
- `sistemnya/design.css` & global token
- shell/header/footer
- Semua komponen V2 di `qora-v2.jsx` (§1–§4)

Yang boleh berubah nanti: **penambahan file backend baru** (`v3_compat_router.py`,
`v3_compat_service.py`, `v3_compat_schemas.py`), plus adapter tipis di sisi
frontend `getSessionApi(...)` yang memilih `V2SessionApi` / `V3CompatSessionApi`
dengan interface sama — hanya bila diperlukan, via feature flag §K (bukan route baru).

---

## 11. Renikon rute feature flag (Phase K — untuk awal)

- `case_content_engine` = `v2` (default semua user) | `v3_compat` (khusus akun uji).
- `QoraV2Screen` tetap render untuk kedua mode.
- Bila `v3_compat`: `GET /api/v2/cases` (atau endpoint compat) mengembalikan card
  `source_type = v3_family`; `POST /api/v2/sessions` dengan `case_id` berupa
  **family public ref** utama; seluruh alur di bawah render di QV2Session.
- Bila error → set flag ke `v2`, konten lama kembali instan tanpa rollback frontend.