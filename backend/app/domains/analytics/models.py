"""Pilot behavioural events (Fase 5 §35) — every pilot session becomes evidence.

A lightweight, append-only event log decoupled from the session/scoring tables, so
pilot analytics can answer the §35 questions (who practised, completed, returned,
where they dropped, debrief opened, voice vs text, retry) without coupling to core
domain rows.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PilotEvent(Base):
    __tablename__ = "pilot_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str | None] = mapped_column(String, index=True, default=None)
    event: Mapped[str] = mapped_column(String, index=True)  # whitelisted name
    stage: Mapped[str | None] = mapped_column(String, default=None)  # chat|pf|assess|result
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # extra context (mode, lang, ...)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # denormalised for cheap funnel counts without joining sessions
    case_id: Mapped[str | None] = mapped_column(String, index=True, default=None)


# Whitelist — keeps the event table clean and queryable. Client may only send these.
ALLOWED_EVENTS = {
    "session_started",
    "pf_revealed",
    "debrief_opened",
    "answer_key_revealed",
    "retry_attempt",
    "abandoned",
}