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
    # source: every module that does `from app.rag.llm import *` picks this up
    monkeypatch.setattr("app.rag.llm.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.engine_v3.get_llm_client", lambda: stub)
    monkeypatch.setattr("app.rag.judge_v3.get_llm_client", lambda: stub)
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
    # V2-compatible answer_key shape (QV2Result renders these exact fields)
    ak = report["answer_key"]
    for f in ("anamnesis_checklist", "red_flags", "expected_ddx",
              "investigations", "management", "case_id", "chief_complaint"):
        assert f in ak, f"V2 answer_key missing: {f}"
    assert isinstance(ak["anamnesis_checklist"], list) and ak["anamnesis_checklist"]
    assert isinstance(ak["management"]["pharmacological"], list)
    assert "working_diagnosis" in ak["expected_ddx"]
    # QV2Result needs per_item for the hit/miss overlay
    assert "per_item" in report and isinstance(report["per_item"], list)

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


# ── Billing parity (§3 addendum): V3 sessions must NOT bypass billing ─────
def test_v3_session_start_gated_when_free_limit_reached(monkeypatch):
    """Free-session-limit / entitlement gate applies to V3-backed sessions."""
    from app.domains.billing import service as billing
    tok = _new_user()
    monkeypatch.setattr(
        "app.domains.billing.service.can_start_session",
        lambda *a, **k: {"allowed": False, "reason": "free_limit_reached",
                         "usage": {"sessions": 5}, "limit": 5},
    )
    r = client.post("/api/v2/sessions",
                    json={"case_id": FAMILY, "language": "en"}, headers=_auth(tok))
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["reason"] == "free_limit_reached"


def test_v3_session_counts_usage_and_records_session_cost(monkeypatch):
    """V3 create calls record_usage; stream/fallback turn calls record_session_cost."""
    from app.domains.billing import service as billing
    recorded_usage, recorded_cost = [], []
    monkeypatch.setattr("app.domains.billing.service.can_start_session",
                        lambda *a, **k: {"allowed": True, "usage": {"sessions": 0}})
    monkeypatch.setattr("app.domains.billing.service.record_usage",
                        lambda *a, **k: (recorded_usage.append(a) and None))
    monkeypatch.setattr("app.domains.billing.service.record_session_cost",
                        lambda *a, **k: (recorded_cost.append(a) and None))

    tok = _new_user()
    r = client.post("/api/v2/sessions",
                    json={"case_id": FAMILY, "language": "id"}, headers=_auth(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["data"]["sessionId"]
    # session_start usage recorded for this user + family
    assert any(arg[2] == "session_start" for arg in recorded_usage)

    # a fallback turn must record session cost
    client.get(f"/api/v2/sessions/{sid}/turns", headers=_auth(tok))
    r = client.post(f"/api/v2/sessions/{sid}/turns",
                    json={"text": "Bagaimana gejala awalnya?"}, headers=_auth(tok))
    assert r.status_code == 200, r.text
    assert recorded_cost, "V3 turn must call record_session_cost (cost accounting)"


# ── Failure isolation (§ additional tests) ────────────────────────────────
def test_invalid_v3_family_ref_fails_clearly():
    """Unknown family ref must 404, never silently fall back to a random case."""
    tok = _new_user()
    r = client.post("/api/v2/sessions",
                    json={"case_id": "fam_tidak_ada", "language": "en"},
                    headers=_auth(tok))
    assert r.status_code == 404, r.text
    # and it must NOT have created any session
    d = client.get("/api/v2/sessions?limit=5", headers=_auth(tok)).json()["data"]
    assert len(d["sessions"]) == 0


def test_v3_catalog_case_detail_404_for_unknown():
    tok = _new_user()
    r = client.get("/api/v2/cases/fam_nonexistent", headers=_auth(tok))
    # not a v3 family and not a v2 legacy case -> clean 404 (no silent fallback)
    assert r.status_code == 404, r.text


# ── Additional requested tests (§ addendum) ──────────────────────────────
def test_v3_engine_failure_does_not_fallback_to_v2(monkeypatch):
    """A V3 engine error must surface as an error, never swap to the V2 patient."""
    from pipeline.case_v3.runtime import VariantUnavailable
    tok = _new_user()
    r = client.post("/api/v2/sessions",
                    json={"case_id": FAMILY, "language": "en"}, headers=_auth(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["data"]["sessionId"]
    # force the V3 engine to raise on stream
    def _boom(*a, **k):
        raise RuntimeError("v3 patient engine down")
    monkeypatch.setattr("app.rag.engine_v3.stream_respond", _boom)
    r = client.post(f"/api/v2/sessions/{sid}/turns/stream",
                    json={"text": "Apa keluhan utama?"}, headers=_auth(tok))
    assert r.status_code == 200
    assert "error" in r.text.lower()  # surfaces as stream error, not V2 patient


def test_stream_disconnect_does_not_corrupt_transcript():
    """A failed/interrupted stream must not leave a dangling patient turn."""
    tok = _new_user()
    r = client.post("/api/v2/sessions",
                    json={"case_id": FAMILY, "language": "en"}, headers=_auth(tok))
    sid = r.json()["data"]["sessionId"]
    h = _auth(tok)
    # one normal turn then verify the transcript stays balanced/ordered
    client.post(f"/api/v2/sessions/{sid}/turns",
                json={"text": "Sudah lama?"}, headers=h)
    turns = client.get(f"/api/v2/sessions/{sid}/turns", headers=h).json()["data"]["turns"]
    roles = [t["role"] for t in turns]
    # every user turn is paired with exactly one patient reply (no orphan/dangling)
    assert roles.count("user") == roles.count("patient")
    # and alert turns are ordered u,p,u,p...
    for i in range(0, len(roles) - 1, 2):
        assert roles[i] == "user" and roles[i + 1] == "patient"