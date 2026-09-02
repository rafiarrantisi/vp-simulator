"""STEP-6 superseding rules 1-2 — live backend wiring + session immutability.

Validates:
  - v3 runtime is wired into the existing HTTP API (reuses sessions table /
    owned / billing / ratelimit — no new DB subsystem).
  - session persistence of family/variant/persona seed/learner/mode/competency/
    schema; reload returns the SAME patient & clinical truth.
  - scoring/debrief use the persisted selected variant (never re-selection).
  - analytics receive the actual live session IDs.
  - immutability: after start, variant/persona/canonical facts frozen; a reload
    after the clinical truth changed → 409 conflict (refuses to resume/score).
"""
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.domains.sessions.models import SessionRow
from app.main import app
from pipeline.case_v3.loader import CaseRegistry

init_db()
client = TestClient(app)


def _new_user():
    email = f"v3_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "V"})
    return client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]


def _auth(tok):
    return {"Authorization": "Bearer " + tok}


def test_v3_families_endpoint_skd2026_metadata():
    tok = _new_user()
    r = client.get("/api/v3/families", headers=_auth(tok))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["competencyStandard"] == "SKD 2026"
    fams = {f["id"]: f for f in data["families"]}
    assert "fam_dengue" in fams
    # competency categories available for filtering/detail (SKD 2026, not 3A/3B/4A)
    assert fams["fam_dengue"]["competencyCategories"]
    assert all(c in ("tuntas", "initial_management_and_referral")
               for c in fams["fam_dengue"]["competencyCategories"])


def test_v3_competency_filter_works():
    tok = _new_user()
    r = client.get("/api/v3/families?competency=tuntas", headers=_auth(tok))
    fams = r.json()["data"]["families"]
    # only families having at least one Tuntas variant
    assert fams and all("tuntas" in f["competencyCategories"] for f in fams)


def test_start_session_persists_runtime_state():
    tok = _new_user()
    r = client.post("/api/v3/sessions", headers=_auth(tok),
                    json={"family_id": "fam_dengue", "learner_level": "koas",
                          "interaction_mode": "targeted", "seed": 3},
                    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["schema"] == "new" and d["variantId"]
    db = SessionLocal()
    try:
        row = db.scalars(select(SessionRow).where(SessionRow.id == d["sessionId"])).one()
        assert row.content_schema == "new"
        assert row.family_id == "fam_dengue"
        assert row.variant_id == d["variantId"]
        assert row.persona_seed is not None
        assert row.persona is not None
        assert row.learner_level == "koas"
        assert row.interaction_mode == "targeted"
        assert row.competency_category in ("tuntas", "initial_management_and_referral")
        assert row.variant_canonical_hash  # frozen fingerprint persisted
    finally:
        db.close()


def test_reload_returns_same_patient_and_truth():
    tok = _new_user()
    start = client.post("/api/v3/sessions", headers=_auth(tok),
                        json={"family_id": "fam_dengue", "learner_level": "koas",
                              "interaction_mode": "targeted", "seed": 3}).json()["data"]
    reg = CaseRegistry.from_dir()
    v = reg.variant(start["variantId"])
    r = client.get(f"/api/v3/sessions/{start['sessionId']}", headers=_auth(tok))
    assert r.status_code == 200
    reloaded = r.json()["data"]
    assert reloaded["variantId"] == start["variantId"]       # same variant
    persona = reloaded["candidateView"]["persona"]
    # same clinical truth (protected) — same patient after refresh
    assert persona["working_diagnosis"] == v.diagnostic.working_diagnosis
    assert persona["vitals"] == [x.to_dict() for x in v.physical_exam.vitals]


def test_scoring_uses_persisted_variant_not_reselection():
    tok = _new_user()
    start = client.post("/api/v3/sessions", headers=_auth(tok),
                        json={"family_id": "fam_dengue", "learner_level": "koas",
                              "interaction_mode": "targeted", "seed": 3}).json()["data"]
    sreq = {
        "collected_items": {"fever_onset": True},
        "stabilized": True, "gave_referral": True,
        "diagnosis_submitted": "Severe dengue",
    }
    r = client.post(f"/api/v3/sessions/{start['sessionId']}/score", headers=_auth(tok), json=sreq)
    assert r.status_code == 200
    report = r.json()["data"]
    assert report["schema"] == "new"
    assert report["variantId"] == start["variantId"]
    assert report["debrief"]["competency_mapping"]["standard"] == "SKD 2026"
    assert "answer_key" in report and report["answer_key"]["sources"]


def test_resume_after_refresh_gives_same_score_session():
    tok = _new_user()
    start = client.post("/api/v3/sessions", headers=_auth(tok),
                        json={"family_id": "fam_hypertension", "learner_level": "koas",
                              "interaction_mode": "targeted", "seed": 1}).json()["data"]
    # reload on a fresh "page view" (like a browser refresh) — same persona
    r1 = client.get(f"/api/v3/sessions/{start['sessionId']}", headers=_auth(tok)).json()["data"]
    r2 = client.get(f"/api/v3/sessions/{start['sessionId']}", headers=_auth(tok)).json()["data"]
    assert r1["candidateView"]["persona"]["name"] == r2["candidateView"]["persona"]["name"]  # same person, no regeneration
    assert r1["variantId"] == r2["variantId"]


def test_immutability_conflict_when_truth_changes():
    # after a session is started, if the canonical clinical truth changes, the
    # persisted hash no longer matches → refuse to resume/score (rule 2 frozen)
    tok = _new_user()
    start = client.post("/api/v3/sessions", headers=_auth(tok),
                        json={"family_id": "fam_dengue", "learner_level": "koas",
                              "interaction_mode": "targeted", "seed": 3}).json()["data"]
    db = SessionLocal()
    try:
        row = db.scalars(select(SessionRow).where(SessionRow.id == start["sessionId"])).one()
        row.variant_canonical_hash = "DIFFERENT-HASH"   # simulate clinical truth drift
        db.commit()
    finally:
        db.close()
    # resume refuses with 409 (immutability violated)
    r = client.get(f"/api/v3/sessions/{start['sessionId']}", headers=_auth(tok))
    assert r.status_code == 409


def test_v3_history_and_state_are_new_schema_only():
    tok = _new_user()
    client.post("/api/v3/sessions", headers=_auth(tok),
                json={"family_id": "fam_uti", "learner_level": "koas", "interaction_mode": "targeted"})
    hist = client.get("/api/v3/sessions", headers=_auth(tok)).json()["data"]
    assert hist["sessions"] and all(s["status"] in ("active", "completed") for s in hist["sessions"])
    state = client.get("/api/v3/state", headers=_auth(tok)).json()["data"]
    assert state["schema"] == "new" and state["variantId"]


# ── Rule 4: eligible count shown, not all files ────────────────────────────

def test_families_reports_eligible_not_raw_count():
    tok = _new_user()
    r = client.get("/api/v3/families?learner_level=koas", headers=_auth(tok))
    fams = {f["id"]: f for f in r.json()["data"]["families"]}
    # preclinical-aware count is smaller than raw file count for dengue
    pre = client.get("/api/v3/families?learner_level=preclinical", headers=_auth(tok)).json()["data"]["families"]
    premap = {f["id"]: f for f in pre}
    assert fams["fam_dengue"]["eligibleVariantCount"] == 3       # koas -> all 3
    assert fams["fam_dengue"]["totalVariantFiles"] == 3
    assert premap["fam_dengue"]["eligibleVariantCount"] < 3        # preclinical -> fewer eligible
    # unreviewed/draft NEVER counted as eligible in released/verified flows
    # (covered by selection-release test below)


def test_families_count_zero_for_released_only_since_none_verified():
    # there's no released_only param on /families; but the underlying selection
    # shows verified-only eligible == 0 (rule 4). Assert selection-level.
    from pipeline.case_v3.loader import CaseRegistry
    from pipeline.case_v3.runtime import SelectionPolicy, SelectionRequest
    pol = SelectionPolicy(CaseRegistry.from_dir())
    assert pol.eligible_count(SelectionRequest(family_id="fam_dengue", released_ids=set())) == 0


# ── Rule 5: another-patient endpoint ───────────────────────────────────────

def test_another_patient_endpoint_returns_different_variant():
    tok = _new_user()
    r = client.post("/api/v3/another-patient", headers=_auth(tok),
                    json={"family_id": "fam_dengue", "current_variant_id": "dengue_001_mild",
                          "learner_level": "koas"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["kind"] == "new_clinical_variant"
    assert d["variant_id"] != "dengue_001_mild"


def test_another_patient_released_only_is_replay():
    tok = _new_user()
    r = client.post("/api/v3/another-patient", headers=_auth(tok),
                    json={"family_id": "fam_dengue", "current_variant_id": "dengue_001_mild",
                          "released_only": True})
    assert r.json()["data"]["kind"] == "replay_persona_variation"


# ── Rule 6: blind start/resume never leak diagnosis in the DTO ─────────────

def test_blind_start_dto_does_not_leak():
    tok = _new_user()
    r = client.post("/api/v3/sessions", headers=_auth(tok),
                    json={"family_id": "fam_dengue", "learner_level": "koas",
                          "interaction_mode": "blind"})
    d = r.json()["data"]
    payload = str(d)
    assert "diagnosis" not in payload or d["candidateView"]["diagnosis_hidden"] is True
    assert "Severe dengue" not in payload and "rubric" not in payload
    cv = d["candidateView"]
    assert cv["mode"] == "blind" and "candidate_brief" in cv


def test_targeted_start_dto_keeps_diagnosis_but_hides_rubric():
    tok = _new_user()
    r = client.post("/api/v3/sessions", headers=_auth(tok),
                    json={"family_id": "fam_dengue", "learner_level": "koas",
                          "interaction_mode": "targeted"})
    payload = str(r.json()["data"])
    assert "answer_key" not in payload and "rubric" not in payload