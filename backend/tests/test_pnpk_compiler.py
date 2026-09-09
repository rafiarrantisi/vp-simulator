"""Phase PNPK-2 — compiler tests (brief §12 rejection rules + determinism).

Synthetic fixtures only (no clinical content, no PDFs, no network). Each
rejection rule has a failing case; the happy path proves deterministic
byte-identical output and approval gating.
"""
from __future__ import annotations

import copy
import json

import pytest

from pipeline.case_v3.loader import CaseRegistry
from pipeline.evidence.compiler import (
    CompileError,
    compile_pack,
    emit_pack,
    reverse_index,
)


@pytest.fixture(scope="module")
def registry():
    return CaseRegistry.from_dir()


@pytest.fixture()
def authoring(tmp_path):
    claims_d = tmp_path / "claims"
    mappings_d = tmp_path / "mappings"
    templates_d = tmp_path / "templates"
    for d in (claims_d, mappings_d, templates_d):
        d.mkdir()
    span = {
        "source_version_id": "PNPK-UTI-2025@sha256:" + "a" * 64,
        "section_path": ["Tata Laksana", "Sistitis"],
        "heading": "Terapi",
        "pdf_page_start": 34,
        "pdf_page_end": 34,
        "printed_page_label": "34",
        "locator": "Tabel 2",
        "excerpt_hash": "e" * 16,
    }
    claim = {
        "claim_id": "UTI-TX-001",
        "claim_revision": 1,
        "statement": "Sistitis akut tanpa komplikasi diterapi antibiotik lini pertama.",
        "category": "management",
        "support_kind": "direct_guideline",
        "applicability": {"pregnancy": "any"},
        "evidence_spans": [span],
        "review_status": "approved",
        "reviewer": "dr. Test",
        "reviewed_at": "2026-09-01",
        "approval_record_id": "APR-1",
    }
    (claims_d / "c1.json").write_text(json.dumps(claim))
    template = {
        "template_id": "T-MISS-001",
        "template_revision": 1,
        "statuses": ["miss", "partial"],
        "text": "Item {label} belum mendapat kredit penuh pada penilaian ini. {reason}.[{ref}]",
        "placeholders": ["label", "reason", "ref"],
        "review_status": "approved",
        "approval_record_id": "APR-1",
    }
    (templates_d / "t1.json").write_text(json.dumps(template))
    mapping = {
        "mapping_id": "M-UTI-001",
        "canonical_target_id": "PLACEHOLDER_TARGET",
        "target_kind": "per_item",
        "claim_ids": ["UTI-TX-001"],
        "trigger_statuses": ["miss"],
        "template_id": "T-MISS-001",
        "display_priority": 1,
        "applicable_variant_ids": ["uti_adult_002"],
        "review_status": "approved",
        "approval_record_id": "APR-1",
    }
    (mappings_d / "m1.json").write_text(json.dumps(mapping))
    pack = {
        "pack_id": "PNPK-UTI-PILOT",
        "pack_revision": 1,
        "clinical_content_version": "v3.0",
        "compatible_scoring_versions": ["qora-score-1.0"],
        "content_release_id": "rel-test-1",
        "families": ["fam_uti"],
        "allowed_conditions": ["uti"],
        "supported_modes": ["practice"],
        "supported_stages": ["koas"],
        "review_record": {"record": "APR-PACK-1"},
    }
    catalog = {"editions": [{
        "edition_id": "PNPK-UTI-2025",
        "clinical_review_status": "unreviewed",
    }]}
    manifest = {"documents": {"uti": {"artifacts": [{
        "artifact_id": "PNPK-UTI-2025@sha256:" + "a" * 64,
        "sha256": "a" * 64,
    }]}}}
    return {
        "claims_d": claims_d, "mappings_d": mappings_d,
        "templates_d": templates_d, "pack": pack, "catalog": catalog,
        "manifest": manifest,
    }


def _compile_ok(authoring, registry, tmp_path, target="inv_1"):
    import json as _json

    mpath = authoring["mappings_d"] / "m1.json"
    m = _json.loads(mpath.read_text())
    if m.get("canonical_target_id") in (None, "", "PLACEHOLDER_TARGET"):
        m["canonical_target_id"] = target
        mpath.write_text(_json.dumps(m))
    claim_path = authoring["claims_d"] / "c1.json"
    c = _json.loads(claim_path.read_text())
    c["applicability"]["condition_codes"] = ["uti"]
    claim_path.write_text(_json.dumps(c))
    return compile_pack(
        authoring["pack"], claims_dir=authoring["claims_d"],
        mappings_dir=authoring["mappings_d"],
        templates_dir=authoring["templates_d"],
        catalog=authoring["catalog"], manifest=authoring["manifest"],
        registry=registry, pdf_root=None)


def test_happy_path_deterministic(authoring, registry, tmp_path):
    pack, bindings = _compile_ok(authoring, registry, tmp_path)
    assert pack.pack_sha256 and len(pack.pack_sha256) == 64
    assert bindings and all(b.variant_id for b in bindings)
    p1, i1 = emit_pack(pack, bindings, tmp_path / "out")
    pack2, bindings2 = _compile_ok(authoring, registry, tmp_path)
    p2, i2 = emit_pack(pack2, bindings2, tmp_path / "out2")
    assert p1.read_bytes() == p2.read_bytes()
    assert pack2.pack_sha256 == pack.pack_sha256
    assert i1.read_bytes() != b""
    rev = reverse_index(pack, bindings)
    assert "uti_adult_002" in rev["variants"]


def _break(authoring, kind):
    import json as _json

    if kind == "unapproved_claim":
        p = authoring["claims_d"] / "c1.json"
        d = _json.loads(p.read_text())
        d["review_status"] = "draft"
        p.write_text(_json.dumps(d))
    elif kind == "unknown_claim":
        p = authoring["mappings_d"] / "m1.json"
        d = _json.loads(p.read_text())
        d["claim_ids"] = ["NOPE"]
        p.write_text(_json.dumps(d))
    elif kind == "bad_target":
        p = authoring["mappings_d"] / "m1.json"
        d = _json.loads(p.read_text())
        d["canonical_target_id"] = "no_such_item"
        p.write_text(_json.dumps(d))
    elif kind == "family_autoapprove":
        p = authoring["mappings_d"] / "m1.json"
        d = _json.loads(p.read_text())
        d["applicable_variant_ids"] = []
        p.write_text(_json.dumps(d))
    elif kind == "bad_placeholder":
        p = authoring["templates_d"] / "t1.json"
        d = _json.loads(p.read_text())
        d["placeholders"] = ["label"]
        p.write_text(_json.dumps(d))
    elif kind == "nonpnpk_source":
        p = authoring["claims_d"] / "c1.json"
        d = _json.loads(p.read_text())
        d["evidence_spans"][0]["source_version_id"] = "WHO-XYZ@sha256:" + "b" * 64
        p.write_text(_json.dumps(d))
    elif kind == "pregnancy_mismatch":
        p = authoring["claims_d"] / "c1.json"
        d = _json.loads(p.read_text())
        d["applicability"] = {"pregnancy": "yes", "condition_codes": ["uti"]}
        p.write_text(_json.dumps(d))


@pytest.mark.parametrize("kind", [
    "unapproved_claim", "unknown_claim", "bad_target", "family_autoapprove",
    "bad_placeholder", "nonpnpk_source", "pregnancy_mismatch",
])
def test_rejection_rules(authoring, registry, tmp_path, kind):
    _break(authoring, kind)
    with pytest.raises(CompileError):
        _compile_ok(authoring, registry, tmp_path)


def test_source_hold_rejected(authoring, registry, tmp_path):
    authoring["catalog"] = {"editions": [{
        "edition_id": "PNPK-UTI-2025",
        "clinical_review_status": "source_hold",
    }]}
    with pytest.raises(CompileError, match="source_hold"):
        _compile_ok(authoring, registry, tmp_path)


def test_patient_payload_key_rejected(authoring, registry, tmp_path):
    authoring["pack"]["answer_key"] = {"x": 1}
    with pytest.raises(CompileError, match="banned payload key"):
        _compile_ok(authoring, registry, tmp_path)


def test_rubric_mismatch_rejected(authoring, registry, tmp_path):
    import json as _json

    _compile_ok(authoring, registry, tmp_path)  # fills rubric_hash in-memory
    p = authoring["mappings_d"] / "m1.json"
    d = _json.loads(p.read_text())
    d["rubric_hash"] = "0" * 64  # wrong pin must be rejected
    p.write_text(_json.dumps(d))
    with pytest.raises(CompileError, match="rubric_hash mismatch"):
        _compile_ok(authoring, registry, tmp_path, target=d["canonical_target_id"])
