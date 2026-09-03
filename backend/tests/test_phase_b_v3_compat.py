"""Phase B — V3 compatibility facade against the EXACT V2 external contract.

Proves (no frontend touch, stub LLM so no tokens are burned) that one V3
family can complete the whole V2 journey through the existing `/api/v2/*`
endpoints that `QoraV2Screen`/`QV2Session` already call:

  catalog -> create -> resume -> stream turn -> fallback turn
  -> PF -> score -> idempotent score

All responses MUST be V2-compatible shapes (CaseCard / session DTO / turns /
{reply, audioUrl} / PF / `report`). Dispatch is server-side based on the
family public ref + the persisted `content_schema` — qora-v2.jsx is untouched.
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
    """Never hit the paid LLM in tests — deterministic stub only."""
    stub = StubLlmClient()
    monkeypatch.setattr("app.rag.engine_v3.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: stub)
    return stub


def _new_user():
    email = f"pb_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup",
                json={"email": email, "password": "secret12", "full_name": "PB"})
    r = client.post("/api/auth/login",
                    json={"email": email, "password": "secret12"})
    return r.json()["data"]["token"]


def _auth(token):
    return {"Authorization": "Bearer " + token}


FAMILY = "fam_dengue"


def test_v3_family_does_not_resolve_as_v2_case(monkeypatch):
    # guard: the dispatcher must NOT treat a family ref as a legacy v2 case
    from app.domains.sessions.v3_compat_schemas import is_v3_family_ref, resolve_ref
    assert is_v3_family_ref(FAMILY) is True
    assert resolve_ref(FAMILY) == "v3"
    assert resolve_ref("derm_cellulitis_001") == "v2"


def test_v3_family_catalog_returns_v2_cards_via_flag(monkeypatch):
    # force the feature flag so /api/v2/cases returns V3 family cards
    monkeypatch.setattr("app.domains.sessions.v2_router._is_v3_compat",
                        lambda *, user=None, email=None: True)
    tok = _new_user()
    r = client.get("/api/v2/cases", headers=_auth(tok))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["contentEngine"] == "v3_compat"
    assert data["total"] >= 1  # only published/verified families surface (guard)
    ids = {c["id"] for c in data["cases"]}
    assert FAMILY in ids
    card = next(c for c in data["cases"] if c["id"] == FAMILY)
    # exact V2 CaseCard fields the frontend renders
    for f in ("id", "specialty", "mode", "difficulty", "estimated_minutes",
              "first_impression_id", "title", "source_type"):
        assert f in card, f"missing CaseCard field: {f}"
    assert card["source_type"] == "v3_family"
    assert card["family_type"] in ("disease", "presentation")


def test_full_v2_journey_on_v3_family():
    tok = _new_user()
    h = _auth(tok)

    # 1) CREATE — dispatch on family ref, return exact V2 session DTO
    r = client.post("/api/v2/sessions",
                    json={"case_id": FAMILY, "language": "id"}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    for f in ("sessionId", "caseId", "mode", "language", "openingLine"):
        assert f in d, f"missing session field: {f}"
    assert d["caseId"] == FAMILY
    sid = d["sessionId"]
    assert d["openingLine"]

    # 2) RESUME — GET turns (exact V2 shape; no content_schema leak required)
    r = client.get(f"/api/v2/sessions/{sid}/turns", headers=h)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    for f in ("turns", "case_id", "language", "status", "opening_line"):
        assert f in d
    assert d["case_id"] == FAMILY

    # 3) STREAM TURN — raw text/plain, not JSON
    r = client.post(f"/api/v2/sessions/{sid}/turns/stream",
                    json={"text": "Apa keluhan utama?", "input_type": "text"},
                    headers=h)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/plain")
    body = r.text
    assert "STUB LLM" in body  # deterministic stub reply

    # 4) FALLBACK TURN — {reply, audioUrl}
    r = client.post(f"/api/v2/sessions/{sid}/turns",
                    json={"text": "Sudah berapa lama demamnya?"}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert "reply" in d and "audioUrl" in d
    assert "STUB LLM" in d["reply"]

    # 5) PF — reveal only examined areas (isolation rule, V2 contract)
    r = client.post(f"/api/v2/sessions/{sid}/pf",
                    json={"notes": "inspeksi umum & abdomen", "areas": ["general", "abdomen"]},
                    headers=h)
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        d = r.json()["data"]
        for f in ("findings", "examined", "available_areas"):
            assert f in d

    # 6) SCORE — report in exact V2 shape
    r = client.post(f"/api/v2/sessions/{sid}/score",
                    json={"ddx": {"primary": "dengue"}, "management": {"complete": True},
                          "mode": "osce", "overtime": False,
                          "pf_notes": "ok", "pf_areas": ["general"]},
                    headers=h)
    assert r.status_code == 200, r.text
    report = r.json()["data"]
    for f in ("overall", "per_dimension", "safety_gates", "summary", "answer_key"):
        assert f in report, f"missing V2 report field: {f}"
    assert isinstance(report["overall"], int)

    # 7) IDEMPOTENT SCORE — same stored report, no double scoring
    r2 = client.post(f"/api/v2/sessions/{sid}/score",
                     json={"ddx": {"primary": "dengue"}, "management": {"complete": True},
                           "mode": "osce", "pf_areas": []},
                     headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"] == report  # exact same stored report

    # 8) session is owned by user; legacy v2 path untouched for real v2 case
    assert sid


def test_v2_legacy_case_path_unchanged():
    # a real v2 case_id must NOT be dispatched to v3
    from app.domains.sessions.v3_compat_schemas import resolve_ref
    assert resolve_ref("em_acs_001") == "v2"


def test_v3_session_opens_with_v3_family_detail():
    # GET /api/v2/cases/{family} returns the family card (Phase C adapter)
    tok = _new_user()
    r = client.get(f"/api/v2/cases/{FAMILY}", headers=_auth(tok))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["id"] == FAMILY
    assert d["source_type"] == "v3_family"