"""Plan catalogue (BUILD_PLAN_pivot_v4 §7.3) — plans + prices are DATA/config.

Free (a few cases + a low monthly session cap) vs paid unlimited (fair-use)
monthly / annual / exam-crunch pass. Prices live in Settings (env-overridable).
"""
from __future__ import annotations

from app.config import Settings

PAID_PLANS = frozenset({"monthly", "annual", "exam_pass"})
ALL_PLANS = frozenset({"free"}) | PAID_PLANS


def is_unlimited(plan: str) -> bool:
    """Paid plans get fair-use unlimited sessions."""
    return plan in PAID_PLANS


def plan_price(s: Settings, plan: str) -> float:
    return {
        "free": 0.0,
        "monthly": s.price_monthly_usd,
        "annual": s.price_annual_usd,
        "exam_pass": s.price_exam_pass_usd,
    }.get(plan, 0.0)


def checkout_url(s: Settings, plan: str) -> str:
    return {
        "monthly": s.lemonsqueezy_checkout_monthly,
        "annual": s.lemonsqueezy_checkout_annual,
        "exam_pass": s.lemonsqueezy_checkout_exam_pass,
    }.get(plan, "")


def plan_catalog(s: Settings) -> list[dict]:
    """Public plan list for the pricing UI."""
    return [
        {"id": "free", "label": "Free", "price_usd": 0.0, "interval": None,
         "unlimited": False, "session_limit": s.free_session_limit,
         "case_limit": s.free_case_limit},
        {"id": "monthly", "label": "Monthly", "price_usd": s.price_monthly_usd,
         "interval": "month", "unlimited": True,
         "checkout_url": s.lemonsqueezy_checkout_monthly},
        {"id": "annual", "label": "Annual", "price_usd": s.price_annual_usd,
         "interval": "year", "unlimited": True,
         "checkout_url": s.lemonsqueezy_checkout_annual},
        {"id": "exam_pass", "label": "Exam-crunch pass", "price_usd": s.price_exam_pass_usd,
         "interval": "one_time", "unlimited": True,
         "checkout_url": s.lemonsqueezy_checkout_exam_pass},
    ]
