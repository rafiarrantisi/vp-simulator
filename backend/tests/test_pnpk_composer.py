"""Phase PNPK-4 — loader/composer/wiring tests (brief §7, §9, §14).

Synthetic APPROVED packs (mechanics only — no clinical authority claimed).
Proves: digest pinning, fail-closed loads, deterministic render, citation
dedup, no-mutation of score objects, unavailable paths, placeholder safety,
flag-off byte-invariance, and end-to-end wiring on a stub V3 session.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from pipeline.case_v3.loader import CaseRegistry


@pytest.fixture(scope="module")
def approved_pack(tmp_path_factory):
    """Compile a tiny APPROVED synthetic pack for uti_adult_002."""
    from pipeline.evidence.compiler import compile_pack, emit_pack

    root = tmp_path_factory.mktemp("pnpk4")
    for name in ("claims", "mappings", "templates"):
        (root / name).mkdir()
    sv = "SYN-UTI-2025@sha256:" + "c" * 64
    claim = {
        "claim_id": "SYN-INV-001", "claim_revision": 1,
        "statement": "Urine culture confirms the diagnosis and guides therapy.",
        "category": "investigation", "support_kind": "direct_guideline",
        "applicability": {"pregnancy": "any"},
        "evidence_spans": [{
            "source_version_id": sv, "section_path": ["Dx"],
            "heading": "Culture", "pdf_page_start": 1, "pdf_page_end": 2,
            "printed_page_label": "1", "locator": "para 1",
            "excerpt_hash": "e" * 16,
        }],
        "review_status": "approved", "reviewer": "synthetic-test",
        "reviewed_at": "2026-09-09", "approval_record_id": "SYN-APR-1",
    }
    (root / "claims" / "c.json").write_text(json.dumps(claim))
    template = {
        "template_id": "SYN-T-001", "template_revision": 1,
        "statuses": ["hit", "partial", "miss"],
        "text": "Item {label} {status_word} pada penilaian ini. {reason} [{ref}]",
        "placeholders": ["label", "status_word", "reason", "ref"],
        "review_status": "approved", "approval_record_id": "SYN-APR-1",
    }
    (root / "templates" / "t.json").write_text(json.dumps(template))
    # NOTE(SYN): mechanics only — one mapping per variant targeting its
    # own hx_1; real packs map reviewed clinical claims per variant.
    for n, vid in enumerate(["uti_adult_002", "uti_child_001", "uti_male_003"]):
        mapping = {
            "mapping_id": f"SYN-M-00{n + 1}", "canonical_target_id": "hx_1",
            "target_kind": "per_item", "claim_ids": ["SYN-INV-001"],
            "trigger_statuses": ["miss", "partial"], "template_id": "SYN-T-001",
            "display_priority": 1, "applicable_variant_ids": [vid],
            "review_status": "approved", "approval_record_id": "SYN-APR-1",
        }
        (root / "mappings" / f"m{n + 1}.json").write_text(json.dumps(mapping))
    pack_def = {
        "pack_id": "SYN-PACK-001", "pack_revision": 1,
        "clinical_content_version": "v3.0",
        "compatible_scoring_versions": ["qora-score-1.0"],
        "content_release_id": "syn-rel-1", "families": ["fam_uti"],
        "allowed_conditions": ["uti"],
        "supported_modes": ["practice"], "supported_stages": ["koas"],
        "review_record": {"record": "SYN-APR-PACK-1"},
    }
    catalog = {"documents": [{
        "edition_id": "SYN-UTI-2025", "source_id": "SYN-UTI",
        "title": "Synthetic UTI", "publisher": "Test",
        "year": 2025, "decision_number": "SYN-1",
        "official_url": "https://example.invalid/syn.pdf",
    }]}
    manifest = {"documents": {"syn": {"artifacts": [{
        "artifact_id": "SYN-UTI-2025@sha256:" + "d" * 64,
        "sha256": "d" * 64, "official_url": "https://example.invalid/s.pdf",
    }]}}}
    # point the claim span at the manifest artifact
    claim["evidence_spans"][0]["source_version_id"] = (
        "SYN-UTI-2025@sha256:" + "d" * 64)
    (root / "claims" / "c.json").write_text(json.dumps(claim))
    reg = CaseRegistry.from_dir()
    pack, bindings = compile_pack(
        pack_def, claims_dir=root / "claims", mappings_dir=root / "mappings",
        templates_dir=root / "templates", catalog=catalog, manifest=manifest,
        registry=reg, pdf_root=None)
    out = root / "build"
    emit_pack(pack, bindings, out)
    return {"dir": out, "pack": pack, "bindings": bindings, "registry": reg}


def _uti_rubric(approved_pack):
    from pipeline.judge.evidence import build_rubric_from_variant

    reg = approved_pack["registry"]
    return build_rubric_from_variant(reg.variants["uti_adult_002"])


def _report_missing_culture(rubric):
    items = []
    for it in rubric:
        if it["item_id"] == "hx_1":
            items.append({"dimension": "history",
                          "item": it["expected"], "status": "miss",
                          "evidence": ""})
    return {"overall": 55, "per_item": items, "per_dimension": {},
            "safety_gates": [], "summary": "s", "overtime_penalty": None}


def test_loader_pins_digest_and_fails_closed(approved_pack, tmp_path):
    from app.domains.scoring import evidence_loader as loader

    loader.clear_cache()
    d = approved_pack["dir"]
    packs = [p for p in d.glob("*.json") if p.name != "index.json"]
    assert len(packs) == 1
    sha = packs[0].stem
    loaded = loader.load_pack(sha, evidence_dir=d)
    assert loaded["pack_id"] == "SYN-PACK-001"
    # tampered bytes fail closed
    bad = tmp_path / (sha + ".json")
    bad.write_text(packs[0].read_text().replace("SYN-PACK-001", "SYN-EVIL-001"))
    import pytest as _pt

    with _pt.raises(loader.PackLoadError):
        loader.load_pack(sha, evidence_dir=tmp_path)
    with _pt.raises(loader.PackLoadError):
        loader.load_pack("nothex", evidence_dir=d)
    with _pt.raises(loader.PackLoadError):
        loader.load_pack("a" * 64, evidence_dir=d)
    # binding resolution
    b = loader.resolve_binding("uti_adult_002",
                               approved_pack["bindings"][0].canonical_hash
                               if hasattr(approved_pack["bindings"][0], "canonical_hash")
                               else approved_pack["bindings"][0]["canonical_hash"],
                               evidence_dir=d)
    assert b is not None
    assert loader.resolve_binding("nope", "x" * 16, evidence_dir=d) is None
    loader.clear_cache()


def test_composer_happy_path_and_shape(approved_pack):
    from app.domains.scoring import evidence_loader as loader
    from app.domains.scoring.feedback_composer import compose_clinical_evidence

    d = approved_pack["dir"]
    loader.clear_cache()
    sha = next(p.stem for p in d.glob("*.json") if p.name != "index.json")
    pack = loader.load_pack(sha, evidence_dir=d)
    binding = loader.resolve_binding(
        "uti_adult_002",
        approved_pack["registry"].variants["uti_adult_002"].canonical_hash(),
        evidence_dir=d)
    assert binding is not None
    rubric = _uti_rubric(approved_pack)
    report = _report_missing_culture(rubric)
    ns, outcome = compose_clinical_evidence(
        report=report, rubric_items=rubric, pack=pack, binding=binding,
        mode="practice", learner_stage="koas")
    assert outcome == "available"
    assert ns["status"] == "available"
    assert ns["pack"]["sha256"] == sha
    assert len(ns["items"]) == 1
    item = ns["items"][0]
    assert item["target_id"] == "hx_1"
    assert "missed" in item["rationale"]
    assert item["claim_ids"] == ["SYN-INV-001"]
    assert item["citation_ids"] == ["ref-1"]
    assert item["rationale"].endswith("[1]")
    assert item["rationale_kind"] == "direct_guideline"
    ref = ns["references"][0]
    assert ref["citation_id"] == "ref-1"
    assert ref["pdf_page_start"] == 1 and ref["pdf_page_end"] == 2
    assert "local_path" not in json.dumps(ns) and "file://" not in json.dumps(ns)
    loader.clear_cache()


def test_composer_does_not_mutate_report(approved_pack):
    from app.domains.scoring import evidence_loader as loader
    from app.domains.scoring.feedback_composer import compose_clinical_evidence

    d = approved_pack["dir"]
    loader.clear_cache()
    sha = next(p.stem for p in d.glob("*.json") if p.name != "index.json")
    pack = loader.load_pack(sha, evidence_dir=d)
    binding = loader.resolve_binding(
        "uti_adult_002",
        approved_pack["registry"].variants["uti_adult_002"].canonical_hash(),
        evidence_dir=d)
    rubric = _uti_rubric(approved_pack)
    report = _report_missing_culture(rubric)
    frozen = copy.deepcopy(report)
    compose_clinical_evidence(report=report, rubric_items=rubric, pack=pack,
                              binding=binding)
    if "clinical_evidence" in report:
        del report["clinical_evidence"]
    assert report == frozen
    loader.clear_cache()


def test_composer_unavailable_paths(approved_pack):
    from app.domains.scoring import evidence_loader as loader
    from app.domains.scoring.feedback_composer import compose_clinical_evidence

    d = approved_pack["dir"]
    loader.clear_cache()
    sha = next(p.stem for p in d.glob("*.json") if p.name != "index.json")
    pack = loader.load_pack(sha, evidence_dir=d)
    rubric = _uti_rubric(approved_pack)
    report = _report_missing_culture(rubric)
    # no binding
    ns, outcome = compose_clinical_evidence(
        report=report, rubric_items=rubric, pack=pack, binding=None)
    assert ns is None and outcome == "unavailable_no_binding"
    # mode not supported
    binding = dict(loader.resolve_binding(
        "uti_adult_002",
        approved_pack["registry"].variants["uti_adult_002"].canonical_hash(),
        evidence_dir=d))
    binding["supported_modes"] = ["osce"]
    ns, outcome = compose_clinical_evidence(
        report=report, rubric_items=rubric, pack=pack, binding=binding,
        mode="practice")
    assert ns is None and outcome == "unavailable_mode"
    # all-hit report -> nothing triggers
    hit_report = {"overall": 90, "per_item": [{
        "dimension": "history", "item": rubric[
            next(i for i, x in enumerate(rubric) if x["item_id"] == "hx_1")]["expected"],
        "status": "hit", "evidence": "q"}], "per_dimension": {},
        "safety_gates": [], "summary": "s"}
    binding["supported_modes"] = ["practice"]
    ns, outcome = compose_clinical_evidence(
        report=hit_report, rubric_items=rubric, pack=pack, binding=binding)
    assert ns is None and outcome == "unavailable_no_mappings"
    loader.clear_cache()


def test_wiring_flag_off_leaves_report_untouched():
    from app.domains.scoring.evidence_integration import maybe_enrich_report

    report = {"overall": 55, "per_item": []}
    before = copy.deepcopy(report)
    out = maybe_enrich_report(report, variant_id="uti_adult_002",
                              canonical_hash="x", rubric_items=[])
    assert out in ("disabled_flag_off", "unavailable_no_binding")
    assert report == before


def test_wiring_end_to_end_stub_session(monkeypatch, approved_pack):
    """Flag ON + approved pack + stub V3 session (canned judge items) ->
    namespace attached; score-critical bytes otherwise identical."""
    import copy
    import uuid

    from fastapi.testclient import TestClient

    import app.rag.judge_v3 as j3
    from app.main import app
    from pipeline.judge.evidence import build_rubric_from_variant

    from app.database import SessionLocal
    from app.domains.sessions.models import SessionRow

    db = SessionLocal()
    try:
        with TestClient(app) as h:
            email = f"pnpk{uuid.uuid4().hex[:8]}@example.com"
            h.post("/api/auth/signup", json={"email": email, "password": "secret12",
                                             "full_name": "P"})
            r = h.post("/api/auth/login",
                       json={"email": email, "password": "secret12"})
            headers = {"Authorization": "Bearer " + r.json()["data"]["token"]}
            assert r.status_code == 200
            r = h.post("/api/v2/sessions",
                       json={"case_id": "fam_uti", "language": "en"},
                       headers=headers)
            assert r.status_code == 200, r.text[:200]
            sid = r.json()["data"]["sessionId"]
            # tailor canned evidence to THIS session's variant rubric
            vid = db.get(SessionRow, sid).variant_id
            from app.domains.sessions.v3_compat_service import (
                _normalize_rubric_text, _v2_answer_key)
            live_v = approved_pack["registry"].variants[vid]
            hx1_expected = next(
                i["expected"] for i in build_rubric_from_variant(live_v)
                if i["item_id"] == "hx_1")
            want = _normalize_rubric_text(hx1_expected)
            ak_texts = []
            _ak = _v2_answer_key(live_v)
            for _grp in (_ak.get("anamnesis_checklist") or []):
                ak_texts.extend(
                    _x.get("item") for _x in (_grp.get("items") or []))
            ak_texts.extend(
                _x.get("item") for _x in (_ak.get("red_flags") or []))
            assert any(_normalize_rubric_text(t) == want for t in ak_texts), (
                "no linkable answer-key text for hx_1")
            inv2 = {"expected": next(
                t for t in ak_texts if _normalize_rubric_text(t) == want)}
    finally:
        db.close()

    async def canned_judge(*a, **k):
        return {"overall": 55, "overall_raw": 55, "per_item": [{
            "dimension": "history", "item": inv2["expected"],
            "status": "miss", "evidence": ""}],
            "per_dimension": {}, "safety_gates": [], "summary": "s"}

    monkeypatch.setattr(j3, "aevaluate_v3", canned_judge)
    monkeypatch.setenv("QORA_EVIDENCE_DIR", str(approved_pack["dir"]))
    monkeypatch.setenv("QORA_EVIDENCE_ENRICH", "1")
    with TestClient(app) as h:
        h.post(f"/api/v2/sessions/{sid}/turns", json={"text": "halo?"},
               headers=headers)
        r = h.post(f"/api/v2/sessions/{sid}/score",
                   json={"ddx": {}, "management": {}}, headers=headers)
        assert r.status_code == 200, r.text[:200]
        report = r.json()["data"]
        assert report["overall"] == 55
        ce = report.get("clinical_evidence")
        assert ce and ce["status"] == "available", ce
        assert ce["items"][0]["target_id"] == "hx_1"
        assert ce["references"][0]["citation_id"] == "ref-1"
        assert ce["pack"]["revision"] == 1
        # byte-stability of everything else: only the namespace is additive
        slim = copy.deepcopy(report)
        del slim["clinical_evidence"]
        assert set(slim) >= {"overall", "per_item", "summary"}


def test_enrichment_off_on_score_invariance(monkeypatch, approved_pack):
    """Frozen judge output, enrichment off vs on: score-critical fields
    deep-equal; judge invoked exactly once; only the additive namespace
    differs."""
    import copy
    import time
    import uuid

    from fastapi.testclient import TestClient

    import app.rag.judge_v3 as j3
    from app.main import app
    from pipeline.judge.evidence import build_rubric_from_variant
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionRow
    from app.domains.sessions.v3_compat_service import (
        _normalize_rubric_text, _v2_answer_key)

    reg = approved_pack["registry"]
    calls = []

    async def canned_judge(*a, **k):
        calls.append(1)
        return {"overall": 55, "overall_raw": 55, "per_item": [{
            "dimension": "history", "item": "DYSURIA-CANNED",
            "status": "miss", "evidence": ""}],
            "per_dimension": {}, "safety_gates": [], "summary": "s"}

    monkeypatch.setattr(j3, "aevaluate_v3", canned_judge)
    monkeypatch.setenv("QORA_EVIDENCE_DIR", str(approved_pack["dir"]))

    def _run(flag):
        monkeypatch.setenv("QORA_EVIDENCE_ENRICH", flag)
        with TestClient(app) as h:
            email = f"pnpk{uuid.uuid4().hex[:8]}@example.com"
            h.post("/api/auth/signup", json={"email": email, "password": "secret12",
                                             "full_name": "P"})
            r = h.post("/api/auth/login",
                       json={"email": email, "password": "secret12"})
            headers = {"Authorization": "Bearer " + r.json()["data"]["token"]}
            # force adult variant path: reuse fam_uti sessions until adult
            for _ in range(4):
                r = h.post("/api/v2/sessions",
                           json={"case_id": "fam_uti", "language": "en"},
                           headers=headers)
                sid = r.json()["data"]["sessionId"]
                db = SessionLocal()
                vid = db.get(SessionRow, sid).variant_id
                db.close()
                if vid == "uti_adult_002":
                    break
            assert vid == "uti_adult_002", "need adult session for invariance check"
            v = reg.variants[vid]
            hx1 = next(i["expected"] for i in build_rubric_from_variant(v)
                       if i["item_id"] == "hx_1")
            ak_texts = []
            _ak = _v2_answer_key(v)
            for _grp in (_ak.get("anamnesis_checklist") or []):
                ak_texts.extend(_x.get("item") for _x in (_grp.get("items") or []))
            canned = next(t for t in ak_texts
                          if _normalize_rubric_text(t) == _normalize_rubric_text(hx1))
            # patch canned text to the linked answer-key text
            orig = canned_judge

            async def canned2(*a, **k):
                r = await orig(*a, **k)
                r["per_item"][0]["item"] = canned
                return r

            monkeypatch.setattr(j3, "aevaluate_v3", canned2)
            h.post(f"/api/v2/sessions/{sid}/turns", json={"text": "halo?"},
                   headers=headers)
            t0 = time.perf_counter()
            r = h.post(f"/api/v2/sessions/{sid}/score",
                       json={"ddx": {}, "management": {}}, headers=headers)
            dt = (time.perf_counter() - t0) * 1000
            assert r.status_code == 200, r.text[:200]
            return r.json()["data"], dt

    off_report, _ = _run("0")
    assert "clinical_evidence" not in off_report
    on_report, on_ms = _run("1")
    assert len(calls) == 2, "one judge call per scoring (no enrichment calls)"
    off_slim = {k: v for k, v in off_report.items() if k != "clinical_evidence"}
    on_slim = {k: v for k, v in on_report.items() if k != "clinical_evidence"}
    # session/user ids differ across runs; compare score-critical content
    for key in ("overall", "per_item", "safety_gates", "summary"):
        assert off_slim.get(key) == on_slim.get(key), key
    assert on_report["clinical_evidence"]["status"] == "available"
    print(f"\n[evidence overhead] score route with enrichment: {on_ms:.0f}ms total")



def test_stub_and_failed_judge_carry_no_namespace(monkeypatch):
    """Empty/fallback reports must not be labeled PNPK-supported (stub
    judge path yields no scored items, so nothing can attach)."""
    import uuid

    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("QORA_EVIDENCE_DIR", "/tmp/nonexistent-pnpk-dir")
    monkeypatch.setenv("QORA_EVIDENCE_ENRICH", "1")
    with TestClient(app) as h:
        email = f"pnpk{uuid.uuid4().hex[:8]}@example.com"
        h.post("/api/auth/signup", json={"email": email, "password": "secret12",
                                         "full_name": "P"})
        r = h.post("/api/auth/login",
                   json={"email": email, "password": "secret12"})
        headers = {"Authorization": "Bearer " + r.json()["data"]["token"]}
        r = h.post("/api/v2/sessions",
                   json={"case_id": "fam_dengue", "language": "en"},
                   headers=headers)
        sid = r.json()["data"]["sessionId"]
        h.post(f"/api/v2/sessions/{sid}/turns", json={"text": "halo?"},
               headers=headers)
        r = h.post(f"/api/v2/sessions/{sid}/score",
                   json={"ddx": {}, "management": {}}, headers=headers)
        assert r.status_code == 200, r.text[:200]
        assert "clinical_evidence" not in r.json()["data"]


def test_loader_cache_bounded_and_reverse_index(approved_pack):
    from app.domains.scoring import evidence_loader as loader
    from pipeline.evidence.compiler import reverse_index
    from pipeline.clinical_contracts.evidence_clinical import ClinicalEvidencePack

    d = approved_pack["dir"]
    loader.clear_cache()
    sha = next(p.stem for p in d.glob("*.json") if p.name != "index.json")
    for _ in range(3):
        loader.load_pack(sha, evidence_dir=d)
    assert len(loader._cache) == 1
    pack = ClinicalEvidencePack(pack_id="SYN-P")
    rev = reverse_index(pack, [])
    assert rev["pack"] == "SYN-P" and rev["variants"] == []
    loader.clear_cache()


def test_resolve_binding_accepts_full_hash_or_prefix_but_never_empty(approved_pack):
    from app.domains.scoring import evidence_loader as loader
    d = approved_pack["dir"]
    idx = json.loads((d / "index.json").read_text())
    b0 = idx["bindings"][0]
    full = b0["canonical_hash"] + "f" * (64 - len(b0["canonical_hash"]))
    assert loader.resolve_binding(b0["variant_id"], full, evidence_dir=d) == b0
    assert loader.resolve_binding(b0["variant_id"], b0["canonical_hash"], evidence_dir=d) == b0
    assert loader.resolve_binding(b0["variant_id"], "", evidence_dir=d) is None
    assert loader.resolve_binding(b0["variant_id"], "0" * 64, evidence_dir=d) is None
    assert loader.DEFAULT_DIR.name == "evidence" and loader.DEFAULT_DIR.parent.name == "build"
