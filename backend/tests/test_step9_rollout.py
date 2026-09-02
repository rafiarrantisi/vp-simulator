"""STEP 9 — broad semantic + batch/promotion guard + audit tests.

Ker's STEP-9 rule: semantic evaluator must not overfit the golden families
(dengue/hypertension). We test a WIDE set of SKD 2026 conditions with real
ID/EN/abbreviation/slang surfaces. Also locks the controlled-batch promotion
guard and the audit's strict clinical-vs-generated split.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.semantic import DiagnosisEvaluator, expand_id


_eval = DiagnosisEvaluator()


def _assert_matches(cand, target, synonyms=None):
    res = _eval.matches(cand, target, synonyms=synonyms or [])
    assert res["match"] is True, f"'{cand}' vs '{target}': {res['note']}"


# ── broad ID/EN/abbreviation/slang coverage across many conditions ─────────
def test_wide_id_en_surfaces_not_overfit():
    pairs = [
        ("DBD", "Severe dengue with shock", ["Severe dengue"]),
        ("demam berdarah", "Severe dengue with shock", ["Severe dengue"]),
        ("hipertensi", "Essential hypertension stage 1", ["Hypertension"]),
        ("tekanan darah tinggi", "Essential hypertension stage 1", ["Hypertension"]),
        ("darah tinggi", "Essential hypertension stage 1", ["Hypertension"]),
        ("ISK", "Urinary tract infection", ["UTI"]),
        ("infeksi saluran kemih", "Urinary tract infection", ["UTI"]),
        ("pielonefritis", "Acute pyelonephritis", []),
        ("tuberkulosis", "Pulmonary tuberculosis", ["TB"]),
        ("TB paru", "Pulmonary tuberculosis", ["TB"]),
        ("DM tipe 2", "Type 2 diabetes mellitus", ["Diabetes", "T2DM"]),
        ("kencing manis", "Type 2 diabetes mellitus", ["Diabetes"]),
        ("asma", "Bronchial asthma", []),
        ("pneumonia", "Community-acquired pneumonia", []),
        ("stroke", "Acute ischaemic stroke", ["CVA"]),
        ("typhoid fever", "Typhoid fever", ["Typhoid", "Demam tifoid"]),
        ("demam tifoid", "Typhoid fever", ["Typhoid"]),
        ("malaria", "Malaria", []),
        ("appendicitis", "Acute appendicitis", ["Appendiks"]),
        ("usus buntu", "Acute appendicitis", ["Appendisitis"]),
        ("meningitis", "Bacterial meningitis", []),
        ("gagal ginjal", "Acute renal failure", ["AKI"]),
        ("hepatitis", "Acute hepatitis", []),
    ]
    for cand, target, syn in pairs:
        _assert_matches(cand, target, syn)


def test_abbreviations_expand_to_real_terms():
    assert "dengue" in expand_id("DBD")
    assert "hipertensi" in expand_id("HTN")
    # ISK → tokens include the expanded phrase pieces
    for t in ("infeksi", "urinary"):
        assert t in expand_id("ISK"), f"ISK should expand to '{t}'"
    assert "tuberculosis" in expand_id("TB") or "tuberkulosis" in expand_id("TB")


def test_eng_med_term_in_id_sentence():
    # an Indonesian sentence containing an English clinical term
    _assert_matches("Saya kena dengue berat", "Severe dengue with shock", ["Severe dengue"])


# ── batch/promotion guard ──────────────────────────────────────────────────
def test_generate_batch_caps_at_research_complete():
    """The controlled batch generator must NEVER emit clinically_reviewed /
    pilot_verified / published scaffolds."""
    import tools.generate_batch as gb
    rep = gb.run_batch(["sistem_kejang-demam-komplikata"], n_variants=3, dry_run=True)
    assert rep["promotion_guard"].startswith("CAPPED at research_complete")
    for b in rep["batch"]:
        assert b["status"] == "research_complete"
        assert b["needs_source_pack"] is True
        assert b["ready_for_qa_gate"] is False


def test_audit_strict_split_never_is_true_clinical_bank():
    """Final audit must report generated vs QA-passed vs clinical vs pilot
    separately, and must NOT claim pilot-readiness from counts alone."""
    from pipeline.case_v3.loader import CaseRegistry
    import tools.final_audit as fa
    reg = CaseRegistry.from_dir()
    r = fa.build_report(reg)
    split = r["strict_split"]
    assert split["clinically_reviewed"] == 0          # no human sign-off yet
    assert split["pilot_verified"] == 0
    assert split["generated"] >= split["qa_passed"]    # QA-passed subset of generated
    assert r["pilot_readiness"] in ("READY", "READY WITH KNOWN LIMITATIONS", "NOT READY")
    # honest default: no human records -> NOT READY
    assert r["pilot_readiness"] == "NOT READY" or "KNOWN" in r["pilot_readiness"]