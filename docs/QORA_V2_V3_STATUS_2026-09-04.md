# Qora — Ringkasan Teknis & Keputusan Rollback v2

> Dokumen ini menjelaskan: **kasus/latar proyek**, **apa itu v2 vs v3**, **permasalahan yang kita temui 2–3 hari terakhir**, **hasil investigasi blank screen**, dan **keputusan yang kita ambil (rollback frontend penuh ke v2)**. Serta **struktur folder/file yang sebenarnya**.
>
> Tanggal: 2026-09-04
> Repo: `github.com/rafiarrantisi/vp-simulator` · Branch: `feature/pivot-v4`

---

## 1. Qora itu apa

**Qora** = Clinical Interview Trainer (virtual patient simulator) untuk melatih anamnesis (tanya-jawab klinis). Target pasar: Indonesia dulu (grounding ke PNPK Kemenkes), lalu APAC.

Arsitektur besar:
- **Frontend** di `sistemnya/` (Vite + React via Babel, tanpa bundler berat; pakai script loading order kustom).
- **Backend** di `backend/` (FastAPI + SQLAlchemy + Supabase Postgres), dijalankan via systemd `qora-backend`.
- **Content/case library** (data pasien virtual) di `content/`.
- **Deploy**: Cloudflare Pages `qoramedical.com` → fungsi `/api/*` → Cloudflare Tunnel → VPS (port 8000).

Ada **dua "generasi" sistem kasus** di codebase: **v2 (legacy, production)** dan **v3 (case rebuild, eksperimental)**.

---

## 2. v2 (LEGACY) — yang saat ini jadi production utama

v2 adalah sistem kasus **yang sudah ada sejak lama dan beneran dipakai/diparkir sebagai production** sebelum ada rebuild.

- File content: `content/cases/*.md` — relatif **92 file berformat `.md` dengan frontmatter YAML** (contoh: `em_acs_001.md`, `derm_cellulitis_001.md`, dsb).
  - `schema_version: 2` (makanya disebut v2), `status`, `specialty`, `presentation`, `first_impression`, `target_condition`, `mode_default: osce_full`, `source_refs`, `languages`, dsb.
- Backend pendukung v2:
  - `backend/app/domains/sessions/v2_router.py` + `router.py` — endpoint `/api/v2/...` dan `/api/...` untuk sesi, turn, score.
  - `backend/app/rag/engine_v2.py`, `prompt_v2.py`, `judge_v2.py`, `retriever.py`, `llm.py` — engine pasien AI & evaluator versi 2.
- Frontend component utama v2: **`sistemnya/qora-v2.jsx`** — berisi `QoraV2Screen` (daftar kasus/case library), `QV2Session` (sesi chat), `QV2SessionSetup` (setup: pilih mode Practice/OSCE, bahasa, mic), dan komponen reusable: `QV2MicButton`, `QV2TaskPanel`, `QV2TimeUpModal`, `QV2PrepRow`, `QV2ModeCard`.
- **Route**: `/cases` (hash `#/cases`) → `QoraV2Screen`.

**Ciri v2:** daftar kasus per-entri (92 file `.md`), masing-masing punya target condition & skenario, mode OSCE/khatam, mic untuk tanya jawab suara. Tanpa family-based grouping, tanpa SKD terstruktur, tanpa pipeline validasi besar.

---

## 3. v3 (CASE REBUILD) — eksperimental yang kita bangun lalu rollback

Mulai **~STEP 1 s/d STEP 9** kita bangun sistem kasus generasi baru ("case rebuild") dengan tujuan lebih klinis & terkontrol:

- Content baru di **`content/v3/`**: **berbeda sama sekali dari v2** (bukan `.md`, tapi `families/` + `variants/` yaml + `catalog/`).
  - `content/v3/families/` — 5 family: `fam_dengue`, `fam_fever_child`, `fam_hypertension`, `fam_pyelonephritis`, `fam_uti`.
  - `content/v3/variants/` — **12 variant** (contoh `dengue_003_severe.yaml`).
  - `content/v3/catalog/` — master catalog **SKD 2026 (515 entri)** dari PDF resmi `skd_dokter_2026.pdf`, plus `roadmap.json`, `canonical_entities.json`.
  - `content/v3/human_review_records.json` — catatan review manusia (promosi ke `pilot_verified`).
- Backend v3:
  - `backend/app/domains/sessions/v3_router.py`, `v3_service.py` — endpoint `/api/v3/...`.
  - `backend/app/rag/engine_v3.py` — live patient engine untuk v3.
  - `backend/pipeline/case_v3/` — pipeline besar: `loader`, `models` (ClinicalVariant dataclass), `derive`, `lint`, `qa`, `redteam`, `semantic`, `sourceqa`, `governance`, `runtime`, `persona`, `vocab`.
  - `backend/tools/` — tool generate/audit/promosi: `generate_batch.py`, `final_audit.py`, `redteam_live.py`, `promote_cases.py`, `run_qa.py`, `source_spotcheck.py`, dst.
- Frontend v3: **`sistemnya/qora-v3.jsx`** (baru, dibuat STEP 7) → `QoraV3App` (library, family cards, session, debrief).

**Ciri v3:** family-based, variant klinis, canonical layer, SKD 2026 sebagai kompetensi primary, promosi bergate (QA gate → human review → pilot), laporan strict-split (`generated` / `QA-passed` / `clinically_reviewed` / `pilot_verified`), blind-mode aman di level API.

---

## 4. Kronologi permasalahan (kenapa akhirnya rollback)

### 4.1 Awalnya: kita naikkan v3 ke `/cases`
User minta `/cases` jadi library v3 dan alurnya mirip v2 (pilih Practice/OSCE → setup mic → chat dengan AI pasien). Workflow yang kita kerjakan:
1. Ubah route `/cases` → render `QoraV3App` (v3 library).
2. Bangun `engine_v3` + endpoint `/api/v3/sessions/{id}/turns` biar pasien AI live.
3. `QoraV3Session` jadi chat UI (mirror v2: brief → vitals → chat → debrief).
4. Setup screen pakai `QV2SessionSetup` (reuse komponen v2).
5. Klik family → (awalnya) ke halaman detail `#/v3/family/<id>`, lalu "Start practising" → setup → session.

### 4.2 Bug pertama yang bikin frustrasi: halaman detail redundan
- User klik family dari `/cases` **nyasar ke `#/v3/family/fam_dengue`** dulu (halaman detail), baru "Start practising" ke setup. User anggap redundan — dan dia **benar**.
- Fix: klik family langsung ke `session/setup/<fam>` (skip halaman detail).

### 4.3 Bug utama & berkepanjangan: **session blank (hanya header + footer)**
Puncak masalah: setelah start session, layar **blank polos** — hanya header nav + footer, tanpa tulisan apa pun, tidak ada error.

Yang kita lakukan & temuan (kronologis):
1. **Cek backend dulu** — `/api/v3/sessions` live **200 OK** (data valid, contoh `htn_003_urgency_diabetes`). Backend **bukan sumber masalahnya**.
2. **Cek bundle live vs lokal** — sempat ada mismatch hash (deploy edge-cache). Setelah propagation, live = lokal.
3. **Cek render/logic** — `QoraV3Session` punya guards: kalau `data` null → render "Starting…", kalau `err` → render "Error: ...", kalau stage chat → render chat. Secara logika **mustahil blank polos** kalau komponen benar-benar dimount.
4. **Temuan kunci:** blank tanpa error (bukan "Error:...") berarti **komponen session tidak benar masuk ke DOM `main`** — atau **React render error yang di-swallow diam-diam**, karena error boundary dipasang **terlalu dalam** (di dalam `QoraV3App`), sehingga kalau `QoraV3App` gagal mount, boundary itu tidak pernah aktif.
5. **Beberapa bug nyata yang kita perbaiki di v3:**
   - **Double-mount `QoraV3App`**: ketika hash `#/v3/session/...`, kondisi `screen==='cases'` **dan** kondisi route `#/v3/...` sama-sama render `QoraV3App` → dua router/effect bentrok → dibuat mutually exclusive (satu route = satu mount).
   - **Query `?lang=en` ikut terbaca sebagai mode**: URL `...#/v3/session/fam_x/targeted?lang=en` → parser membaca mode `"targeted?lang=en"` (bukan `targeted`) → backend gagal validasi mode. Parser dipisah dengan `split('?')[0]`.
   - **Fallback render**: `QV2TaskPanel`, `QV2MicButton`, `QV2TimeUpModal` dipaket dengan `typeof X === 'function'` guard; vitals dinormalisasi `String(v.name||'vital').replace(...)` supaya data shape tak sempurna tidak bikin blank.
   - **Boundary dinaikkan ke level app shell** (`V3Boundary` di luar `QoraV3App`) supaya error tampak, bukan blank.
6. **Tetap blank setelah semua itu** (beberapa kali). Walau secara analisis "logika-impossible", faktanya user tetap lihat blank. Kemungkinan akar yang tersisa di v3: ada render error level shell yang tetap di-swallow, atau interaksi load-order/bundle, atau race di routing shell `screen` yang tidak bisa kita reproduksi penuh di lingkungan headless (kita tidak bisa login asli di browser otomatis sehingga tidak 100% mereproduksi kondisi user).

**Kesimpulan investigasi:** masalah v3 bukan di backend (teruji 200), bukan di data, dan bukan di API contract. Akar paling masuk akal adalah **routing/render level shell frontend v3 yang tidak stabil** (double-mount + mode parsing + boundary placement) yang setelah berkali-kali diperbaiki masih belum 100% deterministik di kondisi user.

---

## 5. Keputusan kita (final)

> **Rollback frontend penuh ke v2.** Kembalikan `/cases` ke kasus-kasus lama (QoraV2Screen), hapus `qora-v3.jsx`, sehingga **sejak sisi user seakan-akan v3 tidak pernah dibuat**.

Pertimbangan:
- Frontend v3 belum cukup stabil untuk dijadikan production; tidak mau mengorbankan pengalaman user (case library v2 yang selama ini jalan) demi fitur yang masih bermasalah.
- Backend v3 (`/api/v3/*`) **tidak dihapus**, karena:
  - sudah teruji (QA gate, live red-team, human-gate promotion);
  - frontend v2 tidak memanggilnya sama sekali → dari sisi user tidak kelihatan;
  - menghapusnya berisiko & tidak diminta → nanti bisa dipakai ulang kapan pun.
- Rollback dilakukan **tanpa menghapus history git** (pakai `git checkout` file ke commit lama + `git rm`).

### Yang diubah (commit `1f437c5`)
```
Rollback frontend penuh ke v2
  6 files changed, 19 insertions(+), 1039 deletions(-)
  delete mode 100644 sistemnya/qora-v3.jsx
```
- `sistemnya/Virtual Patient Simulator.html` → `screen==='cases' && React.createElement(QoraV2Screen, null)` (v2).
- `sistemnya/qora-v2.jsx` → dikembalikan ke v2 (tanpa branch `#/v3`).
- `sistemnya/build/bundle-legacy.mjs` → load order kembali tanpa `qora-v3.jsx`.
- `sistemnya/qora-v3.jsx` → **dihapus**.
- `sistemnya/src/main.jsx` & `dist/index.html` → diregenerate dari sumber v2.
- Verifikasi: 0 referensi `QoraV3App` di bundle, `/cases` → `QoraV2Screen`.

### Hasil setelah rollback (terverifikasi)
- Build v2 murni → bundle `index-D8fjBTzb.js`.
- Deploy → `qoramedical.com` serve bundle v2 (sempat edge-cache, sudah propagate).
- `/cases` kembali menampilkan `QoraV2Screen` (kasus-kasus lama).

---

## 6. Struktur folder/file yang sebenarnya

```
vp-simulator/                       # repo root
├── AUDIT.md
├── BUILD_PLAN_pivot_v4.md
├── Caddyfile                       # reverse-proxy (opsional lokal)
├── backend/                        # Backend FastAPI (production)
│   ├── alembic/ ─ alembic.ini     # migrasi DB
│   ├── docker-compose.yml ─ Dockerfile
│   ├── pyproject.toml ─ requirements.txt
│   ├── app/                       # aplikasi
│   │   ├── main.py ─ config.py ─ database.py
│   │   ├── domains/               # auth, billing, cases, sessions, scoring,
│   │   │                          #   ai, admin, analytics, exam, mentor, users, eye_photos
│   │   │   └── sessions/          # models, router (v2 umum), schemas,
│   │   │                          #   v2_router.py, v3_router.py, v3_service.py
│   │   ├── rag/                   # engine.py, engine_v2.py, engine_v3.py,
│   │   │                          #   llm.py, prompt(v2), judge_v2, retriever, evaluator, answer_key
│   │   ├── shared/ ─ voice/       # helper & STT
│   ├── pipeline/case_v3/          # pipeline v3: loader, models, derive, lint,
│   │                              #   qa, redteam, semantic, sourceqa, governance,
│   │                              #   runtime, persona, vocab, validate
│   ├── tests/                     # test suite (core + extensive + live)
│   ├── tools/                     # author/pipeline/audit tooling (lihat §7)
│   ├── data/ ─ qa/ ─ uploads/
│   └── scripts/
│
├── content/                       # Library data kasus
│   ├── cases/                     # ⭐ V2 (LEGACY, PRODUCTION) — 92 file .md
│   │                              #   (frontmatter: id, schema_version:2, status,
│   │                              #    specialty, presentation, first_impression,
│   │                              #    target_condition, mode_default:osce_full,
│   │                              #    source_refs, languages, authoring…)
│   ├── scaffold/                  # template/basis authoring
│   └── v3/                        # Case rebuild (eksperimen, ttak dipakai di UI)
│       ├── families/              # 5 family yaml (fam_dengue, fam_hypertension…)
│       ├── variants/              # 12 variant yaml (contoh dengue_003_severe)
│       ├── catalog/               # SKD 2026 master (515), roadmap, canonical_entities
│       └── human_review_records.json
│
├── sistemnya/                     # ⭐ Frontend (Vite + React via Babel)
│   ├── Virtual Patient Simulator.html   # host + inline App (routing hash, auth, shell)
│   ├── qora-v2.jsx                # ⭐ V2 UI: QoraV2Screen, QV2Session, QV2SessionSetup + micro, mic, task panel
│   ├── qora-landing.jsx           # landing/login
│   ├── qora-pf.jsx ─ qora-mentor.jsx ─ qora-enhancements.jsx ─ qora-catalog.js
│   ├── qora-checkout.jsx          # billing/checkout
│   ├── design.css                 # design tokens (SACRED — jangan diubah)
│   ├── translations.js            # i18n
│   ├── index.html ─ vite.config.js ─ package.json
│   ├── build/bundle-legacy.mjs    # LOAD_ORDER + extract inline App -> src/main.jsx
│   ├── src/                       # hasil bundle (generated) — main.jsx
│   ├── dist/                      # hasil build (generated) — untuk deploy
│   ├── public/ ─ engine/ ─ exam-sim/ ─ uploads/
│   └── (qora-v3.jsx — DIHAPUS saat rollback)
│
├── data-kasus/                    # bahan/mentah kasus
├── deploy/cloudflare/deploy.sh    # build + wrangler pages deploy ke qoramedical
├── docs/                          # dokumen perencanaan
└── scripts/
```

---

## 7. Tooling pipeline v3 (tetap ada di `backend/tools/`, tidak dihapus)

Tool yang kita bangun selama case rebuild — semuanya tetap tersimpan dan bisa dipakai ulang:

| Tool | Fungsi |
|------|--------|
| `author_case.py` | Authoring kasus terpandu |
| `build_master_catalog.py`, `extract_skd2026.py` | Ekstrak/parse SKD 2026 (515 entri) |
| `build_roadmap.py` | Prioritas roadmap kasus |
| `generate_batch.py` | Batch generator terpandu (max `research_complete`) |
| `lint_v3.py`, `case_inventory.py` | Lint & inventori kasus |
| `run_qa.py`, `final_audit.py`, `source_spotcheck.py` | QA gate, audit strict-split, spot-check sumber |
| `redteam_live.py`, `promote_cases.py` | Red-team AI live, promosi human-gated (→ pilot_verified) |
| `seed_patient_series.py`, `assign_unique_names.py`, `localize_cases.py`, `pilot_curate_v2.py` | Pendukung authoring |

---

## 8. Status final & next step (opsional)

- **Sekarang**: frontend = v2 murni di production (`/cases` = kasus lama). Semua stabil & hidup.
- **Backend v3**: tetap ada (teruji), tapi tidak dipakai frontend — tidak terlihat oleh user.
- **Kalau nanti mau lanjut v3**: kita masuk dari titik yang lebih stabil — bakar ulang frontend v3 dengan routing/shell yang sudah divisi ulang (jangan double-mount, parser query dipisah, boundary di shell), atau evaluasi apakah cukup memperbaiki bug-bug yang sudah kita identifikasi. Keputusan bisa dibahas terpisah.

> Inti pelajaran: **backend v3 solid; yang bermasalah adalah integrasi frontend v3 ke shell routing.** Rollback ke v2 mengembalikan UX yang dapat diandalkan sambil menyimpan seluruh work v3 untuk dipakai nanti.