"""Phase PNPK-3 — pilot draft content tests (brief Phase 3 gate, minus clinician).

Draft pack (UTI adult + dengue adult, real PDF locators) must:
- FAIL strict compile (unapproved — never publishable without review);
- PASS draft-check with ONLY approval gaps (zero structural issues);
- bind expected variants; exclude pregnancy claim from adult mapping;
- carry verifiable excerpt hashes (recomputed, not placeholders).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pipeline.case_v3.loader import CaseRegistry
from pipeline.evidence.compiler import CompileError, compile_pack

BASE = Path(__file__).resolve().parents[2] / "content" / "evidence"
ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1] / "tools"


@pytest.fixture(scope="module")
def ctx():
    pack = json.loads((BASE / "packs" / "pilot_draft_001.json").read_text())[0]
    reg = CaseRegistry.from_dir()
    catalog = json.load(open(TOOLS / "pnpk_sources.json"))
    manifest = json.load(open(ROOT / "clinical_sources" / "manifest.json"))
    kw = dict(claims_dir=BASE / "claims", mappings_dir=BASE / "mappings",
              templates_dir=BASE / "templates", catalog=catalog,
              manifest=manifest, registry=reg,
              pdf_root=ROOT / "clinical_sources")
    return pack, kw


def test_strict_rejects_unapproved(ctx):
    pack, kw = ctx
    with pytest.raises(CompileError):
        compile_pack(pack, **kw)


def test_draft_check_structurally_clean(ctx):
    pack, kw = ctx
    pack2, bindings = compile_pack(pack, allow_draft=True, **kw)
    gaps = getattr(pack2, "_draft_gaps", [])
    assert gaps, "expected approval gaps"
    assert all("not approved" in g or "without approval_record_id" in g
               for g in gaps)
    vids = sorted(b.variant_id for b in bindings)
    assert "uti_adult_002" in vids
    assert "dengue_001_mild" in vids
    # pregnancy claim must not be mapped onto the non-pregnant adult variant
    for m in pack2.mappings:
        if "uti_adult_002" in m.applicable_variant_ids:
            assert "UTI-PREG-001" not in m.claim_ids


def test_excerpt_hashes_recomputable():
    for name in ("claims",):
        for f in sorted((BASE / name).glob("*.json")):
            for c in json.loads(f.read_text()):
                for sp in c.get("evidence_spans") or []:
                    norm = " ".join((sp.get("excerpt") or "").split())
                    assert norm, f"empty excerpt {c.get('claim_id')}"
                    assert (hashlib.sha256(norm.encode()).hexdigest()
                            == sp.get("excerpt_hash")), c.get("claim_id")
