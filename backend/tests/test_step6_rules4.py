"""STEP-6 superseding rules (4) — scoring/runtime competency in SKD 2026 terms.

Old test semantics referenced '3B missing stabilization'. Replaced by case-specific
rules:
  - initial_management_and_referral + emergency_stabilization_required=true and
    learner misses stabilization → safety flag.
  - initial_management_and_referral + emergency_stabilization_required=false →
    NO automatic stabilization penalty (stabilisation not universally required).
  - tuntas is judged on case-specific complete management expectation, not a
    generic template.

Also locks rule 1 (no auto-map of category→3A/3B/4A) and rule 2 (runtime/scoring
read management expectations, category alone never decides stabilisation).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.models import (
    Competency, ManagementExpectations, Management,
)
from pipeline.case_v3.vocab import (
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL, SKD2026_CATEGORY_TUNTAS,
)
from pipeline.case_v3.governance import validate_governance
from pipeline.case_v3.lint import lint_variant


def _graded_stabilization_failure(expectations: ManagementExpectations,
                                  management: Management,
                                  *, learner_missed_stabilization: bool) -> bool:
    """EXAMPLE scoring rule (runtime implements the real one in STEP 6).

    Stabilisation only becomes a safety-critical grading requirement when the
    case itself says emergency_stabilization_required is True. If the learner
    missed it under that condition → safety flag. If the case says False,
    missing stabilisation does not itself trigger a penalty.
    """
    if expectations.emergency_stabilization_required is True:
        if learner_missed_stabilization:
            return True  # safety flag
        return False
    # False or None: no automatic stabilisation penalty
    return False


# ── rule 4: stabilisation penalty is case-conditional ─────────────────────

def test_initial_refer_true_missing_stabilization_flags_safety():
    me = ManagementExpectations(
        recognize_diagnose="x", initial_management="x",
        emergency_stabilization_required=True, referral_urgency="immediate",
        referral_indication="shock", do_not_miss_actions=["resuscitate"],
    )
    mgmt = Management()  # no stabilization plan — learner missed it
    assert _graded_stabilization_failure(me, mgmt, learner_missed_stabilization=True) is True


def test_initial_refer_true_did_stabilize_no_flag():
    me = ManagementExpectations(emergency_stabilization_required=True,
                                recognize_diagnose="x", initial_management="x",
                                referral_indication="x", referral_urgency="x",
                                do_not_miss_actions=["x"])
    mgmt = Management(stabilization=["IV crystalloid bolus"])
    assert _graded_stabilization_failure(me, mgmt, learner_missed_stabilization=False) is False


def test_initial_refer_false_no_automatic_penalty():
    # emergency_stabilization_required=False → missing stabilisation is NOT a
    # penalty (stabilise requirement may be absent/non-emergency context).
    me = ManagementExpectations(
        recognize_diagnose="x", initial_management="x",
        emergency_stabilization_required=False, referral_urgency="urgent",
        referral_indication="warning signs", do_not_miss_actions=["observe"],
    )
    mgmt = Management()  # no stabilization plan, and that's OK
    assert _graded_stabilization_failure(me, mgmt, learner_missed_stabilization=True) is False


def test_severe_dengue_is_true_and_flags_when_stab_missed():
    v = __import__("pipeline.case_v3.loader", fromlist=["CaseRegistry"]).CaseRegistry.from_dir().variant("dengue_003_severe")
    me = v.management_expectations
    assert me.emergency_stabilization_required is True
    # a learner who omits stabilization on this true-required case → safety flag
    assert _graded_stabilization_failure(me, v.management, learner_missed_stabilization=True) is True


def test_hypertensive_urgency_false_no_stab_penalty():
    # tuntas + urgency: not an emergency — category alone must NOT force stab
    v = __import__("pipeline.case_v3.loader", fromlist=["CaseRegistry"]).CaseRegistry.from_dir().variant("htn_003_urgency_diabetes")
    assert v.competency.category == SKD2026_CATEGORY_TUNTAS
    assert v.management_expectations.emergency_stabilization_required is not True
    # even a learner who didn't "stabilise" (there's nothing to stabilise) → no flag
    assert _graded_stabilization_failure(v.management_expectations, v.management,
                                         learner_missed_stabilization=True) is False


def test_initial_refer_family_has_stab_plan_in_variant():
    # rule 2: runtime/scoring reads the case's OWN management expectations;
    # a true-required variant must carry an actual stabilization plan.
    v = __import__("pipeline.case_v3.loader", fromlist=["CaseRegistry"]).CaseRegistry.from_dir().variant("pyelo_septic_003")
    assert v.competency.category == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL
    assert v.management_expectations.emergency_stabilization_required is True
    assert v.management.stabilization          # explicit plan present in data
    rep = lint_variant(v)
    assert rep.ok, [str(e) for e in rep.errors]


# ── rule 1: category is never auto-mapped to 3A/3B/4A ─────────────────────

def test_no_auto_map_category_to_skdi_level():
    for cat in (SKD2026_CATEGORY_TUNTAS, SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL):
        assert cat not in ("3A", "3B", "4A")
        # competency.legacy_level stays None unless explicitly verified
        c = Competency(standard="SKD 2026", category=cat)
        assert c.legacy_level is None


# ── rule 2: management not inferred from category for validation/lint ──────

def test_lint_requires_explicit_me_for_initial_refer_not_category_template():
    # a publishable initial&refer variant without management_expectations fails
    # lint/governance explicitly (cannot be inferred from category alone).
    v = __import__("pipeline.case_v3.loader", fromlist=["CaseRegistry"]).CaseRegistry.from_dir().variant("dengue_002_warning")
    # has expectations → passes
    assert v.management_expectations.recognize_diagnose
    rep = lint_variant(v)
    assert rep.ok, [str(e) for e in rep.errors]
    # strip them → governance raises for publishable state
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth, Source
    bad = ClinicalVariant(id="z", family_id="fam_x",
                          competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL),
                          diagnostic=DiagnosticTruth("x"), status="pilot_verified",
                          source_governance={"clinical_reviewer": "dr. R"})
    bad.sources = [Source(title="PNPK", authority="Kemenkes", kind="guideline", url="https://x")]
    g = validate_governance(bad)
    assert not g.ok
    assert any("management_expectations" in str(e) for e in g.errors)


# ── rule 3: analytics logs SKD 2026, not SKDI level as primary ────────────

def test_analytics_schema_uses_skd2026_competency_not_skdi_primary():
    from app.domains.analytics.schemas import PilotEventIn
    ev = PilotEventIn(event="session_started", stage="chat",
                      competency_standard="SKD 2026",
                      competency_category="initial_management_and_referral",
                      legacy_skdi_level=None)
    assert ev.competency_standard == "SKD 2026"
    assert ev.competency_category == "initial_management_and_referral"
    assert ev.legacy_skdi_level is None  # optional, only when verified
    # default standard is SKD 2026 (not SKDI)
    assert PilotEventIn(event="debrief_opened").competency_standard == "SKD 2026"


def test_analytics_model_has_competency_columns_not_skdi_primary():
    from app.domains.analytics.models import PilotEvent, ALLOWED_EVENTS
    cols = {c.name for c in PilotEvent.__table__.columns}
    assert "competency_standard" in cols
    assert "competency_category" in cols
    assert "legacy_skdi_level" in cols  # optional, secondary
    assert "session_started" in ALLOWED_EVENTS


# ── rule 5: epidemiology layering explicit ─────────────────────────────────

def test_epidemiology_three_layers_are_explicit_for_runtime():
    import sys as _sys
    from pipeline.case_v3.models import Epidemiology
    epi = Epidemiology()
    # authoring decides constraints; runtime only randomises persona_variables
    assert epi.to_dict()["evidence"]["facts"] == {}
    assert "variant_constraints" in epi.to_dict()
    assert "persona_variables" in epi.to_dict()
    # persona granularity is explicit (name/occupation/tone), not clinical truth
    pv = epi.persona_variables.to_dict()
    assert "name" in pv and "verbosity" in pv and "emotional_tone" in pv