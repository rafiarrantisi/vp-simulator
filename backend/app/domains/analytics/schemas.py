"""Pilot analytics schemas + validation."""
from pydantic import BaseModel, Field

from app.domains.analytics.models import ALLOWED_EVENTS


class PilotEventIn(BaseModel):
    model_config = {"extra": "allow"}
    event: str = Field(..., min_length=1, max_length=64)
    session_id: str | None = None
    stage: str | None = Field(default=None, max_length=32)
    meta: dict = Field(default_factory=dict)
    # STEP-6 rule 3: competency carried as SKD 2026 (not SKDI level primary).
    competency_standard: str = "SKD 2026"
    competency_category: str | None = None
    legacy_skdi_level: str | None = None

    def validate_event(self) -> None:
        if self.event not in ALLOWED_EVENTS:
            allowed = ", ".join(sorted(ALLOWED_EVENTS))
            raise ValueError(f"Unknown event '{self.event}'. Allowed: {allowed}")