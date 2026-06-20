"""Billing data model (BUILD_PLAN_pivot_v4 §7) — none existed before the pivot.

Entitlement = the user's current plan/status (driven only by verified MoR
webhooks). UsageEvent = metering for the freemium wall. SessionCost = per-session
LLM token spend for the margin guardrail (§7.3).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Entitlement(Base):
    __tablename__ = "entitlements"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    plan: Mapped[str] = mapped_column(String, default="free")        # free|monthly|annual|exam_pass
    status: Mapped[str] = mapped_column(String, default="active")    # active|grace|canceled
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    mor_customer_id: Mapped[str] = mapped_column(String, default="")
    mor_subscription_id: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String, index=True)  # session_start|case_access
    case_id: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class SessionCost(Base):
    __tablename__ = "session_costs"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)  # one row per session
    user_id: Mapped[str] = mapped_column(String, index=True)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    est_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
