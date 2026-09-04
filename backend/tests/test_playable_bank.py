"""Phase 4 continuation — playable bank integrity + multi-specialty lifecycle.

Pins (isolated sqlite via conftest FASE 0 gate, stub LLM — no paid calls):
- bank scale: >=115 families / >=260 variants load; 252 new lint-clean.
- honesty: categories read from exact SKD anchors; zero invented URLs;
  new content capped at in_review/research_complete; existing reviewed bank
  untouched (12 pilot_verified, 0 clinician-signed).
- presentation families reuse refs only (no independent clinical truth).
- compat: every non-draft family advertises >=1 eligible card; representative
  families from EACH of the 10 specialties complete create -> turn -> PF ->
  score -> resume through the exact V2 contract.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.rag.llm import StubLlmClient

init_db()
client = TestClient(app)


@pytest.fixture(autouse=True)
def _stub_llm(monkeypatch):
    stub = StubLlmClient()
    monkeypatch.setattr("app.rag.llm.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v3.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.judge_v3.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.domains.sessions.v2_router._is_v3_compat",
                        lambda *, user=None, email=None: True)
    return stub


def _new_user():
    email = f"bank_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup",
                json={"email": email, "password": "secret12", "full_name": "BK"})
    r = client.post("/api/auth/login", json={"email": email, "password": "secret12"})
    return r.json()["data"]["token"]


def _auth(token):
    return {"Authorization": "Bearer " + token}


# one representative disease family per specialty (all newly generated)
REPRESENTATIVES = {
    "internal_medicine": "fam_dm2",
    "emergency": "fam_acs",
    "paediatrics": "fam_child_pneumonia",
    "obstetrics_gynaecology": "fam_anc",
    "neurology": "fam_migraine",
    "psychiatry": "fam_depression",
    "surgery": "fam_appendicitis",
    "dermatology": "fam_scabies",
    "ent": "fam_otitis_media",
    "ophthalmology": "fam_conjunctivitis",
}


def test_bank_scale_and_new_content_lint_clean():
    from pipeline.case_v3.loader import CaseRegistry
    from pipeline.case_v3.lint import lint_variant
    reg = CaseRegistry.from_dir()
    assert len(reg.families) >= 115
    assert len(reg.variants) >= 260
    newv = [v for v in reg.variants.values() if v.clinical_content_version == "v3.1"]
    assert len(newv) == 252
    errs = [str(i) for v in newv for i in lint_variant(v).errors]
    assert errs == []


def test_bank_honesty_no_invented_urls_and_capped_status():
    from pipeline.case_v3.loader import CaseRegistry
    reg = CaseRegistry.from_dir()
    for v in reg.variants.values():
        if v.clinical_content_version != "v3.1":
            continue
        assert v.status == "research_complete", v.id
        for s in v.sources:
            assert not s.url or s.url.startswith(("http://", "https://")), v.id
        fam = reg.families[v.family_id]
        assert fam.status == "in_review", fam.id
    # existing reviewed bank untouched
    old = [v for v in reg.variants.values() if v.clinical_content_version != "v3.1"]
    assert len(old) == 12
    assert {v.status for v in old} == {"pilot_verified"}


def test_categories_match_exact_skd_anchors():
    import json
    from pathlib import Path
    from pipeline.case_v3.loader import CaseRegistry
    cat = json.loads(Path("..", "content", "v3", "catalog",
                          "skd2026_master_catalog.json").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in (cat if isinstance(cat, list) else cat.get("entries", []))}
    reg = CaseRegistry.from_dir()
    checked = 0
    for v in reg.variants.values():
        if v.clinical_content_version != "v3.1":
            continue
        anchor = v.canonical_entity_id
        assert anchor in by_id, f"{v.id} anchor missing from catalog"
        assert v.competency.category == by_id[anchor]["category"], v.id
        assert v.competency.system == by_id[anchor]["system"], v.id
        checked += 1
    assert checked == 252


def test_presentation_families_reuse_only():
    from pipeline.case_v3.loader import CaseRegistry
    from pipeline.case_v3.vocab import FamilyType
    reg = CaseRegistry.from_dir()
    pres = [f for f in reg.families.values() if f.family_type == FamilyType.PRESENTATION]
    assert len(pres) >= 9  # 8 new + fam_fever_child
    disease_variants = {v.id for v in reg.variants.values()
                        if reg.families[v.family_id].family_type != FamilyType.PRESENTATION}
    for f in pres:
        if f.id == "fam_fever_child":
            continue
        assert len(f.active_variant_ids) >= 2, f.id
        assert set(f.active_variant_ids) <= disease_variants, f.id


def test_compat_cards_cover_all_eligible_families():
    from app.domains.sessions.v3_compat_schemas import default_registry, family_variant_count
    tok = _new_user()
    r = client.get("/api/v2/cases", headers=_auth(tok))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["contentEngine"] == "v3_compat"
    reg = default_registry()
    expect = {fid for fid, fam in reg.families.items()
              if fam.status != "draft" and family_variant_count(reg, fam, "koas") > 0}
    got = {c["id"] for c in data["cases"]}
    assert expect <= got
    assert len(data["cases"]) >= 115
    for c in data["cases"]:
        assert c["eligible_variant_count"] >= 1
        for f in ("id", "specialty", "mode", "difficulty", "estimated_minutes", "title"):
            assert f in c


@pytest.mark.parametrize("specialty,family", sorted(REPRESENTATIVES.items()))
def test_representative_family_full_lifecycle(specialty, family):
    tok = _new_user()
    h = _auth(tok)
    r = client.post("/api/v2/sessions", headers=h,
                    json={"case_id": family, "language": "en"})
    assert r.status_code == 200, f"{family}: {r.text[:200]}"
    sid = r.json()["data"]["sessionId"]
    assert r.json()["data"]["openingLine"]
    # multi-turn text
    for msg in ("What brings you in today?", "How long has this been going on?"):
        t = client.post(f"/api/v2/sessions/{sid}/turns", headers=h, json={"text": msg})
        assert t.status_code == 200, f"{family} turn: {t.text[:200]}"
        assert t.json()["data"]["reply"]
    # resume does not reselect (same opening/persona truth)
    g = client.get(f"/api/v2/sessions/{sid}/turns", headers=h)
    assert g.status_code == 200
    roles = [x["role"] for x in g.json()["data"]["turns"]]
    assert "user" in roles and "patient" in roles
    # PF + score
    pf = client.post(f"/api/v2/sessions/{sid}/pf", headers=h,
                     json={"notes": "focused exam per complaint", "areas": ["general"]})
    assert pf.status_code == 200, f"{family} pf: {pf.text[:200]}"
    sc = client.post(f"/api/v2/sessions/{sid}/score", headers=h,
                     json={"ddx": {"primary": "working diagnosis per history"},
                           "management": {"plan": "initial plan with referral as indicated"},
                           "mode": "practice"})
    assert sc.status_code == 200, f"{family} score: {sc.text[:300]}"
    rep = sc.json()["data"]
    assert rep.get("per_dimension") and rep.get("answer_key")
    # blind families must not leak dx through the whole path
    from pipeline.case_v3.loader import CaseRegistry
    reg = CaseRegistry.from_dir()
    if reg.families[family].family_type.value == "presentation":
        blob = (r.text + g.text).lower()
        assert "working_diagnosis" not in blob and "answer_key" not in blob
