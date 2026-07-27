from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domains.auth.models import User, UserProfile
from app.domains.auth.schemas import AuthSession, SignupRequest
from app.shared.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def _session_for(user: User) -> AuthSession:
    return AuthSession(
        token=create_access_token(user.id, user.institution_id, user.role),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
        email=user.email,
        role=user.role,
        institution_id=user.institution_id,
    )


def signup(db: Session, req: SignupRequest) -> AuthSession:
    exists = db.scalar(select(User).where(User.email == req.email))
    if exists is not None:
        raise ValueError("Email already registered")
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        nim=req.nim,
        institution_id=req.institution_id or get_settings().default_institution_id,
        role="student",
    )
    user.profile = UserProfile(region=req.region)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _session_for(user)


def login(db: Session, email: str, password: str) -> AuthSession:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")
    return _session_for(user)


def refresh(db: Session, user_id: str) -> AuthSession:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    return _session_for(user)


def google_login(db: Session, credential: str) -> AuthSession:
    """Verify a Google Identity Services ID token and log the user in, creating
    the account on first sign-in (pivot-v4 §7.1). The token is verified by Google
    (tokeninfo), then the audience is checked against our own client id."""
    import secrets as _secrets

    import httpx

    s = get_settings()
    if not s.google_client_id:
        raise ValueError("Google sign-in is not configured")
    try:
        r = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=10.0,
        )
    except httpx.HTTPError as e:
        raise ValueError("Could not verify Google token") from e
    if r.status_code != 200:
        raise ValueError("Invalid Google token")
    data = r.json()
    if data.get("aud") != s.google_client_id:
        raise ValueError("Google token audience mismatch")
    email = str(data.get("email") or "").strip().lower()
    verified = str(data.get("email_verified", "")).lower() in ("true", "1")
    if not email or not verified:
        raise ValueError("Google account email is not verified")
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            # Random unusable password — this account signs in via Google.
            hashed_password=hash_password(_secrets.token_urlsafe(32)),
            full_name=str(data.get("name") or ""),
            institution_id=s.default_institution_id,
            role="student",
        )
        user.profile = UserProfile()
        db.add(user)
        db.commit()
        db.refresh(user)
    return _session_for(user)
