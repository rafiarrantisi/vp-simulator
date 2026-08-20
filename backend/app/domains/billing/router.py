"""Billing API (BUILD_PLAN_pivot_v4 §7.2/§7.3).

  POST /api/billing/webhooks/xendit       — Xendit callback (token-verified)
  POST /api/billing/midtrans/notifications — Midtrans notification (signature-verified)
  GET  /api/billing/me                     — current entitlement + usage
  GET  /api/billing/plans                  — public plan catalogue (region-aware)
  POST /api/billing/xendit/checkout/{plan} — Xendit hosted invoice (region-aware)
  GET  /api/billing/checkout/{plan}        — hosted checkout URL (+ user_id custom data)
  GET  /api/billing/portal                 — MoR-hosted customer portal link

Entitlement changes ONLY through the verified webhook — never the client.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.domains.auth.models import User
from app.domains.billing import midtrans
from app.domains.billing import plans, service, xendit
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok

router = APIRouter(prefix="/api/billing", tags=["billing"])
_log = logging.getLogger("ophtha.billing")


@router.get("/plans")
def list_plans(region: str = "row"):
    """Public plan catalogue. Accept optional `region` query (indo|asean|row)
    to show localised prices. Unauthenticated callers should pass region
    detected client-side."""
    s = get_settings()
    provider = "midtrans" if midtrans.is_configured(s) else ("xendit" if xendit.is_configured(s) else None)
    return ok({
        "plans": plans.plan_catalog(s, region),
        "provider": provider,
        "billing_enforced": s.billing_enforced,
        "region": region,
    })


@router.post("/xendit/checkout/{plan}")
def xendit_checkout(
    plan: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Xendit hosted invoice for the plan, using the user's
    stored region for pricing and currency."""
    s = get_settings()
    if plan not in plans.PAID_PLANS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan")
    if not xendit.is_configured(s):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Xendit not configured")

    # Use the user's stored region for pricing
    region = (user.profile.region or "row") if user.profile else "row"
    amount = plans.region_price(s, region, plan)
    currency = plans.region_currency(region)

    try:
        inv = xendit.create_invoice(s, plan, amount, user.id, user.email, currency_override=currency)
    except Exception as e:  # noqa: BLE001 — surface a clean 502, log the detail
        _log.error("[billing] xendit invoice failed: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not create invoice")
    return ok({"checkout_url": inv["invoice_url"], "plan": plan, "invoice_id": inv["invoice_id"],
               "currency": currency, "amount": amount})


@router.post("/midtrans/checkout/{plan}")
def midtrans_checkout(
    plan: str,
    user: User = Depends(get_current_user),
):
    """Create a Midtrans Snap transaction for the plan (IDR, Indonesia).

    Returns {snap_token, redirect_url, order_id} so the frontend can open
    the Snap popup. Entitlement is granted ONLY by the webhook, never here.
    """
    s = get_settings()
    if plan not in plans.PAID_PLANS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan")
    if not midtrans.is_configured(s):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Midtrans not configured")

    # Indonesia price in IDR; Midtrans Snap accepts integer IDR amounts.
    amount = plans.region_price(s, "indo", plan)
    full_name = user.full_name or ""

    try:
        tx = midtrans.create_snap_transaction(
            s, plan, amount, user.id, user.email, full_name=full_name,
        )
    except Exception as e:  # noqa: BLE001 — surface a clean 502, log the detail
        _log.error("[billing] midtrans snap failed: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not create transaction")
    return ok({
        "snap_token": tx["snap_token"],
        "redirect_url": tx["redirect_url"],
        "order_id": tx["order_id"],
        "plan": plan,
        "currency": "IDR",
        "amount": int(amount),
    })


@router.post("/midtrans/notifications")
async def midtrans_webhook(request: Request, db: Session = Depends(get_db)):
    """Midtrans payment notification (signature-verified).

    settlement/capture -> grant entitlement; refund/deny/cancel/expire ->
    revoke. Always acknowledge with 200 so Midtrans doesn't retry forever.
    """
    s = get_settings()
    try:
        body = json.loads(await request.body())
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Malformed body")

    if not midtrans.is_configured(s):
        # Nothing we can do without a key; acknowledge to stop retries.
        _log.warning("[billing] midtrans webhook received but gateway not configured")
        return ok({"handled": False, "reason": "not_configured"})

    if not midtrans.verify_signature(s, body):
        _log.warning("[billing] midtrans webhook signature invalid for order %s",
                     body.get("order_id"))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    parsed = midtrans.parse_event(body)
    ent = service.apply_midtrans_event(db, parsed)
    if ent is None:
        _log.info("[billing] midtrans %s not applied (status=%s)",
                  parsed.get("order_id"), parsed.get("transaction_status"))
        db.commit()
        return ok({"handled": False, "status": parsed.get("transaction_status")})
    db.commit()
    _log.info("[billing] midtrans %s -> user %s plan=%s status=%s",
              parsed.get("transaction_status"), ent.user_id, ent.plan, ent.status)
    return ok({"handled": True, "plan": ent.plan, "status": ent.status})


@router.post("/webhooks/xendit")
async def xendit_webhook(request: Request, db: Session = Depends(get_db)):
    """Xendit invoice callback (x-callback-token verified). PAID -> entitlement."""
    if not xendit.verify_webhook(get_settings(), request.headers.get("x-callback-token")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid callback token")
    try:
        body = json.loads(await request.body())
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Malformed body")
    parsed = xendit.parse_event(body)
    ent = service.apply_xendit_event(db, parsed)
    if ent is None:
        _log.info("[billing] xendit %s not applied (status=%s)",
                  parsed.get("external_id"), parsed.get("status"))
        return ok({"handled": False, "status": parsed.get("status")})
    db.commit()
    _log.info("[billing] xendit PAID -> user %s plan=%s", ent.user_id, ent.plan)
    return ok({"handled": True, "plan": ent.plan, "status": ent.status})


@router.get("/me")
def my_entitlement(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ent = service.get_entitlement(db, user.id)
    region = (user.profile.region or "row") if user.profile else "row"
    return ok({
        "plan": ent.plan,
        "status": ent.status,
        "unlimited": plans.is_unlimited(ent.plan) and service.is_active_paid(ent),
        "current_period_end": ent.current_period_end.isoformat() if ent.current_period_end else None,
        "usage": service.usage_this_period(db, user.id),
        "free_session_limit": get_settings().free_session_limit,
        "region": region,
    })


@router.get("/history")
def payment_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Billing history for the payment page: current entitlement, usage this
    period, and recent sessions with their scores. Frontend renders this as
    the payment/subscription status page."""
    ent = service.get_entitlement(db, user.id)
    usage = service.usage_this_period(db, user.id)
    from app.domains.sessions.models import SessionRow
    rows = (
        db.query(SessionRow)
        .filter(SessionRow.user_id == user.id)
        .order_by(SessionRow.started_at.desc())
        .limit(10)
        .all()
    )
    history = [
        {
            "id": r.id, "caseId": r.case_id, "mode": r.mode,
            "status": r.status,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "endedAt": r.ended_at.isoformat() if r.ended_at else None,
            "totalScore": r.total_score,
        }
        for r in rows
    ]
    return ok({
        "plan": ent.plan,
        "status": ent.status,
        "current_period_end": ent.current_period_end.isoformat() if ent.current_period_end else None,
        "usage": usage,
        "free_session_limit": get_settings().free_session_limit,
        "history": history,
    })


