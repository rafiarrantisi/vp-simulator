# SCORING.md — Calibrated, data-driven assessment (Pivot v4, moat P2)

> Implements `BUILD_PLAN_pivot_v4.md` §6. Scores come from each case's **explicit
> hidden checklist** (`anamnesis_checklist` + `red_flags`), not inferred from
> physical-exam findings (the bug confirmed in `AUDIT.md` §5).

---

## 1. Rubric = data, not code

Weights live in `app/domains/scoring/rubric_v2.py` (`RUBRICS`), are selected by
**mode**, and are overridable **per case** via frontmatter `scoring_weights_override`.
No single rubric is hardcoded in the judge.

| Dimension | `anamnesis` (default) | `osce_full` | Ground truth source |
|---|---|---|---|
| History coverage | 35 | 25 | `anamnesis_checklist` (hpi/associated/pmh/meds/family_social) |
| Red-flag screening | 20 | 15 | `red_flags` |
| ICE / FIFE | 15 | 10 | `anamnesis_checklist.ice_fife` |
| Communication | 15 | 10 | transcript (intro, consent, empathy, signposting, structure) |
| Investigation selection | — | 15 | `investigations` |
| Diagnostic reasoning (DDx) | 15 | 15 | `expected_ddx` |
| Management | — | 10 | `management` |
| **Total** | **100** | **100** | |

The legacy OphthaSim rubric is preserved as the named preset
`classic_anamnesis` (coverage 40 / fife 20 / red_flags 20 / communication 20)
for pure eye-style cases. `resolve_weights(mode, override)` enforces the
precedence: valid per-case override → mode rubric → default mode. Every preset
is unit-tested to sum to 100.

---

## 2. Judge contract (corrects the documented upward bias)

`app/rag/judge_v2.py` → `evaluate_v2(case, transcript, mode=…)`. Calibration
levers, all implemented:

1. **Elicited-only credit.** The system prompt instructs: *credit an item ONLY
   if the transcript shows the student actually elicited it; when in doubt, mark
   'miss'.* Information merely present in the case is never credited.
2. **Explicit ground truth.** The judge grades against the `anamnesis_checklist`
   / `red_flags` / `expected_ddx` / `investigations` / `management` — not exam
   findings. (Only the dimensions in the active rubric are sent.)
3. **Structured per-item output.** `per_item: [{dimension, item, status:
   hit|partial|miss, evidence}]` with a verbatim transcript quote per hit, plus
   `per_dimension: {score, max, feedback}` and a `summary`.
4. **Low temperature.** Runs at `temperature = 0.1` (added as an optional,
   backward-compatible param on the LLM client).
5. **Server-side total.** `overall` is **recomputed** from clamped per-dimension
   scores — the model's own arithmetic is never trusted (`_normalize`, unit-tested
   with a deliberately lying total).
6. **Never fails the session.** Stub LLM or a parse failure returns a valid-shaped
   zero report.

Context separation holds: the judge receives Part A frontmatter + transcript
only (via `build_judge_ground_truth`), never the persona body — asserted in
`tests/test_scoring_v2.py` and `tests/test_leakage_p1.py`.

**Ensemble (optional, §6.2):** for high-stakes scoring, call the judge twice and
average per-dimension scores. Not enabled by default (cost); wire when justified.

---

## 3. Answer-key reveal (the "Kunci Jawaban", §6.3)

`app/rag/answer_key.py` → `build_answer_key(case)` returns the full model answer
from Part A (grouped checklist with critical flags, red flags, working dx +
differentials, appropriate investigations + expected results, management). It is
attached to every report as `report["answer_key"]`. The frontend overlays the
student's per-item hit/partial/miss (from `per_item`) on top of this — that UI is
delivered in **Phase 5** (this is the data layer it consumes).

---

## 4. Calibration — methodology & status (HONEST)

The plan's DoD asks for **≥20 human-vs-AI comparisons** with a conservatively-set
pass threshold. That requires (a) a live judge model key and (b) human-graded
sessions — neither can be fabricated. Status:

- ✅ **Conservative-by-construction** mechanisms above are in place and tested.
- ⏳ **Pending real data:** the 20–30 human-vs-AI comparison set. Methodology to run:
  1. Collect 20–30 real sessions across ≥3 specialties at varied skill levels.
  2. Have 1–2 clinicians grade each on the same rubric (blind to the AI score).
  3. Compute agreement (ICC / mean signed error per dimension). Literature shows
     ICC ~0.77–0.91 vs humans **with an upward bias** — expect the AI to read high.
  4. Set the **pass threshold** above the naive 50% to absorb the residual bias,
     and apply per-dimension offsets if a dimension is systematically generous.
  5. Re-test after each model swap (`JUDGE_MODEL`); calibration is model-specific.

A calibration harness lives at `backend/qa/restraint_qa.py` for P1 behaviour; a
sibling scoring-calibration harness should record `(case, transcript, ai_report,
human_report)` rows to a CSV for analysis — **scheduled when a judge key + grader
are available.**

> Bottom line: the scoring *engine* is calibration-ready and conservative by
> construction; the empirical threshold-setting is a real-world data task, not a
> code task, and is explicitly outstanding.
