"""STEP 5 — generation pipeline tests (golden families, persona, modes, linter).

Validates 05_CASE_GENERATION_PIPELINE.md §13 on the golden demo families:
  - same variant generates different personas but identical protected truth
  - different variants are truly clinically distinct (canonical hash)
  - targeted mode shows disease appropriately
  - blind mode hides diagnosis
  - family core rubric + variant rubric combine
  - safety requirement works (emergency/stabilisation for tatalaksana-awal-rujuk)
  - source-backed answer key resolves
  - no canonical inconsistencies
  - linter passes for generated variants
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.lint import lint_variant
from pipeline.case_v3.derive import (
    derive_generation_bundle, derive_mode_views, derive_answer_key,
    derive_history_checklist, derive_scoring_profile,
)
from pipeline.case_v3.persona import (
    PersonaConstraints, persona_from_constraints,
)
from pipeline.case_v3.vocab import (
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL, SKD2026_CATEGORY_TUNTAS,
    FamilyType, ItemImportance,
)

_reg = None


def registry() -> CaseRegistry:
    global _reg
    if _reg is None:
        _reg = CaseRegistry.from_dir()
    return _reg


# ── golden demo structure ──────────────────────────────────────────────────

def test_three_golden_families_exist_with_min_3_variants():
    r = registry()
    assert {"fam_dengue", "fam_hypertension", "fam_uti"} <= set(r.families)
    for fid in ("fam_dengue", "fam_hypertension", "fam_uti"):
        assert len(r.variants_for_family(fid)) >= 3, fid


def test_golden_families_span_skd2026_categories():
    r = registry()
    fams = ["fam_dengue", "fam_hypertension", "fam_uti"]
    cats = set()
    for fid in fams:
        for v in r.variants_for_family(fid):
            cats.add(v.competency.category)
    # we need at least one Tuntas and one initial_management_and_referral family
    assert SKD2026_CATEGORY_TUNTAS in cats
    assert SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL in cats


def test_golden_families_lint_clean():
    r = registry()
    err = []
    for fid, fam in r.families.items():
        for v in r.variants_for_family(fid):
            rep = lint_variant(v)
            err += [f"{v.id}: {i}" for i in rep.errors]
    assert not err, err[:10]


def test_presentation_family_cross_references_disease_variants():
    r = registry()
    fever = r.by_entry_point("presentation:fever in a child")
    ids = {v.id for v in fever}
    # fever presentation surfaces dengue + uti variants from DIFFERENT families
    assert ids & {"dengue_001_mild", "dengue_003_severe", "uti_child_001", "uti_adult_002"}


# ── persona is constrained; protected truth identical ─────────────────────

def test_persona_differs_but_protected_truth_identical():
    r = registry()
    v = r.variant("dengue_003_severe")
    pc = PersonaConstraints(relationship="self", allow_name_generation=True)
    p1 = persona_from_constraints(v, pc, seed=1)
    p2 = persona_from_constraints(v, pc, seed=2)
    # randomisable skin differs
    assert p1["name"] != p2["name"]
    # protected clinical truth identical (single source of truth invariant)
    assert p1["working_diagnosis"] == p2["working_diagnosis"]
    assert p1["vitals"] == p2["vitals"]
    assert p1["red_flags"] == p2["red_flags"]


def test_variants_are_truly_clinically_distinct():
    r = registry()
    # within hypertension: canonical hashes differ (not name-only churn)
    hashes = {r.variant(v).canonical_hash() for v in
              ("htn_001_typical", "htn_002_salt_sensitive", "htn_003_urgency_diabetes")}
    assert len(hashes) == 3


# ── targeted vs blind mode ─────────────────────────────────────────────────

def test_targeted_mode_shows_disease():
    v = registry().variant("dengue_003_severe")
    modes = derive_mode_views(v, family_title="Dengue")
    assert modes["targeted"]["diagnosis_visible"] is True
    assert modes["targeted"]["diagnosis"]  # diagnosis shown
    assert "Dengue" in modes["targeted"]["title"]


def test_blind_mode_hides_diagnosis():
    v = registry().variant("dengue_003_severe")
    modes = derive_mode_views(v, family_title="Dengue")
    blind = modes["blind"]
    assert blind["diagnosis_visible"] is False
    assert blind["diagnosis"] is None
    assert blind["candidate_brief"]  # only candidate brief shown


# ── scoring / rubric / answer key / debrief ────────────────────────────────

def test_scoring_and_debrief_derive_from_canonical():
    v = registry().variant("uti_pyelonephritis_003")
    bundle = derive_generation_bundle(v, family_title="Urinary tract infection")
    assert bundle["answer_key"]["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert bundle["debrief"]["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert bundle["scoring_profile"]["safety_critical_errors"]
    assert bundle["modes"]["targeted"]["diagnosis_visible"] is True


def test_answer_key_source_backed():
    v = registry().variant("dengue_003_severe")
    ak = derive_answer_key(v)
    assert ak["sources"], "answer key must carry sources (source-backed)"
    assert any("WHO" in (s["title"] or "") or "PNPK" in (s["title"] or "")
               for s in ak["sources"])


def test_family_core_and_variant_rubric_combine():
    # history checklist = canonical history facts + explicit assessment items
    v = registry().variant("htn_001_typical")
    items = derive_history_checklist(v)
    assert items
    assert any(i["canonical_key"] for i in items)          # from history facts
    assert any(i["importance"] == ItemImportance.CRITICAL.value for i in items)


def test_safety_requirement_works_for_initial_refer():
    # severe dengue (initial_management_and_referral) must demand stabilisation
    v = registry().variant("dengue_003_severe")
    assert v.competency.category == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL
    me = v.management_expectations
    assert me.emergency_stabilization_required is True
    assert v.management.stabilization           # explicit stabilisation plan
    assert v.management.referral                # referral behaviour
    assert v.safety_critical_errors             # safety gates


def test_management_expectations_not_inferred_from_category():
    # mild variant is Tuntas; management expectations differ per disease, not
    # blanket — e.g. hypertensive urgency is NOT an emergency even though severe
    v = registry().variant("htn_003_urgency_diabetes")
    assert v.competency.category == SKD2026_CATEGORY_TUNTAS
    assert "not a hypertensive emergency" in (v.management.stabilization[0] or "").lower()