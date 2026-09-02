"""STEP-6 superseding rules 4-8 — integration honesty & security tests.

  4. variant count shown = ELIGIBLE (not all files).
  5. 'another patient' = genuinely different eligible variant, else replay flag.
  6. Blind-mode candidate payload never leaks diagnosis/rubric/answer-key/management.
  7. semantic grading is tolerant (no exact-string fail) & pluggable, labelled
     advisory (not clinically robust).
  8. presentation families select existing canonical variants (no dup generation).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.runtime import (
    SelectionPolicy, SelectionRequest, candidate_safe_view,
    score_encounter, ScoreInput,
)
from pipeline.case_v3.semantic import DiagnosisEvaluator, diagnose_match
from pipeline.case_v3.models import PersonaConstraints

_reg = None


def registry() -> CaseRegistry:
    global _reg
    if _reg is None:
        _reg = CaseRegistry.from_dir()
    return _reg


# ── Rule 4: eligible variant count ─────────────────────────────────────────

def test_eligible_count_excludes_unavailable_variants():
    r = registry()
    pol = SelectionPolicy(r)
    # all variants are research_complete (unverified) — a verified-only request
    # has ZERO eligible. The user-facing count must reflect that.
    req = SelectionRequest(family_id="fam_dengue", released_ids=set())
    assert pol.eligible_count(req) == 0            # nothing verified -> 0 shown
    # without release filter (pilot), count = stage-compatible variants
    req2 = SelectionRequest(family_id="fam_dengue", learner_stage="koas", released_ids=None)
    assert pol.eligible_count(req2) == len([v for v in r.variants.values()
                                            if v.family_id == "fam_dengue"])


def test_eligible_count_is_learner_level_aware():
    r = registry()
    pol = SelectionPolicy(r)
    preclin = SelectionRequest(family_id="fam_dengue", learner_stage="preclinical", released_ids=None)
    koas = SelectionRequest(family_id="fam_dengue", learner_stage="koas", released_ids=None)
    # dengue: only dengue_001_mild supports preclinical; koas supports all 3
    pre = pol.eligible_for(preclin)
    assert all("preclinical" in v.supported_stages for v in pre)
    assert pol.eligible_count(preclin) < pol.eligible_count(koas)


# ── Rule 5: another patient ────────────────────────────────────────────────

def test_another_patient_returns_different_eligible_variant():
    r = registry()
    pol = SelectionPolicy(r)
    req = SelectionRequest(family_id="fam_dengue", learner_stage="koas", released_ids=None, seed=0)
    res = pol.next_for_another_patient(req, "dengue_001_mild")
    assert res["kind"] == "new_clinical_variant"
    assert res["variant_id"] != "dengue_001_mild"       # genuinely different variant


def test_another_patient_replay_when_only_same_available():
    r = registry()
    pol = SelectionPolicy(r)
    # verified-only flow has zero eligible -> honest replay, NOT a new case
    req = SelectionRequest(family_id="fam_dengue", released_ids=set())
    res = pol.next_for_another_patient(req, "dengue_001_mild")
    assert res["kind"] == "replay_persona_variation"
    assert res["different_from_current"] is False
    assert "replay" in res["note"]


# ── Rule 6: candidate-safe blind DTO ───────────────────────────────────────

def test_candidate_safe_blind_never_leaks():
    r = registry()
    v = r.variant("dengue_003_severe")
    persona = v.protected_fields_canonical()
    dto = candidate_safe_view(v, persona, mode="blind", family_title="Dengue")
    assert dto["diagnosis_hidden"] is True
    payload = str(dto)
    assert "working_diagnosis" not in payload       # no target dx
    assert "Severe dengue" not in payload           # no diagnosis value
    assert "rubric" not in payload and "answer_key" not in payload
    assert "management" not in payload
    # candidate brief only
    assert dto["candidate_brief"]


def test_targeted_mode_still_hides_rubric_answerkey():
    r = registry()
    v = r.variant("dengue_003_severe")
    persona = v.protected_fields_canonical()
    dto = candidate_safe_view(v, persona, mode="targeted", family_title="Dengue")
    # targeted shows the diagnosis (it is the point) but never the rubric/answer
    payload = str(dto)
    assert "rubric" not in payload and "answer_key" not in payload
    assert "management" not in payload


# ── Rule 7: semantic grading is tolerant & pluggable ───────────────────────

def test_semantic_exact_and_paraphrase_both_pass():
    ev = DiagnosisEvaluator()
    # exact
    assert ev.matches("Severe dengue with shock", "Severe dengue with shock (Dengue Shock Syndrome)",
                      synonyms=[])[
        "match"] is True
    # paraphrase / core-term (not exact) still passes
    r = ev.matches("Dengue shock", "Severe dengue with shock (Dengue Shock Syndrome)",
                   synonyms=["Dengue shock syndrome", "Severe dengue"])
    assert r["match"] is True and r["grade"] in ("synonym", "paraphrase", "partial")
    # a typo is tolerated (no exact-string clinical failure)
    r2 = ev.matches("Dengue shoock", "Severe dengue with shock (Dengue Shock Syndrome)",
                    synonyms=["Dengue shock syndrome"])
    # heuristic grader must not fail a learner purely for a typo
    assert r2["match"] is True


def test_mismatch_is_not_a_silent_clinical_fail():
    ev = DiagnosisEvaluator()
    r = ev.matches("Malaria", "Severe dengue with shock", synonyms=["Severe dengue"])
    assert r["match"] is False
    assert "clinically robust" not in str(r)  # must not over-claim


def test_scoring_does_not_fail_on_paraphrase():
    v = registry().variant("dengue_003_severe")
    res = score_encounter(ScoreInput(variant=v, learner_stage="koas",
                                     collected_items={}, stabilized=False, gave_referral=True,
                                     diagnosis_submitted="Severe Dengue Shock Syndrome"))
    dq = res.by_dimension["diagnostic_quality"]
    assert dq["score"] >= 0.99     # paraphrase counted as correct
    assert dq["grade"] in ("paraphrase", "exact", "synonym")


def test_semantic_evaluator_is_pluggable():
    class FakeEval(DiagnosisEvaluator):
        def name(self): return "grounded_eval_v2"

    ev = FakeEval()
    assert ev.name() == "grounded_eval_v2"
    # diagnose_match honours an injected evaluator
    assert isinstance(diagnose_match("x", "y", evaluator=ev), dict)


# ── Rule 8: presentation families reuse canonical variants ────────────────

def test_presentation_family_resolves_to_existing_variants():
    r = registry()
    # presentation family has NO its-own variants; it resolves via entry points
    assert len(r.variants_for_family("fam_fever_child")) == 0
    fever = r.by_entry_point("presentation:fever in a child")
    assert fever, "presentation family must surface existing eligible variants"
    ids = {v.id for v in fever}
    # these are canonical disease-family variants, not duplicates
    assert ids & {"dengue_001_mild", "dengue_003_severe", "uti_child_001", "uti_adult_002"}