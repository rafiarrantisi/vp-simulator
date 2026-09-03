"""FASE 2 — normalized medication concept contract tests (pure, no I/O)."""
from pipeline.case_v3.models import MedicationConcept


def test_valid_medication_concept():
    m = MedicationConcept(
        generic_name="amoxicillin",
        drug_class="aminopenicillin",
        preferred_local_agent="amoxicillin 500 mg kapsul",
        acceptable_alternatives=["cefadroxil"],
        dose_range="500 mg",
        route="oral",
        frequency="3x sehari",
        duration="5 hari",
        contraindications=["alergi penisilin"],
        monitoring=["perbaikan gejala 48-72 jam"],
        referral_restriction="",
        source_refs=["PNPK ISK 2021"],
        formulary_status="in_stock",
    )
    assert m.validate() == []
    d = m.to_dict()
    assert d["generic_name"] == "amoxicillin"
    assert d["formulary_status"] == "in_stock"


def test_generic_name_required():
    assert any("generic_name" in e for e in MedicationConcept(generic_name="").validate())


def test_formulary_status_closed_vocab():
    m = MedicationConcept(generic_name="x", formulary_status="bebas")
    assert any("formulary_status" in e for e in m.validate())
    for ok in ("in_stock", "limited", "non_formulary", "unknown"):
        assert MedicationConcept(generic_name="x", formulary_status=ok).validate() == []


def test_preferred_agent_needs_source():
    m = MedicationConcept(generic_name="x", preferred_local_agent="merek Y")
    assert any("source_refs" in e for e in m.validate())


def test_defaults_are_empty_not_none():
    m = MedicationConcept(generic_name="paracetamol")
    assert m.validate() == []
    assert m.acceptable_alternatives == [] and m.contraindications == []
    assert m.formulary_status == "unknown"
