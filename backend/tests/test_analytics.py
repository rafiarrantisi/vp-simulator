"""Pilot analytics — §35 instrumentation (Fase 5)."""
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.domains.analytics.models import ALLOWED_EVENTS, PilotEvent
from app.domains.analytics.service import build_analytics, record_event
from app.main import app

init_db()
client = TestClient(app)


def _new_user():
    email = f"an_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "A"})
    return client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]


def test_allowed_events_whitelist():
    for e in ("session_started", "debrief_opened", "answer_key_revealed", "retry_attempt", "abandoned"):
        assert e in ALLOWED_EVENTS


def test_record_event_and_persist():
    db = SessionLocal()
    try:
        uid = "usr-" + uuid.uuid4().hex[:8]
        rec = record_event(db, uid, "sess-1", "debrief_opened", "result", {"case_id": "em_x"})
        assert rec["event"] == "debrief_opened" and rec["recorded"] is True
        row = db.execute(select(PilotEvent).where(PilotEvent.user_id == uid)).scalar_one()
        assert row.meta.get("case_id") == "em_x"
    finally:
        db.close()


def test_build_analytics_does_not_crash_and_shape():
    db = SessionLocal()
    try:
        a = build_analytics(db)
        assert a["total_users"] >= 0
        assert a["active_users"] >= 0
        assert isinstance(a["events"], dict)
        assert isinstance(a["weakest_dimensions"], list)
        assert isinstance(a["top_specialties"], dict)
        assert "voice_turns" in a and "text_turns" in a
        assert is_float_percentage(a["completion_rate"])
    finally:
        db.close()


def is_float_percentage(v):
    return isinstance(v, (int, float)) and 0 <= v <= 100


def test_events_endpoint_rejects_unknown_event():
    tok = _new_user()
    r = client.post(
        "/api/v2/pilot/events",
        headers={"Authorization": "Bearer " + tok},
        json={"event": "not_a_real_event"},
    )
    assert r.status_code == 422


def test_events_endpoint_accepts_valid_event():
    tok = _new_user()
    r = client.post(
        "/api/v2/pilot/events",
        headers={"Authorization": "Bearer " + tok},
        json={"event": "session_started", "stage": "chat", "session_id": "sess-1",
              "meta": {"mode": "osce", "case_id": "em_x"}},
    )
    assert r.status_code == 200
    assert r.json()["data"]["recorded"] is True