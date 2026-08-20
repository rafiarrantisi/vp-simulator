"""Entitlement / gating / metering / cost-guardrail service (§7.3).

Server-side ONLY — never trust the client. Entitlement changes only
via verified Midtrans/Xendit callbacks.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.domains.auth.models import User
from app.domains.billing import plans
from app.domains.billing.models import Entitlement, SessionCost, UsageEvent

_PERIOD_DAYS = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _period_start() -> datetime:
    return _now() - timedelta(days=_PERIOD_DAYS)


def get_entitlement(db: Session, user_id: str) -> Entitlement:
    """Return the user's entitlement, or a transient free one if none exists."""
    ent = db.get(Entitlement, user_id)
    return ent if ent is not None else Entitlement(user_id=user_id, plan="free", status="active")


def is_active_paid(ent: Entitlement) -> bool:
    if ent.plan not in plans.PAID_PLANS:
        return False
    if ent.status in ("active", "grace"):
        return True
    # Cancelled-but-paid-through: keep access until the period ends.
    return ent.status == "canceled" and ent.current_period_end is not None \
        and ent.current_period_end > _now()


def usage_this_period(db: Session, user_id: str) -> dict:
    start = _period_start()
    sessions = db.scalar(
        select(func.count()).select_from(UsageEvent).where(
            UsageEvent.user_id == user_id,
            UsageEvent.kind == "session_start",
            UsageEvent.created_at >= start,
        )
    ) or 0
    cases = db.scalar(
        select(func.count(func.distinct(UsageEvent.case_id))).where(
            UsageEvent.user_id == user_id,
            UsageEvent.kind == "session_start",
            UsageEvent.created_at >= start,
            UsageEvent.case_id != "",
        )
    ) or 0
    return {"sessions": int(sessions), "cases": int(cases)}


def can_start_session(db: Session, user_id: str, s: Settings | None = None) -> dict:
    """The freemium wall. Returns {allowed, reason, ...}. Server-side enforcement."""
    s = s or get_settings()
    if not s.billing_enforced:
        return {"allowed": True, "reason": "billing_disabled"}
    ent = get_entitlement(db, user_id)
    if is_active_paid(ent):
        return {"allowed": True, "reason": "paid", "plan": ent.plan}
    used = usage_this_period(db, user_id)
    limit = s.free_session_limit
    if used["sessions"] >= limit:
        return {"allowed": False, "reason": "free_limit_reached", "usage": used, "limit": limit}
    return {"allowed": True, "reason": "free_within_limit", "usage": used, "limit": limit}


def record_usage(db: Session, user_id: str, kind: str, case_id: str = "") -> UsageEvent:
    ev = UsageEvent(user_id=user_id, kind=kind, case_id=case_id)
    db.add(ev)
    return ev


def estimate_cost_usd(tokens_in: int, tokens_out: int, s: Settings) -> float:
    return round((max(0, tokens_in) + max(0, tokens_out)) / 1000.0 * s.cost_per_1k_tokens_usd, 6)


def period_spend_usd(db: Session, user_id: str) -> float:
    total = db.scalar(
        select(func.coalesce(func.sum(SessionCost.est_cost_usd), 0.0)).where(
            SessionCost.user_id == user_id,
            SessionCost.created_at >= _period_start(),
        )
    ) or 0.0
    return float(total)


def record_session_cost(db: Session, session_id: str, user_id: str,
                        tokens_in: int, tokens_out: int, s: Settings | None = None) -> dict:
    """Log per-session token spend and flag the margin guardrail (§7.3)."""
    s = s or get_settings()
    cost = estimate_cost_usd(tokens_in, tokens_out, s)
    prior_spend = period_spend_usd(db, user_id)
    row = db.get(SessionCost, session_id)
    if row is None:
        db.add(SessionCost(session_id=session_id, user_id=user_id,
                           tokens_in=tokens_in, tokens_out=tokens_out, est_cost_usd=cost))
    else:
        row.tokens_in += tokens_in
        row.tokens_out += tokens_out
        row.est_cost_usd += cost
    ent = get_entitlement(db, user_id)
    # Free users are compared to the entry (monthly) price as the cost ceiling.
    ref_price = plans.plan_price(s, ent.plan) if ent.plan != "free" else s.price_monthly_usd
    spend_after = prior_spend + cost
    alert = ref_price > 0 and spend_after > s.cost_alert_ratio * ref_price
    return {"est_cost_usd": cost, "period_spend_usd": round(spend_after, 6),
            "alert": alert, "ref_price_usd": ref_price}


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


_XENDIT_PLAN_DAYS = {"monthly": 30, "annual": 365, "exam_pass": 30}
_MIDTRANS_PLAN_DAYS = {"monthly": 30, "annual": 365, "exam_pass": 30}


def apply_xendit_event(db: Session, parsed: dict) -> Entitlement | None:
    """Map a verified Xendit invoice callback to entitlement state. Only a PAID
    invoice grants access; an expired/failed invoice makes no change. Returns the
    Entitlement (added to the session) or None if nothing was applied."""
    user_id = str(parsed.get("user_id") or "").strip()
    plan = parsed.get("plan")
    if not user_id or plan not in plans.PAID_PLANS:
        return None
    if parsed.get("status") != "PAID":
        return None
    xendit_id = str(parsed.get("xendit_id") or "").strip()
    ent = db.get(Entitlement, user_id) or Entitlement(user_id=user_id)
    # Provider callbacks can be retried. The same paid invoice must not extend
    # the entitlement repeatedly; a new invoice has a new provider id.
    if xendit_id and ent.mor_subscription_id == xendit_id and ent.status == "active":
        return ent
    ent.plan = plan
    ent.status = "active"
    ent.current_period_end = _now() + timedelta(days=_XENDIT_PLAN_DAYS.get(plan, 30))
    ent.mor_subscription_id = xendit_id or ent.mor_subscription_id
    ent.updated_at = _now()
    db.add(ent)
    return ent


def apply_midtrans_event(db: Session, parsed: dict) -> Entitlement | None:
    """Map a verified Midtrans notification to entitlement state.

    Only settlement/capture grants access (extending the current period);
    refund/deny/cancel/expire revokes. Returns the Entitlement (added to the
    session) or None if nothing was applied.
    """
    user_id = str(parsed.get("user_id") or "").strip()
    plan = parsed.get("plan")
    if not user_id or plan not in plans.PAID_PLANS:
        return None
    status = str(parsed.get("transaction_status") or "").lower()
    ent = db.get(Entitlement, user_id) or Entitlement(user_id=user_id)

    if status in ("settlement", "capture"):
        transaction_id = str(parsed.get("transaction_id") or "").strip()
        if transaction_id and ent.mor_subscription_id == transaction_id and ent.status == "active":
            return ent
        ent.plan = plan
        ent.status = "active"
        ent.current_period_end = _now() + timedelta(days=_MIDTRANS_PLAN_DAYS.get(plan, 30))
        ent.mor_subscription_id = transaction_id or ent.mor_subscription_id
        ent.updated_at = _now()
        db.add(ent)
        return ent

    if status in ("refund", "deny", "cancel", "expire"):
        # Only revoke when this payment was the user's current plan source.
        if ent.mor_subscription_id == str(parsed.get("transaction_id") or ""):
            ent.plan = "free"
            ent.status = "canceled"
            ent.updated_at = _now()
            db.add(ent)
            return ent
        return None

    # pending / other statuses: no entitlement change
    return None
