"""FASE 4 — expansion roadmap integrity + family-first catalogue guard.

The roadmap is deterministic output over verified artifacts; this suite pins
its integrity so future re-plans cannot silently duplicate, drop, or promote
content. Counts are asserted as SEPARATE stages (generated vs reviewed vs
published) — never a single "ready" number.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content" / "v3"


def _roadmap():
    return json.loads((CONTENT / "roadmap_expansion.json").read_text(encoding="utf-8"))


def _catalog_ids():
    catalog = json.loads((CONTENT / "catalog" / "skd2026_master_catalog.json").read_text(encoding="utf-8"))
    entries = catalog if isinstance(catalog, list) else catalog.get("entries", [])
    return {e["id"] for e in entries}


def _existing_ids():
    from pipeline.case_v3.loader import CaseRegistry
    reg = CaseRegistry.from_dir()
    return set(reg.families) | set(reg.variants)


def _canonical_ids():
    canon = json.loads((CONTENT / "catalog" / "canonical_entities.json").read_text(encoding="utf-8"))
    return {e["id"] for e in canon["canonical_entities"]}


def test_roadmap_partitions_canonical_without_overlap():
    o = _roadmap()
    tiers = o["tiers"]
    seen = set()
    for name, ids in tiers.items():
        assert not (set(ids) & seen), f"tier {name} overlaps another tier"
        seen |= set(ids)
    canon_ids = _canonical_ids()
    assert seen <= canon_ids  # every tiered id resolves
    covered = {i for hits in o["covered_by_existing_bank"].values() for i in hits}
    assert covered <= canon_ids
    assert not (seen & covered)  # covered bank entries are not re-planned
    assert o["tier_counts"] == {k: len(v) for k, v in tiers.items()}
    assert sum(o["tier_counts"].values()) + len(covered) == len(canon_ids)


def test_batch_a_breadth_rules():
    o = _roadmap()
    a = o["batches"]["A_breadth"]
    assert len(a) == 12
    assert len(set(a)) == 12
    assert len(o["batches"]["A_systems"]) >= 8
    catalog_ids = _catalog_ids()
    assert set(a) <= catalog_ids  # every id resolves
    assert not (set(a) & _existing_ids())  # no collision with live bank
    # Batch A draws only from high_risk + core tiers.
    allowed = set(o["tiers"]["high_risk"]) | set(o["tiers"]["core"])
    assert set(a) <= allowed
    # Forensic artifacts are excluded by rule.
    assert not any(i.startswith("forensik_") for i in a)


def test_batch_a_manifest_capped_and_source_gated():
    man = json.loads(Path(__file__).resolve().parents[1].joinpath(
        "data", "reports", "fase4_batchA_manifest.json").read_text(encoding="utf-8"))
    assert len(man["batch"]) == 12
    for b in man["batch"]:
        assert b["status"] == "research_complete"
        assert b["needs_source_pack"] is True
        assert b.get("ready_for_qa_gate") is False


def test_batches_disjoint_and_b_is_briefs_only():
    o = _roadmap()
    a = set(o["batches"]["A_breadth"])
    b_fams = set(o["batches"]["B_depth_briefs"])
    assert not (a & b_fams)
    assert b_fams == {"fam_dengue", "fam_uti", "fam_hypertension",
                      "fam_pyelonephritis", "fam_fever_child"}


def test_zero_variant_families_never_advertised():
    # FASE 4 catalogue guard: a family `start` cannot serve must not surface
    # as a card (the fever_child count-0/404 class of mismatch).
    from app.domains.sessions.v3_compat_service import library_cards
    from app.domains.sessions.v3_compat_schemas import (
        default_registry, family_variant_count)
    reg = default_registry()
    cards = library_cards()
    ids = {c["id"] for c in cards}
    for fid, fam in reg.families.items():
        if fam.status == "draft":
            assert fid not in ids
        elif family_variant_count(reg, fam, "koas") <= 0:
            assert fid not in ids
    for c in cards:
        assert c["eligible_variant_count"] >= 1
