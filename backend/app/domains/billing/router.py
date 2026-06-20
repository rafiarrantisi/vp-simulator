"""Billing API (BUILD_PLAN_pivot_v4 §7.2/§7.3).

  POST /api/billing/webhooks/lemonsqueezy  — MoR webhook (signature-verified)
  GET  /api/billing/me                     — current entitlement + usage
  GET  /api/billing/plans                  — public plan catalogue
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
from app.domains.billing import lemonsqueezy as ls
from app.domains.billing import plans, service
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok

router = APIRouter(prefix="/api/billing", tags=["billing"])
_log = logging.getLogger("ophtha.billing")


@router.get("/plans")
def list_plans():
    return ok({"plans": plans.plan_catalog(get_settings())})


@router.get("/me")
def my_entitlement(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ent = service.get_entitlement(db, user.id)
    return ok({
        "plan": ent.plan,
        "status": ent.status,
        "unlimited": plans.is_unlimited(ent.plan) and service.is_active_paid(ent),
        "current_period_end": ent.current_period_end.isoformat() if ent.current_period_end else None,
        "usage": service.usage_this_period(db, user.id),
        "free_session_limit": get_settings().free_session_limit,
    })


@router.get("/checkout/{plan}")
def checkout(plan: str, user: User = Depends(get_current_user)):
    s = get_settings()
    if plan not in plans.PAID_PLANS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan")
    url = plans.checkout_url(s, plan)
    if not url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Checkout not configured")
    # Pass user_id as Lemon Squeezy custom data so the webhook can reconcile.
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}checkout[custom][user_id]={user.id}"
    return ok({"checkout_url": url, "plan": plan})


@router.get("/portal")
def portal(user: User = Depends(get_current_user)):
    url = get_settings().lemonsqueezy_portal_url
    if not url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Portal not configured")
    return ok({"portal_url": url})


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    signature = request.headers.get("X-Signature")
    if not ls.verify_signature(raw, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Malformed body")

    parsed = ls.parse_event(body)
    ent = service.apply_mor_event(db, parsed)
    if ent is None:
        # Acknowledge so the MoR doesn't retry forever; log for investigation.
        _log.warning("[billing] webhook %s could not resolve a user", parsed.get("event"))
        return ok({"handled": False, "event": parsed.get("event")})
    db.commit()
    _log.info("[billing] %s -> user %s plan=%s status=%s",
              parsed.get("event"), ent.user_id, ent.plan, ent.status)
    return ok({"handled": True, "event": parsed.get("event"), "plan": ent.plan, "status": ent.status})
