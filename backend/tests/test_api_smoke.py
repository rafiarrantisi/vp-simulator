"""Smoke test alur API Fase 2 (kontrak §6) via TestClient.

Menguji: health · signup → login · users/me · cases (hasil ingest) ·
session start+turn+patch · scoring/evaluate shape · ai stub 501.
DB = sqlite (file dev), dibuat init_db saat startup.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_full_flow():
    assert client.get("/health").json()["data"]["status"] == "up"

    su = client.post("/api/auth/signup", json={
        "email": "smoke@uni.ac.id", "password": "secret12", "full_name": "Smoke",
    })
    # signup boleh 200 (baru) atau 409 (sudah ada dari run sebelumnya)
    assert su.status_code in (200, 409)

    lg = client.post("/api/auth/login", json={
        "email": "smoke@uni.ac.id", "password": "secret12",
    }).json()
    assert lg["success"] is True
    token = lg["data"]["token"]
    H = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/users/me", headers=H).json()
    assert me["data"]["email"] == "smoke@uni.ac.id"
    assert me["data"]["role"] == "student"

    cases = client.get("/api/v2/cases", headers=H).json()  # v2 catalogue (content/cases) — legacy registry is empty post-pivot
    assert cases["success"] is True
    assert cases["data"]["total"] >= 1
    c0 = cases["data"]["cases"][0]
    for k in ("id", "specialty", "presentation", "difficulty"):
        assert k in c0
    assert "anamnesis_checklist" not in c0  # Part A TIDAK bocor ke katalog
    assert "target_condition" not in c0

    st = client.post("/api/v2/sessions", json={"case_id": c0["id"]}, headers=H).json()
    sid = st["data"]["sessionId"]

    turn = client.post(f"/api/v2/sessions/{sid}/turns", json={"text": "Selamat pagi"},
                        headers=H).json()
    assert turn["success"] is True
    assert turn["data"]["reply"]

    ev = client.post(f"/api/v2/sessions/{sid}/score", json={"mode": "practice"}, headers=H).json()
    d = ev["data"]
    assert "per_dimension" in d and "overall" in d and "answer_key" in d
    assert d["weights"]["history_coverage"] == 25  # anamnesis rubric intact

    # Fase 4: /api/ai/transcribe kini WAJIB auth (bukan lagi stub 501).
    assert client.post("/api/ai/transcribe").status_code == 401

    # endpoint tanpa token harus 401
    assert client.get("/api/users/me").status_code == 401
