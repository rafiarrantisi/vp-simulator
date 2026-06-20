"""Lemon Squeezy (Merchant-of-Record) webhook verification + event mapping (§7.2).

The owner is in Indonesia selling to individuals globally; the MoR is the legal
seller and remits VAT/GST/sales-tax, so we only consume webhooks and map them to
internal entitlement. No raw card handling. Signature is HMAC-SHA256 of the RAW
body with the webhook secret — verified constant-time.
"""
from __future__ import annotations

import hashlib
import hmac

from app.config import get_settings

# Lemon Squeezy event_name -> coarse status when the payload status is absent.
_EVENT_STATUS = {
    "subscription_created": "active",
    "subscription_resumed": "active",
    "subscription_unpaused": "active",
    "subscription_payment_success": "active",
    "subscription_payment_recovered": "active",
    "subscription_payment_failed": "grace",
    "subscription_paused": "grace",
    "subscription_cancelled": "canceled",
    "subscription_expired": "canceled",
    "order_created": "active",  # one-time exam-crunch pass
}


def verify_signature(raw_body: bytes, signature: str | None, secret: str | None = None) -> bool:
    """Constant-time HMAC-SHA256 check over the RAW request body."""
    secret = get_settings().lemonsqueezy_webhook_secret if secret is None else secret
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature.strip())


def parse_event(body: dict) -> dict:
    meta = body.get("meta") or {}
    data = body.get("data") or {}
    attrs = data.get("attributes") or {}
    return {
        "event": meta.get("event_name", ""),
        "subscription_id": str(data.get("id", "")),
        "customer_id": str(attrs.get("customer_id", "")),
        "ls_status": (attrs.get("status") or "").lower(),
        "variant_name": attrs.get("variant_name", ""),
        "renews_at": attrs.get("renews_at") or attrs.get("ends_at"),
        "user_email": (attrs.get("user_email") or "").strip().lower(),
        "custom": meta.get("custom_data") or {},  # we pass {user_id} at checkout
    }


def map_status(parsed: dict) -> str:
    ls = parsed.get("ls_status") or ""
    if ls in ("active", "on_trial"):
        return "active"
    if ls in ("past_due", "unpaid"):
        return "grace"
    if ls in ("cancelled", "canceled", "expired"):
        return "canceled"
    return _EVENT_STATUS.get(parsed.get("event", ""), "active")


def map_plan(parsed: dict) -> str | None:
    """Map the purchased variant to an internal plan id; None = leave unchanged."""
    name = (parsed.get("variant_name") or "").lower()
    if "annual" in name or "year" in name:
        return "annual"
    if "exam" in name or "pass" in name:
        return "exam_pass"
    if "month" in name:
        return "monthly"
    return None
