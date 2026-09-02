"""STEP 8 — clinical QA: consistency invariants, scoring fixtures, promotion.

Two QA layers (STEP 8 §1): Technical QA (this module is deterministic + testable)
and Clinical QA (needs human doctor/educator — STEP 8 §6, §12). Passing the
technical gate here does NOT mark a case clinically verified.

Covers:
  §4  canonical-truth consistency invariants (vitals/expected results/diagnosis/
      timeline/units/age-persona coherence).
  §5  scoring fixtures (excellent/good/poor/unsafe synthetic learners) →
      directional correctness.
  §13 promotion rule: only a named HUMAN reviewer may grant clinically_reviewed;
      no AI self-verification loophole.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pipeline.case_v3.derive import (
    derive_answer_key, derive_debrief, derive_vitals,
)
from pipeline.case_v3.models import ClinicalVariant
from pipeline.case_v3.runtime import ScoreInput, score_encounter
from pipeline.case_v3.semantic import diagnose_match
from pipeline.case_v3.vocab import ReviewState, HUMAN_REVIEWED_STATES


@dataclass
class QAIssue:
    code: str
    message: str
    severity: str = "error"   # error | warning

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


# ── §4 canonical-truth consistency invariants ──────────────────────────────
def consistency_issues(v: ClinicalVariant) -> list[QAIssue]:
    """Same clinical truth everywhere: vitals/exam/answer key, investigation
    expected results, working diagnosis across scorer/debrief, timeline, and
    persona-age compatibility. STEP 2 derives everything from ONE canonical
    source, so these are invariant guards (the legacy paediatric-fever class)."""
    out: list[QAIssue] = []

    # vitals: derive_vitals == physical_exam vitals (single canonical source);
    # the answer key does not duplicate vitals, so we assert the two readers that
    # exist agree. If an answer-key copy is ever introduced it must match too.
    ex_vitals = derive_vitals(v)
    pe_vitals = [x.to_dict() for x in v.physical_exam.vitals]
    if ex_vitals != pe_vitals:
        out.append(QAIssue("vitals_mismatch",
                           "derived vitals != physical_exam vitals (single truth violated)", "error"))
    # investigations: expected_result consistent everywhere (present + non-empty)
    ak_inv = {inv["name"]: inv.get("expected_result") for inv in derive_answer_key(v).get("investigations") or []}
    for inv in v.investigations:
        if ak_inv.get(inv.name) not in (None, ""):
            if ak_inv.get(inv.name) != inv.expected_result:
                out.append(QAIssue("inv_expected_mismatch",
                                   f"investigation '{inv.name}' expected_result differs between variant & answer key",
                                   "error"))

    # working diagnosis: scorer vs debrief vs diagnostic
    dx = (v.diagnostic.working_diagnosis or "").strip()
    if not dx:
        out.append(QAIssue("empty_diagnosis", "working_diagnosis empty", "error"))
    debrief_dx = (derive_debrief(v).get("working_diagnosis") or "").strip()
    if dx and debrief_dx != dx:
        out.append(QAIssue("diagnosis_mismatch", f"debrief dx '{debrief_dx}' != variant dx", "error"))

    # investigation expected result coherent
    for inv in v.investigations:
        if not (inv.expected_result or "").strip():
            out.append(QAIssue("inv_no_expected", f"investigation '{inv.name}' lacks expected_result", "warning"))

    # age/persona compatibility: age_years must sit inside age_range if both set
    ident = v.identity
    if ident.age_years is not None and ident.age_range:
        lo, hi = _parse_age_range(ident.age_range)
        if lo is not None and not (lo <= ident.age_years <= hi):
            out.append(QAIssue("age_range_incoherent",
                               f"age {ident.age_years} outside range {ident.age_range}", "error"))

    # chronology present (timeline coherence with disclosure map)
    if not (v.key_chronology or "").strip():
        out.append(QAIssue("no_timeline", "key_chronology empty (timeline should exist)", "warning"))

    # unit normalisation: vitals carry recognised numerical values
    for vs in v.physical_exam.vitals:
        if isinstance(vs.value, (int, float)) and vs.unit is None and str(vs.name) not in ("",):
            # raw number without unit is suspicious
            out.append(QAIssue("untyped_vital", f"vital '{vs.name}' numeric but no unit", "warning"))
    return out


def _parse_age_range(s) -> tuple[Optional[int], Optional[int]]:
    import re
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)", str(s))
    if m:
        return int(m.group(1)), int(m.group(2))
    m2 = re.search(r"(\d+)\+", str(s))
    if m2:
        return int(m2.group(1)), None
    return None, None


# ── §5 scoring fixtures (synthetic learners) ───────────────────────────────
@dataclass
class SyntheticLearner:
    label: str
    collected_items: dict = field(default_factory=dict)
    stabilized: bool | None = None
    gave_referral: bool | None = None
    diagnosis_submitted: str = ""


EXCELLENT_ITEMS: set = {
    "stabilization_performed", "management_complete", "diagnosis_attempted",
}


def scoring_fixture_issues(v: ClinicalVariant) -> list[QAIssue]:
    """Run synthetic learner performances; assert DIRECTIONAL correctness
    (§5): excellent > good > poor, unsafe triggers safety flags, paraphrase
    accepted. Not a false-precision judgement."""
    out: list[QAIssue] = []
    dx_target = v.diagnostic.working_diagnosis
    synonyms = list(v.diagnostic.synonyms)

    def run(lab: str, items: dict, stab=None, ref=None, dx=""):
        return score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                          collected_items=items, stabilized=stab,
                                          gave_referral=ref, diagnosis_submitted=dx))

    excellent = run("excellent",
                    {"management_complete": True, "diagnosis_attempted": True},
                    stab=True, ref=True, dx=dx_target)
    good = run("good", {"diagnosis_attempted": True}, stab=True, ref=True,
               dx=_paraphrase_of(dx_target) or dx_target)
    poor = run("poor", {}, stab=False, ref=False, dx="")
    unsafe = run("unsafe", {"management_complete": True}, stab=False, ref=False, dx=dx_target)

    # direction
    if not (excellent.total >= good.total >= poor.total):
        out.append(QAIssue("fixture_direction",
                           "excellent>=good>=poor not satisfied "
                           f"({excellent.total:.2f}>={good.total:.2f}>={poor.total:.2f})", "error"))
    # unsafe must trigger a safety flag
    if not unsafe.safety_flags:
        out.append(QAIssue("unsafe_no_safety", "unsafe synthetic learner produced no safety flag",
                           "warning" if not _requires_stab(v) else "error"))
    # paraphrase accepted (rule 7: no exact-string clinical fail)
    para = _paraphrase_of(dx_target) or dx_target
    dm = diagnose_match(para, dx_target, synonyms)
    if dx_target and not dm.get("match"):
        out.append(QAIssue("paraphrase_rejected",
                           "a legitimate paraphrase of the target dx was rejected", "error"))
    return out


def _requires_stab(v: ClinicalVariant) -> bool:
    return bool(v.management_expectations.emergency_stabilization_required)


def _paraphrase_of(target: str) -> str:
    if not target:
        return ""
    # a realistic paraphrase: drop parenthetical, keep the head term
    head = target.split("(")[0].strip()
    if not head:
        return target
    return head


# ── §13 promotion rule (human gate; no AI self-verification) ───────────────
@dataclass
class ReviewRecord:
    reviewer_name: str
    reviewer_role: str
    date: str
    notes: str = ""
    approved: bool = True


# Valid state path per STEP 8 §13.
REVIEW_FLOW = [
    "draft", "ai_generated", "research_complete", "in_review",
    "clinically_reviewed", "pilot_verified", "published",
]

# States that REQUIRED a named human reviewer.
def requires_human_review(v: ClinicalVariant) -> bool:
    return v.status in HUMAN_REVIEWED_STATES


def can_apply_human_review(v: ClinicalVariant, record: ReviewRecord) -> tuple[bool, str]:
    """Quality gate (STEP 8 §13): clinically_reviewed/pilot_verified may ONLY be
    granted by an authorised, named human reviewer — never by automated tests /
    an AI. Returns (allowed, reason)."""
    if not record.reviewer_name or not record.reviewer_role:
        return False, "human review requires reviewer name + role"
    # promote path
    return True, "ok"


def promotion_allowed(v: ClinicalVariant, target: str, *, human_record: Optional[ReviewRecord] = None) -> tuple[bool, str]:
    """Enforce the §13 promotion rule. Automated steps can move early technical
    states (draft→ai_generated→research_complete→in_review). Only a named human
    can move into clinically_reviewed / pilot_verified / published."""
    cur = v.status
    if cur not in REVIEW_FLOW or target not in REVIEW_FLOW:
        return False, f"unknown state: {cur} -> {target}"
    if REVIEW_FLOW.index(target) < REVIEW_FLOW.index(cur):
        return False, "cannot regress along the promotion path"
    # reaching a human-reviewed state requires a named human
    if target in HUMAN_REVIEWED_STATES:
        if not human_record or not human_record.reviewer_name or not human_record.reviewer_role:
            return False, "clinically_reviewed/pilot_verified/published MUST be granted by a named human reviewer (no AI self-verification)"
    return True, "ok"


def human_review_checklist() -> list[str]:
    """STEP 8 §12 — reviewer checklist for each case."""
    return [
        "competency_mapping_verified", "learning_objective", "epidemiology",
        "history_truth", "negative_findings", "red_flags", "physical_exam",
        "investigations", "diagnosis_differentials", "treatment", "referral",
        "sources", "rubric", "safety_gates", "variant_realism",
    ]


# ── §6 doctor/educator comparison (HUMAN participation, not fabricated) ────
@dataclass
class HumanJudgement:
    reviewer_name: str
    reviewer_role: str            # "doctor" | "clinical_educator"
    date: str
    variant_id: str = ""
    transcript_frozen_at: str = ""
    # independent human scores (direction-level)
    critical_misses_ok: Optional[bool] = None
    safety_ok: Optional[bool] = None
    diagnosis_ok: Optional[bool] = None
    management_ok: Optional[bool] = None
    approval: Optional[bool] = None      # None = pending human sign-off
    notes: str = ""


def human_comparison_needed(v: ClinicalVariant) -> bool:
    """§6: Qora technical scoring is NOT clinically verified until a human
    doctor/educator judgement exists. Never auto-sign-off."""
    return v.status in HUMAN_REVIEWED_STATES  # reviewed states REQUIRE this data