"""SQLAlchemy engine + session factory (backend-plan §6.1).

DB URL configurable: sqlite (dev, runnable tanpa Docker) atau Postgres (prod
via env). Schema multi-tenant: setiap tabel domain punya institution_id.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

_connect_args = (
    {"check_same_thread": False}
    if _settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    future=True,
    # v0.16.1: prod = Supabase TRANSACTION pooler (port 6543). Session pooler
    # (5432) caps at 15 clients (EMAXCONNSESSION) -> DB bottleneck saat
    # concurrency >15. Supavisor free tier: banyak client conn, tapi ~15
    # server conn (transaksi simultan). pool_pre_ping + recycle handle
    # connection recycling; pool sengaja kecil (10+10) biar reconnect storm
    # pas burst gak menumpuk; pool_timeout=10 fail-fast (503) bukan hang 30s.
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=10,
    pool_timeout=10,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Dev convenience; prod pakai Alembic (backend-plan §10)."""
    # Import models so they register on Base.metadata.
    # (users domain pakai model dari auth — tidak punya models.py sendiri)
    from app.domains.admin import models as _admin  # noqa: F401
    from app.domains.analytics import models as _analytics  # noqa: F401
    from app.domains.auth import models as _auth  # noqa: F401
    from app.domains.billing import models as _billing  # noqa: F401
    from app.domains.cases import models as _cases  # noqa: F401
    from app.domains.exam import models as _exam  # noqa: F401
    from app.domains.eye_photos import models as _eye_photos  # noqa: F401
    from app.domains.mentor import models as _mentor  # noqa: F401
    from app.domains.sessions import models as _sessions  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_runtime_columns()


def _ensure_runtime_columns() -> None:
    """Tambah kolom baru secara idempoten utk jalur create_all (live sqlite
    bootstrap TIDAK menjalankan Alembic, dan create_all tak meng-ALTER tabel
    yang sudah ada). Tiap statement diisolasi — gagal (kolom sudah ada) =
    di-skip. Alembic tetap sumber kebenaran migrasi utk Postgres/prod.

    v0.16.0: cases.locked.
    STEP-6: new-schema session columns (sessions table, extended not duplicated).
    """
    from sqlalchemy import text

    stmts = [
        "ALTER TABLE cases ADD COLUMN locked BOOLEAN DEFAULT 0",
        "ALTER TABLE session_turns ADD COLUMN input_type VARCHAR DEFAULT 'text'",
        # STEP-6 superseding rule 1 — v3 runtime state (existing sessions table)
        "ALTER TABLE sessions ADD COLUMN content_schema VARCHAR DEFAULT 'legacy'",
        "ALTER TABLE sessions ADD COLUMN family_id VARCHAR",
        "ALTER TABLE sessions ADD COLUMN variant_id VARCHAR",
        "ALTER TABLE sessions ADD COLUMN persona_seed INTEGER",
        "ALTER TABLE sessions ADD COLUMN persona JSON",
        "ALTER TABLE sessions ADD COLUMN learner_level VARCHAR",
        "ALTER TABLE sessions ADD COLUMN interaction_mode VARCHAR",
        "ALTER TABLE sessions ADD COLUMN competency_category VARCHAR",
        "ALTER TABLE sessions ADD COLUMN legacy_skdi_level VARCHAR",
        "ALTER TABLE sessions ADD COLUMN presentation_path VARCHAR",
        "ALTER TABLE sessions ADD COLUMN selection_reason VARCHAR",
        "ALTER TABLE sessions ADD COLUMN variant_canonical_hash VARCHAR",
        # STEP-6 rules — pilot_events behavioural/competency columns
        "ALTER TABLE pilot_events ADD COLUMN competency_standard VARCHAR DEFAULT 'SKD 2026'",
        "ALTER TABLE pilot_events ADD COLUMN competency_category VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN legacy_skdi_level VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN family_id VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN variant_id VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN presentation_path VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN interaction_mode VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN learner_level VARCHAR",
        "ALTER TABLE pilot_events ADD COLUMN persona_fallback BOOLEAN DEFAULT FALSE",
        "ALTER TABLE pilot_events ADD COLUMN content_schema VARCHAR DEFAULT 'new'",
    ]
    for s in stmts:
        try:
            with engine.begin() as conn:
                conn.execute(text(s))
        except Exception:
            pass  # kolom sudah ada — aman diabaikan
