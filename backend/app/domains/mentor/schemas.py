"""Qora Mentor — Pydantic schemas (PRD_QORA_MENTOR §5.3)."""
from typing import Any

from pydantic import BaseModel, Field


class StoryRequest(BaseModel):
    """Phase 1: user's natural-language story."""

    story: str = Field(..., min_length=3, max_length=2000)


class CustomizeRequest(BaseModel):
    """Chat-based adjustment to a proposed journey."""

    feedback: str = Field(..., min_length=2, max_length=1000)


class AcceptRequest(BaseModel):
    """Accept the proposal and start the journey."""

    plan: dict[str, Any] | None = None  # optional adjusted plan (accepted as-is)


class CompleteCaseRequest(BaseModel):
    """Mark a journey case completed, linking the session + score."""

    case_id: str
    session_id: str
    score: int = Field(..., ge=0, le=100)
