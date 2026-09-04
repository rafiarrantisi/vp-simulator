"""FASE 10 — Adaptive Mentor V1 acceptance (local mirror of the STOP gate).

Isolated sqlite + stub LLM, no migration, no generated-file changes.
E2E: "Internal Medicine OSCE in 7 days, beginner" → goal → plan →
mission → session UX → judge ingest → remediation → variant novelty →
readiness → final report.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app

init_db()
client = TestClient(app)


def _auth():
    email = f"m10_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "M10"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {tok}"}


def _uid(H):
    return client.get("/api/users/me", headers=H).json()["data"]["user_id"]


def _report_for(overall, safety=False, **dim_pcts):
    per_dim = {k: {"score": v, "max": 100, "feedback": ""} for k, v in dim_pcts.items()}
    gates = [{"type": "missed_critical_red_flag", "detail": "x"}] if safety else []
    return {"overall": overall, "per_item": [], "per_dimension": per_dim,
            "safety_gates": gates}


def _fabricate_session(db, user_id, case_id, report, family_id=None, variant_id=None, days_ago=0):
    from app.domains.sessions.models import SessionRow
    s = SessionRow(user_id=user_id, institution_id="default", case_id=case_id,
                   mode="osce", status="completed", language="en",
                   content_schema="new" if family_id else "legacy",
                   family_id=family_id, variant_id=variant_id,
                   total_score=int(report.get("overall", 0) or 0), report=report)
    s.ended_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    s.started_at = s.ended_at
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


V2D = {"history_coverage": 80, "red_flags": 70, "diagnostic_reasoning": 75,
       "management": 70, "physical_exam": 60, "communication": 80,
       "ice_fife": 65, "questioning_technique": 70}


def test_goal_extraction_and_minimal_clarification():
    from app.domains.mentor.journey_builder import extract_context, needs_clarification
    ctx = extract_context("Internal Medicine OSCE in 7 days; I am a beginner.")
    assert ctx["timeline_days"] == 7
    assert ctx["goal"] == "osce"
    assert ctx["target_specialty"] == "internal_medicine"
    assert "internal_medicine" in ctx["weaknesses"]
    assert ctx["confidence_score"] <= 20
    assert ctx["available_minutes_per_day"] == 45
    assert needs_clarification(ctx) == []
    vague = {"level": "general", "timeline_days": None, "goal": None,
             "target_specialty": None, "weaknesses": []}
    assert 1 <= len(needs_clarification(vague)) <= 2
    ctx2 = extract_context("OSCE penyakit dalam 7 hari, bisa 2 jam sehari")
    assert ctx2["available_minutes_per_day"] == 120


def test_planning_policy_gates():
    from app.domains.mentor import planning_policy as pp
    from app.domains.sessions.v3_compat_schemas import default_registry
    reg = default_registry()
    ids = {f.id for f in pp.eligible_v3_families(reg, "koas")}
    assert "fam_hypertension" not in ids and "fam_dengue" in ids
    cands = [{"kind": "v3_family", "ref": "fam_x", "specialty": "internal_medicine",
              "difficulty": 9, "mode": "osce_full", "review_rank": -1,
              "title": "X", "presentation": "X", "estimated_minutes": 15}]
    ctx = {"level": "koas", "target_specialty": "internal_medicine",
           "weaknesses": ["internal_medicine"]}
    a = pp.rank_candidates(cands, ctx, day=1, duration_days=7)
    b = pp.rank_candidates(cands, ctx, day=1, duration_days=7)
    assert [c["ref"] for c in a] == [c["ref"] for c in b]


def test_multiday_plan_shape():
    from app.domains.cases.v2_catalog import list_v2_cases
    from app.domains.mentor.case_selector import select_journey_cases
    ctx = {"timeline_days": 7, "level": "koas", "goal": "osce",
           "target_specialty": "internal_medicine", "weaknesses": ["internal_medicine"],
           "available_minutes_per_day": 45}
    sel = select_journey_cases(ctx, list(list_v2_cases()))
    assert len(sel) == 7
    assert all(c["slot_type"] == "core" for c in sel)
    assert all(c.get("selection_reason") for c in sel)
    assert sel[0]["specialty"] == "internal_medicine"
    assert sel[-1]["mode"] == "osce_full"
    assert all(c["estimated_minutes"] == 45 for c in sel)


def test_e2e_mission_and_server_ingest():
    H = _auth()
    uid = _uid(H)
    r = client.post("/api/v2/mentor/story",
                    json={"story": "Internal Medicine OSCE in 7 days; I am a beginner."},
                    headers=H).json()
    assert r["success"], r
    assert len(r["data"]["cases"]) == 7
    assert r["data"]["cases"][0].get("selection_reason")
    assert r["data"]["cases"][0].get("slot_type") == "core"
    jid = r["data"]["id"]
    client.post(f"/api/v2/mentor/journeys/{jid}/accept", headers=H)
    m = client.get(f"/api/v2/mentor/journeys/{jid}/mission", headers=H).json()["data"]
    assert m["state"] == "ready"
    assert m["expected_minutes"] >= 20 and m["encounters"] == 1
    assert m["why"] and m["cta"] and m["cta"]["case_id"]
    first = m["cta"]
    db = SessionLocal()
    try:
        s = _fabricate_session(db, uid, first["case_id"], _report_for(72, **V2D))
        sid = s.id
    finally:
        db.close()
    d = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": first["case_id"], "session_id": sid, "score": 5},
                    headers=H).json()["data"]
    assert d["ingested"]["score"] == 72
    assert d["ingested"]["score_source"] == "server"
    assert d["readiness"]["current"] != 5


def test_ingest_rejects_incomplete_session():
    H = _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    client.post(f"/api/v2/mentor/journeys/{jid}/accept", headers=H)
    nxt = client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H).json()["data"]["case"]
    sid = client.post("/api/v2/sessions", json={"case_id": nxt["case_id"]},
                      headers=H).json()["data"]["sessionId"]
    r = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": nxt["case_id"], "session_id": sid, "score": 90}, headers=H)
    assert r.status_code == 409


def test_safety_miss_mandatory_remediation():
    H = _auth()
    uid = _uid(H)
    jid = client.post("/api/v2/mentor/story",
                      json={"story": "Internal Medicine OSCE in 7 days; I am a beginner."},
                      headers=H).json()["data"]["id"]
    client.post(f"/api/v2/mentor/journeys/{jid}/accept", headers=H)
    first = client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H).json()["data"]["case"]
    db = SessionLocal()
    try:
        s = _fabricate_session(db, uid, first["case_id"], _report_for(80, True, **V2D))
        sid = s.id
    finally:
        db.close()
    d = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": first["case_id"], "session_id": sid, "score": 80},
                    headers=H).json()["data"]
    assert d["ingested"]["safety_triggered"] is True
    assert d["adaptation"]["action"] == "remediate"
    assert d["adaptation"]["slot_kind"] == "remediation"
    assert d["adaptation"]["mandatory"] is True
    slots = d["adaptation"]["slots"]
    assert len(slots) == 1 and slots[0]["day"] == first["day"] + 1
    assert d["coach_insight"]["safety_flag"] is True
    assert "safety" in d["coach_insight"]["headline"].lower()
    detail = client.get(f"/api/v2/mentor/journeys/{jid}", headers=H).json()["data"]
    assert any(c.get("slot_type") == "remediation" for c in detail["cases"])


def test_poor_score_reinforce_and_rebalance():
    H = _auth()
    uid = _uid(H)
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    client.post(f"/api/v2/mentor/journeys/{jid}/accept", headers=H)
    first = client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H).json()["data"]["case"]
    db = SessionLocal()
    try:
        s = _fabricate_session(db, uid, first["case_id"], _report_for(45, **V2D))
        sid = s.id
    finally:
        db.close()
    d = client.post(f"/api/v2/mentor/journeys/{jid}/complete-case",
                    json={"case_id": first["case_id"], "session_id": sid, "score": 45},
                    headers=H).json()["data"]
    assert d["adaptation"]["action"] == "reinforce"
    before = {c["case_id"]: c["day"] for c in d["cases"] if c["status"] != "completed"}
    rb = client.post(f"/api/v2/mentor/journeys/{jid}/rebalance",
                     json={"missed_days": 2}, headers=H).json()["data"]
    after = {c["case_id"]: c["day"] for c in rb["cases"] if c["status"] != "completed"}
    assert set(after) == set(before)
    assert all(after[k] == before[k] + 2 for k in after)


def test_repeat_variant_novelty():
    H = _auth()
    db = SessionLocal()
    try:
        from app.domains.sessions.models import SessionRow
        s1 = client.post("/api/v2/sessions", json={"case_id": "fam_dengue"}, headers=H).json()["data"]["sessionId"]
        v1 = db.get(SessionRow, s1).variant_id
        s2 = client.post("/api/v2/sessions", json={"case_id": "fam_dengue"}, headers=H).json()["data"]["sessionId"]
        v2 = db.get(SessionRow, s2).variant_id
        assert v1 != v2
    finally:
        db.close()


def test_report_and_recap():
    H = _auth()
    uid = _uid(H)
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    rep = client.get(f"/api/v2/mentor/journeys/{jid}/report", headers=H).json()["data"]
    assert rep["verdict"] in ("completed", "ready") and rep["verdict"] == "completed"
    assert rep["note"] and rep["next_recommendation"]
    assert rep["evidence"]["sessions"] == 0
    db = SessionLocal()
    try:
        _fabricate_session(db, uid, "c1", _report_for(50, **V2D))
    finally:
        db.close()
    recap = client.get(f"/api/v2/mentor/journeys/{jid}/recap", headers=H).json()["data"]
    assert "next_focus" in recap and "cases_completed" in recap


def test_no_schema_change_and_legacy_stable():
    import glob as _glob
    from pathlib import Path
    versions = Path(__file__).parent.parent / "alembic" / "versions"
    assert len(_glob.glob(str(versions / "*.py"))) == 10
    from app.domains.mentor.models import JourneyCase, LearningJourney  # noqa
    assert not hasattr(JourneyCase, "mission")
    assert not hasattr(JourneyCase, "slot_type")
    H = _auth()
    jid = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"},
                      headers=H).json()["data"]["id"]
    d = client.get(f"/api/v2/mentor/journeys/{jid}", headers=H).json()["data"]
    assert {"id", "status", "progress", "cases", "readiness"} <= set(d)
    r = client.get(f"/api/v2/mentor/journeys/{jid}/next-case", headers=H)
    assert r.status_code in (200, 409)
