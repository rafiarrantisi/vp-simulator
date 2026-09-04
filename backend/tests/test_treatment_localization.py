"""FASE 5 — treatment localization tests (deterministic, offline, no LLM, no DB).

Covers: ID/EN aliases, brand->generic, class terms, abbreviations, typo
tolerance, dose errors, unsafe contraindications, acceptable alternatives,
spelling variance, learner-stage detail rules, Fornas isolation (formulary
context never changes a verdict), and the STOP guard: the LLM judges must
NOT import the treatment layer (FASE 5 stops before judge rewiring).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.case_v3 import formulary_id as FID
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.treatment import (DoseSpec, TreatmentAgent, TreatmentProfile,
                                        assess_treatment, parse_segment,
                                        profile_from_variant, required_detail)


def _profile() -> TreatmentProfile:
    return TreatmentProfile(
        variant_id="demo", indication="demo",
        agents=[
            TreatmentAgent(generic="amoxicillin", role="preferred",
                           dose=DoseSpec(min_amount=500, max_amount=1000, unit="mg",
                                         route="PO", freq_per_day="3",
                                         duration="5-7 days"), verified=True),
            TreatmentAgent(generic="azithromycin", role="alternative",
                           dose=DoseSpec(min_amount=500, max_amount=500, unit="mg",
                                         route="PO", freq_per_day="1",
                                         duration="3 days"), verified=True),
        ])


def test_aliases_id_en_brand():
    assert FID.lookup_generic("amoksisilin") == "amoxicillin"
    assert FID.lookup_generic("Amoxsan") == "amoxicillin"
    assert FID.lookup_generic("parasetamol") == "paracetamol"
    assert FID.lookup_generic("Panadol") == "paracetamol"
    assert FID.lookup_generic("acetaminophen") == "paracetamol"
    assert FID.lookup_generic("aspilet") == "aspirin"
    assert FID.lookup_generic("oralit") == "oral rehydration salts"
    assert FID.lookup_generic("ttd") == "ferrous sulfate"  # Tablet Tambah Darah = iron


def test_class_terms_and_abbreviations():
    assert FID.lookup_class("PPI") == "proton-pump inhibitor"
    assert FID.lookup_class("oains") == "nsaid"
    assert FID.lookup_class("antibiotik") == "antibiotic"
    p = parse_segment("beri antibiotik dan antihipertensi")
    assert "antibiotic" in p["class_terms"] and not p["agents"]
    a = assess_treatment("beri antibiotik", _profile(), learner_stage="koas")
    assert a.overall == "incomplete"


def test_typo_tolerance():
    g, d = FID.fuzzy_generic("amoxcillin")
    assert g == "amoxicillin" and d <= 2
    a = assess_treatment("amoxcillin 500mg TID 7 days", _profile(), learner_stage="koas")
    assert a.overall == "preferred"


def test_spelling_variance_id():
    a = assess_treatment("amoksisilin 500mg 3x sehari 7 hari", _profile(), learner_stage="koas")
    assert a.overall == "preferred"


def test_acceptable_alternative_not_zeroed():
    a = assess_treatment("azithromycin 500 mg once daily 3 days", _profile(), learner_stage="koas")
    assert a.overall == "acceptable"
    # international alternative stays acceptable even though not local-preferred
    assert not any("formulary" in n.lower() and "wrong" in n.lower() for n in a.notes)


def test_dose_error_is_inappropriate():
    a = assess_treatment("amoxicillin 3000 mg TID", _profile(), learner_stage="koas")
    assert a.overall == "inappropriate"
    assert any("dose" in n for ag in a.agents for n in ag.notes)


def test_unsafe_nsaid_in_bleeding_context():
    prof = TreatmentProfile(variant_id="x", indication="dengue-like febrile",
                            agents=[TreatmentAgent(generic="paracetamol", role="preferred")])
    a = assess_treatment("ibuprofen for the fever", prof, learner_stage="koas",
                         bleeding_context=True)
    assert a.overall == "unsafe"
    assert a.unsafe_hits


def test_unsafe_aspirin_in_child():
    prof = TreatmentProfile(variant_id="x", indication="fever",
                            agents=[TreatmentAgent(generic="paracetamol", role="preferred")])
    a = assess_treatment("aspirin", prof, learner_stage="koas", age_years=7)
    assert a.overall == "unsafe"


def test_unsafe_iv_bolus_adrenaline():
    prof = TreatmentProfile(
        variant_id="x", indication="anaphylaxis",
        agents=[TreatmentAgent(generic="adrenaline", role="preferred",
                               dose=DoseSpec(route="IM"), verified=True)])
    a = assess_treatment("adrenaline IV bolus", prof, learner_stage="koas")
    assert a.overall == "unsafe"


def test_learner_stage_detail_rules():
    # koas demands dose detail when truth specifies it
    a = assess_treatment("amoxicillin", _profile(), learner_stage="koas")
    assert a.overall == "incomplete"
    assert any("dose" in m for ag in a.agents for m in ag.detail_missing)
    # preclinical: agent concept suffices
    b = assess_treatment("amoxicillin", _profile(), learner_stage="preclinical")
    assert b.overall == "preferred"
    # thin truth (no dose specified) never punishes the student
    thin = TreatmentProfile(variant_id="t", indication="t",
                            agents=[TreatmentAgent(generic="amoxicillin", role="preferred")])
    assert required_detail("koas", "management", thin) == {"agent"}
    c = assess_treatment("amoxicillin", thin, learner_stage="koas")
    assert c.overall == "preferred"


def test_fornas_never_changes_verdict():
    a = assess_treatment("amoxicillin 500 mg TID 7 days", _profile(), learner_stage="koas")
    assert a.overall == "preferred"
    # formulary notes exist (context) but carry no penalty language
    assert a.formulary_notes
    assert all("never changes correctness" in n for n in a.formulary_notes)


def test_profile_derives_from_variant_truth():
    reg = CaseRegistry.from_dir()
    v = reg.variants["dengue_002_warning"]
    prof = profile_from_variant(v)
    assert any(a.generic == "paracetamol" for a in prof.agents)  # mined from mgmt text
    assert not any(a.generic == "aspirin" for a in prof.agents)  # negation-guarded
    assert prof.indication == v.diagnostic.working_diagnosis


def test_stop_guard_judge_does_not_import_treatment():
    import subprocess
    r = subprocess.run(["grep", "-rn", "-E",
                        "case_v3.treatment|treatment\\.(assess|profile|parse_|required_detail)|from pipeline.case_v3 import treatment",
                        "app/rag/judge_v2.py",
                        "app/rag/judge_v3.py", "app/domains/sessions/v2_router.py",
                        "app/domains/sessions/v3_compat_service.py"],
                       capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
    assert r.stdout.strip() == "", f"judge wired to treatment layer:\n{r.stdout}"
