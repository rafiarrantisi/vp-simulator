"""Transactional email seam (pivot-v4 §7.1).

Prototype default = **console mode**: when SMTP is unconfigured, the message
(e.g. a verification or password-reset link) is logged to the server console so
flows work locally without any provider. Plug a real provider later by setting
the SMTP_* env vars (works with Resend/SES/Postmark/any SMTP). Never raises —
email must not break a request.
"""
from __future__ import annotations

import logging

from app.config import Settings, get_settings

_log = logging.getLogger("qora.mailer")


def send_email(to: str, subject: str, body: str) -> bool:
    """Send (or, unconfigured, log) a transactional email. Returns True if it was
    actually dispatched to a provider, False in console mode / on failure."""
    s = get_settings()
    if not s.smtp_host:
        _log.info("[mailer:console] (no SMTP configured)\n  To: %s\n  Subject: %s\n  %s",
                  to, subject, body)
        return False
    try:
        return _send_smtp(s, to, subject, body)
    except Exception as e:  # noqa: BLE001 — email failure must not break the flow
        _log.warning("[mailer] send to %s failed: %s", to, e)
        return False


def _send_smtp(s: Settings, to: str, subject: str, body: str) -> bool:
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = s.smtp_from or s.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(s.smtp_host, s.smtp_port or 587, timeout=10) as srv:
        srv.starttls()
        if s.smtp_user:
            srv.login(s.smtp_user, s.smtp_password)
        srv.send_message(msg)
    return True
