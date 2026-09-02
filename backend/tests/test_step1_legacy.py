"""STEP 1 — Legacy case inventory, quarantine & migration foundation.

Validates the acceptance criteria of 01_LEGACY_CASE_INVENTORY_AND_MIGRATION.md:
  - loader compatibility: existing valid legacy case still loads; new (legacy-
    flagged) schema is recognised separately; invalid schema gives a clear error
  - status isolation: legacy/unverified never appears in a verified-only query;
    pilot scope returns only pilot-candidate (and legacy is excluded)
  - ID safety: duplicate IDs are detected; no silent overwrite
  - inventory: counts match discovered files; malformed files are reported
  - non-destructive: inventory never deletes/overwrites any case file
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/
from pipeline.case_v2 import (
    CURRENT_SCHEMA_VERSION,
    VERIFIED_STATUSES,
    CaseV2,
    lint,
    parse_case_v2,
    parse_string,
)
from app.domains.cases import v2_catalog


def _mk(id="test_case", status="ai_generated", schema_version=2, **extra):
    fm = {
        "id": str(id),
        "schema_version": schema_version,
        "status": status,
        "specialty": "internal_medicine",
        "system": "renal",
        "presentation": "test",
        "target_condition": "Test disease",
        "difficulty": 2,
        "mode_default": "anamnesis",
        "chief_complaint": "test",
        "source_refs": ["PNPK Kemenkes: X (KMK 1/2000) — https://jdih.kemkes.go.id"],
        "anamnesis_checklist": {"ice_fife": [{"item": "Ideas", "critical": True}]},
        "red_flags": [{"item": "Fever", "critical": True}],
        "expected_ddx": {"working_diagnosis": "Test disease", "differentials": ["A", "B"]},
    }
    fm.update(extra)
    body = """## Identity

I'm a test patient.

## Opening line

Doctor, I feel unwell.

## How I present

I sit here calmly.

## What I know

I have a fever and ideas about it.

## Communication profile

Simple and direct.

## Disclosure rules

I answer only what is asked.
"""
    return parse_string("---\n" + yaml.safe_dump(fm, sort_keys=False) + "\n---\n" + body)


# ── 1. Loader compatibility ─────────────────────────────────────────────────

def test_existing_valid_legacy_case_still_loads():
    # A schema-v2 prototype case (the entire current bank) must keep loading.
    c = _mk(status="ai_generated")
    assert c.frontmatter_ok is True
    assert lint(c).ok
    assert c.schema_origin() == "v2-legacy"


def test_verified_case_is_recognised_as_non_legacy():
    c = _mk(status="published")
    assert not c.is_legacy()
    assert c.schema_origin() == "v2-legacy"


def test_new_schema_recognised_separately():
    c = _mk(schema_version=CURRENT_SCHEMA_VERSION)
    assert c.schema_origin() == "v3"


def test_invalid_schema_version_clear_error():
    c = _mk(schema_version="bogus")
    res = lint(c)
    assert not res.ok
    assert any("schema_version" in e for e in res.errors)


# ── 2. is_legacy isolation ──────────────────────────────────────────────────

def test_unverified_is_legacy():
    assert _mk(status="ai_generated").is_legacy()
    assert _mk(status="in_review").is_legacy()
    assert _mk(status="draft").is_legacy()
    assert _mk(status="needs_update").is_legacy()


def test_verified_with_signer_is_not_legacy():
    c = _mk(status="clinically_reviewed", authoring={"reviewed_by": "dr. X", "reviewed_at": "2026-09-01"})
    assert c.review_state in VERIFIED_STATUSES
    assert not c.is_legacy()


def test_published_is_never_legacy_even_unsigned():
    assert not _mk(status="published").is_legacy()


def test_explicit_legacy_opt_out_overrides():
    c = _mk(status="ai_generated", legacy=False)
    assert not c.is_legacy()
    c2 = _mk(status="published", legacy=True)
    assert c2.is_legacy()


# ── 3. Status isolation via catalog (verified-only excludes legacy) ─────────

def test_catalog_verified_scope_excludes_legacy(tmp_path, monkeypatch):
    # A legacy (ai_generated) and a verified (published) case in a temp dir.
    (tmp_path / "legacy_001.md").write_text(
        "---\n" + yaml.safe_dump(_mk("legacy_001", status="ai_generated").frontmatter, sort_keys=False) + "\n---\n" + "## Identity\n\nX\n\n## Opening line\n\nHi\n\n## Communication profile\n\na\n\n## Disclosure rules\n\nb")
    (tmp_path / "pub_002.md").write_text(
        "---\n" + yaml.safe_dump(_mk("pub_002", status="published", authoring={"drafted_by": "ai_v1", "reviewed_by": "dr. X", "reviewed_at": "2026-09-01"}).frontmatter, sort_keys=False) + "\n---\n" + "## Identity\n\nX\n\n## Opening line\n\nHi\n\n## Communication profile\n\na\n\n## Disclosure rules\n\nb")
    monkeypatch.setattr(v2_catalog, "_dir", lambda: tmp_path)
    v2_catalog._catalog_cached.cache_clear()
    try:
        all_cases = v2_catalog.list_v2_cases()
        assert {c.id for c in all_cases} == {"legacy_001", "pub_002"}
        non_legacy = v2_catalog.list_v2_cases(exclude_legacy=True)
        ids = {c.id for c in non_legacy}
        assert "pub_002" in ids
        assert "legacy_001" not in ids  # legacy never surfaces in verified-only
    finally:
        v2_catalog._catalog_cached.cache_clear()


def test_legacy_files_still_load_in_default_path(tmp_path, monkeypatch):
    # The existing live flow (no exclude_legacy) must still see legacy cases.
    (tmp_path / "l.md").write_text(
        "---\n" + yaml.safe_dump(_mk("l1", status="ai_generated").frontmatter, sort_keys=False) + "\n---\n" + "## Identity\n\nX\n\n## Opening line\n\nHi\n\n## Communication profile\n\na\n\n## Disclosure rules\n\nb")
    monkeypatch.setattr(v2_catalog, "_dir", lambda: tmp_path)
    v2_catalog._catalog_cached.cache_clear()
    try:
        assert any(c.id == "l1" for c in v2_catalog.list_v2_cases())
    finally:
        v2_catalog._catalog_cached.cache_clear()


# ── 4. Versioning boundary ──────────────────────────────────────────────────

def test_versioning_fields_exposed():
    c = _mk(status="clinically_reviewed",
            clinical_content_version="v3.1", source_review_date="2026-09-01",
            superseded_by="", authoring={"reviewed_by": "dr. X"})
    assert c.clinical_content_version() == "v3.1"
    assert c.source_review_date() == "2026-09-01"
    assert c.superseded_by() == ""


def test_schema_origin_unknown_when_non_numeric():
    assert _mk(schema_version="x.y").schema_origin() == "unknown"


# ── 5. Inventory: counts + malformed + duplicate-ID detection ───────────────

def test_inventory_counts_and_non_destructive(tmp_path):
    # Write two valid + one malformed; ensure counts + malformed reported.
    for fn, status in [("a_001.md", "ai_generated"), ("b_002.md", "published")]:
        (tmp_path / fn).write_text(
            "---\n" + yaml.safe_dump(_mk(fn[:-3], status=status).frontmatter, sort_keys=False) + "\n---\n" + "## Identity\n\nX\n\n## Opening line\n\nHi\n\n## Communication profile\n\na\n\n## Disclosure rules\n\nb")
    (tmp_path / "malformed_003.md").write_text("this is not frontmatter")
    before = {p.name: p.read_bytes() for p in tmp_path.glob("*.md")}
    from tools import case_inventory as inv
    # point inventory at the temp dir
    entries = []
    flags = []
    inv._scan_v2(tmp_path, entries, flags)
    by_name = {e.filename: e for e in entries}
    assert set(by_name) == {"a_001.md", "b_002.md", "malformed_003.md"}
    assert by_name["malformed_003.md"].lint_ok is False
    assert by_name["a_001.md"].is_legacy is True
    assert by_name["b_002.md"].is_legacy is False
    after = {p.name: p.read_bytes() for p in tmp_path.glob("*.md")}
    assert before == after  # non-destructive: nothing written/deleted/overwritten


def test_duplicate_id_detected():
    from tools import case_inventory as inv
    e1 = inv.InventoryEntry("dup_001", "x.md", "v2", "im", "", "", "", None, "ai_generated", "v2-legacy", True, True, False, "", 1, True, [], [], [])
    e2 = inv.InventoryEntry("dup_001", "y.md", "v2", "im", "", "", "", None, "ai_generated", "v2-legacy", True, True, False, "", 1, True, [], [], [])
    dups = inv._find_duplicate_ids([e1, e2])
    assert len(dups) == 1
    assert dups[0]["id"] == "dup_001"
    assert len(dups[0]["files"]) == 2


def test_duplicated_truth_detector_reports_diagnosis_mismatch():
    from tools import case_inventory as inv
    c = parse_string("---\ntarget_condition: 'Disease A'\nexpected_ddx:\n  working_diagnosis: 'Disease B'\n  differentials: [x, y]\n---\n## Identity\n\nI\n\n## Opening line\n\nHi\n\n## Communication profile\n\nc\n\n## Disclosure rules\n\nd")
    flags = inv._duplicated_truth(c)
    assert any(f.kind == "diagnosis_mismatch" for f in flags)