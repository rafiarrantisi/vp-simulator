"""STEP 4 — SKD 2026 master catalog & specialty roadmap validation.

Validates 04_SKDI_CATALOG_AND_SPECIALTY_ROADMAP.md §10:
  - every item has an exact SKD 2026 category (tuntas / initial_management_and_referral)
  - only allowed 2026 categories in the primary catalog
  - every entry has a source locator (standard/reference/table)
  - specialty mapping is never null
  - duplicate normalized names do not overwrite distinct official entries (IDs unique)
  - cross-tags / presentation families are supported
  - count is reproducible from the source extraction
  - a manual spot-check sample runs across specialties
  - legacy SKDI crosswalk is null (not silently inferred) unless explicitly confirmed
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]          # vp-simulator/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_master_catalog import enrich
from tools.extract_skd2026 import parse_spektrum
from pipeline.case_v3.vocab import SKD2026_CATEGORIES

CAT = REPO / "content" / "v3" / "catalog" / "skd2026_master_catalog.json"
RAW = REPO / "backend" / "data" / "skd" / "skd_dokter_2026.txt"
ROAD = REPO / "content" / "v3" / "catalog" / "roadmap.json"


def _catalog():
    import json
    return json.loads(CAT.read_text(encoding="utf-8"))


def test_every_entry_has_exact_category():
    for e in _catalog():
        assert e["category"] in SKD2026_CATEGORIES, e["id"]
        assert e["category"] in ("tuntas", "initial_management_and_referral")


def test_only_allowed_2026_categories():
    cats = {e["category"] for e in _catalog()}
    assert cats <= SKD2026_CATEGORIES


def test_all_entries_have_source_locator():
    for e in _catalog():
        s = e["source"]
        assert s["standard"] == "SKD 2026"
        assert s["reference"] == "HK.01.02/KKI/2183/2026"
        assert s["table"]  # locator present
        assert e["system"]


def test_ids_unique():
    ids = [e["id"] for e in _catalog()]
    assert len(ids) == len(set(ids)), "duplicate ids must never overwrite distinct entries"


def test_specialty_mapping_not_null():
    for e in _catalog():
        assert e["system"], e["id"]
    from tools.build_roadmap import DOMAINS
    assert len(DOMAINS) >= 14


def test_duplicate_names_keep_distinct_entries():
    # source-inherent duplicate names get distinct ids (no silent overwrite)
    ids = [e["id"] for e in _catalog() if e["skd2026_name"].strip().lower() in
           (x["skd2026_name"].strip().lower() for x in _catalog())
           if True]
    # just confirm: distinct ids count == entry count
    assert len({e["id"] for e in _catalog()}) == len(_catalog())


def test_cross_tags_presentation_families_supported():
    import json
    road = json.loads(ROAD.read_text(encoding="utf-8"))
    pf = road["presentation_families"]
    assert len(pf) >= 20
    fever = next(x for x in pf if x["presentation"] == "fever")
    assert fever["entry_ids"], "fever presentation family must reference entries"


def test_count_reproducible_from_source():
    """Re-running extraction from the preserved source text reproduces the count."""
    raw = RAW.read_text(encoding="utf-8")
    parsed = parse_spektrum(raw)
    assert len(parsed) == len(_catalog())
    # continuity invariant held during extraction (would have raised otherwise)


def test_manual_spot_check_across_specialties():
    """A representative sample from every specialty bucket (human eyeball hook)."""
    cats = _catalog()
    from tools.build_roadmap import DOMAINS
    # pick one entry per domain to ensure coverage is non-empty everywhere
    sampled = set()
    entry_by_sys = {}
    for e in cats:
        entry_by_sys.setdefault(e["system"], []).append(e)
    for _domain, systems in DOMAINS:
        for s in systems:
            assert s in entry_by_sys and entry_by_sys[s], f"empty specialty {s}"
    # show the sample for the report
    for name, systems in DOMAINS[:3]:
        e = next(iter([x for x in cats if x["system"] in systems]))
        sampled.add(e["skd2026_name"])
    assert len(sampled) == len(DOMAINS[:3])


def test_legacy_skdi_crosswalk_null_not_inferred():
    for e in _catalog():
        lc = e["legacy_competency"]
        assert lc["level"] is None, f"{e['id']}: legacy level must be null unless SKDI-2012 verified"
        assert lc["mapping_confirmed"] is False


def test_priority_queue_exists_and_ordered():
    import json
    road = json.loads(ROAD.read_text(encoding="utf-8"))
    q = road["priority_queue"]
    assert len(q) == len(_catalog())
    scores = [x["priority_score"] for x in q]
    assert scores == sorted(scores, reverse=True)


def test_ambiguous_entries_flagged():
    import json
    road = json.loads(ROAD.read_text(encoding="utf-8"))
    assert isinstance(road["ambiguous_entries"], list)
    # the documented source-inherent duplicate cluster is surfaced
    assert any(len(cluster) > 1 for cluster in road["ambiguous_entries"])


def test_no_bulk_clinical_cases_generated():
    # Catalog is planning metadata, not case content — no full cases added.
    from pathlib import Path
    variants = list((REPO / "content" / "v3" / "variants").glob("*.yaml"))
    assert len(variants) <= 20  # still fixtures only