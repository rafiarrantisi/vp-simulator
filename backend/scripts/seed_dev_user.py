"""Seed a local demo user so the prototype is one-command usable (idempotent).

  python -m scripts.seed_dev_user

Creates demo@qora.local / demo1234 (role=student). DEV ONLY — never run in prod.
"""
from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.domains.auth.models import User, UserProfile
from app.shared.security import hash_password

EMAIL = "demo@qora.app"
PASSWORD = "demo1234"


def main() -> int:
    init_db()
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == EMAIL)):
            print(f"[seed-dev-user] already exists: {EMAIL} (password: {PASSWORD})")
            return 0
        user = User(
            email=EMAIL,
            hashed_password=hash_password(PASSWORD),
            full_name="Demo Student",
            role="student",
        )
        user.profile = UserProfile()
        db.add(user)
        db.commit()
        print(f"[seed-dev-user] created {EMAIL} / {PASSWORD}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    sys.exit(main())
