"""Qora Mentor domain — SQLAlchemy models (PRD_QORA_MENTOR §5.1).

Mirrors the alembic migration `c4d5e6f7a8b9_add_mentor_system`.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# JSONB on Postgres (prod), JSON elsewhere (sqlite dev) — same as migration.
JSONB = JSON().with_variant(postgresql.JSONB(), "postgresql")


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LearningJourney(Base):
    __tablename__ = "learning_journeys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    institution_id: Mapped[str] = mapped_column(String, index=True, default="default")

    # User input (raw)
    user_story: Mapped[str] = mapped_column(Text)
    extracted_context: Mapped[dict] = mapped_column(JSONB)

    # LLM proposal
    proposed_plan: Mapped[dict] = mapped_column(JSONB)
    user_feedback: Mapped[str | None] = mapped_column(Text, default=None)
    final_plan: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # State: proposed | active | completed | abandoned
    status: Mapped[str] = mapped_column(String, default="proposed")
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Readiness
    readiness_start: Mapped[int | None] = mapped_column(Integer, default=None)
    readiness_current: Mapped[int | None] = mapped_column(Integer, default=None)
    readiness_target: Mapped[int] = mapped_column(Integer, default=80)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    cases: Mapped[list["JourneyCase"]] = relationship(
        back_populates="journey", cascade="all, delete-orphan", order_by="JourneyCase.day_number"
    )


class JourneyCase(Base):
    __tablename__ = "journey_cases"
    __table_args__ = (UniqueConstraint("journey_id", "day_number", name="uq_journey_cases_day"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    journey_id: Mapped[str] = mapped_column(
        String, ForeignKey("learning_journeys.id", ondelete="CASCADE"), index=True
    )
    day_number: Mapped[int] = mapped_column(Integer)
    case_id: Mapped[str] = mapped_column(String)
    focus_area: Mapped[str | None] = mapped_column(String, default=None)
    learning_objective: Mapped[str | None] = mapped_column(String, default=None)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=45)

    # locked | available | in_progress | completed
    status: Mapped[str] = mapped_column(String, default="locked")
    session_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="SET NULL"), default=None
    )
    score: Mapped[int | None] = mapped_column(Integer, default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    journey: Mapped["LearningJourney"] = relationship(back_populates="cases")


class ReasoningAutopsy(Base):
    __tablename__ = "reasoning_autopsies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    journey_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("learning_journeys.id", ondelete="SET NULL"), index=True, default=None
    )

    user_pathway: Mapped[list | None] = mapped_column(JSONB, default=None)
    expert_pathway: Mapped[list | None] = mapped_column(JSONB, default=None)
    divergence_points: Mapped[list | None] = mapped_column(JSONB, default=None)
    errors_detected: Mapped[list | None] = mapped_column(JSONB, default=None)
    pearl: Mapped[str | None] = mapped_column(Text, default=None)

    readiness_impact: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PatientSeries(Base):
    __tablename__ = "patient_series"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    base_condition: Mapped[str] = mapped_column(String)
    age: Mapped[int | None] = mapped_column(Integer, default=None)
    gender: Mapped[str | None] = mapped_column(String, default=None)
    occupation: Mapped[str | None] = mapped_column(String, default=None)

    case_sequence: Mapped[list] = mapped_column(JSONB)  # [case_id, ...]
    triggers: Mapped[list] = mapped_column(JSONB)        # [{type, value, target_case}]
    next_visit_context: Mapped[dict | None] = mapped_column(JSONB, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UserPatientHistory(Base):
    __tablename__ = "user_patient_history"
    __table_args__ = (UniqueConstraint("user_id", "series_id", name="uq_user_patient_history"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    series_id: Mapped[str] = mapped_column(
        String, ForeignKey("patient_series.id", ondelete="CASCADE")
    )
    current_visit: Mapped[int] = mapped_column(Integer, default=1)
    last_session_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="SET NULL"), default=None
    )
    errors_detected: Mapped[list | None] = mapped_column(JSONB, default=None)
    status: Mapped[str] = mapped_column(String, default="active")  # active | completed | abandoned

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
