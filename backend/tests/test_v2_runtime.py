"""v2 runtime: catalogue, session lifecycle, patient engine, scoring+answer-key."""
import uuid

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app

init_db()
client = TestClient(app)


def _auth() -> dict:
    email = f"v2_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "V"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {tok}"}


def test_v2_cases_requires_auth():
    assert client.get("/api/v2/cases").status_code == 401


def test_v2_cases_listed_without_part_a_leakage():
    r = client.get("/api/v2/cases", headers=_auth()).json()
    assert r["success"]
    ids = {c["id"] for c in r["data"]["cases"]}
    assert "oph_dry_eye_001" in ids and "im_gi_appendicitis_001" in ids
    assert r["data"]["total"] >= 10
    assert "ophthalmology" in r["data"]["specialties"]
    c0 = r["data"]["cases"][0]
    assert "anamnesis_checklist" not in c0 and "red_flags" not in c0  # no Part A


def test_v2_cases_filter_specialty():
    r = client.get("/api/v2/cases?specialty=internal_medicine", headers=_auth()).json()
    cases = r["data"]["cases"]
    assert cases and all(c["specialty"] == "internal_medicine" for c in cases)


def test_v2_case_detail_and_404():
    H = _auth()
    r = client.get("/api/v2/cases/oph_dry_eye_001", headers=H).json()
    assert r["data"]["target_condition"].lower().startswith("dry eye")
    assert client.get("/api/v2/cases/nope_999", headers=H).status_code == 404


def test_v2_session_start_returns_opening_line():
    H = _auth()
    r = client.post("/api/v2/sessions", json={"case_id": "oph_dry_eye_001"}, headers=H).json()
    assert r["data"]["sessionId"]
    assert "uncomfortable" in r["data"]["openingLine"].lower()
    assert client.post("/api/v2/sessions", json={"case_id": "nope_999"}, headers=H).status_code == 404


def test_v2_turn_and_score_with_stub(monkeypatch):
    from app.rag.llm import StubLlmClient
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: StubLlmClient())
    monkeypatch.setattr("app.rag.judge_v2.is_stub", lambda: True)
    H = _auth()
    sid = client.post("/api/v2/sessions", json={"case_id": "oph_dry_eye_001"}, headers=H).json()["data"]["sessionId"]
    t = client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "Hi, what brings you in?"}, headers=H).json()
    assert t["data"]["reply"]
    sc = client.post(f"/api/v2/sessions/{sid}/score", json={}, headers=H).json()
    d = sc["data"]
    assert d["mode"] == "anamnesis" and "answer_key" in d
    assert d["answer_key"]["expected_ddx"]["working_diagnosis"].lower().startswith("dry eye")
    assert d["answer_key"]["red_flags"]  # model answer present for the reveal


def test_v2_case_media_requires_auth():
    assert client.get("/api/v2/cases/im_gi_appendicitis_001/media").status_code == 401


def test_v2_case_media_returns_typed_items():
    H = _auth()
    r = client.get("/api/v2/cases/im_gi_appendicitis_001/media", headers=H).json()
    assert r["success"]
    media = r["data"]["media"]
    assert len(media) == 2  # abdominal exam + ultrasound
    kinds = {m["type"] for m in media}
    assert "image" in kinds and "ultrasound" in kinds
    for m in media:
        assert m["src"] and m["label"] and m["caption"]  # viewer needs these
    assert "working_diagnosis" not in str(r["data"])  # no Part A leakage


def test_v2_case_media_empty_when_none():
    r = client.get("/api/v2/cases/oph_dry_eye_001/media", headers=_auth()).json()
    assert r["success"] and r["data"]["media"] == []


def test_v2_case_media_404():
    assert client.get("/api/v2/cases/nope_999/media", headers=_auth()).status_code == 404


def test_v2_progress_requires_auth():
    assert client.get("/api/v2/progress").status_code == 401


def test_v2_progress_records_after_score(monkeypatch):
    from app.rag.llm import StubLlmClient
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: StubLlmClient())
    monkeypatch.setattr("app.rag.judge_v2.is_stub", lambda: True)
    H = _auth()
    p0 = client.get("/api/v2/progress", headers=H).json()["data"]
    sid = client.post("/api/v2/sessions", json={"case_id": "oph_dry_eye_001"}, headers=H).json()["data"]["sessionId"]
    client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "Hi"}, headers=H)
    client.post(f"/api/v2/sessions/{sid}/score", json={}, headers=H)
    p1 = client.get("/api/v2/progress", headers=H).json()["data"]
    assert p1["totalSessions"] == p0["totalSessions"] + 1
    assert p1["completedCases"] >= 1
    assert p1["specialtyCounts"].get("ophthalmology", 0) >= 1
    assert "really uncomfortable" not in str(p1)  # no persona leakage into progress
