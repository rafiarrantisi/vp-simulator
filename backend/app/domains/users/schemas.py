from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    school: str | None = None
    year: str | None = None
    avatar_emoji: str | None = None
    avatar_color: str | None = None
    preferred_language: str | None = None  # en | id | ms | tl | vi | th


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    nim: str
    role: str
    institution_id: str
    xp: int
    streak: int
    total_sessions: int
    avatar_emoji: str
    avatar_color: str
    school: str
    year: str
    region: str  # indo | asean | row
    preferred_language: str  # en | id | ms | tl | vi | th
