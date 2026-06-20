# BUILD PLAN — Broad-Specialty Anamnesis Simulator (Pivot v4)

> **Audience:** Claude Code (agentic build agent).
> **Author of intent:** Rafi (product owner). Strategy is locked; this document is the execution spec.
> **Starting point:** An existing **live** product ("OphthaSim" — ophthalmology-only, hosted on AWS EC2 + HTTPS) is the starting codebase. This plan pivots it. Do **not** assume — audit first (Phase 0).

---

## 0. How to use this document

- Read the whole document before writing any code. The phases are **ordered**; respect dependencies.
- This is a brief, not gospel. Where a `// DECISION:` block states a choice, follow it unless the Phase 0 audit reveals it is impossible — in which case surface the conflict and propose an alternative, do not silently diverge.
- **Work on a long-lived branch** `feature/pivot-v4` against a **staging** environment. `main` must stay deployable to the current live ophthalmology build until cutover (Phase 6). Never break production mid-flight.
- Every phase has a **Definition of Done (DoD)**. Do not advance until DoD is met and tests pass.
- The product, codebase, and all UI copy are in **English**. (The product owner is Indonesian; the *market* is English-speaking. Do not localise to Bahasa.)
- Replace the token `{{PRODUCT_NAME}}` everywhere it appears once a name is chosen (see §3). Until then, leave the token.
- Preserve the three **moat features** (§2) as hard requirements. Engineering convenience must never sand these off.

---

## 1. Mission & product thesis

We are building a **B2C, text-first, broad-specialty patient-interview (anamnesis) trainer** for **individual medical students in English-speaking Asia-Pacific / Australia and IMG exam candidates** (UKMLA/PLAB, AMC, USMLE-adjacent). Students interview an AI patient, then receive **instant, transparent, calibrated scoring against a hidden checklist plus a full model-answer reveal**.

We are deliberately positioned **between** two real competitors:
- **Above** "Cogni by Mediko" (Indonesia-only, Bahasa-only, quota-gated lite OSCE tool — proves the UX works but is geographically boxed in).
- **Below** "Geeky Medics SimChat" (institution-sold B2B; text + voice + **video avatars**; 1000+ scenarios — too heavy/expensive to replicate; its video avatars are a cost moat, not a student need).

**Pricing posture:** cheap, exam-season-skewed subscription (~US$8–20/mo) plus freemium. Monetised via Merchant-of-Record (no global tax-compliance burden).

### Out of scope (do NOT build)
- ❌ **Video avatars** of any kind. Ever. (Text + optional voice covers the realism that matters for history-taking.)
- ❌ B2B-first / institutional admin (SSO, LMS/LTI, cohort analytics). A *light* educator tier is a **post-launch** option (Phase 8+), pulled by student demand — not built up front.
- ❌ Heavy infra migration. Stay pragmatic; keep current hosting for MVP.
- ❌ Real-time diagnosis / medical-device claims. This is a **study aid**, not a clinical tool. Disclaimers required (§12).

---

## 2. The three moat features (hard requirements — preserve & harden)

These are the differentiation. Treat as non-negotiable acceptance criteria across all phases.

| # | Feature | What it means | What you must do |
|---|---------|---------------|------------------|
| **P1** | **Answer restraint** | The AI patient answers **only what is asked**, like a real lay patient; never volunteers the full symptom set; reveals red-flag info only when specifically elicited. | Preserve the existing restraint mechanism. Encode it as **explicit per-case disclosure rules** (§5.2). Add **automated tests** asserting the patient does not leak un-elicited findings. |
| **P2** | **Transparent, calibrated scoring + model-answer reveal** | After a session the student sees per-dimension scores, **per-item hit/miss against a hidden checklist**, *and* a full "what a complete workup should have included" answer key (the "Kunci Jawaban" pattern Cogni uses). | Make scoring **data-driven** from the case's hidden checklist (§6). Build the **answer-key reveal** screen. Correct the known LLM-judge upward-scoring bias by calibrating thresholds against human-graded sessions. |
| **P3** | **Breadth-at-launch via AI-drafted cases** | Cover many specialties at launch without a large specialist-validator network — by AI-drafting cases from authoritative clinical sources, then light human review. | Build the **content authoring pipeline + case linter** (§5). Do not treat "needs a validator per case" as a blocker; light review + clear study-aid framing is sufficient for the formative-practice market. |

---

## 3. Naming & rebrand

`OphthaSim` is ophthalmology-specific and must go. The product owner will choose the final name; until then use the token `{{PRODUCT_NAME}}`.

**Candidate names** (short, brandable, EN-friendly — owner to pick or override): *Anamnesa*, *Clerk* / *Clerkly*, *Probe*, *Wardly*, *Histora*. The pick is a human decision — do not auto-decide.

**Claude Code tasks:**
- [ ] Grep the codebase for every literal occurrence of the old name and ophthalmology-specific branding ("OphthaSim", "eye", "ophthalmology", "fundus"-as-branding, etc.) and catalogue them.
- [ ] Replace **branding** strings with `{{PRODUCT_NAME}}`. Do **not** replace genuinely clinical ophthalmology content (the 31 existing eye cases stay as one specialty among many — see §5.4).
- [ ] Centralise the product name into one config constant / env var so the final swap is one change.

---

## 4. Phase 0 — Repo audit & inventory (DO THIS FIRST)

Claude Code has **no prior knowledge of the actual code**. Discover it. Produce a written `AUDIT.md` at repo root capturing the real state. The verbal description below (from the owner) is a hint, not ground truth — verify each claim.

**Reported state to verify:**
- Backend: Python (has a `pytest` suite). Likely FastAPI/Flask — confirm.
- Frontend: confirm framework (React?), build tooling; owner keeps a strict "design unchanged" discipline.
- LLM: via **OpenRouter**, currently **DeepSeek** models for both patient-persona and judge. Token streaming enabled.
- **RAG**: per-case isolation retrieval — confirm the actual implementation (vector store? which one? embeddings? or simpler?).
- Case format: **2-part markdown per case** — Part A (objective clinical data + scoring ground truth, never shown to student) + Part B (patient persona: identity, complaint, SOCRATES, ROS, PMH/meds/FH/SH, FIFE).
- Session flow: **4 stages** → (1) Anamnesis → (2) Differential Dx (DDx) → (3) Management plan → (4) Debrief/scoring.
- Scoring: **LLM-as-judge**, 4 dimensions — Coverage Anamnesis 40 / FIFE 20 / Red-Flag Screening 20 / Communication 20 (0–100).
- Admin: "Developer Dashboard" (case CRUD + photo upload, admin login).
- Media: "Eye Photo Viewer" (button to view the eye condition during anamnesis).
- Gamification: XP, streaks, badges, score history, skill heatmap, performance profile.
- Voice: architecture **present but disabled**.
- Content: **31 ophthalmology cases** (9 active, preclinical, PPK-Kemenkes-based; 22 locked/legacy). **All unvalidated drafts.**
- Auth/payments: confirm whether ANY auth exists beyond admin login, and whether any billing exists (likely none).

**`AUDIT.md` must answer:**
1. Exact stack (languages, frameworks, DB, package managers, infra, hosting topology, how it deploys today).
2. How a case file is parsed and how Part A / Part B are kept apart at runtime (this is the leakage-prevention core).
3. Exactly how the RAG layer works and **whether it is actually needed** (see DECISION below).
4. How the judge prompt is constructed and where the rubric weights live (hardcoded? config?).
5. Confirm the known gap: the owner reports newer cases' Part A lacks an explicit **anamnesis checklist** + **red-flag list**, so Coverage & Red-Flag scoring currently falls back to physical-exam findings. Verify in code.
6. Test coverage map (what is tested, what is not).
7. Auth & data model: what user/session tables exist today.

```
// DECISION (RAG): Default to REMOVING vector-RAG for the single-active-case flow.
// A single case markdown is small and fits comfortably in context. "Per-case isolation"
// becomes trivial: load ONLY the selected case's Part B (+ controlled disclosure rules)
// into the patient context, and ONLY Part A into the judge context. Keep a thin retrieval
// abstraction ONLY if Phase 0 shows cases are large, or reserve it for a future
// knowledge-base/explanation feature. Document the change in AUDIT.md and confirm with the
// owner before deleting code.
```

**Phase 0 DoD:** `AUDIT.md` committed; staging environment stood up from current `main`; `feature/pivot-v4` branch created; CI runs existing tests green.

---

## 5. Content system — the spine of the pivot (Phase 1–2)

This is **P3**. Everything else depends on a clean, specialty-agnostic case schema and a pipeline that drafts cases fast.

### 5.1 Case schema v2 (specialty-agnostic; fixes the known gap)

Replace the loose 2-part markdown with a **structured, validated** format: YAML frontmatter (machine-readable metadata + scoring ground truth) + markdown body for the prose persona. **Every case must carry an explicit `anamnesis_checklist` and `red_flags` list** — this closes the gap the owner identified and makes P2 scoring correct rather than inferred from exam findings.

```yaml
# ---------- FRONTMATTER (metadata + Part A scoring ground truth; NEVER sent to the patient model) ----------
id: im_gi_appendicitis_001
schema_version: 2
status: draft            # draft | in_review | published | retired
specialty: internal_medicine   # controlled vocab (see §5.4)
system: gastrointestinal
presentation: "Acute abdominal pain"   # from GMC MLA presentation list
target_condition: "Appendicitis"       # from GMC MLA condition list
difficulty: 2            # 1..5 (preclinical band)
estimated_minutes: 15
mode_default: anamnesis  # anamnesis | osce_full  (see §6)
languages: [en]
source_refs:
  - "GMC MLA Content Map (2026)"
  - "NICE CKS / standard reference used to draft"
authoring:
  drafted_by: ai_v1
  model: <model-id>
  reviewed_by: null      # human reviewer id once reviewed
  reviewed_at: null
  review_notes: null

# ---- PART A: hidden scoring ground truth (drives the judge & the answer key) ----
chief_complaint: "Worsening central-then-right-lower abdominal pain for 18h"

anamnesis_checklist:        # explicit items a good student should ELICIT. Each item is scorable.
  hpi_socrates:
    - { item: "Onset/timing of pain", critical: true }
    - { item: "Site + migration (periumbilical -> RIF)", critical: true }
    - { item: "Character / severity / radiation", critical: false }
    - { item: "Aggravating/relieving (movement, coughing)", critical: false }
  associated_symptoms:
    - { item: "Anorexia", critical: true }
    - { item: "Nausea/vomiting", critical: false }
    - { item: "Fever", critical: true }
    - { item: "Bowel/urinary change (to exclude mimics)", critical: false }
  pmh: [ { item: "Prior abdominal surgery", critical: false } ]
  medications: [ { item: "Analgesia taken / allergies", critical: false } ]
  family_social: [ { item: "Relevant FH / social (alcohol, occupation)", critical: false } ]
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }

red_flags:                  # MUST-SCREEN items for THIS presentation. Drives the Red-Flag dimension.
  - { item: "Signs of peritonitis / generalised guarding", critical: true }
  - { item: "Haemodynamic instability (syncope, severe tachycardia)", critical: true }
  - { item: "GI bleeding / black stools", critical: true }
  - { item: "Pregnancy (ectopic) in a person who can be pregnant", critical: true }

expected_ddx:               # ranked; working dx + plausible differentials
  working_diagnosis: "Acute appendicitis"
  differentials:
    - "Mesenteric adenitis"
    - "Ectopic pregnancy"      # if applicable
    - "Ovarian torsion / ruptured cyst"
    - "Ureteric colic"
    - "Gastroenteritis"

investigations:             # for osce_full mode investigation-selection step
  appropriate:
    - { name: "FBC", expected: "Neutrophilia / raised WCC" }
    - { name: "CRP", expected: "Elevated" }
    - { name: "Urinalysis", expected: "Mild pyuria possible; exclude UTI/stone" }
    - { name: "Beta-hCG (if applicable)", expected: "Negative" }
    - { name: "USS / CT abdomen", expected: "Inflamed appendix" }
  inappropriate:            # selecting these costs points / is flagged
    - "Echocardiogram"
    - "Thyroid function tests"

physical_exam_findings:     # for the observational/exam step; may reference media
  general: "Lying still, looks unwell, low-grade fever"
  abdomen: "RIF tenderness, Rovsing's sign positive, guarding"
  vitals: { hr: 98, bp: "120/76", temp: 37.9, rr: 18, spo2: 99 }
  media: []                 # see §8.4 generic media viewer (rash, fundus, ECG, X-ray...)

management:
  pharmacological: [ "Analgesia", "IV fluids", "Antibiotics per local policy" ]
  non_pharmacological: [ "NBM", "Surgical referral for appendicectomy" ]
  education_safety_netting: [ "Explain likely appendicitis", "Consent for surgery", "Red-flag return advice" ]

scoring_weights_override: null   # null -> use mode default (§6). Else per-case override.
---

# ---------- PART B: PATIENT PERSONA (markdown body; THIS is what the patient model sees) ----------

## Identity
Name: Tina A. — 23, university student.

## Opening line (verbatim first message)
"Hi doctor... my tummy's been really hurting since yesterday."

## How I present (lay terms only — no medical vocabulary)
Pain started near the belly button, now it's lower right and worse when I move or cough...

## What I know (disclose ONLY when asked — see Disclosure Rules)
- Onset: ~18 hours ago, came on gradually then sharpened.
- Anorexia: "Haven't felt like eating at all."
- Nausea: mild, no vomiting.
- Fever: "Felt a bit hot last night."
- (...full SOCRATES / ROS / PMH / meds / FH / SH / FIFE...)

## Communication profile
Anxious but cooperative; short answers; hidden worry that it's "something serious like cancer"
(reveal only if concerns are explicitly explored).

## Disclosure rules (ANSWER RESTRAINT — P1)
- Answer ONLY the specific question asked, then stop. Do not pre-empt the next question.
- Never recite a list of symptoms unprompted. One concern at a time.
- Reveal red-flag information ONLY if directly asked about it.
- Use lay language; if asked a jargon question you don't understand, say so naturally.
- Never reveal anything in Part A that isn't in this persona body. Never reference being an AI/case/simulation.
- Stay in character even under leading or out-of-scope questions.
```

```
// DECISION (schema): YAML frontmatter for Part A + markdown body for Part B is the format.
// Rationale: frontmatter is machine-validatable (linter, scoring) and trivially separable at
// runtime (the patient model receives ONLY the body + a generated disclosure-rules block; the
// judge receives ONLY the frontmatter + transcript). This makes leakage-prevention a structural
// guarantee, not a prompt-hope.
```

### 5.2 Runtime context separation (enforces P1 leakage-prevention)

- **Patient turn:** system context = Part B body + Disclosure Rules ONLY. Never inject Part A. Keep streaming.
- **Judge turn:** context = Part A frontmatter (checklist/red-flags/ddx/etc.) + full transcript ONLY.
- Add an integration test that feeds a known case and asserts the patient response to a generic opener ("what's wrong?") does **not** contain un-elicited red-flag tokens.

### 5.3 Authoring pipeline (how breadth gets built fast — P3)

Build a **CLI/script** (`tools/author_case.py` or equivalent) plus an admin UI path:

1. **Input:** a `(specialty, presentation, target_condition, difficulty)` tuple from the scaffold (§5.4) + optional pasted reference text (guideline excerpt).
2. **Draft:** call a strong LLM with a structured prompt that emits a **complete, schema-valid case** (frontmatter + body), including a fully populated `anamnesis_checklist` and `red_flags`. Prompt enforces: lay-language persona, internal consistency (Part B facts must cover everything Part A expects to be elicitable), no contradictions.
3. **Lint:** run the **case linter** (§5.5). Iterate until green.
4. **Light human review:** mark `status: in_review`; a human (owner, or a clinician reviewer later) skims for clinical sanity, edits, sets `status: published`. The pipeline's job is to make review *fast* (review-and-edit, never author-from-scratch).
5. **Batch mode:** `tools/author_case.py --batch presentations.csv` drafts N cases, all landing in `in_review`.

```
// DECISION (models): Keep OpenRouter as the provider abstraction (model-agnostic, one-line swaps).
// Use a CHEAP fast model for the patient persona (instruction-following for restraint matters more
// than heavy reasoning). Use a STRONGER reasoning model for (a) the judge and (b) case authoring,
// given documented LLM-judge bias and the need for clinically coherent drafts. Make all configurable
// via env (PATIENT_MODEL, JUDGE_MODEL, AUTHOR_MODEL). Evaluate 2-3 options empirically before committing.
```

### 5.4 Content scaffold & specialty vocabulary

Adopt the **GMC MLA Content Map** as the master list of `presentation` and `target_condition` values, and as the seed backlog for breadth. (Public PDF: `gmc-uk.org/mla`. ~212–217 presentations, ~430 conditions, organised by area of clinical practice. Presentation-organised — ideal for an anamnesis trainer.)

- [ ] Create `content/scaffold/mla_presentations.csv` and `mla_conditions.csv` (presentation, condition, area-of-clinical-practice).
- [ ] Define the controlled `specialty` vocabulary (launch set): **internal_medicine, surgery, paediatrics, obstetrics_gynaecology, psychiatry, neurology, ent, dermatology, ophthalmology, emergency**. (Ophthalmology = the existing 31 cases, re-homed as one specialty — migrate, don't delete.)
- [ ] **Migrate the 9 active ophthalmology cases** to schema v2 first (proves the migration path on known-good content), then the 22 legacy cases (`status: retired` until reviewed).

> Note: SKDI/PPK-Kemenkes mapping can be layered later if an Indonesian SKU is ever wanted, but the **launch market is English** -> MLA scaffold is primary. Don't build SKDI mapping now.

### 5.5 Case linter (quality gate — runs in CI and in the pipeline)

`tools/lint_case.py` must hard-fail a case unless:
- [ ] Frontmatter parses; all required keys present; controlled-vocab fields valid.
- [ ] `anamnesis_checklist` non-empty AND has >=1 `critical: true` item; `ice_fife` present.
- [ ] `red_flags` non-empty AND has >=1 `critical: true` item.
- [ ] `expected_ddx.working_diagnosis` present; >=2 differentials.
- [ ] `investigations.appropriate` non-empty (for `osce_full`); each has an `expected` result.
- [ ] **Consistency check:** every checklist item that expects a patient answer has a corresponding fact in Part B (LLM-assisted check acceptable, flagged for human if uncertain).
- [ ] **Leakage check:** Part B body contains no Part A-only artefacts (no scoring language, no "differential", no checklist tables).
- [ ] Persona body has an `Opening line`, `Disclosure rules`, and `Communication profile`.

**Phase 1 DoD:** schema v2 defined; parser splits A/B with structural guarantee; linter green on the migrated 9 eye cases; P1 leakage test passing.
**Phase 2 DoD:** authoring pipeline drafts a schema-valid case end-to-end; **40–60 launch cases** drafted across >=8 specialties, all `published` after light review; catalogue browsable.

---

## 6. Scoring & assessment redesign (Phase 3 — this is P2)

Generalise the 40/20/20/20 rubric into a **data-driven, mode-aware** engine. Scores come from the case's hidden checklist, **not** inferred from exam findings.

### 6.1 Two modes
- **`anamnesis` mode (MVP default):** pure history-taking. Dimensions + default weights:
  - History coverage **35** (vs `anamnesis_checklist`)
  - Red-flag screening **20** (vs `red_flags`)
  - ICE/FIFE **15** (vs `ice_fife`)
  - Communication & professionalism **15** (intro, consent, empathy, signposting, structure)
  - Diagnostic reasoning (DDx) **15** (vs `expected_ddx`)
- **`osce_full` mode:** adds the full OSCE arc (mirrors what Cogni does and what real OSCE stations test):
  - History **25** / Red-flags **15** / ICE **10** / Communication **10** / Investigation selection **15** (vs `investigations`) / DDx **15** / Management **10** (vs `management`)

```
// DECISION (rubric): Weights are DATA, not code. Read from mode config, overridable per case via
// `scoring_weights_override`. Keep the owner's original 40/20/20/20 available as a named preset
// ("classic_anamnesis") for pure eye-style cases. Do NOT hardcode any single rubric.
```

### 6.2 Judge contract (calibration — corrects the known upward bias)

The judge prompt/output must:
- [ ] Credit an item **only** if the transcript shows it was actually elicited by the student (not merely present in the case).
- [ ] Use the explicit `anamnesis_checklist` / `red_flags` as ground truth (closes the gap).
- [ ] Output structured JSON: `per_item` (hit/miss/partial + evidence quote span), `per_dimension` scores, `overall`, and short qualitative feedback per dimension.
- [ ] Run at **low temperature**; optionally **ensemble** (2 calls, average) for stability on high-stakes scoring.
- [ ] Be **conservative**: set the pass threshold against a small set of **human-graded sessions** (collect ~20–30, compare AI vs human, adjust). Document calibration in `SCORING.md`.

### 6.3 Answer-key reveal (the "Kunci Jawaban" screen — high-value, drives word-of-mouth)

After scoring, show a results view with tabs mirroring the session arc (Conversation / Investigations / Diagnosis / Management / Summary) and, critically, a **full model answer**: the complete `anamnesis_checklist`, `red_flags`, `expected_ddx`, appropriate `investigations` + expected results, and `management` — with the student's hits/misses marked inline. This is what makes the tool *teach*, not just *test*.

**Phase 3 DoD:** data-driven rubric live for both modes; judge emits structured per-item JSON; answer-key reveal screen built; calibration note in `SCORING.md` with >=20 human-vs-AI comparisons.

---

## 7. B2C infrastructure (Phase 4 — new build)

### 7.1 Auth
- [ ] Email/password + OAuth (Google at minimum). Email verification, password reset.
- [ ] User model: id, email, auth provider, created_at, plan/entitlement, usage counters.
- [ ] Keep the existing admin login as a separate role; don't conflate with student auth.

### 7.2 Payments — Merchant of Record (NOT Stripe-direct)
```
// DECISION (payments): Use a Merchant-of-Record (Lemon Squeezy OR Paddle, ~5% + $0.50/txn).
// Rationale: the owner is in Indonesia selling to individuals globally; an MoR is the legal seller
// and remits VAT/GST/sales-tax across all jurisdictions, so the owner files nothing per-country and
// avoids Stripe-direct cross-border + tax-registration overhead. Integrate via the MoR's hosted
// checkout + webhooks; do NOT build raw card handling. Lemon Squeezy = fastest indie onboarding;
// Paddle = widest jurisdiction/feature depth. Default to Lemon Squeezy for speed unless onboarding
// is rejected, then Paddle/Polar. Confirm final choice with the owner before integrating.
```
- [ ] Hosted checkout + webhook handler (subscription created/updated/cancelled/payment-failed).
- [ ] Map MoR subscription state -> internal entitlement. Handle dunning/grace on failed payment.
- [ ] Customer portal link (MoR-hosted) for cancel/update.

### 7.3 Plans, gating & metering (freemium)
- **Free:** a few free cases + a low monthly session cap (e.g. 3 cases / 5 sessions) to prove value.
- **Monthly (~US$9.99) / Annual (~US$59):** unlimited (fair-use) sessions + full library.
- **Exam-crunch pass (~US$14.99, 1 month):** for seasonal buyers; consider a "pass guarantee"/extension hook later.
- [ ] Centralised **entitlement check** at session-start and case-access. Track usage in a `usage` table.
- [ ] Server-side enforcement (never trust the client for gating).
- [ ] **Cost guardrail:** track LLM token spend per session; alert if per-user spend approaches the plan price (margin protection).

**Phase 4 DoD:** a new user can sign up, hit the free wall, pay via MoR checkout, get entitlement unlocked, and run unlimited sessions; webhooks reconcile state; usage metered; cost-per-session logged.

---

## 8. UX & frontend (Phase 5 — preserve "design discipline")

The owner runs a strict "design doesn't change without reason" practice. **Extend, don't restyle.** Reuse existing components and visual language.

### 8.1 Multi-specialty catalogue
- [ ] Replace the eye-only list with a **filterable catalogue**: filter by specialty, system, presentation, difficulty, mode. Search. (Cogni's catalogue — topic + batch filters, per-case cards — is a fine layout reference, not a content reference.)
- [ ] Case cards show specialty, presentation, difficulty, est. minutes, mode badge.

### 8.2 Onboarding
- [ ] First-run: 60-second explainer (what anamnesis practice is, how scoring works, that the patient won't volunteer info -> *you must ask*), then a free sample case. The "answer restraint" behaviour must be **explained up front** or new users think the AI is "broken."

### 8.3 Session flow (preserve the 4 stages)
- [ ] Keep Anamnesis -> DDx -> Management -> Debrief. Add the **investigation-selection** step (from `osce_full`) as an optional stage between anamnesis and DDx, gated by case `mode`. A timer (like Cogni's 15-min station) is a nice optional realism toggle.

### 8.4 Generic examination-media viewer (generalise "Eye Photo Viewer")
- [ ] Rename/refactor "Eye Photo Viewer" -> **Examination Media Viewer**: shows any case media (skin rash, fundus, ECG strip, CXR, otoscopy, etc.) keyed off `physical_exam_findings.media`. Same UX pattern, now specialty-agnostic. Admin upload generalised accordingly.

### 8.5 Results / debrief
- [ ] Build the answer-key reveal (§6.3) with the tabbed layout. Make the score breakdown + per-item hit/miss legible and shareable (a clean shareable score card drives cohort word-of-mouth).

### 8.6 Gamification
- [ ] **Keep** XP, streaks, badges, score history, skill heatmap, performance profile. Re-key the **skill heatmap by specialty/system** (so it shows breadth coverage — directly reinforces the "broad" positioning).

**Phase 5 DoD:** catalogue filterable across all launch specialties; onboarding explains restraint; media viewer generic; results/answer-key screen live; gamification re-keyed to specialties.

---

## 9. Voice (Phase 7+ — deferred, optional, labelled beta)

- Keep the dormant voice architecture in place; do **not** delete it (owner previously considered removing it — research says keep it as a *later* optional beta, not MVP).
- When enabled: speech-to-text in -> existing text patient pipeline -> text-to-speech out. Clearly label **BETA**. Voice must not change scoring (transcript is the source of truth).
- **No video avatars** — reconfirmed. Voice + text is the ceiling.

---

## 10. Phasing summary (ordered) & overall DoD

| Phase | Theme | Key output | Gate |
|------|-------|-----------|------|
| **0** | Audit & setup | `AUDIT.md`, staging, branch | CI green on existing tests |
| **1** | Core generalisation | Schema v2, A/B structural split, linter, P1 leakage test, 9 eye cases migrated | Linter green; restraint test passing |
| **2** | Content breadth (P3) | Authoring pipeline + linter; **40–60 cases / >=8 specialties** published | Catalogue populated; cases lint-clean |
| **3** | Scoring (P2) | Data-driven mode-aware rubric; structured judge; **answer-key reveal**; calibration | `SCORING.md` with >=20 human-vs-AI comparisons |
| **4** | B2C infra | Auth + MoR payments + freemium gating/metering + cost guardrail | End-to-end signup->pay->unlock works |
| **5** | UX | Filterable catalogue, onboarding, generic media viewer, results UI, gamification re-key | Manual UX pass on all launch specialties |
| **6** | Launch prep & cutover | Disclaimers, analytics, error monitoring, backups, perf pass; cut staging->prod | Go/no-go checklist (§13) all green |
| **7+** | Post-launch | Voice beta; light educator tier (only if pulled by demand); more cases | — |

**Overall MVP DoD (end of Phase 6):** A net-new English-speaking student can sign up, browse a broad multi-specialty catalogue, run a realistic answer-restrained anamnesis, receive transparent calibrated per-item scoring + a full model-answer reveal, hit a freemium wall, pay via Merchant-of-Record, and continue — with cost-per-session monitored and a clinical-study-aid disclaimer shown.

---

## 11. Technical conventions & guardrails

- **Branch/deploy:** all pivot work on `feature/pivot-v4`; `main` stays live-deployable until cutover. Use staging for integration testing.
- **Config:** all model IDs, the product name, MoR keys, and plan prices live in env/config — never hardcoded. Provide `.env.example`.
- **Secrets:** never commit keys. MoR + OpenRouter keys via env/secret store.
- **Testing:** preserve and extend the `pytest` suite. New required tests: (a) A/B leakage / answer-restraint (P1), (b) case linter unit tests, (c) judge output schema validation, (d) entitlement/gating server-side enforcement, (e) webhook handling. Don't let coverage regress.
- **Observability:** add request/error logging + an error monitor; log per-session token spend (cost guardrail). Basic analytics: signups, activation (first case completed), conversion, sessions/user, score distributions.
- **Data:** move to a managed Postgres if not already; add automated backups; object storage for case media; consider a CDN. Keep it lean — no premature microservices.
- **Privacy:** global users -> write a basic privacy policy + ToS; minimise PII; the MoR handles payment data. Show the study-aid disclaimer.
- **Performance:** streaming must stay smooth; cache the static catalogue; keep case loading O(1) per session.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking the live product mid-pivot | Branch + staging; `main` stays deployable; cut over only at the Phase 6 gate. |
| LLM-judge scores too generously (documented bias) | Conservative thresholds; calibrate vs human grades; ensemble judge; show evidence spans per item. |
| Clinical inaccuracy in AI-drafted cases at breadth | Linter consistency checks + light human review before `published`; clear **study-aid (not clinical advice)** disclaimer; in-app "report this case" + feedback loop. |
| Answer restraint reads as "broken AI" to new users | Onboarding explains it explicitly; sample case demonstrates "you must ask." |
| Margin erosion from token costs | Per-session spend logging + alerts; cheap persona model; cap fair-use; right-size models. |
| Payment/tax complexity for an Indonesia-based seller going global | Merchant-of-Record absorbs VAT/GST/sales-tax + liability (§7.2). |
| Over-building toward SimChat parity | The out-of-scope list (§1) is binding: no video avatars, no B2B-first, no heavy infra. |

---

## 13. Go/No-Go launch checklist (Phase 6)

- [ ] >=40 published, lint-clean cases across >=8 specialties; ophthalmology cases migrated.
- [ ] P1 answer-restraint test suite green; manual spot-check on 10 random cases shows no un-elicited leakage.
- [ ] Scoring calibrated (>=20 human-vs-AI comparisons documented; pass threshold set conservatively).
- [ ] Answer-key reveal works for every published case.
- [ ] Signup -> free wall -> MoR checkout -> entitlement unlock -> unlimited sessions verified end-to-end (real test transaction).
- [ ] Webhooks reconcile subscription lifecycle (create/cancel/fail/grace).
- [ ] Cost-per-session logged; alert thresholds set.
- [ ] Error monitoring + analytics live; backups configured.
- [ ] Privacy policy, ToS, and clinical study-aid disclaimer published and shown.
- [ ] Onboarding explains answer restraint.
- [ ] `main` cut over from staging; rollback plan documented.

---

## 14. Open decisions for the product owner (Rafi — answer before/at the relevant phase)

1. **Final product name** (§3) — pick from candidates or supply your own. Needed before Phase 5/6.
2. **MoR choice** — Lemon Squeezy (fastest) vs Paddle (deepest). Default Lemon Squeezy unless you have a reason. (§7.2)
3. **Exact price points & free-tier limits** — the ~$9.99/$59/$14.99 figures are placeholders; confirm. (§7.3)
4. **Launch specialty set & case count** — confirm the 10-specialty list and whether 40 or 60 cases for launch. (§5.4)
5. **Reviewer model** — is light review *you only* for MVP, or do you want a clinician reviewer per specialty before launch? (Affects how conservative the disclaimer must be.) (§5.3)
6. **Timer/OSCE-realism toggle** — ship the 15-min timed station option at MVP, or post-launch? (§8.3)

---

### Appendix A — Sources this plan is built on (for the owner's reference)
- GMC MLA Content Map (presentations/conditions scaffold) — `gmc-uk.org/mla`.
- Merchant-of-Record landscape (Lemon Squeezy/Paddle, ~5% + $0.50, MoR vs Stripe tax liability) — 2026 comparisons.
- LLM-as-judge for clinical assessment (ICC ~0.77–0.91 vs humans, but upward-scoring bias) — BMC Med Educ / MDPI 2025.
- LLM virtual-patient methodology & answer-restraint best practice — Cook (Medical Teacher 2024/25); NEJM AI ASCE RCT (history-taking practice improved OSCE scores).
- Competitor benchmarks — SimChat/Geeky Medics (B2B + consumer), Cogni by Mediko (quota-gated, Bahasa-only), Oscer/Heidi (B2C analogue, now moving up-market).
