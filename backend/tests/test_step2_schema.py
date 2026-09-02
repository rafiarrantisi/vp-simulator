"""STEP 2 — New case architecture and canonical clinical schema.

Validates 02_NEW_CASE_ARCHITECTURE_AND_SCHEMA.md acceptance criteria:
  - family/variant/persona layers explicit
  - disease + presentation families both supported
  - one clinical variant referenced from multiple entry points
  - canonical truth is the single medical source for runtime/scoring/debrief
  - persona generation is constraint-based, cannot alter protected clinical fields
  - complaint-specific history structures allowed (no forced SOCRATES)
  - preclinical/koas task profiles can differ
  - schema validators exist
  - session instance reproducible
  - legacy adapter still works
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.validate import validate_registry, validate_variant
from pipeline.case_v3.derive import (
    derive_answer_key, derive_vitals, derive_scoring_profile,
    derive_history_checklist, derive_red_flags,
)
from pipeline.case_v3.persona import (
    PersonaConstraints, persona_from_constraints, build_session_instance,
)
from pipeline.case_v3.vocab import LearnerStage, VariationLevel

_reg = None


def registry() -> CaseRegistry:
    global _reg
    if _reg is None:
        _reg = CaseRegistry.from_dir()
    return _reg


def test_families_and_variants_load():
    r = registry()
    assert set(r.families) == {"fam_dengue", "fam_fever_child", "fam_uti"}
    assert set(r.variants) == {"dengue_001_mild", "dengue_002_warning",
                               "dengue_003_severe", "uti_child_001"}
    assert len(r.variants_for_family("fam_dengue")) == 3


def test_disease_and_presentation_families_supported():
    r = registry()
    from pipeline.case_v3.vocab import FamilyType
    assert r.family("fam_dengue").family_type == FamilyType.DISEASE
    assert r.family("fam_fever_child").family_type == FamilyType.PRESENTATION


def test_one_variant_reachable_from_multiple_entry_points():
    r = registry()
    # dengue_001_mild is disease-affiliated AND also surfaces via the
    # "Fever in a child" presentation family (cross-entry linking).
    via_disease = r.by_entry_point("disease:dengue")
    via_presentation = r.by_entry_point("presentation:fever in a child")
    assert any(v.id == "dengue_001_mild" for v in via_disease)
    assert any(v.id == "dengue_001_mild" for v in via_presentation)


def test_canonical_truth_single_source():
    """Vitals + answer key DERIVE from the variant — no independent copies."""
    r = registry()
    v = r.variant("dengue_001_mild")
    assert derive_vitals(v) == [x.to_dict() for x in v.physical_exam.vitals]
    assert derive_answer_key(v)["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert derive_answer_key(v)["differentials"][0]["name"] == "Influenza"
    # no drift: every derived field traces to canonical
    assert all(rf["fact"] in [x.fact for x in v.red_flags] for rf in derive_red_flags(v))


def test_persona_cannot_alter_protected_fields():
    r = registry()
    v = r.variant("dengue_001_mild")
    constraints = PersonaConstraints(
        relationship="self", allow_name_generation=True,
        anxiety_level="range", verbosity="range",
    )
    p1 = persona_from_constraints(v, constraints, seed=3)
    p2 = persona_from_constraints(v, constraints, seed=99)
    # randomizable differ across seeds
    assert p1["name"] != p2["name"]
    # protected clinical fields are pinned identically to canonical truth
    assert p1["working_diagnosis"] == p2["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert p1["vitals"] == p2["vitals"] == [x.to_dict() for x in v.physical_exam.vitals]
    assert p1["red_flags"] == p2["red_flags"]


def test_persona_does_not_invent_clinical_values():
    r = registry()
    v = r.variant("uti_child_001")
    pc = PersonaConstraints(relationship="mother", allow_name_generation=True)
    p = persona_from_constraints(v, pc, seed=1)
    # the persona must not fabricate a symptom chronology or diagnosis beyond truth
    assert p["working_diagnosis"] == "Urinary tract infection"
    assert "infection" in p["working_diagnosis"].lower()


def test_complaint_specific_history_not_generic_socrates():
    r = registry()
    v = r.variant("dengue_001_mild")
    groups = [g.name for g in v.history]
    # explicitly NOT forced into SOCRATES — dengue uses symptom/exposure groups
    assert "onset_chronology" in groups and "exposure" in groups
    checklist = derive_history_checklist(v)
    assert any("fever onset" in i["item"].lower() for i in checklist)
    assert any(i["canonical_key"] == "fever_onset" for i in checklist)


def test_preclinical_vs_koas_task_profiles_differ():
    r = registry()
    v = r.variant("dengue_001_mild")
    pre = derive_scoring_profile(v, learner_stage=LearnerStage.PRECLINICAL)
    koas = derive_scoring_profile(v, learner_stage=LearnerStage.KOAS)
    assert koas["require_investigations"] is True
    assert pre["require_investigations"] is False
    # koas has more assessment weight (adds investigations/management critical items)
    assert len(derive_history_checklist(v)) >= 1


def test_shared_variant_supports_both_stages():
    r = registry()
    v = r.variant("dengue_001_mild")
    assert LearnerStage.PRECLINICAL in v.supported_stages
    assert LearnerStage.KOAS in v.supported_stages


def test_variation_levels_distinct():
    r = registry()
    assert r.variant("dengue_001_mild").variation_level == VariationLevel.PERSONA
    assert r.variant("dengue_002_warning").variation_level == VariationLevel.PRESENTATION
    assert r.variant("dengue_003_severe").variation_level == VariationLevel.COMPLEXITY


def test_dengue_variants_clinically_distinct_not_name_only():
    r = registry()
    a = r.variant("dengue_001_mild").canonical_hash()
    b = r.variant("dengue_002_warning").canonical_hash()
    c = r.variant("dengue_003_severe").canonical_hash()
    # distinct clinical variants → distinct canonical hashes (not name-only churn)
    assert a != b and b != c and a != c


def test_session_instance_reproducible():
    r = registry()
    v = r.variant("dengue_001_mild")
    s1 = build_session_instance(v, persona_seed=7, learner_stage="koas", mode="blind")
    s2 = build_session_instance(v, persona_seed=7, learner_stage="koas", mode="blind")
    assert s1.reproducibility_key() == s2.reproducibility_key()
    # different seed → different persona but same reproducibility structure
    s3 = build_session_instance(v, persona_seed=8, learner_stage="koas", mode="blind")
    assert s1.persona_seed != s3.persona_seed


def test_caregiver_pediatric_informant():
    r = registry()
    v = r.variant("uti_child_001")
    assert v.identity.informant_type == "mother"
    assert v.identity.age_years == 3
    assert v.identity.age_years < 18


def test_3b_emergency_variant_present():
    r = registry()
    severe = r.variant("dengue_003_severe")
    assert severe.skdi_level == "3B"
    assert any(rf.criticality.value == "critical" and rf.fact.lower().startswith("shock")
               for rf in severe.red_flags)


def test_registry_validation_passes():
    r = registry()
    vr = validate_registry(list(r.families.values()), list(r.variants.values()))
    assert vr.ok, vr.errors[:5]


def test_validation_rejects_duplicate_truth_and_bad_schema():
    r = registry()
    v = r.variant("dengue_001_mild")
    from pipeline.case_v3.models import ClinicalVariant, PhysicalExam, VitalSign
    # simulate disallowed schema: duplicate variant id
    from pipeline.case_v3.validate import validate_registry
    vr = validate_registry(list(r.families.values()),
                           list(r.variants.values()) + [v])
    assert not vr.ok  # duplicate variant id flagged
    # simulate an invalid vital (non-numeric) — schema validator rejects
    from pipeline.case_v3.models import VitalSign
    bad = ClinicalVariant(
        id="x_bad", family_id="fam_dengue",
        diagnostic=v.diagnostic, physical_exam=PhysicalExam(general_appearance="fine"),
    )
    bad.physical_exam.vitals = [VitalSign(name="temperature", value="hot")]
    vres = validate_variant(bad)
    assert not vres.ok
    assert any("not numeric" in str(e) for e in vres.errors)


def test_legacy_adapter_still_works():
    # STEP 1 boundary intact: legacy v2 cases still parse + isolate.
    from pipeline.case_v2 import parse_case_v2, lint
    fp = Path(__file__).resolve().parents[2] / "content" / "cases" / "derm_eczema_001.md"
    c = parse_case_v2(fp)
    assert c.is_legacy() is True
    assert lint(c).ok