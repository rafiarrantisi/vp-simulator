"""STEP 8 — clinical QA, red-teaming, consistency, promotion gate tests.

Covers 08_CLINICAL_QA_AND_AUTOMATED_TESTING.md:
  §4  canonical-truth consistency invariants
  §5  scoring fixtures directional correctness
  §3  patient red-team (overshare / immutability / dx leak / prompt leak /
      paraphrase / ID-EN / repeat / irrelevant)
  §7  source QA (Fornas-as-guideline guard, url, currentness)
  §13 promotion rule (human gate; no AI self-verification loophole)
  §6  doctor/educator comparison contract (must not be fabricated)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.qa import (
    QAIssue, ReviewRecord, consistency_issues, human_comparison_needed,
    human_review_checklist, promotion_allowed, scoring_fixture_issues,
)
from pipeline.case_v3.redteam import run_red_team
from pipeline.case_v3.semantic import DiagnosisEvaluator, diagnose_match, expand_id
from pipeline.case_v3.sourceqa import source_issues, random_audit_sample
from pipeline.case_v3.models import ClinicalVariant, Competency
from pipeline.case_v3.vocab import SKD2026_CATEGORY_TUNTAS

_reg = None


def registry() -> CaseRegistry:
    global _reg
    if _reg is None:
        _reg = CaseRegistry.from_dir()
    return _reg


# ── §4 consistency invariants ─────────────────────────────────────────────

def test_all_golden_variants_are_consistent():
    r = registry()
    for v in r.variants.values():
        errs = [x for x in consistency_issues(v) if x.severity == "error"]
        assert not errs, f"{v.id}: {[str(e) for e in errs]}"


def test_vitals_and_dx_single_source():
    v = registry().variant("dengue_003_severe")
    # derive_vitals == physical_exam vitals (no second copy to drift)
    from pipeline.case_v3.derive import derive_vitals
    assert derive_vitals(v) == [x.to_dict() for x in v.physical_exam.vitals]
    # dx the same in diagnostic + debrief
    from pipeline.case_v3.derive import derive_debrief
    assert derive_debrief(v)["working_diagnosis"] == v.diagnostic.working_diagnosis


def test_consistency_catches_a_fabricated_vitals_copy():
    # If someone introduced a duplicate vitals list, the invariant must flag it.
    v = registry().variant("dengue_001_mild")
    # simulate: derive_vitals would still read PE, so we monkeypatch a mismatch
    from pipeline.case_v3 import qa as qa_mod
    from pipeline.case_v3.derive import derive_vitals
    orig = qa_mod.derive_vitals
    qa_mod.derive_vitals = lambda _v: orig(_v) + [{"name": "extra", "value": 999, "unit": "x"}]
    try:
        issues = consistency_issues(v)
        assert any(i.code == "vitals_mismatch" and i.severity == "error" for i in issues)
    finally:
        qa_mod.derive_vitals = orig


# ── §5 scoring fixtures ───────────────────────────────────────────────────

def test_scoring_fixture_direction_all_variants():
    r = registry()
    for v in r.variants.values():
        errs = [x for x in scoring_fixture_issues(v) if x.severity == "error"]
        assert not errs, f"{v.id}: {[str(e) for e in errs]}"


def test_unsafe_fixture_triggers_safety_for_initial_refer():
    from pipeline.case_v3.runtime import ScoreInput, score_encounter
    v = registry().variant("dengue_003_severe")  # emergency_stabilization_required True
    unsafe = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                        collected_items={}, stabilized=False,
                                        gave_referral=False, diagnosis_submitted="Severe dengue"))
    assert any(g["gate"] in ("failure_to_stabilize", "missed_emergency_red_flag")
               for g in unsafe.safety_flags)


# ── §3 patient red-team ───────────────────────────────────────────────────

def test_red_team_all_pass_for_golden():
    r = registry()
    for v in r.variants.values():
        fails = [c for c in run_red_team(v) if not c.ok]
        assert not fails, f"{v.id}: {[c.name for c in fails]}"


def test_no_dx_leak_in_red_team():
    v = registry().variant("dengue_003_severe")
    for c in run_red_team(v):
        if c.name in ("no_dx_leak_dto", "no_rubric_leak", "no_prompt_leak"):
            assert c.ok, c.detail


# ── semantic grading ID / EN / abbreviation / typo / synonym ──────────────

def test_id_abbreviation_dbd_resolves_to_dengue():
    ev = DiagnosisEvaluator()
    res = ev.matches("DBD", "Severe dengue with shock (Dengue Shock Syndrome)",
                     synonyms=["Dengue shock syndrome", "Severe dengue"])
    assert res["match"] is True, res["note"]
    assert "dbd" in expand_id("DBD") or "dengue" in expand_id("DBD")


def test_id_synonym_hipertensi_matches_hypertension():
    ev = DiagnosisEvaluator()
    for surface in ("Hipertensi", "Tensi tinggi", "hypertension"):
        res = ev.matches(surface, "Essential (primary) hypertension, stage 1",
                         synonyms=["Primary hypertension", "Hypertension stage 1"])
        assert res["match"] is True, f"{surface}: {res['note']}"


def test_typo_and_synonym_and_paraphrase_all_accepted():
    ev = DiagnosisEvaluator()
    for cand in ("Severe dengue with shock", "Dengue shoock", "DBD", "Dengue syok berat",
                 "Dengue Shock Syndrome"):
        res = ev.matches(cand, "Severe dengue with shock (Dengue Shock Syndrome)",
                         synonyms=["Dengue shock syndrome", "Severe dengue"])
        assert res["match"] is True, f"{cand}: {res['note']}"


# ── §7 source QA ──────────────────────────────────────────────────────────

def test_no_fornas_as_guideline_in_golden():
    r = registry()
    for v in r.variants.values():
        errs = [x for x in source_issues(v) if x.severity == "error"]
        assert not errs, f"{v.id}: {[str(e) for e in errs]}"
        for x in source_issues(v):
            assert x.code != "fornas_as_guideline"


def test_source_audit_sample_is_deterministic_and_bounded():
    r = registry()
    a1 = random_audit_sample(list(r.variants.values()), k=3, seed=1)
    a2 = random_audit_sample(list(r.variants.values()), k=3, seed=1)
    assert a1.sample == a2.sample and len(a1.sample) <= 3


# ── §13 promotion rule (human gate) ───────────────────────────────────────

def test_ai_cannot_self_promote_to_reviewed():
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth
    v = ClinicalVariant(id="x", family_id="fam",
                        competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_TUNTAS),
                        diagnostic=DiagnosticTruth("Disease"), status="research_complete")
    # AI (no human record) trying to self-promote -> BLOCKED
    ok, why = promotion_allowed(v, "pilot_verified", human_record=None)
    assert ok is False
    assert "human" in why.lower()


def test_human_review_grants_reviewed_state():
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth
    v = ClinicalVariant(id="x", family_id="fam",
                        competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_TUNTAS),
                        diagnostic=DiagnosticTruth("Disease"), status="research_complete")
    rec = ReviewRecord(reviewer_name="dr. Ningsih", reviewer_role="clinical_educator", date="2026-09-02")
    ok, why = promotion_allowed(v, "clinically_reviewed", human_record=rec)
    assert ok is True
    # but a reviewed state is ONLY valid with a real judgement behind it
    assert human_comparison_needed(v) is False  # not yet reviewed


def test_promotion_requires_named_human_for_reviewed_state():
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth
    v = ClinicalVariant(id="x", family_id="fam",
                        competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_TUNTAS),
                        diagnostic=DiagnosticTruth("Disease"), status="research_complete")
    # empty reviewer = not a real human sign-off
    bad = ReviewRecord(reviewer_name="", reviewer_role="", date="2026-09-02")
    ok, why = promotion_allowed(v, "pilot_verified", human_record=bad)
    assert ok is False


def test_human_review_checklist_present():
    cl = human_review_checklist()
    assert "safety_gates" in cl and "sources" in cl and "treatment" in cl


def test_human_comparison_is_not_fabricated():
    # HumanJudgement is a contract; approval stays Optional[None] until a real
    # doctor/educator provides it. The test only asserts the field can be None.
    from pipeline.case_v3.qa import HumanJudgement
    hj = HumanJudgement(reviewer_name="", reviewer_role="doctor", date="2026-09-02")
    assert hj.approval is None   # pending human sign-off, never auto-set