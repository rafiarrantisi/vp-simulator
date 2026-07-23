"""Xendit payment gateway (instruksi §8).

Xendit hosts the checkout: we create an invoice via the API and hand the user
its `invoice_url`; entitlement is only ever granted from the signed webhook
(`x-callback-token`). Env-driven — no `XENDIT_API_KEY` means Xendit is disabled.
We never touch raw card data (Xendit hosts the payment page).

Docs: https://developer.xendit.co/api-reference/#create-invoice
"""
from __future__ import annotations

import base64
import uuid

import httpx

from app.config import Settings

_INVOICE_URL = "https://api.xendit.co/v2/invoices"


def is_configured(s: Settings) -> bool:
    return bool(s.xendit_api_key)


def _auth_header(api_key: str) -> str:
    # Xendit uses HTTP Basic auth: secret key as the username, empty password.
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return f"Basic {token}"


def make_external_id(user_id: str, plan: str) -> str:
    """Encode the user + plan in the invoice's external_id so the webhook can
    reconcile without a separate lookup table."""
    return f"qora:{user_id}:{plan}:{uuid.uuid4().hex[:12]}"


def parse_external_id(external_id: str) -> tuple[str, str]:
    parts = (external_id or "").split(":")
    if len(parts) >= 3 and parts[0] == "qora":
        return parts[1], parts[2]  # (user_id, plan)
    return "", ""


def create_invoice(s: Settings, plan: str, amount: float, user_id: str, email: str) -> dict:
    """Create a hosted Xendit invoice and return its checkout URL. Raises on
    transport/HTTP error (the caller maps that to a 502)."""
    payload = {
        "external_id": make_external_id(user_id, plan),
        "amount": amount,
        "currency": s.xendit_currency or "USD",
        "payer_email": email or None,
        "description": f"Qora — {plan} plan",
        "success_redirect_url": s.xendit_success_url or None,
        "failure_redirect_url": s.xendit_failure_url or None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    r = httpx.post(
        _INVOICE_URL, json=payload,
        headers={"Authorization": _auth_header(s.xendit_api_key)}, timeout=20.0,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "invoice_url": data.get("invoice_url"),
        "invoice_id": data.get("id"),
        "external_id": payload["external_id"],
        "status": data.get("status"),
    }


def verify_webhook(s: Settings, token_header: str | None) -> bool:
    """Xendit signs callbacks with a static verification token in the
    `x-callback-token` header. Constant-configured comparison."""
    expected = s.xendit_webhook_token
    return bool(expected) and token_header == expected


def parse_event(body: dict) -> dict:
    external_id = str(body.get("external_id") or "")
    user_id, plan = parse_external_id(external_id)
    return {
        "status": str(body.get("status") or "").upper(),  # PAID | EXPIRED | ...
        "external_id": external_id,
        "user_id": user_id,
        "plan": plan,
        "xendit_id": body.get("id"),
    }
