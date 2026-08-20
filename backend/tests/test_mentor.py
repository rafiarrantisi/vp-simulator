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

    # 3b. Create a REAL v2 session for this case so journey_cases.session_id
    # FK (-> sessions.id) is valid — a fake "sess_x" violates the constraint.
    sess = client.post("/api/v2/sessions",
                       json={"case_id": first["case_id"]}, headers=H).json()
    assert sess["success"], sess
    sid = sess["data"]["sessionId"]

    # 4. Complete first case → next unlocks
    r = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": first["case_id"], "session_id": sid,
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


# ---------------------------------------------------------------------------
# Phase 2: reasoning autopsy (PRD §8.1/§8.3, deterministic path)
# ---------------------------------------------------------------------------

def test_autopsy_detects_missed_red_flag():
    from app.domains.cases.v2_catalog import load_v2_case
    from app.domains.mentor.autopsy_generator import generate_autopsy
    case = load_v2_case("im_uta_001")
    transcript = [{"role": "user", "content": "Kaki bengkak sejak kapan?"},
                  {"role": "patient", "content": "3 hari dok."}]
    report = {"overall": 60, "per_item": [
        {"dimension": "red_flags", "item": "Sudden chest pain or difficulty breathing",
         "status": "miss", "evidence": ""},
        {"dimension": "anamnesis_checklist", "item": "Onset", "status": "hit", "evidence": ""},
    ], "per_dimension": {"red_flags": {"score": 0, "max": 10, "feedback": ""}}}
    a = generate_autopsy(case, transcript, report)
    assert any(e["type"] == "missed_red_flag" and e["severity"] == "critical"
               for e in a["errors_detected"])
    assert a["readiness_impact"] <= -2
    assert a["pearl"]
    assert a["expert_pathway"]  # gold-standard steps derived from checklist


def test_autopsy_no_errors_when_clean():
    from app.domains.cases.v2_catalog import load_v2_case
    from app.domains.mentor.autopsy_generator import generate_autopsy
    case = load_v2_case("im_uta_001")
    report = {"overall": 90, "per_item": [
        {"dimension": "red_flags", "item": "Sudden chest pain or difficulty breathing",
         "status": "hit", "evidence": ""},
    ], "per_dimension": {}}
    a = generate_autopsy(case, [{"role": "user", "content": "Hi"}], report)
    assert a["errors_detected"] == []
    assert a["readiness_impact"] == 0


def _auth_user():
    H = _auth()
    me = client.get("/api/users/me", headers=H).json()["data"]
    return H, me["user_id"]


def _fabricate_completed_session(db, user_id, case_id, report, days_ago=0):
    from datetime import datetime, timedelta, timezone
    from app.domains.sessions.models import SessionRow
    s = SessionRow(user_id=user_id, institution_id="default", case_id=case_id,
                   mode="anamnesis", status="completed", language="id",
                   total_score=report.get("overall", 0), report=report)
    s.ended_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def test_autopsy_endpoint_triggers_continuity():
    from app.database import SessionLocal
    from app.domains.mentor.models import PatientSeries
    from tools.seed_patient_series import _SERIES
    H, uid = _auth_user()
    # Seed the patient series into the test DB (prod seed doesn't reach sqlite).
    db = SessionLocal()
    try:
        for s in _SERIES:
            if db.get(PatientSeries, s["id"]) is None:
                db.add(PatientSeries(**s))
        db.commit()
    finally:
        db.close()
    # Start a real session for im_uta_001 (the series trigger case).
    sid = client.post("/api/v2/sessions", json={"case_id": "im_uta_001"}, headers=H
                      ).json()["data"]["sessionId"]
    # Fabricate a completed report where the PE red flag was MISSED.
    report = {"overall": 55, "per_item": [
        {"dimension": "red_flags",
         "item": "Sudden chest pain or difficulty breathing",
         "status": "miss", "evidence": ""},
    ], "per_dimension": {"red_flags": {"score": 0, "max": 10, "feedback": ""}}}
    db = SessionLocal()
    try:
        from app.domains.sessions.models import SessionRow
        s = db.get(SessionRow, sid)
        s.status = "completed"
        s.total_score = 55
        s.report = report
        db.commit()
    finally:
        db.close()

    # POST autopsy → missed red flag → continuity queued (Pak Budi visit 2).
    r = client.post(f"/api/v2/mentor/sessions/{sid}/autopsy", headers=H).json()
    assert r["success"], r
    d = r["data"]
    assert any(e["type"] == "missed_red_flag" for e in d["autopsy"]["errors_detected"])
    assert d["continuity"] is not None
    assert d["continuity"]["next_case_id"] == "em_pulmonary_embolism_001"
    assert d["continuity"]["visit_number"] == 2
    assert d["continuity"]["total_visits"] == 2

    # GET autopsy returns the stored one.
    g = client.get(f"/api/v2/mentor/sessions/{sid}/autopsy", headers=H).json()
    assert g["data"]["autopsy"]["id"] == d["autopsy"]["id"]

    # Pending continuity surfaces for the next session.
    p = client.get("/api/v2/mentor/continuity/pending", headers=H).json()["data"]["pending"]
    assert p and p["next_case_id"] == "em_pulmonary_embolism_001"
    assert p["name"] == "Pak Budi" and p["visit_number"] == 2

    # Idempotent: re-running the autopsy must NOT advance to a 3rd visit.
    r2 = client.post(f"/api/v2/mentor/sessions/{sid}/autopsy", headers=H).json()
    assert r2["data"]["continuity"]["visit_number"] == 2


def test_continuity_prompt_injection():
    from app.domains.cases.v2_catalog import load_v2_case
    from app.rag.prompt_v2 import build_patient_prompt
    case = load_v2_case("em_pulmonary_embolism_001")
    prompt = build_patient_prompt(case, language="id",
                                  continuity_context=case.frontmatter.get("continuity"))
    assert "RETURNING patient" in prompt
    assert "deep vein thrombosis" in prompt
    assert "5 days ago" in prompt
    assert "CONTINUITY CONTEXT" in prompt


# ---------------------------------------------------------------------------
# Phase 2: readiness (PRD §4.4.2 / §8.1)
# ---------------------------------------------------------------------------

def _report_for(overall, **dim_pcts):
    per_dim = {k: {"score": v, "max": 100, "feedback": ""} for k, v in dim_pcts.items()}
    return {"overall": overall, "per_item": [], "per_dimension": per_dim}


def test_readiness_endpoint_formula():
    from app.database import SessionLocal
    H, uid = _auth_user()
    db = SessionLocal()
    try:
        for i in range(5):
            _fabricate_completed_session(db, uid, f"case_{i}", _report_for(
                70,
                history_coverage=80, red_flags=70, diagnostic_reasoning=75,
                management=70, physical_exam=60, communication=80,
                ice_fife=65, questioning_technique=70))
    finally:
        db.close()

    r = client.get("/api/v2/mentor/readiness", headers=H).json()["data"]
    assert r["session_count"] == 5
    assert r["confidence"] == "medium"
    # base = .2*80+.15*70+.15*75+.15*70+.1*60+.1*80+.1*65+.05*70 = 72.25
    assert 70 <= r["score"] <= 75
    assert r["interpretation"]["level"] in ("borderline", "pass")


def test_readiness_report_weakest_and_recs():
    from app.database import SessionLocal
    H, uid = _auth_user()
    db = SessionLocal()
    try:
        _fabricate_completed_session(db, uid, "c1", _report_for(
            70, history_coverage=80, red_flags=70, diagnostic_reasoning=75,
            management=70, physical_exam=40, communication=80,
            ice_fife=65, questioning_technique=70))
    finally:
        db.close()
    r = client.get("/api/v2/mentor/readiness/report", headers=H).json()["data"]
    assert r["weakest"]["dimension"] == "physical_exam"
    assert r["disclaimer"]  # required PRD §10.2
    assert r["recommendations"]


def test_readiness_empty_when_no_sessions():
    H = _auth()
    r = client.get("/api/v2/mentor/readiness", headers=H).json()["data"]
    assert r["session_count"] == 0
    assert r["confidence"] == "insufficient_data"
