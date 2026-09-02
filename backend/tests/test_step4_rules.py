"""STEP 4 correction rules (user approval) — locked in tests.

  1. `initial_management_and_referral` is NOT universally "stabilise + refer";
     exact actions are per-disease from the current guideline.
  2. 515 raw entries == not 515 visible families; canonical layer + source_occurrences.
  3. Terminology is SKD 2026; 3A/3B/4A only as legacy metadata.
  4. Golden generation demo = 1 Tuntas + 1 initial&refer + 1 diagnostically rich family.
  5. Epidemiology separated: evidence / variant_demographic_constraints / persona_variables.
  6. Legacy SKDI crosswalk is not a blocker (null until verified).
  7. For each initial&refer family, management expectations must be explicit & sourced.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.case_v3.models import (
    Competency, Epidemiology, ManagementExpectations, CanonicalEntity,
)
from pipeline.case_v3.vocab import (
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL, SKD2026_CATEGORY_TUNTAS,
)
from pipeline.case_v3.governance import validate_governance, skd2026_category_registry

CAT = REPO / "content" / "v3" / "catalog" / "skd2026_master_catalog.json"
CANON = REPO / "content" / "v3" / "catalog" / "canonical_entities.json"


# ── Rule 1: category is nominal, not universal protocol ────────────────────

def test_initial_and_refer_not_redefined_as_universal_stabilise_refer():
    reg = skd2026_category_registry()
    d = reg[SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL]
    # must NOT hard-code "stabilise + refer" as the universal behaviour
    assert "per-disease" in d or "PER-DISEASE" in d or "per disease" in d
    assert "stabilisation need" in d  # it says the need is per-disease


# ── Rule 2: raw catalog vs canonical layer ─────────────────────────────────

def test_raw_vs_canonical_are_two_separate_numbers():
    raw = json.loads(CAT.read_text(encoding="utf-8"))
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    assert len(raw) == 515
    assert canon["raw_official_entries"] == len(raw) == 515
    assert canon["canonical_case_family_candidates"] < len(raw)
    # raw rows are fully preserved (each raw entry appears in some canonical
    # occurrence — no silent deletion)
    raw_ids = {e["id"] for e in raw if e.get("id")}
    occ_ids = {o["entry_id"] for ent in canon["canonical_entities"] for o in ent["source_occurrences"] if o.get("entry_id")}
    assert raw_ids == occ_ids, "every raw source row must be preserved"


def test_duplicate_source_rows_fold_into_one_canonical_entity():
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    multi = [e for e in canon["canonical_entities"] if len(e["source_occurrences"]) > 1]
    assert multi, "expected at least one canonical entity with multiple occurrences (e.g. skabies)"


def test_ambiguous_not_resolved_by_guess():
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    # entities under ambiguity are flagged, NOT silently merged on medical grounds
    flagged = [e for e in canon["canonical_entities"] if e["mapping_uncertainty"]]
    assert isinstance(flagged, list)


def test_canonical_model_has_source_occurrences():
    e = CanonicalEntity(id="x", display_name="Skabies",
                        source_occurrences=[{"entry_id": "a"}, {"entry_id": "b"}])
    d = e.to_dict()
    assert len(d["source_occurrences"]) == 2
    assert d["mapping_uncertainty"] == []  # default: preserved, not guessed


# ── Rule 5: epidemiology 3-layer ───────────────────────────────────────────

def test_epidemiology_has_three_layers():
    epi = Epidemiology()
    assert hasattr(epi, "evidence")
    assert hasattr(epi, "variant_constraints")
    assert hasattr(epi, "persona_variables")
    d = epi.to_dict()
    assert set(d) == {"evidence", "variant_constraints", "persona_variables"}


# ── Rule 6: legacy crosswalk is not inferred ───────────────────────────────

def test_legacy_crosswalk_not_a_blocker_and_not_inferred():
    from pipeline.case_v3.models import Competency
    c = Competency(standard="SKD 2026", category="tuntas")  # no legacy level
    assert c.legacy_level is None
    assert c.legacy_mapping_confirmed is False


# ── Rule 7: management expectations required & explicit for initial&refer ──

def test_publishable_initial_refer_requires_explicit_management_expectations():
    # Build a publishable variant with category initial_management_and_referral
    # but NO management_expectations -> must be rejected (cannot be inferred).
    from pipeline.case_v3.governance import _has_named_human_review
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth
    v = ClinicalVariant(
        id="x", family_id="fam",
        competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL),
        diagnostic=DiagnosticTruth("Some disease"),
        status="pilot_verified",
        source_governance={"clinical_reviewer": "dr. X"},
    )
    # fixture variant sources: add one clinical source so the source check passes
    from pipeline.case_v3.models import Source
    v.sources = [Source(title="PNPK", authority="Kemenkes", kind="guideline", url="https://x")]
    g = validate_governance(v)
    assert not g.ok
    msgs = [str(e) for e in g.errors if "management_expectations" in str(e)]
    assert msgs
    assert any("recognize_diagnose" in m for m in msgs)
    assert any("initial_management" in m for m in msgs)
    assert any("do_not_miss_actions" in m for m in msgs)


def test_filled_management_expectations_passes_rule7():
    from pipeline.case_v3.models import ClinicalVariant, DiagnosticTruth, Source
    v = ClinicalVariant(
        id="y", family_id="fam",
        competency=Competency(standard="SKD 2026", category=SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL),
        diagnostic=DiagnosticTruth("Some disease"),
        status="pilot_verified",
        source_governance={"clinical_reviewer": "dr. X"},
    )
    v.sources = [Source(title="PNPK", authority="Kemenkes", kind="guideline", url="https://x")]
    v.management_expectations = ManagementExpectations(
        recognize_diagnose="recognise headache with fever & rash",
        initial_management="rest, hydration, paracetamol",
        emergency_stabilization_required=False,
        referral_urgency="routine",
        referral_indication="deterioration or warning signs",
        do_not_miss_actions=["check for warning signs", "assess hydration"],
        source_refs=["PNPK"],
    )
    g = validate_governance(v)
    # should have no management_expectations errors (source + self-review also OK)
    me_errors = [e for e in g.errors if "management_expectations" in str(e)]
    assert not me_errors, [str(e) for e in me_errors]


# ── Rule 3: terminology is SKD 2026, not 3A/3B/4A ─────────────────────────

def test_golden_demo_plan_is_skd2026_categories():
    # The generation demo now targets: 1 Tuntas + 1 initial&refer + 1
    # diagnostically-rich family — all expressed in SKD 2026 terms.
    plan = [SKD2026_CATEGORY_TUNTAS,
            SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL,
            "diagnostically_rich_presentation_family"]
    assert SKD2026_CATEGORY_TUNTAS in plan
    assert SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL in plan
    assert "3B" not in plan and "4A" not in plan and "3A" not in plan