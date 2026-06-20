# AUDIT.md — Phase 0 Repo Audit (Pivot v4)

> **Purpose:** Ground-truth inventory of the existing **OphthaSim** codebase before the broad-specialty pivot (`BUILD_PLAN_pivot_v4.md`). Every claim below was verified against the actual code, not the owner's verbal description. Divergences from the build plan's assumptions are flagged **⚠**.
>
> **Audited:** 2026-06-20 · **Branch:** `master` (see §0) · **Product version in code:** `0.16.0`

---

## 0. Local repository / environment state (verify-first findings)

This local working copy is **not** the live repo's history — it is a file snapshot.

| Fact | Finding | Implication |
|---|---|---|
| Git history | **Zero commits.** Branch `master`, no `main`, no other branches. | The plan's "branch off `main`, keep `main` deployable" model has no local baseline. We must create a baseline commit first (§ Phase-0 actions). |
| Git remote | **None configured** (`git remote -v` empty). | The live GitHub repo (`rafiarrantisi/new-simulator-anamnesis`, per `docs/HANDOFF.md`) is not wired here. Cutover/PR flow will need the remote added, or this stays a local-only pivot tree. |
| Secrets hygiene | `.gitignore` ignores `.env`, `**/.env`, `*.key`, `*.pem`, `*.db`. `git check-ignore` confirms `backend/.env` + `sistemnya/.env` are ignored. | Baseline commit is **safe** — real secrets won't be committed. `.env.example` files are tracked templates. |
| Backend runtime | No `.venv` present. System Python **3.13.11** available. | Created `backend/.venv` + installed `requirements.txt` as Phase-0 setup. |
| Frontend runtime | No `node_modules` in `sistemnya/`. | `npm install` needed before any FE build/verify. |
| Cases on disk | **31** markdown files: 9 active `kasus-101..109` + 22 legacy `kasus-01..22`. 6 disclosure sidecars (`kasus-01,02,09,10,16,17`), 1 exam sidecar (`kasus-02`). | Matches HANDOFF. **⚠ All cases are in Bahasa Indonesia** (see §8). |

---

## 1. Exact stack, infra, and how it deploys today

### Backend — `backend/`
- **Language/Framework:** Python 3.13, **FastAPI** (`app/main.py`), Uvicorn, domain-modular layout (`app/domains/<domain>/{models,schemas,service,router}.py`).
- **ORM/DB:** SQLAlchemy 2.0. **Dev = SQLite** (`ophtha_dev.db`); **prod target = PostgreSQL** (`psycopg2-binary`). Migrations via **Alembic** (`alembic/versions/`: baseline, exam_records, eye_photos_and_admin_audit, cases_locked). A `_ensure_runtime_columns()` startup ALTER guards SQLite drift.
- **Auth:** Custom **JWT** (`pyjwt`), bcrypt password hashing, access+refresh tokens. No third-party auth SDK.
- **LLM access:** **OpenRouter** (OpenAI-compatible) via the `openai` SDK; provider-agnostic abstraction with an Anthropic adapter stubbed and a deterministic `StubLlmClient` fallback when no key is set.
- **RAG:** **BM25** (`rank-bm25`) over a single case's Part-A sections — *not* a vector store (Qdrant is config-stubbed but dormant). See §3.
- **Voice:** Architecture present (`app/voice/stt.py`, `tts.py`), **disabled** (no STT/TTS keys → mic hidden, TTS silent).
- **Other middleware:** custom security headers, in-memory rate limiting, response envelope `{success,data,error,meta}`, prod-safety guard that refuses unsafe prod/staging config.
- **Tests:** **pytest** (`pyproject.toml`: `pythonpath=["."]`, `testpaths=["tests"]`). See §6.

### Frontend — `sistemnya/`
- **Framework:** **React 18**, authored as **plain `.jsx`/`.js` in a single shared scope** (no per-file imports/exports), concatenated by a custom bundler (`build/bundle-legacy.mjs` → generated `src/main.jsx`) and built with **Vite**.
- **Hard discipline (§8.1 of ARCHITECTURE):** `design.css` + markup are **byte-identical** across builds; the production CSS hash must stay `index-Bj97HpXF.css`. `src/main.jsx` is generated — never hand-edited.
- **Seams:** UI talks only to `PatientEngine`, `Evaluator`, `DataStore` (`sistemnya/engine/*.js`). `StaticPatientEngine` (legacy/offline) and `RagPatientEngine` (backend WS streaming) both satisfy the seam; selector = `window.OPHTHA_API_BASE`.
- **Exam-sim sub-package:** `sistemnya/exam-sim/` is a **separate, dormant** TypeScript+Vite+Zustand+Pixi/R3F package (scoped exception, Shadow-DOM isolated). **Out of the pivot's MVP scope** and de-wired from `LOAD_ORDER`.

### Infra / hosting (live today)
- **AWS EC2** `t3.small`, Ubuntu, **Sydney `ap-southeast-2`**, Elastic IP, domain `ophtasim.duckdns.org` (DuckDNS), **Let's Encrypt** TLS via certbot, **nginx** (HTTP/2 + WS upgrade map) reverse-proxying `^/(api|health)` → uvicorn.
- **Deploy kit:** `deploy/` — `setup.sh` (idempotent provisioner), `nginx-ophtha.conf`, `ophtha-backend.service` (systemd, 1 uvicorn worker, SQLite-safe), `apply-update.sh` (turnkey update+ingest+lock+verify), `duckdns-update.sh`.
- **Prod DB:** SQLite file on EBS (`ophtha_prod.db`) — *not yet Postgres*.
- **Deploy flow:** SSH/EC2-Instance-Connect → `git pull` → `bash deploy/setup.sh` → `pipeline.ingest` → `manage_cases` lock/stage → `systemctl restart`.

**⚠ Plan-vs-reality:** The build plan's "reported state" undersells this. There is already a full FastAPI backend, JWT auth, an admin CMS ("Developer Dashboard"), Alembic migrations, eye-photo upload/serving, and a working WS streaming patient chat — all **live in production**. The pivot is an *extension/generalisation*, not a greenfield backend build.

---

## 2. Case file parsing & how Part A / Part B are kept apart at runtime

**This is the leakage-prevention core (moat P1).**

- **Parser:** `backend/pipeline/parser.py`. Filename contract `kasus-XX-slug.md` (regex). Splits the document on `## BAGIAN A` … `## BAGIAN B` markers into:
  - `bagian_a_sections: list[Section]` — Part A clinical knowledge, chunked **per `### N.` section**.
  - `bagian_b_text: str` — Part B persona prose (not chunked).
  - `disclosure_text` — from in-file `### 0. DISCLOSURE LAYERS` **or** a sidecar `data-kasus/_disclosure/kasus-XX.md`.
- **Runtime separation:**
  - **Patient turn** (`app/rag/engine.py` → `prompt.build_system_prompt`): system prompt = Part B persona **+** disclosure **+** `ANSWER_RESTRAINT` **+** `GUARDRAIL` **+ retrieved Part-A chunks** **+** first-turn instruction. Streamed to client as **reply text only** — Part B / disclosure prose never leaves the server.
  - **Judge turn** (`app/rag/evaluator.py`): context = a Part-A section (the "checklist") **+** transcript only. Never sees Part B.
- **Client isolation:** the frontend only ever receives `CaseSummary` metadata + streamed reply tokens. Part B and Part A raw text are server-only.

**⚠ Important divergence from BUILD_PLAN §5.2.** The plan says: *"Patient turn: system context = Part B body + Disclosure Rules ONLY. Never inject Part A."* The current implementation **does inject retrieved Part-A chunks** into the patient prompt (block: `FAKTA KLINIS RELEVAN`) so the persona can answer factual questions it can't infer from the persona body. This is a deliberate design choice, not a bug. Schema v2 should make Part B's "What I know" block self-sufficient so Part-A injection into the patient context can be dropped — bringing the implementation in line with the plan's structural guarantee. **Decision needed in Phase 1** (see §9).

---

## 3. RAG layer — what it actually is, and whether it is needed

- **Implementation:** `app/rag/retriever.py`. Pure **BM25** (`rank_bm25.BM25Okapi`, with a pure-Python overlap-count fallback if the lib is missing). The index is built **only from the active case's Part-A sections** (`@lru_cache` per `case_id`). `retrieve(case_id, query, k=3)` returns top-k sections of **that case only**.
- **Per-case isolation:** structural — the corpus literally contains only one case's sections, so cross-case retrieval is impossible. No Qdrant, no embeddings, no vector DB in the running path. `qdrant_url` / `embed_model` exist in config but nothing uses them. `pipeline/embedder.py` is a stub.

> ### DECISION (RAG) — CONFIRMED, aligns with BUILD_PLAN
> The build plan's `// DECISION (RAG): default to REMOVING vector-RAG` is **already the de-facto state** — there is no vector RAG to remove. A single case markdown is small and fits in context.
>
> **Recommendation:** Keep the thin BM25 retrieval abstraction for now (it's cheap, infra-free, and already provides the "inject only relevant Part-A facts" behaviour the patient model uses). For schema v2, the cleaner long-term move is: **load only the selected case's Part B into the patient context, and only Part A into the judge context** — and either (a) drop Part-A retrieval from the patient path once Part B is self-sufficient, or (b) keep BM25 purely as an internal "relevant-facts" selector for large cases. Reserve any future vector store for a *knowledge-base / explanation* feature, not per-case isolation. **No Qdrant work needed for the pivot.** Confirm (a) vs (b) with the owner in Phase 1.

---

## 4. Judge prompt construction & where rubric weights live

- **Judge:** `app/rag/evaluator.py` → `evaluate(case_id, transcript, ddx, management_plan)`.
- **Prompt:** built in `_judge_prompt()`. System message describes an OSCE anamnesis grader; user message = `CHECKLIST` (a Part-A section) + `LOG` (formatted transcript) + optional student DDx/management block. Output is required to be JSON matching `EvaluationReport`.
- **Model:** uses a **separate, cheaper** `llm_judge_model` (config), distinct from the persona model. Runs through the same `LlmClient`. Stub fallback returns a valid-shaped zero report; parse failure falls back to a valid empty report (scoring never fails the session).
- **⚠ Rubric weights are HARDCODED in code,** not config:
  ```python
  # app/rag/evaluator.py
  _RUBRIC = {"coverage": 40, "fife": 20, "redFlags": 20, "communication": 20}
  ```
  The frontend `EvaluationReport` type and the ARCHITECTURE contract (§3A) also bake in `coverage 40 / fife 20 / redFlags 20 / communication 20`. **Phase 3 must make weights data-driven** (mode config + per-case `scoring_weights_override`) and add the `osce_full` mode + DDx/investigation/management dimensions. The plan keeps the legacy 40/20/20/20 as a named `classic_anamnesis` preset.
- **Calibration:** none today. No temperature pinning for the judge (temperature 0.5 in the OpenAI adapter), no ensemble, no human-vs-AI threshold tuning. Phase 3 work.

---

## 5. Confirmation of the known gap (checklist / red-flag fallback) — VERIFIED IN CODE

The owner reported that newer cases' Part A lacks an explicit anamnesis checklist + red-flag list, so Coverage & Red-Flag scoring falls back to physical-exam findings. **Confirmed:**

```python
# app/rag/evaluator.py
def _checklist(case_id):
    pc = load_case(case_id)
    for s in pc.bagian_a_sections:
        if "anamnesis" in s.name.lower():
            return s.text
    return pc.bagian_a_sections[3].text if len(pc.bagian_a_sections) > 3 else ""
```

- The 9 active PPK preclinical cases (`kasus-101..109`) have Part-A sections: *Diagnosis, Patofisiologi, Faktor Risiko, **Temuan Klinis Objektif**, Komplikasi, Tatalaksana*. **None is named "anamnesis."**
- So `_checklist()` falls through to `bagian_a_sections[3]` = **"Temuan Klinis Objektif" (objective/physical-exam findings)**. The judge therefore grades anamnesis *coverage* and *red-flags* against **physical-exam data**, not against an elicitation checklist.
- There is **no dedicated `red_flags` structure** anywhere; the "Red-Flag" dimension is inferred by the LLM from whatever section it's handed.

**This is exactly the gap schema v2 closes** (explicit `anamnesis_checklist` + `red_flags` in frontmatter, moat P2). It is the single highest-leverage correctness fix in the pivot.

---

## 6. Test coverage map

Suite location `backend/tests/`. HANDOFF reports **79 passed, 1 skipped** at v0.16.0 (to be re-confirmed against the fresh venv — see Phase-0 setup task).

| Test file | Covers | Notes |
|---|---|---|
| `test_parser.py` | Markdown parse + validate, parametrized over all 31 cases | Strong; the migration safety net. |
| `test_restraint_qa.py` | Answer-restraint QA harness wiring (`qa/restraint_qa.py`) | **⚠ Heuristic + LLM-dependent**; skips under StubLLM. Only kasus-02. Not a strict structural P1 test. |
| `test_rag.py` | BM25 retrieval + per-case isolation | |
| `test_api_smoke.py` | App boots, routes mount, health | |
| `test_security.py` | Security headers, prod guard, rate limit | |
| `test_exam.py` | Exam scorer (dormant module) | |
| `test_admin_dashboard.py` | Admin gating (403/401), case CRUD, photo upload, audit | 14 tests. |
| `test_voice.py` | Voice endpoints (degrade when keys absent) | |

**Gaps for the pivot (new tests required):**
- (P1) A **structural** A/B leakage test: assert the patient never emits un-elicited red-flag tokens to a generic opener, and assert Part-A/Part-B are never co-injected where the plan forbids it. The existing restraint QA is LLM-dependent and not a hard gate.
- Case **linter** unit tests (Phase 1).
- Judge **output-schema** validation (Phase 3).
- **Entitlement/gating** server-side enforcement + **webhook** handling (Phase 4).

---

## 7. Auth & data model (what exists today)

- **`User`** (`app/domains/auth/models.py`): `id, email (unique), hashed_password, full_name, nim, institution_id (multi-tenant since day 1), role ∈ {student,instructor,admin}, created_at`.
- **`UserProfile`**: `user_id (PK/FK), xp, streak, total_sessions, avatar_emoji, avatar_color, school, year, extra (JSON blob for un-normalised gamification)`.
- **`SessionRow`** (`app/domains/sessions/models.py`): `id, user_id, institution_id, case_id, mode, status (active|completed), started_at, ended_at, total_score, report (JSON = EvaluationReport)`.
- **`SessionTurn`**: `id, session_id, turn_number, role (user|patient|system), content, created_at`.
- **`CaseRegistry`** (`app/domains/cases/models.py`): catalogue metadata only — `case_id, filename, title_id, title_en, icd10, skdi, organ_system, difficulty, tags, references, stage (preklinik|koas), case_type (practice|osce), collection_name, chunk_count, has_disclosure_layers, is_active, locked, ...`. **⚠ Eye-centric defaults** (`organ_system` defaults to `"Mata"`).
- **`EyePhoto`** + **`AdminAuditLog`** (eye_photos / admin domains): media metadata + admin forensic log.

**What's MISSING for B2C (Phase 4):**
- **No billing/entitlement at all** — no plan, subscription, usage-counter, or MoR tables. `role` exists but there is no paid tier concept.
- **No OAuth** (Google etc.) — email/password JWT only. No email verification / password-reset flow.
- **No per-session cost/token-spend tracking** (cost guardrail).
- Admin auth is a single `.env`-seeded super-admin (intentional, §9 K9 of ARCHITECTURE).

---

## 8. ⚠ Language: the cases are Bahasa Indonesia; the pivot target is English

- All 31 case files (Part A clinical + Part B persona) are written in **Indonesian**, with richly idiomatic casual-Jakarta personas (e.g. kasus-101 "Mbak Sinta", *"kayak sepet, perih, ada sensasi berpasir"*). Answer-restraint is encoded in Indonesian persona rules ("ATURAN KOMUNIKASI").
- `BUILD_PLAN §1/§15` mandates **English** product + content (market = English-speaking APAC/Australia + IMG exam candidates).
- **Implication:** migrating the 9 active cases to schema v2 is **restructure + translate**, and the translation must *preserve persona quality and the lay-language answer-restraint*, not just word-swap. The judge/persona prompts in `app/rag/prompt.py` and `app/rag/evaluator.py` are also **Indonesian** and will need English equivalents (config/locale-driven, ideally).
- This raises an owner question: do the migrated ophthalmology cases ship **English-only**, or is there a bilingual interim? (Plan says English-only; flagging because it affects effort and the live ID users.)

---

## 9. Decisions/divergences to confirm before/within Phase 1

1. **Part-A injection into patient context** (§2): adopt the plan's strict "Part B only" rule once schema v2's persona body is self-sufficient? (Recommended: yes; keep BM25 as an optional large-case fact selector.)
2. **RAG abstraction** (§3): keep thin BM25 (a) as dormant or (b) as patient-side fact selector? (Recommended: keep, demote.)
3. **Language** (§8): English-only migration of the 9 eye cases, English persona/judge prompts. (Plan says yes.)
4. **Git baseline & remote**: create local baseline commit + `feature/pivot-v4` now (done in Phase-0 setup); wire the GitHub remote later for real cutover. The live prod tree is the rollback, not this local `master`.
5. **Owner decisions still open** (BUILD_PLAN §14): product name, MoR (Lemon Squeezy vs Paddle), price points, launch specialty set & count, reviewer model, OSCE timer toggle. None block Phase 1; name/MoR/prices block Phases 4–6.

---

## 10. Phase 0 Definition of Done — status

| DoD item | Status |
|---|---|
| `AUDIT.md` committed | **This file** (commit in Phase-0 git task). |
| Staging stood up from current `main` | **Adapted** — no local `main`/remote. Baseline commit on `master` + `feature/pivot-v4` branch created as the working tree; live EC2 remains prod. Real staging deploy deferred until a remote is wired (owner action). |
| `feature/pivot-v4` branch created | In Phase-0 git task. |
| CI runs existing tests green | Fresh venv created; baseline `pytest` run in Phase-0 setup task. |

> **Bottom line:** The codebase is a mature, live, well-documented ophthalmology trainer. The pivot is a *generalisation* along three axes — (1) specialty-agnostic schema v2 that closes the checklist/red-flag gap, (2) data-driven mode-aware scoring + answer-key reveal, (3) B2C auth/payments — layered onto solid existing seams (PatientEngine / Evaluator / DataStore, domain-modular FastAPI). Biggest non-obvious lifts: **English translation of persona/judge/content**, and **net-new billing/entitlement** (none exists today).
