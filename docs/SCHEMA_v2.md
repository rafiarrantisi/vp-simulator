# Case Schema v2 — Specialty-Agnostic Anamnesis Cases (Pivot v4)

> Implements `BUILD_PLAN_pivot_v4.md` §5.1. This is the **locked** format for all new
> and migrated cases. It closes the known scoring gap (AUDIT.md §5) by making the
> **anamnesis checklist** and **red-flag list** explicit, machine-readable ground truth.
>
> **Format:** YAML frontmatter (Part A — hidden scoring ground truth) + Markdown body
> (Part B — patient persona). One file per case, English, under `content/cases/`.

---

## Why v2 (vs the legacy `data-kasus/kasus-XX.md` format)

| Legacy (`## BAGIAN A` / `## BAGIAN B` prose) | Schema v2 |
|---|---|
| Indonesian, ophthalmology-only | English, specialty-agnostic |
| No explicit checklist → judge falls back to physical-exam findings (AUDIT §5) | Explicit `anamnesis_checklist` + `red_flags` drive scoring (moat **P2**) |
| A/B split by markdown headers (textual) | A = frontmatter, B = body → **structural** separation (moat **P1**) |
| Validated loosely (≥6 sections) | Validated by `tools/lint_case.py` (hard gate) |

The legacy format and its 31 cases remain untouched and live until cutover (Phase 6).
v2 lives in parallel under `content/cases/`.

---

## Structural separation = the P1 guarantee

- **Patient model context** is built **only** from the Markdown **body** (Part B) + a
  generated answer-restraint scaffold. It **never** receives frontmatter.
  → `app/rag/prompt_v2.build_patient_prompt()`
- **Judge context** is built **only** from the frontmatter (Part A) scoring ground truth
  + the transcript. It **never** receives the persona body.
  → `app/rag/prompt_v2.build_judge_ground_truth()`

Because Part A is frontmatter and Part B is the body, leakage prevention is a property of
the parser, not a prompt we hope the model obeys. `tests/test_leakage_p1.py` asserts the
working diagnosis and red-flag clinical labels never appear in the patient prompt.

---

## Frontmatter (Part A) — keys

**Required:** `id`, `schema_version` (=2), `status`, `specialty`, `presentation`,
`target_condition`, `difficulty`, `mode_default`, `chief_complaint`,
`anamnesis_checklist`, `red_flags`, `expected_ddx`.

**Recommended:** `system`, `estimated_minutes`, `languages`, `source_refs`, `authoring`,
`investigations` (required when `mode_default: osce_full`), `physical_exam_findings`,
`management`, `scoring_weights_override`.

### Controlled vocabularies
- `status`: `draft | in_review | published | retired`
- `mode_default`: `anamnesis | osce_full`
- `specialty` (launch set, §5.4): `internal_medicine, surgery, paediatrics,
  obstetrics_gynaecology, psychiatry, neurology, ent, dermatology, ophthalmology, emergency`
- `difficulty`: integer `1..5` (preclinical band)

### `anamnesis_checklist` — scorable elicitation items
A mapping of dimension → list of `{ item, critical }`. `ice_fife` is **required** and
non-empty. At least one item across the whole checklist must be `critical: true`.
```yaml
anamnesis_checklist:
  hpi_socrates:      [ { item: "...", critical: true } ]
  associated_symptoms: [ ... ]
  pmh: [ ... ]
  medications: [ ... ]
  family_social: [ ... ]
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
```

### `red_flags` — MUST-SCREEN items for this presentation
Non-empty; ≥1 `critical: true`. Drives the Red-Flag dimension. These are **clinical
screening labels** and must NOT appear in the persona body (the lay patient doesn't
know them).
```yaml
red_flags:
  - { item: "Acute vision loss", critical: true }
```

### `expected_ddx`
`working_diagnosis` (required) + `differentials` (≥2).

### `investigations` (osce_full)
`appropriate: [ { name, expected } ]` (each needs an `expected` result) + `inappropriate: [ ... ]`.

See `BUILD_PLAN_pivot_v4.md` §5.1 for the full annotated example and the
`physical_exam_findings` / `management` shapes.

---

## Markdown body (Part B) — required sections

`## Identity`, `## Opening line` (verbatim first message), `## How I present`,
`## What I know` (disclose only when asked), `## Communication profile`,
`## Disclosure rules` (answer restraint — P1).

**Body must NOT contain Part-A artefacts:** no `working_diagnosis`, `anamnesis_checklist`,
`expected_ddx`, `schema_version`, ICD codes, or the word "differential". (`tools/lint_case.py`
hard-fails on these.) The disclosure-rules section may reference "red-flag information"
in instruction text — that is allowed; the banned items are the structural/diagnosis tokens.

---

## Linter contract (`tools/lint_case.py`, §5.5)

Hard-fails (ERROR, non-zero exit) unless: frontmatter parses; all required keys present;
controlled-vocab valid; `anamnesis_checklist` non-empty + ≥1 critical + `ice_fife` present;
`red_flags` non-empty + ≥1 critical; `expected_ddx.working_diagnosis` + ≥2 differentials;
`investigations.appropriate` non-empty w/ `expected` (osce_full); body has Opening line +
Disclosure rules + Communication profile; **no Part-A leakage in body**.

Soft WARNINGS (do not fail CI): missing `source_refs`/`estimated_minutes`; heuristic
persona-consistency gaps (a checklist item with no apparent matching fact in the body) —
flagged for human review (true consistency is an LLM-assisted Phase 2 check).

---

## ID convention

`<specialty-abbrev>_<slug>_<nnn>`, e.g. `oph_dry_eye_001`, `im_gi_appendicitis_001`.
Abbreviations: `im, surg, paed, og, psych, neuro, ent, derm, oph, em`. The id must be
stable (it keys sessions/scores) and unique.
