# Arsitektur Backend Qora

> **Status dokumen:** Ringkasan arsitektur menyeluruh backend Qora per 2026-09-08.
> **Branch:** `feature/pivot-v4` · **Backend HEAD:** `2387a14`
> **Versi efektif:** ~v0.16.x (lihat §Versi & Catatan). Path repo: `/home/ubuntu/vp-simulator/backend`.

---

## 1. Gambaran Besar

Qora adalah aplikasi **medical OSCE training** berbasis virtual patient. Backend-nya adalah lapisan orchestration tipis yang bertipe **I/O-bound dan hampir stateless** — hampir semua komputasi berat didelegasikan ke layanan eksternal.

```
Frontend (React/Vite, Cloudflare Pages 'qoramedical')
        │  HTTPS (qoramedical.com, DNS Cloudflare)
        ▼
  cloudflared tunnel ──► VPS (127.0.0.1:8000)
        │
        ▼
  Caddy (reverse proxy / TLS termination)
        │
        ▼
  FastAPI (uvicorn --host 127.0.0.1 --port 8000 --workers 2)
        ├── Domains (13 modul bisnis)
        ├── rag/         (engine pasien + judge)
        ├── pipeline/    (authoring & validasi kasus, offline)
        ├── shared/      (middleware, security, ratelimit)
        └── voice/       (STT + TTS)
        │
        ├──► Supabase (PostgreSQL, transaction pooler :6543)
        ├──► OpenRouter (LLM deepseek/deepseek-v4-flash)
        ├──► Groq (STT whisper-large-v3-turbo)
        └──► Gemini TTS (Cloud Text-to-Speech, ADC auth)
```

**Kunci:** VPS hanya menjalankan FastAPI + orchestration. Database, LLM, STT, dan TTS semuanya eksternal.

---

## 2. Teknologi & Runtime

| Aspek | Detail |
|---|---|
| Bahasa | Python 3.11 |
| Framework | FastAPI |
| ASGI server | uvicorn (`--workers 2`) |
| Process manager | systemd `qora-backend.service` |
| ORM | SQLAlchemy 2.x (future=True) |
| Migrasi | Alembic (10 versi) |
| Reverse proxy | Caddy (TLS) |
| Tunnel | cloudflared → `api.qoramedical.com` |
| Validasi data | Pydantic |

---

## 3. Lapisan Web & Routing

`app/main.py` membangun aplikasi, memasang middleware, dan meng-include semua router.

### Middleware (urutan penting)
1. `RequestContextMiddleware` — request_id correlation, stamp response headers.
2. `SecurityHeadersMiddleware` — header keamanan.
3. CORS (`CORSMiddleware`) — origin dari `CORS_ORIGINS`.

### Router yang di-include
`auth`, `users`, `cases` (public + admin), `sessions` (v1), `sessions.v2` (`v2_router`), `sessions.v3` (`v3_router`), `exam`, `scoring`, `ai`, `eye_photos`, `admin`, `billing`, `mentor`, `analytics`, `ops`.

### Lifecycle (`lifespan`)
- Pastikan direktori upload (`upload_dir` + `eye-photos`).
- Seed super-admin dari `.env` (idempoten).
- Pre-warm catalog cache (v0.16.1, per-worker `lru_cache`).

---

## 4. Domains (`app/domains/`)

Pola standar per domain: `router.py` (HTTP) + `models.py` (SQLAlchemy) + `service.py` (logic) + `schemas.py` (Pydantic). Tidak semua domain punya keempatnya.

| Domain | Tanggung jawab |
|---|---|
| **auth** | JWT access/refresh, login, token refresh |
| **users** | profil & data user |
| **cases** | registry kasus + `v2_catalog.py` (loader kasus v2) |
| **sessions** | inti conversation; 3 router (v1/v2/v3) |
| **scoring** | rubric, hybrid scoring, kontrak output klinis |
| **mentor** | adaptive learning & journey (lihat §8) |
| **exam** | soal ujian + scorer |
| **ai** | STT transcribe + TTS (`/api/ai/*`) |
| **billing** | Midtrans (IDR) + Xendit (USD) |
| **eye_photos** | upload + analisis foto mata |
| **analytics** | metrik penggunaan |
| **admin** | super-admin ops |
| **ops** | healthcheck/ops |

---

## 5. Inti AI — Tiga Engine Conversation

Ini bagian terpenting. Ada **tiga generasi engine** yang hidup berdampingan, dan evolusi arsitekturalnya krusial untuk dipahami.

### 5.1 Engine v1 (legacy RAG) — `app/rag/engine.py`
RAG klasik:
```
load_case(case_id) → retrieve() BM25 → build_system_prompt() → LLM.stream()
```
- **Satu-satunya yang memakai BM25** (`app/rag/retriever.py`, in-memory `lru_cache`).
- Route: `/api/sessions/{id}/turns` (prefix `/api/sessions`).
- Retrieval mengisolasi per-kasus (Bagian A saja), tak pernah lintas kasus.
- **Status:** masih ter-mount, tapi tergeser oleh v2/v3.

### 5.2 Engine v2 — `app/rag/engine_v2.py`
```
load_v2_case(case_id) → build_patient_prompt() → LLM.stream()
```
- **Nol retrieval.** Patient context = **Part B persona body + answer-restraint scaffold** saja.
- **P1 guarantee:** Part A frontmatter TIDAK PERNAH masuk patient context.
- Mendukung multibahasa (parameter `language`).
- Live di `/api/v2/sessions/{id}/turns/stream`.

### 5.3 Engine v3 — `app/rag/engine_v3.py`
```
candidate_safe_view(variant) → v3_patient_prompt() → LLM.stream()
```
- **Nol retrieval.** Pasien dibangun dari **disclosure map** (canonical truth).
- Fakta hanya bocor lewat kategori `spontaneous` + aturan gating "jawab hanya yang ditanya".
- **Security:** prompt pasien TIDAK PERNAH menerima working_diagnosis, rubric, atau answer key.
- Dipakai saat `content_schema == "new"` (session v3).

### 5.4 Konsekuensi Arsitektural
> **Qora telah pivot dari RAG → "virtual patient berbasis disclosure gating".**
> Retrieval (BM25/Qdrant) adalah warisan v1, tidak relevan di v2/v3.
> Qdrant dikonfigurasi (`qdrant_url`) tapi **tidak berjalan**; dense retrieval ditunda.

### 5.5 Pemilihan Engine
- Field `sessions.content_schema` (`legacy` | `new`) menentukan jalur.
- `case_content_engine` setting (`v2` | `v3_compat`) memilih engine konten.
- `judge_engine` setting (`v2` | `hybrid`) memilih engine penilaian.

---

## 6. LLM Client — `app/rag/llm.py`

Abstraksi provider tunggal via `get_llm_client()`.

- **Provider default:** OpenRouter (OpenAI-compatible); fallback Anthropic; stub deterministik tanpa API key.
- **Retry:** 3x backoff untuk 5xx/timeout (free tier flaky).
- **Reasoning guard:** `deepseek-v4-flash` adalah reasoning model → reasoning **dimatikan** (`reasoning: {enabled: false}`) agar tidak menghabiskan `max_tokens` untuk chain-of-thought dan mengembalikan konten kosong.
- **Empty-content guard:** output seperti `"...."` / `"…"` dianggap transient → retry.
- **Timeout:** 120s (judge/patient tidak boleh hang UI).
- **Model:** `llm_model` (persona + judge), `llm_judge_model` (evaluator murah), `llm_author_model` (authoring).

---

## 7. Judging / Scoring

### `app/rag/judge_v2.py` & `judge_v3.py`
- LLM judge terkalibrasi, **bukan stub**.
- Menilai terhadap **anamnesis_checklist + red_flags** (bukan exam findings).
- Per-item: hit/partial/miss + evidence.
- Temperatur rendah (0.1); skor dihitung ulang server-side (tidak percaya aritmatika model).
- **Latency judge 47–86s** di OpenRouter; tidak di-cut terlalu dini.
- Judge context = Part A frontmatter + transcript (bukan diagnosis).

### `app/domains/scoring/`
- `rubric_v2.py` — dimensi & bobot penilaian.
- `hybrid.py` — hybrid scoring.
- `contracts.py` — kontrak output.

---

## 8. Mentor (`app/domains/mentor/`)

Sistem adaptive learning. **Prinsip desain sentral: LLM memahami & menjelaskan, planning engine (deterministik) yang memutuskan.**

| Modul | Fungsi |
|---|---|
| `journey_builder.py` | Pipeline LLM: story → extracted context (JSON) → case selection → proposal |
| `case_selector.py` | Algoritma seleksi kasus (PRD §4.1.2) |
| `planning_policy.py` | Keputusan kurikulum deterministik |
| `adaptive.py` | Keputusan remediasi/advance deterministik atas journey report |
| `coach.py` | Komposer kartu coach singkat & jujur |
| `mission.py` | Kartu "Today's Mission" + laporan akhir |
| `continuity_engine.py` | Memori pasien; missed red-flag → kasus "returning patient" |
| `readiness_calculator.py` | Skor readiness berbobot + trajectory + consistency |
| `autopsy_generator.py` | Autopsi penalaran: jalur siswa vs jalur expert, deteksi bias kognitif |

---

## 9. Pipeline Case Authoring (`pipeline/`)

Alat **offline** untuk build & validasi kasus (bukan runtime live).

```
pipeline/
├── parser.py              # parse file kasus .md → ParsedCase
├── case_v2.py             # schema v2
├── case_v3/               # schema v3 (canonical truth + disclosure map)
│   ├── models.py          # data model (ClinicalVariant, dll)
│   ├── loader.py          # loader kasus
│   ├── runtime.py         # candidate_safe_view (view aman untuk engine)
│   ├── derive.py          # derivasi
│   ├── semantic.py        # analisis semantik
│   ├── evidence.py        # bukti klinis
│   ├── governance.py      # governance konten
│   ├── redteam.py         # red-team testing
│   ├── qa.py / sourceqa.py# QA & source QA
│   ├── lint.py            # linting
│   ├── validate.py        # validasi
│   ├── treatment.py       # penanganan
│   ├── vocab.py           # kosakata klinis
│   ├── persona.py         # persona
│   └── formulary_id.py    # formularium
├── judge/                 # pipeline penilaian (engine, rating, feedback, calibration)
├── progress/              # longitudinal + readiness
├── surveillance/          # diff, impact, queue (monitor perubahan kasus)
├── clinical_contracts/    # fornas_reference, medication, scoring_output
├── embedder.py            # embedding (dense, ditunda)
├── ingest.py              # ingest kasus
├── registry.py            # registry kasus
└── author.py              # authoring
```

---

## 10. Data Layer

| Item | Detail |
|---|---|
| DB produksi | **Supabase** (PostgreSQL), transaction pooler `:6543` |
| DB dev | SQLite (`ophtha_dev.db`) |
| Engine config | `pool_size=10`, `max_overflow=10`, `pool_pre_ping`, `pool_recycle=300`, `pool_timeout=10` |
| Fail-fast | pool habis → 503 cepat (bukan 500/hang 30s) |
| Multi-tenant | tiap tabel punya `institution_id` |
| RLS | ON; grants anon/authenticated di-revoke |
| Migrasi | Alembic (10 versi) + `_ensure_runtime_columns()` fallback idempoten |
| Qdrant | Dikonfigurasi (`http://localhost:6333`) tapi **tidak berjalan** |

---

## 11. Shared Infrastructure (`app/shared/`)

| Modul | Fungsi |
|---|---|
| `security.py` | JWT encode/decode, bcrypt password |
| `dependencies.py` | `get_current_user`, `get_db` |
| `ratelimit.py` | Sliding-window rate limiter in-memory |
| `envelope.py` | Response wrapper `ok()` / `err()` |
| `request_id.py` | Request ID middleware |
| `security_headers.py` | Header keamanan HTTP |
| `feature_flags.py` | Feature flag |
| `mailer.py` | SMTP email |
| `observability.py` | Logging/observability |

---

## 12. Voice (`app/voice/`)

- **STT** (`stt.py`): Groq `whisper-large-v3-turbo`, bahasa Indonesia, MD5 dedup guard (window 5s).
- **TTS** (`tts.py`): Gemini `gemini-3.1-flash-tts-preview` (voice Gacrux, id-ID).

---

## 13. Payment (`app/domains/billing/`)

- **Midtrans** (IDR): server key, Snap.js, sandbox dulu (`midtrans_is_production=false`).
- **Xendit** (USD): secret key + webhook token verification (`x-callback-token`).

### Pricing (dari config)
- IDR: monthly Rp119.000, annual Rp999.000.
- ASEAN: monthly $9.99, annual $84.
- ROW: monthly $14.99, annual $119.
- Exam pass: $14.99.

---

## 14. Konfigurasi (`app/config.py`)

Pydantic `Settings` (env-driven). Kategori utama:

- **LLM:** `llm_provider`, `llm_model`, `llm_judge_model`, `llm_author_model`, `llm_base_url`, `llm_persona_max_tokens=1024`, `llm_judge_max_tokens=8000`.
- **Voice:** `stt_model`, `stt_language=id`, `tts_provider`, `tts_voice_id`, `tts_model`.
- **Auth:** `jwt_secret`, `jwt_alg=HS256`, `access_token_minutes=15`, `refresh_token_days=7`.
- **Rate limit:** `rate_limit_enabled`, `rate_limit_auth=20`, `rate_limit_ai=30`, `rate_limit_window_sec=60`.
- **Billing:** `billing_enforced`, `free_session_limit=5`, `free_case_limit=3`, `cost_alert_ratio=0.8`.
- **Content:** `case_content_engine`, `judge_engine`, `cases_dir`, `content_cases_dir`.
- **RAG (dormant):** `qdrant_url`, `embed_model`.

---

## 15. Karakter Arsitektur (Sifat Menyeluruh)

1. **Domain-modular** — tiap domain self-contained.
2. **I/O-bound, hampir stateless** — compute berat semua eksternal (DB/LLM/STT/TTS).
3. **Multi-engine coexist** — v1/v2/v3 paralel, dipilih via `content_schema`.
4. **Security-first di AI** — disclosure gating, anti-leak diagnosis/rubric, guardrail konten kosong, reasoning disabled.
5. **Sumber kebenaran kanonik** — `pipeline/case_v3` adalah canonical truth; engine live hanya membaca, tidak meng-generate.
6. **Planning deterministik, LLM untuk bahasa** — prinsip mentor (dan umumnya): engine memutuskan, LLM menjelaskan.

---

## 16. Versi & Catatan

- `app/main.py` menyatakan `version="0.15.0"`, namun komentar internal sudah merujuk hingga **v0.16.1** (pre-warm cache, 503 fail-fast, serve SPA). Field versi **tidak ikut di-bump** saat development — berpotensi misleading.
- Schema session: `content_schema` (`legacy` | `new`), `variant_id`, `variant_canonical_hash` (v3).
- Alembic saat ini **terblokir: 2 heads** yang perlu di-reconcile (catatan di source-of-truth).
