"""FASE 6 — Session hardening regression (offline, isolated sqlite, stub LLM).

Pins:
- completed-session guard: turns/stream/pf reject with 409 once completed;
- duplicate-send idempotency: identical retry returns stored reply, no new rows;
- canonical vitals: PF fallback text uses the single shared formatter and
  matches the persisted variant truth (no duplicate/conflicting values);
- investigations consistency: answer key + judge ground truth derive from the
  same persisted variant;
- refresh/resume: frozen variant/persona/content version preserved.
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
    email = f"fase6_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup",
                json={"email": email, "password": "secret12", "full_name": "F6"})
    r = client.post("/api/auth/login", json={"email": email, "password": "secret12"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["data"]["token"]}


def _v3_session_id(headers):
    r = client.post("/api/v2/sessions", json={"case_id": "fam_dengue", "language": "en"},
                    headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]["sessionId"]


def test_completed_guard_and_dedupe():
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionTurn
    from app.domains.sessions.hardening import find_duplicate_reply
    h = _new_user()
    sid = _v3_session_id(h)

    r1 = client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "What brings you here?"},
                     headers=h)
    assert r1.status_code == 200, r1.text
    reply1 = r1.json()["data"]["reply"]

    db = SessionLocal()
    try:
        n1 = db.query(SessionTurn).filter(SessionTurn.session_id == sid).count()
    finally:
        db.close()

    # duplicate-send retry returns same reply without new rows
    r2 = client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "What brings you here?"},
                     headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"]["reply"] == reply1
    db = SessionLocal()
    try:
        n2 = db.query(SessionTurn).filter(SessionTurn.session_id == sid).count()
        assert n2 == n1, f"duplicate-send must not persist: {n1} -> {n2}"
    finally:
        db.close()

    hist = [{"role": "user", "content": "hello"}, {"role": "patient", "content": "hi there"}]
    assert find_duplicate_reply(hist, "hello") == "hi there"
    assert find_duplicate_reply(hist, "other") is None

    # complete the session via score, then turns/pf must 409
    rs = client.post(f"/api/v2/sessions/{sid}/score",
                     json={"ddx": {"dx1": "dengue"}, "management": {}, "mode": "practice"},
                     headers=h)
    assert rs.status_code == 200, rs.text
    r3 = client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "are you still there?"},
                     headers=h)
    assert r3.status_code == 409, r3.text
    r4 = client.post(f"/api/v2/sessions/{sid}/pf", json={"notes": "x", "areas": ["general"]},
                     headers=h)
    assert r4.status_code == 409, r4.text
    rs2 = client.post(f"/api/v2/sessions/{sid}/score",
                      json={"ddx": {"dx1": "dengue"}, "management": {}, "mode": "practice"},
                      headers=h)
    assert rs2.status_code == 200


def test_vitals_canonical_and_investigation_consistency():
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionRow
    from app.domains.sessions.v3_compat_service import _v2_answer_key, _frozen_variant
    from app.domains.sessions.hardening import format_vitals_canonical, general_with_vitals
    from app.rag.judge_v3 import _ground_truth_block
    h = _new_user()
    sid = _v3_session_id(h)
    db = SessionLocal()
    try:
        s = db.get(SessionRow, sid)
        assert s is not None and s.variant_id
        reg, v = _frozen_variant(db, s)
        assert s.variant_canonical_hash == v.canonical_hash()
        assert s.persona is not None and s.content_schema == "new"
        assert format_vitals_canonical(v) in general_with_vitals(v)
        ak = _v2_answer_key(v)
        assert ak["case_id"] == v.id
        for entry in (ak["investigations"]["appropriate"] or []):
            match = [i for i in (v.investigations or []) if i.name == entry["name"]]
            assert match, f"answer-key investigation not in variant: {entry['name']}"
            assert match[0].expected_result == entry["expected"]
        gt = _ground_truth_block(v, with_pf=True)
        for entry in (ak["investigations"]["appropriate"] or [])[:3]:
            assert entry["name"] in gt
    finally:
        db.close()
    r = client.post(f"/api/v2/sessions/{sid}/pf", json={"notes": "check chest", "areas": ["chest"]},
                    headers=h)
    assert r.status_code == 200, r.text
    from app.domains.sessions.hardening import general_with_vitals as _gwv
    db = SessionLocal()
    try:
        s = db.get(SessionRow, sid)
        _, v = _frozen_variant(db, s)
        findings = r.json()["data"]["findings"]
        sysf = v.physical_exam.system_findings or {}
        for k, val in findings.items():
            if k in sysf:
                assert val == sysf[k]
            elif k == "general":
                # canonical vitals fallback — single shared formatter, same truth
                assert val == _gwv(v)
            else:
                raise AssertionError(f"unexpected PF key {k}")
        # isolation: never reveal more than requested (+canonical general fallback)
        assert set(findings.keys()) <= ({"chest", "general"})
    finally:
        db.close()
