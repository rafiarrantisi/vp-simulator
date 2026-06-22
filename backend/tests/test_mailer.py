"""Email seam (pivot-v4 §7.1) — console mode when unconfigured."""
from app.shared.mailer import send_email


def test_console_mode_returns_false_and_never_raises():
    # Dev has no SMTP_HOST -> console mode: logs the link, returns False, no raise.
    assert send_email("user@example.com", "Verify your email",
                      "https://qora.app/verify?token=abc") is False
