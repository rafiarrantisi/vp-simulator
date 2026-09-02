import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    institution_id: Mapped[str] = mapped_column(String, index=True, default="default")
    case_id: Mapped[str] = mapped_column(String, index=True)
    mode: Mapped[str] = mapped_column(String, default="normal")
    status: Mapped[str] = mapped_column(String, default="active")  # active|completed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    total_score: Mapped[int | None] = mapped_column(Integer, default=None)
    report: Mapped[dict | None] = mapped_column(JSON, default=None)  # EvaluationReport §3A
    language: Mapped[str] = mapped_column(String, default="en")  # en | id | ms | tl | vi | th | ...
    # ── STEP-6 superseding: new-schema (case_v3) runtime session state ──
    # (extended existing `sessions` table — no new DB subsystem, per rule 1)
    content_schema: Mapped[str] = mapped_column(String, default="legacy")  # legacy | new
    family_id: Mapped[str | None] = mapped_column(String, index=True, default=None)   # canonical family
    variant_id: Mapped[str | None] = mapped_column(String, index=True, default=None)  # selected ClinicalVariant
    persona_seed: Mapped[int | None] = mapped_column(Integer, default=None)
    persona: Mapped[dict | None] = mapped_column(JSON, default=None)         # rendered persona instance (immutable post-start)
    learner_level: Mapped[str | None] = mapped_column(String, default=None)  # preclinical | koas
    interaction_mode: Mapped[str | None] = mapped_column(String, default=None)  # targeted | blind | random
    competency_category: Mapped[str | None] = mapped_column(String, default=None)  # tuntas | initial_management_and_referral (SKD 2026)
    legacy_skdi_level: Mapped[str | None] = mapped_column(String, default=None)     # optional, verified-only
    presentation_path: Mapped[str | None] = mapped_column(String, default=None)
    selection_reason: Mapped[str | None] = mapped_column(String, default=None)      # audit trail
    # reproducibility: fingerprint of the canonical clinical truth so a reload
    # can confirm the EXACT session instance (immutability, rule 2).
    variant_canonical_hash: Mapped[str | None] = mapped_column(String, default=None)


class SessionTurn(Base):
    __tablename__ = "session_turns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), index=True)
    turn_number: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String)  # user|patient|system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # input medium for user turns — 'text' | 'voice' (Fase 5 §35.7 voice-vs-text)
    input_type: Mapped[str] = mapped_column(String, default="text")
