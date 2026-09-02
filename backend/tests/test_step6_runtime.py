"""STEP 6 — backend runtime, selection, scoring, debrief, analytics tests.

Covers 06_BACKEND_RUNTIME_SCORING_AND_ANALYTICS.md §14, adapted to SKD 2026
terminology (superseding rules): no 3A/3B/4A as primary; stabilisation logic
is case-specific (rule 4), analytics logs competency_category (rule 3).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.runtime import (
    SelectionPolicy, SelectionRequest, ScoreInput, VariantUnavailable,
    build_debrief, encounter_stages_for, instantiate_persona,
    safe_select, score_encounter, build_session,
)
from pipeline.case_v3.vocab import (
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL, SKD2026_CATEGORY_TUNTAS,
)
from pipeline.case_v3.models import PersonaConstraints

_reg = None


def registry() -> CaseRegistry:
    global _reg
    if _reg is None:
        _reg = CaseRegistry.from_dir()
    return _reg


def _all_released_ids(r):
    # no variant is verified yet — publishable/verified set is empty for now;
    # tests that need a verified flow pass an explicit set where required.
    return {v.id for v in r.variants.values()}


# ── §14 Selection ──────────────────────────────────────────────────────────

def test_targeted_family_selects_only_its_variants():
    r = registry()
    pol = SelectionPolicy(r)
    s = pol.select(SelectionRequest(mode="targeted", family_id="fam_dengue"))
    assert s.variant.family_id == "fam_dengue"
    assert s.family_title


def test_blind_presentation_cross_selects():
    r = registry()
    pol = SelectionPolicy(r)
    s = pol.select(SelectionRequest(mode="blind", specialty="paediatrics"))
    # a paediatrics-related variant is selected (via primary or cross tag)
    fam = r.families[s.variant.family_id]
    assert "paediatrics" == fam.primary_specialty or "paediatrics" in fam.cross_specialty_tags


def test_recent_variant_avoidance():
    r = registry()
    pol = SelectionPolicy(r)
    req = SelectionRequest(family_id="fam_dengue", seed=0)
    a = pol.select(req)
    # exclude the just-selected one → picks a different variant
    req.exclude_recent_variant_ids = [a.variant.id]
    b = pol.select(req)
    assert b.variant.id != a.variant.id


def test_unverified_excluded_from_verified_only_flow():
    r = registry()
    pol = SelectionPolicy(r)
    # none of the current variants are clinically verified → verified-only must
    # NOT silently substitute an unreviewed case (safe_select raises)
    with pytest.raises(VariantUnavailable):
        safe_select(SelectionRequest(family_id="fam_dengue"), pol, released_ids=set())


# ── §14 Persona ────────────────────────────────────────────────────────────

def test_persona_protected_fields_unchanged_and_deterministic():
    r = registry()
    v = r.variant("dengue_003_severe")
    constraints = PersonaConstraints(relationship="self", allow_name_generation=True,
                                     anxiety_level="range")
    pc = v.protected_fields_canonical()
    p1 = instantiate_persona(v, constraints, seed=5, protected_expected=pc)
    p2 = instantiate_persona(v, constraints, seed=5, protected_expected=pc)
    assert p1.persona["name"] == p2.persona["name"]       # deterministic seed
    assert p1.protected_unchanged is True
    # protected (diagnosis/vitals/red flags) identical to canonical
    assert p1.persona["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert p1.persona["vitals"] == [x.to_dict() for x in v.physical_exam.vitals]


def test_persona_fallback_safe():
    r = registry()
    v = r.variant("dengue_003_severe")
    pc = v.protected_fields_canonical()
    # a broken constraint config can't break protected truths
    res = instantiate_persona(v, None, seed=1, protected_expected=pc)
    assert res.used_fallback is True       # safe default persona used
    assert res.persona["working_diagnosis"] == pc["working_diagnosis"]
    assert res.persona["vitals"] == pc["vitals"]


def test_session_reproducible_key():
    r = registry()
    v = r.variant("dengue_003_severe")
    a = build_session(v, persona_seed=7, learner_stage="koas", mode="blind")
    b = build_session(v, persona_seed=7, learner_stage="koas", mode="blind")
    assert a["session_reproducible_key"] == b["session_reproducible_key"]


# ── §14 Scoring ────────────────────────────────────────────────────────────

def test_scoring_family_and_variant_rubric_merge():
    v = registry().variant("htn_001_typical")
    res = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                     collected_items={}))
    assert "info_gathering" in res.by_dimension
    assert "management_safety" in res.by_dimension


def test_preclinical_vs_koas_profile_differ():
    v = registry().variant("dengue_001_mild")
    pre = score_encounter(ScoreInput(variant=v, learner_stage="preclinical", collected_items={}))
    koas = score_encounter(ScoreInput(variant=v, learner_stage="koas", collected_items={}))
    assert pre.by_dimension["info_gathering"]["score"] == koas.by_dimension["info_gathering"]["score"]
    # weights differ structurally
    from pipeline.case_v3.runtime import learner_profile
    assert learner_profile("preclinical")["weights"] != learner_profile("koas")["weights"]


def test_initial_refer_missing_stabilization_flags_safety():
    # rule 4: initial_management_and_referral + emergency_stabilization_required=True
    # + learner missed stabilization → safety flag
    v = registry().variant("dengue_003_severe")  # emergency_stabilization_required True
    assert v.competency.category == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL
    res = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                     stabilized=False, gave_referral=True, collected_items={}))
    gates = {g["gate"] for g in res.safety_flags}
    assert "failure_to_stabilize" in gates


def test_initial_refer_no_emergency_no_stabilization_penalty():
    # rule 4: category "initial_management_and_referral" + case says
    # emergency_stabilization_required=False → NO automatic stabilization penalty
    v = registry().variant("dengue_002_warning")
    assert v.management_expectations.emergency_stabilization_required is False
    res = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                     stabilized=False, gave_referral=True, collected_items={}))
    gates = {g["gate"] for g in res.safety_flags}
    assert "failure_to_stabilize" not in gates


def test_tuntas_judged_on_case_specific_management():
    v = registry().variant("htn_003_urgency_diabetes")  # tuntas, has referral expectation
    res = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                     collected_items={"management_complete": True},
                                     gave_referral=True))
    # management_safety dimension favorable; safety_gates: no forced stab gate for tuntas
    gates = {g["gate"] for g in res.safety_flags}
    assert "failure_to_stabilize" not in gates


# ── §14 Debrief ────────────────────────────────────────────────────────────

def test_debrief_source_metadata_and_no_fabrication():
    v = registry().variant("dengue_003_severe")
    db = build_debrief(v)
    assert db["sources"] and all(s["title"] for s in db["sources"])
    # source URLs/orgs come from canonical content (never invented at scoring)
    assert any("WHO" in (s["organization"] or "") for s in db["sources"])
    assert db["competency_mapping"]["standard"] == "SKD 2026"
    assert db["management_expectations"]["emergency_stabilization_required"] is True


def test_debrief_critical_miss_rationale_present():
    v = registry().variant("dengue_003_severe")
    db = build_debrief(v)
    # biggest_misses derive from present red flags with why-matters rationale
    assert db["biggest_misses"]
    assert any(r["why_matters"] for r in db["biggest_misses"])


# ── §14 Analytics ──────────────────────────────────────────────────────────

def test_analytics_model_has_new_case_behavioural_columns():
    from app.domains.analytics.models import PilotEvent
    cols = {c.name for c in PilotEvent.__table__.columns}
    for col in ("family_id", "variant_id", "presentation_path", "interaction_mode",
                "learner_level", "persona_fallback", "content_schema",
                "competency_category", "competency_standard"):
        assert col in cols, col


def test_analytics_schema_carries_behaviour():
    from app.domains.analytics.schemas import PilotEventIn
    ev = PilotEventIn(event="session_started", family_id="fam_dengue",
                      variant_id="dengue_003_severe", interaction_mode="blind",
                      learner_level="koas", competency_category="initial_management_and_referral",
                      content_schema="new")
    assert ev.family_id == "fam_dengue" and ev.variant_id == "dengue_003_severe"
    assert ev.content_schema == "new"     # new-schema tag (STEP-6 §12)
    assert ev.competency_category == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL


def test_analytics_schema_legacy_separation():
    from app.domains.analytics.schemas import PilotEventIn
    legacy = PilotEventIn(event="session_started", content_schema="legacy")
    assert legacy.content_schema == "legacy"


# ── §14 Failure modes ──────────────────────────────────────────────────────

def test_variant_unavailable_failure_path():
    r = registry()
    pol = SelectionPolicy(r)
    with pytest.raises(VariantUnavailable):
        pol.select(SelectionRequest(family_id="fam_does_not_exist"))
    # encounter stages adapt to case content
    stages = encounter_stages_for(r.variant("dengue_003_severe"), mode="blind")
    assert "vitals" in stages and "investigations" in stages