"""FASE 9 — dashboard backend contract pins (plan §Phase 9).

The reworked QoraDashboard reads ONLY canonical backend output (§3.7, §36).
This test pins every key the new dashboard consumes, in three states:

- new user (no evidence): honest empty values, no invented percentages;
- rich user (V2+V3 mix, safety trigger, OSCE): ranked bars, insight layer,
  readiness, coverage, badges, history — all present and self-consistent;
- mentor journeys: shape the dashboard's continuation card consumes.

Isolation-safe: conftest forces sqlite + stub LLM. No network, no paid calls.
No migration, no generated-file changes.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app

init_db()
client = TestClient(app)

V2_DIMS = {"history_coverage": 80, "red_flags": 70, "diagnostic_reasoning": 75,
           "management": 70, "physical_exam": 60, "communication": 80,
           "ice_fife": 65, "questioning_technique": 70}
V3_DIMS = {"info_gathering": 78, "focus_efficiency": 70, "reasoning_coherence": 72,
           "diagnostic_quality": 75, "investigation_strategy": 68,
           "management_safety": 74, "communication": 80}


def _v2_report(overall=70, dims=None, safety=None):
    dims = V2_DIMS if dims is None else dims
    return {"overall": overall,
            "per_dimension": {k: {"score": v, "max": 100} for k, v in dims.items()},
            "per_item": [], "safety_gates": safety or [], "summary": "ok"}


def _v3_report(overall=70, dims=None, safety=None):
    dims = V3_DIMS if dims is None else dims
    return {"overall": overall, "schema": "new",
            "per_dimension": {k: {"score": v, "max": 100} for k, v in dims.items()},
            "per_item": [], "safety_gates": safety or [], "summary": "ok",
            "variantId": "uti_adult_002", "familyId": "fam_uti"}


def _auth():
    email = f"d9_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "P"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {tok}"}


def _auth_user():
    h = _auth()
    me = client.get("/api/users/me", headers=h).json()["data"]
    return h, me["user_id"]


def _fabricate(db, user_id, case_id, report, mode="anamnesis", schema="legacy",
               family=None, variant=None, days_ago=0):
    from app.domains.sessions.models import SessionRow
    s = SessionRow(user_id=user_id, institution_id="default", case_id=case_id,
                   mode=mode, status="completed", language="en",
                   content_schema=schema, family_id=family, variant_id=variant,
                   total_score=int(report.get("overall", 0) or 0), report=report)
    s.ended_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


class TestDashboardEmptyState:
    def test_new_user_honest_zeros(self):
        h = _auth()
        d = client.get("/api/v2/progress", headers=h).json()["data"]
        assert d["totalSessions"] == 0
        assert d["avgScore"] == 0
        assert d["hasEvidence"] is False
        assert d["sessions"] == []
        assert d["strongestSkill"] is None and d["weakestSkill"] is None
        assert d["coverage"]["distinctCases"] == 0
        assert d["dataSource"]["sessionsIncluded"] == 0
        r = d["readiness"]
        assert r["confidence"] == "insufficient_data" and r["score"] == 0
        # XP/streak stay profile-authoritative (never invented).
        assert d["xp"] == 0 and d["streak"] == 0

    def test_new_user_mentor_empty(self):
        h = _auth()
        r = client.get("/api/v2/mentor/readiness", headers=h).json()["data"]
        assert r["confidence"] == "insufficient_data"
        j = client.get("/api/v2/mentor/journeys", headers=h).json()["data"]
        assert j["journeys"] == []


class TestDashboardRichState:
    def _rich(self):
        h, uid = _auth_user()
        db = SessionLocal()
        try:
            _fabricate(db, uid, "im_uta_001", _v2_report(70), mode="osce_full")
            _fabricate(db, uid, "em_pulmonary_embolism_001", _v2_report(80))
            _fabricate(db, uid, "fam_uti", _v3_report(75), mode="targeted",
                       schema="new", family="fam_uti", variant="uti_adult_002")
        finally:
            db.close()
        return h

    def test_canonical_numbers(self):
        h = self._rich()
        d = client.get("/api/v2/progress", headers=h).json()["data"]
        assert d["totalSessions"] == 3
        assert d["avgScore"] == 75.0
        assert len(d["sessions"]) == 3
        # ranked bars: weakest-first data present with evidence counts
        assert d["weakestSkill"] and d["strongestSkill"]
        assert d["dimensionDetail"][d["weakestSkill"]]["n"] >= 2
        # insight layer reads the same readiness object as Mentor
        assert d["readiness"] is not None
        assert d["readiness"]["drivers"] and d["readiness"]["evidence"]["sessions"] == 3
        # coverage counts (explicit, never called mastery)
        assert d["coverage"]["distinctCases"] == 3
        assert "v3_compat" in d["dataSource"]["engines"]
        assert d["dataSource"]["sessionsIncluded"] == 3
        # achievements inputs present; earned shape has GDV-mappable ids
        assert d["badgeMetrics"]["sessions"] == 3
        assert all({"id", "name", "earned", "progress"} <= set(b) for b in d["badges"])

    def test_cross_product_parity(self):
        h = self._rich()
        d = client.get("/api/v2/progress", headers=h).json()["data"]["readiness"]
        r = client.get("/api/v2/mentor/readiness", headers=h).json()["data"]
        assert d["score"] == r["score"] and d["confidence"] == r["confidence"]

    def test_sessions_history_shape(self):
        h = self._rich()
        s = client.get("/api/v2/sessions?limit=5", headers=h).json()["data"]["sessions"]
        assert len(s) == 3
        assert all({"sessionId", "caseId", "mode", "status", "score"} <= set(x) for x in s)
        # V3-backed rows resolve family metadata (never raw fam_* blanks)
        v3 = [x for x in s if x["caseId"] == "fam_uti"][0]
        assert v3["specialty"] and v3["presentation"]

    def test_journey_continuation_shape(self):
        h, _ = _auth_user()
        r = client.post("/api/v2/mentor/story", json={"story": "OSCE in 7 days, beginner"},
                        headers=h).json()["data"]
        jid = r["id"]
        client.post(f"/api/v2/mentor/journeys/{jid}/accept", headers=h)
        ds = client.get("/api/v2/mentor/journeys", headers=h).json()["data"]["journeys"]
        active = [j for j in ds if j["status"] == "active"]
        assert active
        j = active[0]
        assert {"package_name", "status", "current_day", "progress", "readiness"} <= set(j)
        assert {"completed", "total", "percent"} <= set(j["progress"])
