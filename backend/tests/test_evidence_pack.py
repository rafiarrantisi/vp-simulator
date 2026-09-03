"""FASE 2 — Approved Clinical Evidence Pack: hierarchy + validation tests.

Report-only: these tests pin the source-hierarchy rules and the CURRENT
state of the 5 families. Draft families (hypertension, pyelonephritis) carry
no linked variants yet, so pack errors there are EXPECTED and asserted as
documented gaps — not silently fixed, never auto-promoted.
"""
import pytest

from pipeline.case_v3.evidence import (
    build_evidence_pack,
    infer_tier,
    lint_evidence_family,
    validate_evidence_pack,
)
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.models import CaseFamily, ClinicalVariant, Competency, Source


@pytest.fixture(scope="module")
def registry():
    return CaseRegistry.from_dir()


def _fam_vars(registry, fid):
    fam = registry.families[fid]
    return fam, [registry.variants[vid] for vid in (fam.active_variant_ids or [])
                 if vid in registry.variants]


# ── Tier inference ───────────────────────────────────────────────────────────
def test_infer_tier_hierarchy():
    assert infer_tier(Source(title="PNPK Dengue", authority="Kemenkes", kind="guideline")) == "1"
    assert infer_tier(Source(title="X", authority="KKI", kind="competency")) == "0"
    assert infer_tier(Source(title="Hipertensi", authority="PERHI", kind="guideline")) == "2"
    assert infer_tier(Source(title="Dengue", authority="WHO", kind="guideline")) == "3"
    assert infer_tier(Source(title="UTI under 16", authority="NICE", kind="guideline")) == "3"
    assert infer_tier(Source(title="Fornas", authority="Kemenkes", kind="formulary")) == "formulary"
    # Explicit tier always wins over inference.
    assert infer_tier(Source(title="X", authority="WHO", kind="guideline", tier="1")) == "1"


# ── Reviewed families: national primary present, hierarchy holds ─────────────
def test_dengue_pack_national_primary(registry):
    fam, vars_ = _fam_vars(registry, "fam_dengue")
    pack = build_evidence_pack(fam, vars_)
    assert "Kemenkes" in (pack.primary_guideline.get("authority") or "")
    assert any("WHO" in (d.get("authority") or "") for d in pack.international_refs)
    assert pack.formulary_context == []
    # Severity spans categories — the pack must carry BOTH, never collapse.
    assert sorted(pack.competency_categories) == ["initial_management_and_referral", "tuntas"]
    errs = [i for i in lint_evidence_family(fam, vars_, for_publishable=True)
            if i.severity == "error"]
    assert errs == [], [str(e) for e in errs]


def test_uti_pack_national_primary(registry):
    fam, vars_ = _fam_vars(registry, "fam_uti")
    pack = build_evidence_pack(fam, vars_)
    assert "Kemenkes" in (pack.primary_guideline.get("authority") or "")
    assert pack.competency_categories == ["tuntas"]
    errs = [i for i in lint_evidence_family(fam, vars_, for_publishable=True)
            if i.severity == "error"]
    assert errs == [], [str(e) for e in errs]


# ── Draft families: gaps are reported, not hidden ────────────────────────────
def test_draft_families_report_gaps_not_hide(registry):
    for fid in ("fam_hypertension", "fam_pyelonephritis"):
        fam, vars_ = _fam_vars(registry, fid)
        assert vars_ == []  # no linked variants yet (draft)
        issues = lint_evidence_family(fam, vars_, for_publishable=True)
        msgs = [i.message for i in issues if i.severity == "error"]
        assert any("competency_category" in m for m in msgs)
        assert any("primary national" in m for m in msgs)


# ── Hierarchy rules on synthetic packs ───────────────────────────────────────
def _pack(**kw):
    fam = CaseFamily(id="fam_x")
    base = dict(pack_version="1.0", family_id="fam_x", variant_ids=["v1"],
                competency_standard="SKD 2026", competency_reference="ref",
                competency_categories=["tuntas"], competency_system="s",
                review_status="draft",
                source_review_date="2026-09-01", clinical_content_version="v3.0")
    base.update(kw)
    from pipeline.case_v3.evidence import EvidencePack
    return EvidencePack(**base)


def test_intl_only_management_needs_human_interim_flag():
    pack = _pack(primary_guideline={},
                 international_refs=[{"title": "WHO X", "authority": "WHO"}])
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("international-only" in m for m in errs)
    # With an explicit human rationale the interim state is representable.
    pack.intl_primary_interim = True
    pack.intl_primary_rationale = "No PNPK exists yet; reviewer Dr. A confirmed WHO interim basis."
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("lacks a primary national" in m for m in errs)  # still no primary — honest


def test_formulary_never_management():
    pack = _pack(primary_guideline={"title": "PNPK X", "authority": "Kemenkes",
                                    "publication_date": "2022-01-01", "url": "https://x"},
                 formulary_context=[{"title": "Fornas", "kind": "management"}])
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("formulary" in m for m in errs)


def test_superseded_primary_expires_truth():
    pack = _pack(primary_guideline={"title": "Old PNPK", "authority": "Kemenkes",
                                    "review_status": "superseded",
                                    "publication_date": "2015-01-01", "url": "https://x"})
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("superseded" in m for m in errs)


def test_legacy_crosswalk_unconfirmed_is_error():
    pack = _pack(primary_guideline={"title": "PNPK X", "authority": "Kemenkes",
                                    "publication_date": "2022-01-01", "url": "https://x"},
                 legacy_level="3A", legacy_mapping_confirmed=False)
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("never auto-infer" in m for m in errs)


def test_bad_category_term_rejected():
    pack = _pack(primary_guideline={"title": "PNPK X", "authority": "Kemenkes",
                                    "publication_date": "2022-01-01", "url": "https://x"},
                 competency_categories=["level_4"])
    errs = [i.message for i in validate_evidence_pack(pack) if i.severity == "error"]
    assert any("not an official SKD 2026 term" in m for m in errs)


def test_variant_without_medications_stays_valid():
    v = ClinicalVariant(id="v", family_id="fam_x",
                        competency=Competency(category="tuntas"))
    assert v.medications == []
    assert v.to_dict()["medications"] == []
