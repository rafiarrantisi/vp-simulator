"""Billing: plans, gating, metering, cost guardrail, MoR webhook (pivot-v4 §7)."""
import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.database import SessionLocal, init_db
from app.domains.auth.models import User, UserProfile
from app.domains.billing import lemonsqueezy as ls
from app.domains.billing import plans, service
from app.domains.billing.models import Entitlement
from app.main import app

init_db()  # ensure billing tables exist in the dev sqlite db (idempotent create_all)
client = TestClient(app)


def _mk_user(db) -> User:
    u = User(email=f"bill_{uuid.uuid4().hex[:8]}@t.co", hashed_password="x", full_name="B")
    u.profile = UserProfile()
    db.add(u)
    db.flush()
    return u


# ── Plans (data) ──
def test_plan_catalog_and_helpers():
    s = Settings()
    cat = plans.plan_catalog(s)
    assert {p["id"] for p in cat} == {"free", "monthly", "annual", "exam_pass"}
    assert plans.is_unlimited("monthly") and not plans.is_unlimited("free")
    assert plans.plan_price(s, "annual") == s.price_annual_row


# ── Lemon Squeezy signature + mapping ──
def test_signature_verification():
    secret, body = "whsec_test", b'{"a":1}'
    good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert ls.verify_signature(body, good, secret)
    assert not ls.verify_signature(body, "deadbeef", secret)
    assert not ls.verify_signature(body, None, secret)
    assert not ls.verify_signature(body, good, "")  # no secret configured -> reject


def test_event_parse_and_mapping():
    body = {
        "meta": {"event_name": "subscription_created", "custom_data": {"user_id": "u1"}},
        "data": {"id": "sub_1", "attributes": {
            "customer_id": 42, "status": "active", "variant_name": "Monthly plan",
            "renews_at": "2026-07-20T00:00:00Z", "user_email": "a@b.co"}},
    }
    p = ls.parse_event(body)
    assert p["event"] == "subscription_created" and p["custom"]["user_id"] == "u1"
    assert ls.map_plan(p) == "monthly"
    assert ls.map_status(p) == "active"
    assert ls.map_status({"event": "subscription_payment_failed", "ls_status": ""}) == "grace"
    assert ls.map_status({"event": "x", "ls_status": "cancelled"}) == "canceled"
    assert ls.map_plan({"variant_name": "Annual membership"}) == "annual"


# ── Gating / metering (server-side) ──
def test_gating_disabled_allows_all():
    db = SessionLocal()
    try:
        u = _mk_user(db)
        assert service.can_start_session(db, u.id, Settings(billing_enforced=False))["allowed"]
    finally:
        db.rollback(); db.close()


def test_free_wall_blocks_after_limit():
    db = SessionLocal()
    try:
        u = _mk_user(db)
        s = Settings(billing_enforced=True, free_session_limit=2)
        assert service.can_start_session(db, u.id, s)["allowed"]
        service.record_usage(db, u.id, "session_start", "c1")
        service.record_usage(db, u.id, "session_start", "c2")
        db.flush()  # autoflush is off; simulate the commit a real request would do
        res = service.can_start_session(db, u.id, s)
        assert not res["allowed"] and res["reason"] == "free_limit_reached"
    finally:
        db.rollback(); db.close()


def test_paid_plan_is_unlimited():
    db = SessionLocal()
    try:
        u = _mk_user(db)
        db.add(Entitlement(user_id=u.id, plan="monthly", status="active"))
        db.flush()
        s = Settings(billing_enforced=True, free_session_limit=1)
        for _ in range(5):
            service.record_usage(db, u.id, "session_start", "c")
        assert service.can_start_session(db, u.id, s)["allowed"]
    finally:
        db.rollback(); db.close()


# ── Cost guardrail (margin) ──
def test_cost_guardrail_alert():
    db = SessionLocal()
    try:
        u = _mk_user(db)
        s = Settings(cost_per_1k_tokens_usd=1.0, price_monthly_usd=10.0, cost_alert_ratio=0.8)
        r1 = service.record_session_cost(db, f"s_{uuid.uuid4().hex}", u.id, 1000, 1000, s)
        assert r1["est_cost_usd"] == 2.0 and not r1["alert"]  # 2 < 0.8*10
        db.flush()  # autoflush is off; make r1's cost visible to r2's spend query
        r2 = service.record_session_cost(db, f"s_{uuid.uuid4().hex}", u.id, 3000, 4000, s)  # +7 -> 9
        assert r2["alert"] and r2["period_spend_usd"] >= 8.0
    finally:
        db.rollback(); db.close()


# ── Webhook -> entitlement ──
def test_apply_event_creates_entitlement():
    db = SessionLocal()
    try:
        u = _mk_user(db)
        parsed = {"event": "subscription_created", "subscription_id": "sub9",
                  "customer_id": "99", "ls_status": "active", "variant_name": "Annual",
                  "renews_at": "2027-01-01T00:00:00Z", "user_email": "", "custom": {"user_id": u.id}}
        ent = service.apply_mor_event(db, parsed)
        assert ent and ent.plan == "annual" and ent.status == "active"
        assert service.is_active_paid(ent)
    finally:
        db.rollback(); db.close()


def test_apply_event_unknown_user_returns_none():
    db = SessionLocal()
    try:
        assert service.apply_mor_event(db, {"event": "x", "custom": {}, "user_email": ""}) is None
    finally:
        db.rollback(); db.close()


# ── Endpoints ──
def test_plans_endpoint_is_public():
    r = client.get("/api/billing/plans").json()
    assert r["success"] and len(r["data"]["plans"]) == 4


def test_me_requires_auth():
    assert client.get("/api/billing/me").status_code == 401


def test_session_start_gated_when_over_limit(monkeypatch):
    email = f"gate_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "G"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}).json()["data"]["token"]
    monkeypatch.setattr(
        "app.domains.sessions.router.billing.can_start_session",
        lambda *a, **k: {"allowed": False, "reason": "free_limit_reached", "usage": {"sessions": 5}, "limit": 5},
    )
    r = client.post("/api/sessions", json={"case_id": "kasus-101", "mode": "normal"},
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 402


def test_webhook_rejects_bad_signature():
    r = client.post("/api/billing/webhooks/lemonsqueezy", content=b"{}",
                    headers={"X-Signature": "bad"})
    assert r.status_code == 401


def test_webhook_applies_valid_event(monkeypatch):
    email = f"wh_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "W"})
    db = SessionLocal()
    uid = db.scalar(select(User.id).where(User.email == email))
    db.close()
    # Signature path is unit-tested above; here we exercise the endpoint wiring.
    monkeypatch.setattr("app.domains.billing.router.ls.verify_signature", lambda *a, **k: True)
    body = {"meta": {"event_name": "subscription_created", "custom_data": {"user_id": uid}},
            "data": {"id": "subX", "attributes": {"customer_id": 1, "status": "active",
                     "variant_name": "Monthly", "renews_at": "2027-01-01T00:00:00Z"}}}
    r = client.post("/api/billing/webhooks/lemonsqueezy", content=json.dumps(body).encode(),
                    headers={"X-Signature": "x"})
    assert r.status_code == 200 and r.json()["data"]["plan"] == "monthly"


# ── Midtrans (Indonesia primary gateway) ──
from app.domains.billing import midtrans


def test_midtrans_order_id_roundtrip():
    oid = midtrans.make_order_id("user-abc-123", "annual")
    assert oid.startswith("qora-")
    uid, plan = midtrans.parse_order_id(oid)
    assert uid == "user-abc-123" and plan == "annual"
    assert midtrans.parse_order_id("not-a-qora-order") == ("", "")
    assert midtrans.parse_order_id("qora-only-two") == ("", "")


def test_midtrans_signature():
    s = Settings(midtrans_server_key="SB-Mid-server-test", midtrans_is_production=False)
    body = {"order_id": "qora-u-mo-abc123", "status_code": "200", "gross_amount": "119000"}
    raw = f"{body['order_id']}{body['status_code']}{body['gross_amount']}{s.midtrans_server_key}"
    body["signature_key"] = hashlib.sha512(raw.encode()).hexdigest()
    assert midtrans.verify_signature(s, body)
    assert not midtrans.verify_signature(s, {**body, "signature_key": "deadbeef"})
    assert not midtrans.verify_signature(Settings(), body)  # no key -> reject


def test_midtrans_parse_event_statuses():
    oid = midtrans.make_order_id("u1", "monthly")
    assert midtrans.parse_event({"order_id": oid, "transaction_status": "settlement"})["grants"]
    assert midtrans.parse_event({"order_id": oid, "transaction_status": "capture"})["grants"]
    assert not midtrans.parse_event({"order_id": oid, "transaction_status": "pending"})["grants"]
    assert midtrans.parse_event({"order_id": oid, "transaction_status": "refund"})["revokes"]


def test_midtrans_webhook_grants_entitlement(monkeypatch):
    email = f"mt_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12", "full_name": "M"})
    db = SessionLocal()
    uid = db.scalar(select(User.id).where(User.email == email))
    db.close()
    assert uid, "user should exist"
    # Signature is unit-tested; exercise endpoint wiring.
    monkeypatch.setattr("app.domains.billing.router.midtrans.is_configured", lambda *a, **k: True)
    monkeypatch.setattr("app.domains.billing.router.midtrans.verify_signature", lambda *a, **k: True)
    order_id = midtrans.make_order_id(uid, "monthly")
    body = {"order_id": order_id, "status_code": "200", "gross_amount": "119000",
            "transaction_status": "settlement", "signature_key": "x", "transaction_id": "tx1"}
    r = client.post("/api/billing/midtrans/notifications", content=json.dumps(body).encode())
    assert r.status_code == 200 and r.json()["data"]["plan"] == "monthly"
    db = SessionLocal()
    try:
        ent = db.get(Entitlement, uid)
        assert ent is not None
        assert ent.plan == "monthly" and ent.status == "active"
        assert ent.mor_subscription_id == "tx1"
    finally:
        db.close()


def test_midtrans_webhook_rejects_bad_signature(monkeypatch):
    # Gateway is configured (patched) so the request reaches the signature check.
    monkeypatch.setattr("app.domains.billing.router.midtrans.is_configured", lambda *a, **k: True)
    body = {"order_id": "qora-x-mo-abc", "status_code": "200", "gross_amount": "119000",
            "transaction_status": "settlement", "signature_key": "bad"}
    r = client.post("/api/billing/midtrans/notifications", content=json.dumps(body).encode())
    assert r.status_code == 401


def test_midtrans_checkout_requires_config():
    # No MIDTRANS_SERVER_KEY in test env -> 503.
    client.post("/api/auth/signup", json={"email": "mtc@t.co", "password": "secret12", "full_name": "M"})
    tok = client.post("/api/auth/login", json={"email": "mtc@t.co", "password": "secret12"}).json()["data"]["token"]
    r = client.post("/api/billing/midtrans/checkout/monthly",
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 503
