"""Phase PNPK-3 — pilot content tests (brief Phase 3 gate, clinician DONE).

Approval: dr. Budi Andana, Sp.PD (Dosen FK UI), 2026-09-09, record
APR-BA-20260909 — all 13 claims + 7 mappings + 1 template, high-risk
covered by the same reviewer (documented single-reviewer deviation).
The approved content must:
- PASS strict compile with zero gaps (publishable);
- still REJECT a tampered copy with approvals stripped (safety property);
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


def test_strict_approves_with_record(ctx):
    pack, kw = ctx
    pack2, bindings = compile_pack(pack, **kw)  # strict, no allow_draft
    assert getattr(pack2, "_draft_gaps", []) == []
    assert (pack.get("review_record") or {}).get("record") == "APR-BA-20260909"


def test_strict_still_rejects_when_claim_unapproved(ctx, tmp_path):
    import copy
    import shutil
    pack, kw = ctx
    # Tamper simulation: one claim loses its approval in an isolated copy.
    tclaims = tmp_path / "claims"
    shutil.copytree(kw["claims_dir"], tclaims)
    f = next(tclaims.glob("*.json"))
    items = json.loads(f.read_text())
    items[0].pop("review_status", None)
    items[0].pop("approval_record_id", None)
    f.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    tkw = dict(kw, claims_dir=tclaims)
    with pytest.raises(CompileError):
        compile_pack(copy.deepcopy(pack), **tkw)


def test_approved_content_structurally_clean(ctx):
    pack, kw = ctx
    pack2, bindings = compile_pack(pack, allow_draft=True, **kw)
    gaps = getattr(pack2, "_draft_gaps", [])
    assert gaps == [], f"approved content must have zero gaps: {gaps}"
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
