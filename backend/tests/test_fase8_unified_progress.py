"""FASE 8 — unified progress / readiness acceptance matrix.

Covers the user-required scenarios (all isolated sqlite + stub LLM):
- V2-only history, V3-only history, mixed V2/V3 history
- new user (honest empty state, no fake numbers)
- one excellent session (Building, never Ready, capped)
- many mediocre sessions (stable borderline, real confidence)
- high performance with safety fail (capped + safety driver)
- Practice-only user (OSCE cap, no_osce driver)
- OSCE-heavy user (no OSCE cap, real estimate)
- inactive/stale user (recency decay + confidence downgrade)

Plus adapter guarantees: engine labels, raw never rewritten, V3 dims fold
to core, safety + OSCE flags, and V3 score-path progress parity.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app

init_db()
client = TestClient(app)

V2_DIMS = {
    "history_coverage": 80, "red_flags": 70, "diagnostic_reasoning": 75,
    "management": 70, "physical_exam": 60, "communication": 80,
    "ice_fife": 65, "questioning_technique": 70,
}
V3_DIMS = {
    "info_gathering": 78, "focus_efficiency": 70, "reasoning_coherence": 72,
    "diagnostic_quality": 75, "investigation_strategy": 68,
    "management_safety": 74, "communication": 80,
}


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


def _norm(overall=70, dims=None, engine="v2", safety=False, osce=False,
          days_ago=0, case_id="case_x"):
    from pipeline.progress.longitudinal import adapt_report
    if dims is None:
        dims = dict(V3_DIMS) if engine != "v2" else dict(V2_DIMS)
    else:
        dims = dict(dims)
    schema = "new" if engine != "v2" else "legacy"
    raw = {"overall": overall,
           "per_dimension": {k: {"score": v, "max": 100} for k, v in dims.items()},
           "per_item": [],
           "safety_gates": ([{"type": "missed_emergency_red_flag", "detail": "x"}]
                             if safety else [])}
    ns = adapt_report(raw, content_schema=schema)
    d = ns.to_dict()
    d["session_id"] = f"s-{uuid.uuid4().hex[:6]}"
    d["case_id"] = case_id
    d["engine"] = engine
    d["overall_0_100"] = overall
    d["is_osce"] = osce
    d["completed_at"] = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return d


def _auth():
    email = f"f8_{uuid.uuid4().hex[:8]}@t.co"
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


# ── adapter ──────────────────────────────────────────────────────────────
class TestHistoricalAdapter:
    def test_v2_v3_native_engines_labeled(self):
        from pipeline.progress.longitudinal import adapt_report
        assert adapt_report(_v2_report(), content_schema="legacy").engine == "v2"
        assert adapt_report(_v3_report(), content_schema="new").engine == "v3_compat"

    def test_adapter_never_rewrites_raw(self):
        import copy
        from pipeline.progress.longitudinal import adapt_report
        raw = _v3_report()
        snap = copy.deepcopy(raw)
        adapt_report(raw, content_schema="new")
        assert raw == snap

    def test_v3_dims_fold_to_core(self):
        from pipeline.progress.longitudinal import adapt_report
        ns = adapt_report(_v3_report(), content_schema="new")
        assert "management_non_pharma" in ns.core_pcts

    def test_safety_and_osce_flags(self):
        from pipeline.progress.longitudinal import adapt_session
        ns = adapt_session({"id": "s1", "case_id": "c", "mode": "osce_full",
                            "content_schema": "legacy",
                            "report": _v2_report(90, safety=[{"type": "unsafe_management",
                                                             "detail": "discharged unstable"}]),
                            "ended_at": datetime.now(timezone.utc).isoformat()})
        assert ns.safety_triggered
        assert ns.is_osce
        row2 = {"id": "s2", "case_id": "c", "mode": "anamnesis",
                "content_schema": "legacy", "report": _v2_report(70),
                "ended_at": datetime.now(timezone.utc).isoformat()}
        assert not adapt_session(row2).is_osce


# ── progress ─────────────────────────────────────────────────────────────
class TestProgress:
    def test_empty_history_is_honest(self):
        from pipeline.progress.progress import compute_progress
        p = compute_progress([])
        assert not p["hasEvidence"]
        assert p["totalSessions"] == 0 and p["avgScore"] == 0
        assert p["strongestSkill"] is None and p["weakestSkill"] is None
        assert "completed sessions with a stored report" in p["definitions"]["total_sessions"]

    def test_mixed_v2_v3_counts(self):
        from pipeline.progress.progress import compute_progress
        sess = [_norm(70, engine="v2", case_id="c1"),
                _norm(80, engine="v3_compat", case_id="fam_uti"),
                _norm(60, engine="v3_compat", case_id="fam_dengue")]
        p = compute_progress(sess)
        assert p["totalSessions"] == 3
        assert p["avgScore"] == 70.0
        assert p["coverage"]["distinctCases"] == 3
        assert p["badgeMetrics"]["sessions"] == 3
        assert len(p["sessions"]) == 3

    def test_skill_needs_min_evidence(self):
        from pipeline.progress.progress import compute_progress
        p = compute_progress([_norm(95, engine="v2")])
        assert p["strongestSkill"] is None
        assert all(v["low_evidence"] for v in p["dimensionDetail"].values())

    def test_apply_progress_parity_v2_v3(self):
        from pipeline.progress.progress import apply_progress_for_session
        e1, s1 = apply_progress_for_session({}, {"xp": 0, "streak": 0, "total_sessions": 0},
                                            case_id="c_v2", specialty="internal_medicine",
                                            overall=70, dim_pcts=dict(V2_DIMS))
        e2, s2 = apply_progress_for_session({}, {"xp": 0, "streak": 0, "total_sessions": 0},
                                            case_id="fam_uti", specialty="urology",
                                            overall=70, dim_pcts=dict(V3_DIMS))
        assert s1["xp"] == s2["xp"] and s1["total_sessions"] == s2["total_sessions"] == 1
        assert e1["scoreHistory"][0]["overall"] == e2["scoreHistory"][0]["overall"] == 70


# ── readiness ────────────────────────────────────────────────────────────
class TestReadiness:
    def test_no_sessions_insufficient(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([])
        assert r["score"] == 0 and r["confidence"] == "insufficient_data"
        assert r["interpretation"] is None

    def test_one_session_building_never_ready(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([_norm(95, engine="v2", osce=True)])
        assert r["confidence"] == "low" and r["state"] == "Building"
        assert r["score"] <= 59
        assert any(d["factor"] == "evidence" for d in r["drivers"])

    def test_many_mediocre_stable(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([_norm(65, engine="v2", osce=True) for _ in range(6)])
        assert r["session_count"] == 6
        assert r["confidence"] in ("medium", "high")
        assert r["score"] < 75  # mediocre must not read as exam-ready

    def test_safety_failure_caps_high_scorer(self):
        from pipeline.progress.readiness import compute_readiness
        base = [_norm(90, engine="v2", osce=True) for _ in range(5)]
        bad = _norm(90, engine="v2", osce=True, safety=True)
        r = compute_readiness(base + [bad])
        assert r["score"] <= 59
        assert r["components"]["safety_capped"]
        assert any(d["factor"] == "safety" for d in r["drivers"])

    def test_many_practice_no_osce_capped(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([_norm(88, engine="v2", osce=False) for _ in range(8)])
        assert r["score"] <= 74
        assert r["evidence"]["osce_sessions"] == 0
        assert any(d["factor"] == "osce" for d in r["drivers"])

    def test_osce_heavy_no_cap(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([_norm(80, engine="v2", osce=True) for _ in range(6)])
        assert r["evidence"]["osce_sessions"] == 6
        assert not any(d["factor"] == "osce" for d in r["drivers"])

    def test_stale_user_loses_recency_and_confidence(self):
        from pipeline.progress.readiness import compute_readiness
        fresh = [_norm(85, engine="v2", osce=True, days_ago=0) for _ in range(5)]
        stale = [_norm(85, engine="v2", osce=True, days_ago=90) for _ in range(5)]
        rf = compute_readiness(fresh)["components"]["recency_factor"]
        rs = compute_readiness(stale)["components"]["recency_factor"]
        assert rs < rf and compute_readiness(stale)["components"]["stale"]
        assert compute_readiness(stale)["confidence"] != "high"
        assert any(d["factor"] == "recency" for d in compute_readiness(stale)["drivers"])

    def test_v2_only_matches_legacy_band(self):
        from pipeline.progress.readiness import compute_readiness
        sessions = [_norm(70, engine="v2", osce=True) for _ in range(5)]
        r = compute_readiness(sessions)
        assert 70 <= r["score"] <= 75
        assert r["confidence"] == "medium" and r["session_count"] == 5

    def test_v3_only_gets_real_estimate(self):
        from pipeline.progress.readiness import compute_readiness
        sessions = [_norm(74, engine="v3_compat", osce=True) for _ in range(5)]
        r = compute_readiness(sessions)
        assert r["score"] >= 60
        assert r["components"]["proficiency"] >= 50

    def test_explainability_present(self):
        from pipeline.progress.readiness import compute_readiness
        r = compute_readiness([_norm(70, engine="v2", osce=True) for _ in range(4)])
        assert r["version"].startswith("qora-readiness-")
        assert r["drivers"] and r["evidence"]["sessions"] == 4
        assert r["interpretation"]["level"]


# ── endpoints ────────────────────────────────────────────────────────────
class TestUnifiedEndpoints:
    def test_progress_includes_v2_and_v3(self):
        h, uid = _auth_user()
        db = SessionLocal()
        try:
            _fabricate(db, uid, "im_uta_001", _v2_report(70))
            _fabricate(db, uid, "em_pulmonary_embolism_001", _v2_report(80))
            _fabricate(db, uid, "fam_uti", _v3_report(75), mode="targeted",
                       schema="new", family="fam_uti", variant="uti_adult_002")
        finally:
            db.close()
        d = client.get("/api/v2/progress", headers=h).json()["data"]
        assert d["totalSessions"] == 3
        assert d["avgScore"] == 75.0
        assert len(d["sessions"]) == 3
        assert "v3_compat" in d["dataSource"]["engines"]
        assert d["dataSource"]["sessionsIncluded"] == 3
        assert d["readiness"] is not None
        assert d["coverage"]["distinctCases"] == 3

    def test_cross_product_consistency(self):
        h, uid = _auth_user()
        db = SessionLocal()
        try:
            for i in range(4):
                _fabricate(db, uid, f"case_{i}", _v2_report(70))
        finally:
            db.close()
        d = client.get("/api/v2/progress", headers=h).json()["data"]["readiness"]
        r = client.get("/api/v2/mentor/readiness", headers=h).json()["data"]
        assert d["score"] == r["score"]
        assert d["confidence"] == r["confidence"]

    def test_new_user_honest_empty_state(self):
        h = _auth()
        d = client.get("/api/v2/progress", headers=h).json()["data"]
        assert d["totalSessions"] == 0 and d["avgScore"] == 0
        r = client.get("/api/v2/mentor/readiness", headers=h).json()["data"]
        assert r["confidence"] == "insufficient_data" and r["score"] == 0

    def test_v3_lifecycle_awards_progress(self):
        h = _auth()
        r = client.post("/api/v2/sessions", json={"case_id": "fam_dengue"}, headers=h)
        assert r.status_code == 200, r.text
        sid = r.json()["data"]["sessionId"]
        sc = client.post(f"/api/v2/sessions/{sid}/score",
                         json={"ddx": {"primary": "dengue"}, "mode": "osce",
                               "management": {"complete": True}}, headers=h)
        assert sc.status_code == 200, sc.text
        d = client.get("/api/v2/progress", headers=h).json()["data"]
        assert d["totalSessions"] == 1
        assert len(d["sessions"]) == 1
        assert d["sessions"][0]["caseId"] == "fam_dengue"
