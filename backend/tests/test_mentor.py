"""Qora Mentor tests (PRD_QORA_MENTOR §8.1, §8.2) — Phase 1 scope.

Run with a LOCAL sqlite DB so the suite never touches prod Supabase:
    DATABASE_URL=sqlite:////tmp/mentor_tests.db .venv/bin/pytest tests/test_mentor.py

LLM is stubbed everywhere (Arran's constraint: no paid API calls in dev).
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
    """Journey builder must never hit the real LLM in tests."""
    monkeypatch.setattr("app.domains.mentor.journey_builder.get_llm_client",
                        lambda: StubLlmClient())
    monkeypatch.setattr("app.rag.llm.is_stub", lambda: True)
    yield


def _auth() -> dict:
    email = f"mentor_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12",
                                          "full_name": "M"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}
                      ).json()["data"]["token"]
    return {"Authorization": f"Bearer {tok}"}


# ---------------------------------------------------------------------------
# Case selection (unit, PRD §8.1)
# ---------------------------------------------------------------------------

def _catalog():
    from app.domains.cases.v2_catalog import list_v2_cases
    return list_v2_cases()


def test_case_selection_7_day_paeds():
    from app.domains.mentor.case_selector import select_cases
    context = {"timeline_days": 7, "level": "koas", "weaknesses": ["paediatrics"]}
    selected = select_cases(context, _catalog())
    assert len(selected) == 7
    assert selected[0]["specialty"] == "paediatrics"  # weakness prioritized
    assert any(c["specialty"] == "paediatrics" for c in selected)
    assert selected[-1]["day"] == 7  # mock exam on final day
    # Foundational → advanced ordering
    assert selected[0]["difficulty"] <= selected[-1]["difficulty"]


def test_case_selection_includes_osce_full_for_long_timeline():
    from app.domains.mentor.case_selector import select_cases
    context = {"timeline_days": 7, "level": "koas", "weaknesses": []}
    selected = select_cases(context, _catalog())
    assert any(c["mode"] == "osce_full" for c in selected)
    assert selected[-1]["day"] == 7


def test_case_selection_level_mapping():
    from app.domains.mentor.case_selector import select_cases
    pre = select_cases({"timeline_days": 5, "level": "preklinik", "weaknesses": []}, _catalog())
    ppds = select_cases({"timeline_days": 5, "level": "ppds", "weaknesses": []}, _catalog())
    assert pre and ppds
    assert all(c["difficulty"] <= 2 for c in pre[:3])
    assert all(c["difficulty"] >= 2 for c in ppds[:3])


def test_weakness_alias_mapping():
    from app.domains.mentor.case_selector import map_weaknesses
    assert map_weaknesses(["Pediatrik", "bedah", "mata"]) == \
        ["paediatrics", "surgery", "ophthalmology"]


def test_case_selection_timeline_clamped():
    from app.domains.mentor.case_selector import select_cases
    ctx = {"timeline_days": 999, "level": "koas", "weaknesses": []}
    selected = select_cases(ctx, _catalog())
    assert selected[-1]["day"] <= 90


# ---------------------------------------------------------------------------
# Context extraction (deterministic fallback — no LLM)
# ---------------------------------------------------------------------------

def test_heuristic_context_extraction():
    from app.domains.mentor.journey_builder import extract_context
    ctx = extract_context("Ujian gua 1 minggu lagi, masih bego pediatrik")
    assert ctx["timeline_days"] == 7
    assert "paediatrics" in ctx["weaknesses"]
    assert ctx["level"] == "koas"
    assert ctx["emotional_state"] == "panik"  # "bego" is a panic signal


def test_heuristic_context_stase_bedah():
    from app.domains.mentor.journey_builder import extract_context
    ctx = extract_context(
        "Stase bedah bulan depan, belum pernah latihan appendicitis")
    assert ctx["timeline_days"] == 30
    assert "surgery" in ctx["weaknesses"]
    assert ctx["goal"] == "stase"


# ---------------------------------------------------------------------------
# Journey lifecycle (integration, PRD §8.2 adapted)
# ---------------------------------------------------------------------------

def test_full_journey_flow():
    H = _auth()
    # 1. Story → proposal
    r = client.post("/api/v2/mentor/story",
                    json={"story": "Ujian 1 minggu lagi, pediatrik"}, headers=H).json()
    assert r["success"], r
    j = r["data"]
    jid = j["id"]
    assert j["status"] == "proposed"
    assert j["proposal"]["package_name"]
    assert len(j["cases"]) > 0
    assert all(c["status"] == "locked" for c in j["cases"])

    # 2. Accept → active + first case available
    r = client.post(f"/api/v2/mentor/journeys/{jid}/accept", json={}, headers=H).json()
    assert r["data"]["status"] == "active"
    first = r["data"]["next_case"]
    assert first is not None and first["day"] == 1 and first["status"] == "available"

    # 3. Next-case endpoint agrees
    r = client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H).json()
    assert r["data"]["case"]["case_id"] == first["case_id"]

    # 4. Complete first case → next unlocks
    r = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": first["case_id"], "session_id": "sess_x",
                          "score": 75}, headers=H).json()
    d = r["data"]
    assert d["progress"]["completed"] == 1
    assert d["next_case"] is not None and d["next_case"]["day"] == first["day"] + 1
    assert d["readiness"]["current"] == 75

    # 5. Journey list shows it
    r = client.get("/api/v2/mentor/journeys", headers=H).json()
    assert any(j2["id"] == jid for j2 in r["data"]["journeys"])


def test_customize_before_accept():
    H = _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    r = client.post(f"/api/v2/mentor/journeys/{jid}/customize",
                    json={"feedback": "tambah kasus bedah dong"}, headers=H).json()
    assert r["success"], r
    assert r["data"]["changes"]
    assert r["data"]["updated_proposal"]["status"] == "proposed"


def test_customize_only_before_start():
    H = _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    client.post(f"/api/v2/mentor/journeys/{jid}/accept", json={}, headers=H)
    r = client.post(f"/api/v2/mentor/journeys/{jid}/customize",
                    json={"feedback": "ganti hari 3"}, headers=H)
    assert r.status_code == 409


def test_abandon_journey():
    H = _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    r = client.post(f"/api/v2/mentor/journeys/{jid}/abandon", headers=H).json()
    assert r["data"]["status"] == "abandoned"
    # Abandoned journey has no next case
    assert client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H).status_code == 409


def test_journey_ownership():
    H1, H2 = _auth(), _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H1).json()["data"]["id"]
    assert client.get(f"/api/v2/mentor/journeys/{jid}", headers=H2).status_code == 404
    assert client.post(f"/api/v2/mentor/journeys/{jid}/accept", json={},
                       headers=H2).status_code == 404


def test_mentor_requires_auth():
    assert client.post("/api/v2/mentor/story", json={"story": "x"}).status_code == 401
    assert client.get("/api/v2/mentor/journeys").status_code == 401
