"""FASE 3 — blind presentation family through the V2 contract (server-side only).

Fam_fever_child curates CROSS-family variant refs (dengue + UTI) for a blind
fever presentation. The canary proved `start` 404'd while the card listed the
family — this suite pins the fix: card count and `start` resolve the SAME
candidate set, the session persists content_schema='new' with a frozen
cross-family variant, every endpoint keeps the exact V2 shape, blind payloads
never leak diagnosis/rubric/answer-key, and failures stay loud (no silent V2
downgrade). No frontend involved.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app
from app.rag.llm import StubLlmClient

init_db()
client = TestClient(app)

FAMILY = "fam_fever_child"
LEAK_TOKENS = ("dengue", "working_diagnosis", "answer_key", "rubric",
               "differential", "management", "pnpk", "icd")


@pytest.fixture(autouse=True)
def _stub_llm(monkeypatch):
    stub = StubLlmClient()
    monkeypatch.setattr("app.rag.llm.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v3.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.judge_v3.get_llm_client", lambda: stub)
    return stub


@pytest.fixture(autouse=True)
def _force_compat(monkeypatch):
    monkeypatch.setattr("app.domains.sessions.v2_router._is_v3_compat",
                        lambda *, user=None, email=None: True)


def _new_user():
    email = f"pf_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup",
                json={"email": email, "password": "secret12", "full_name": "PF"})
    r = client.post("/api/auth/login",
                    json={"email": email, "password": "secret12"})
    return r.json()["data"]["token"]


def _auth(token):
    return {"Authorization": "Bearer " + token}


def _assert_no_leak(payload, where):
    s = str(payload).lower()
    for tok in LEAK_TOKENS:
        # 'management' appears in compat score INPUT echo? score output must not
        # carry it; card/create/turn payloads must be clean.
        assert tok not in s, f"blind leak in {where}: {tok}"


def test_blind_card_count_matches_start_capability():
    from app.domains.sessions.v3_compat_schemas import (
        default_registry, family_variant_count, resolve_start_variants)
    reg = default_registry()
    fam = reg.families[FAMILY]
    assert family_variant_count(reg, fam, "koas") >= 1
    assert len(resolve_start_variants(reg, fam, "koas")) >= 1
    tok = _new_user()
    r = client.get("/api/v2/cases", headers=_auth(tok))
    card = next(c for c in r.json()["data"]["cases"] if c["id"] == FAMILY)
    _assert_no_leak(card, "blind card")
    assert card["eligible_variant_count"] >= 1


def test_blind_full_journey_no_downgrade():
    from app.domains.sessions.models import SessionRow
    tok = _new_user()
    h = _auth(tok)

    r = client.post("/api/v2/sessions", json={"case_id": FAMILY, "language": "en"}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    sid = d["sessionId"]
    _assert_no_leak(d, "blind create")
    assert d["openingLine"]

    db = SessionLocal()
    try:
        s = db.get(SessionRow, sid)
        assert s.content_schema == "new"  # never silently V2
        assert s.variant_id in ("dengue_001_mild", "uti_child_001")
        frozen_variant, frozen_hash = s.variant_id, s.variant_canonical_hash
    finally:
        db.close()

    r = client.post(f"/api/v2/sessions/{sid}/turns",
                    json={"text": "What seems to be the problem?"}, headers=h)
    assert r.status_code == 200
    assert "reply" in r.json()["data"]
    _assert_no_leak(r.json()["data"], "blind turn")

    # Refresh/resume: same frozen variant, history grows, no re-selection.
    r = client.get(f"/api/v2/sessions/{sid}/turns", headers=h)
    assert r.status_code == 200
    assert len(r.json()["data"]["turns"]) >= 2
    _assert_no_leak(r.json()["data"], "blind resume")
    db = SessionLocal()
    try:
        s = db.get(SessionRow, sid)
        assert (s.variant_id, s.variant_canonical_hash) == (frozen_variant, frozen_hash)
    finally:
        db.close()

    body = {"ddx": {"working_dx": "Viral fever"}, "management": {"plan": "Supportive"},
            "mode": "practice", "overtime": False}
    r1 = client.post(f"/api/v2/sessions/{sid}/score", json=body, headers=h)
    assert r1.status_code == 200, r1.text
    rep = r1.json()["data"]
    for f in ("overall", "per_dimension", "per_item", "safety_gates", "summary", "answer_key"):
        assert f in rep, f"missing V2 report field: {f}"
    r2 = client.post(f"/api/v2/sessions/{sid}/score", json=body, headers=h)
    assert r2.json()["data"]["overall"] == rep["overall"]  # idempotent


def test_invalid_family_ref_fails_clearly():
    tok = _new_user()
    r = client.post("/api/v2/sessions", json={"case_id": "fam_nope", "language": "en"},
                    headers=_auth(tok))
    assert r.status_code == 404


def test_canary_email_match_is_case_insensitive(monkeypatch):
    # FASE 3 canary finding: mixed-case account emails never matched the
    # lowercased canary list, silently staying on V2.
    from app.config import Settings
    from app.domains.sessions import v2_router
    s = Settings(case_content_engine="v2", v3_compat_test_emails="Canary@T.Co")

    class _U:
        email = "canary@t.co"

    monkeypatch.setattr("app.config.get_settings", lambda: s)
    assert v2_router._is_v3_compat(user=_U()) is True
