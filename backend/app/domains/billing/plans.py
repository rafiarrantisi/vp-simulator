"""Plan catalogue (BUILD_PLAN_pivot_v4 §7.3) — plans + prices are DATA/config.

Region-aware pricing:
  - indo  → IDR (Xendit)
  - asean → USD
  - row   → USD
"""
from __future__ import annotations

from app.config import Settings

PAID_PLANS = frozenset({"monthly", "annual", "exam_pass"})
ALL_PLANS = frozenset({"free"}) | PAID_PLANS
REGIONS = frozenset({"indo", "asean", "row"})


def is_unlimited(plan: str) -> bool:
    """Paid plans get fair-use unlimited sessions."""
    return plan in PAID_PLANS


def region_price(s: Settings, region: str, plan: str) -> float:
    """Return the price for a given region + plan.

    Falls back to ROW pricing for unknown regions.
    """
    region = region if region in REGIONS else "row"
    monthly = {
        "indo": s.price_monthly_idr,
        "asean": s.price_monthly_asean,
        "row": s.price_monthly_row,
    }.get(region, s.price_monthly_row)
    annual = {
        "indo": s.price_annual_idr,
        "asean": s.price_annual_asean,
        "row": s.price_annual_row,
    }.get(region, s.price_annual_row)
    return {"free": 0.0, "monthly": monthly, "annual": annual, "exam_pass": s.price_exam_pass_usd}.get(plan, 0.0)


def region_currency(region: str) -> str:
    """Currency code for a region's pricing."""
    return "IDR" if region == "indo" else "USD"


def plan_price(s: Settings, plan: str) -> float:
    """Legacy — returns ROW USD price (backwards compatible)."""
    return region_price(s, "row", plan)


def plan_catalog(s: Settings, region: str | None = None) -> list[dict]:
    """Public plan list for the pricing UI.

    When region is provided, prices are shown in the local currency.
    Falls back to ROW when region is None/unknown.
    """
    if region not in REGIONS:
        region = "row"

    def _price(plan: str) -> float:
        return region_price(s, region, plan)

    def _currency() -> str:
        return region_currency(region)

    def _label(plan: str) -> str:
        """Human-readable price label for the region."""
        r = region
        if plan == "free":
            return "Free"
        p = _price(plan)
        if r == "indo":
            if plan == "monthly":
                return f"Rp{int(p):,}/bln".replace(",", ".")
            return f"Rp{int(p):,}/thn".replace(",", ".")
        if plan == "monthly":
            return f"${p:.2f}/mo"
        return f"${p:.2f}/yr"

    def _sessions(plan: str) -> str:
        return "Unlimited" if plan in PAID_PLANS else str(s.free_session_limit)

    return [
        {
            "id": "free", "label": "Free", "price": _price("free"),
            "display_price": _label("free"), "interval": None,
            "currency": _currency(),
            "unlimited": False, "session_limit": s.free_session_limit,
            "case_limit": s.free_case_limit,
        },
        {
            "id": "monthly", "label": "Monthly", "price": _price("monthly"),
            "display_price": _label("monthly"), "interval": "month",
            "currency": _currency(),
            "unlimited": True, "sessions": _sessions("monthly"),
        },
        {
            "id": "annual", "label": "Annual", "price": _price("annual"),
            "display_price": _label("annual"), "interval": "year",
            "currency": _currency(),
            "unlimited": True, "sessions": _sessions("annual"),
        },
        {
            "id": "exam_pass", "label": "Exam-crunch pass", "price": _price("exam_pass"),
            "display_price": _label("exam_pass"), "interval": "one_time",
            "currency": _currency(),
            "unlimited": True, "sessions": _sessions("exam_pass"),
        },
    ]
