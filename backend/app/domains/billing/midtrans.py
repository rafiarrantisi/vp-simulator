"""Midtrans payment gateway (Indonesia primary, Snap API).

Midtrans hosts the payment page: we create a Snap transaction via the API and
hand the frontend a `snap_token` (popup via snap.js) plus a `redirect_url`
(fallback). Entitlement is ONLY granted from the signed webhook
(`POST /api/billing/midtrans/notifications`) — signature is SHA512 of
`order_id + status_code + gross_amount + server_key`.

Env-driven — no `MIDTRANS_SERVER_KEY` means Midtrans is disabled.
We never touch raw card data (Snap hosts the payment page).

Docs: https://docs.midtrans.com/reference/snap-overview
"""
from __future__ import annotations

import hashlib
import uuid

import httpx

from app.config import Settings

_SNAP_URL = "https://app.midtrans.com/snap/v1/transactions"
_SNAP_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"


def is_configured(s: Settings) -> bool:
    return bool(s.midtrans_server_key)


def _snap_url(s: Settings) -> str:
    return _SNAP_URL if s.midtrans_is_production else _SNAP_SANDBOX_URL


def _auth_header(server_key: str) -> str:
    # Midtrans uses HTTP Basic auth: server key as username, empty password.
    import base64

    token = base64.b64encode(f"{server_key}:".encode()).decode()
    return f"Basic {token}"


def make_order_id(user_id: str, plan: str) -> str:
    """Encode the user + plan in the order_id so the webhook can reconcile
    without a separate lookup table."""
    return f"qora-{user_id}-{plan}-{uuid.uuid4().hex[:8]}"


def parse_order_id(order_id: str) -> tuple[str, str]:
    """Parse order_id back into (user_id, plan)."""
    parts = (order_id or "").split("-")
    # qora-{user_id}-{plan}-{uuid8}; user_id itself may contain dashes (uuid),
    # so find the plan token from the END instead.
    if len(parts) >= 4 and parts[0] == "qora":
        plan = parts[-2]
        user_id = "-".join(parts[1:-2])
        return user_id, plan
    return "", ""


def create_snap_transaction(s: Settings, plan: str, amount: float,
                            user_id: str, email: str, full_name: str = "") -> dict:
    """Create a Snap transaction and return {snap_token, redirect_url, order_id}.

    Raises on transport/HTTP error (the caller maps that to a 502).
    """
    order_id = make_order_id(user_id, plan)
    payload = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": int(amount),
        },
        "item_details": [
            {
                "id": plan,
                "price": int(amount),
                "quantity": 1,
                "name": f"Qora {plan} plan",
            }
        ],
        "customer_details": {
            "first_name": (full_name or "Qora")[:64],
            "email": email or None,
        },
        "custom_field1": user_id,
        "custom_field2": plan,
        "expiry": {"unit": "hours", "duration": 24},
    }
    # Clean None values
    payload = {k: v for k, v in payload.items() if v is not None}
    if payload.get("customer_details"):
        payload["customer_details"] = {
            k: v for k, v in payload["customer_details"].items() if v is not None
        }
    r = httpx.post(
        _snap_url(s), json=payload,
        headers={
            "Authorization": _auth_header(s.midtrans_server_key),
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=20.0,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "snap_token": data.get("token"),
        "redirect_url": data.get("redirect_url"),
        "order_id": order_id,
    }


def verify_signature(s: Settings, body: dict) -> bool:
    """Verify the Midtrans webhook signature.

    Signature = SHA512(order_id + status_code + gross_amount + server_key),
    compared against body['signature_key'].
    """
    server_key = s.midtrans_server_key
    if not server_key:
        return False
    order_id = str(body.get("order_id") or "")
    status_code = str(body.get("status_code") or "")
    gross_amount = str(body.get("gross_amount") or "")
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    expected = hashlib.sha512(raw.encode()).hexdigest()
    received = str(body.get("signature_key") or "")
    return expected == received


# Statuses that grant entitlement.
_GRANT_STATUSES = frozenset({"settlement", "capture"})
# Statuses that revoke entitlement.
_REVOKE_STATUSES = frozenset({"refund", "deny", "cancel", "expire"})


def parse_event(body: dict) -> dict:
    """Map a verified Midtrans notification to a normalized event dict."""
    order_id = str(body.get("order_id") or "")
    user_id, plan = parse_order_id(order_id)
    status = str(body.get("transaction_status") or "").lower()
    return {
        "order_id": order_id,
        "user_id": user_id,
        "plan": plan,
        "transaction_status": status,
        "status_code": str(body.get("status_code") or ""),
        "gross_amount": str(body.get("gross_amount") or ""),
        "payment_type": body.get("payment_type"),
        "fraud_status": body.get("fraud_status"),
        "transaction_id": body.get("transaction_id"),
        "signature_valid": None,  # set by the router after verification
        "grants": status in _GRANT_STATUSES,
        "revokes": status in _REVOKE_STATUSES,
    }
