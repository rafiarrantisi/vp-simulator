"""Pilot analytics schemas + validation."""
from pydantic import BaseModel, Field

from app.domains.analytics.models import ALLOWED_EVENTS


class PilotEventIn(BaseModel):
    event: str = Field(..., min_length=1, max_length=64)
    session_id: str | None = None
    stage: str | None = Field(default=None, max_length=32)
    meta: dict = Field(default_factory=dict)

    def validate_event(self) -> None:
        if self.event not in ALLOWED_EVENTS:
            allowed = ", ".join(sorted(ALLOWED_EVENTS))
            raise ValueError(f"Unknown event '{self.event}'. Allowed: {allowed}")