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
    assert "target_condition" not in r["data"]
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


def test_v2_score_is_idempotent(monkeypatch):
    from app.rag.llm import StubLlmClient
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: StubLlmClient())
    monkeypatch.setattr("app.rag.judge_v2.is_stub", lambda: True)
    H = _auth()
    sid = client.post("/api/v2/sessions", json={"case_id": "oph_dry_eye_001"}, headers=H).json()["data"]["sessionId"]
    first = client.post(f"/api/v2/sessions/{sid}/score", json={}, headers=H).json()["data"]
    p1 = client.get("/api/v2/progress", headers=H).json()["data"]
    second = client.post(f"/api/v2/sessions/{sid}/score", json={"overtime": True}, headers=H).json()["data"]
    p2 = client.get("/api/v2/progress", headers=H).json()["data"]
    assert second == first
    assert p2["totalSessions"] == p1["totalSessions"]
    assert p2["xp"] == p1["xp"]


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


# ── Physical-exam (PF) step (Aug 2026) ──
def test_v2_pf_reveals_only_examined_areas():
    from app.domains.sessions.v2_router import parse_pf_findings
    from app.domains.cases.v2_catalog import load_v2_case

    case = load_v2_case("em_dengue_001")
    findings = parse_pf_findings(case)
    assert "general" in findings and "skin" in findings and "abdomen" in findings
    assert "chest" in findings  # dengue case has chest findings

    H = _auth()
    sid = client.post("/api/v2/sessions", json={"case_id": "em_dengue_001"}, headers=H).json()["data"]["sessionId"]
    # Examine ONLY skin + abdomen -> those are revealed, chest is NOT
    r = client.post(f"/api/v2/sessions/{sid}/pf",
                    json={"notes": "I check the skin for rash and palpate the abdomen.", "areas": ["skin", "abdomen"]},
                    headers=H).json()["data"]
    assert set(r["examined"]) == {"skin", "abdomen"}
    assert "skin" in r["findings"] and "abdomen" in r["findings"]
    assert "chest" not in r["findings"]  # isolation rule: unexamined area stays hidden
    assert "general" in r["available_areas"]


def test_v2_pf_unknown_areas_ignored_and_404_case():
    H = _auth()
    assert client.post("/api/v2/sessions/nope_999/pf", json={"areas": ["skin"]}, headers=H).status_code == 404


def test_v2_score_accepts_pf_fields_and_rubric_has_physical_exam(monkeypatch):
    from app.rag.llm import StubLlmClient
    from app.domains.scoring.rubric_v2 import RUBRICS
    assert "physical_exam" in RUBRICS["osce_full"]
    assert sum(RUBRICS["osce_full"].values()) == 100

    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: StubLlmClient())
    monkeypatch.setattr("app.rag.judge_v2.is_stub", lambda: True)
    H = _auth()
    sid = client.post("/api/v2/sessions", json={"case_id": "em_dengue_001"}, headers=H).json()["data"]["sessionId"]
    sc = client.post(f"/api/v2/sessions/{sid}/score",
                     json={"mode": "osce", "pf_notes": "Rash on arms, tender abdomen.", "pf_areas": ["skin", "abdomen"]},
                     headers=H).json()
    d = sc["data"]
    assert d["mode"] == "osce_full"
    assert "physical_exam" in d["weights"]
    assert d["weights"]["physical_exam"] == 10
    assert "answer_key" in d


def test_v2_get_turns_restores_session(monkeypatch):
    from app.rag.llm import StubLlmClient
    monkeypatch.setattr("app.rag.engine_v2.get_llm_client", lambda: StubLlmClient())
    H = _auth()
    sid = client.post("/api/v2/sessions", json={"case_id": "em_dengue_001", "language": "id"}, headers=H).json()["data"]["sessionId"]
    client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "Selamat pagi"}, headers=H)
    r = client.get(f"/api/v2/sessions/{sid}/turns", headers=H).json()["data"]
    assert r["case_id"] == "em_dengue_001" and r["language"] == "id"
    roles = [t["role"] for t in r["turns"]]
    assert "user" in roles and "patient" in roles
    assert r["opening_line"]
