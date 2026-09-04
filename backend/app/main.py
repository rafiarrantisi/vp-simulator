"""FastAPI app — domain-modular (backend-plan §6.1, kontrak §6)."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.domains.admin.router import router as admin_router
from app.domains.ai.router import router as ai_router
from app.domains.analytics.router import router as analytics_router
from app.domains.auth.router import router as auth_router
from app.domains.billing.router import router as billing_router
from app.domains.cases.router import admin_router as cases_admin_router
from app.domains.cases.router import router as cases_router
from app.domains.eye_photos.router import router as eye_photos_router
from app.domains.exam.router import router as exam_router
from app.domains.mentor.router import router as mentor_router
from app.domains.ops.router import router as ops_router
from app.domains.scoring.router import router as scoring_router
from app.domains.sessions.router import router as sessions_router
from app.domains.sessions.v2_router import router as v2_router
from app.domains.sessions.v3_router import router as v3_router
from app.domains.users.router import router as users_router
from app.shared.envelope import ok
from app.shared.request_id import RequestContextMiddleware, request_id_of, stamp_response_headers
from app.shared.security_headers import SecurityHeadersMiddleware

_settings = get_settings()
_log = logging.getLogger("ophtha.startup")


def _ensure_upload_dirs() -> Path:
    """v0.15.0: pastikan upload dir + subdir eye-photos ada (idempoten)."""
    base = Path(_settings.upload_dir).resolve()
    (base / "eye-photos").mkdir(parents=True, exist_ok=True)
    return base


def _seed_admin_user() -> None:
    """v0.15.0: seed 1 super-admin dari .env (ADMIN_EMAIL + ADMIN_PASSWORD_HASH).

    Idempoten:
    - Email kosong / hash kosong → skip (akun admin opsional di dev).
    - Email belum ada → insert dgn role='admin'.
    - Email ada + role='admin' → skip (sudah benar).
    - Email ada + role!='admin' → log warning, JANGAN auto-promote (safety).
    """
    email = (_settings.admin_email or "").strip().lower()
    hashed = (_settings.admin_password_hash or "").strip()
    if not email or not hashed:
        return
    # Import di sini (bukan top-level) cegah circular import + tetap ringan.
    from sqlalchemy import select

    from app.domains.auth.models import User, UserProfile

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is None:
            user = User(
                email=email,
                hashed_password=hashed,
                full_name="Developer Admin",
                institution_id=_settings.default_institution_id,
                role="admin",
            )
            user.profile = UserProfile()
            db.add(user)
            db.commit()
            _log.info("[seed-admin] Created admin user: %s", email)
        elif existing.role != "admin":
            _log.warning(
                "[seed-admin] User %s exists with role=%s — NOT auto-promoting "
                "to admin (safety). Ubah manual via DB bila memang dimaksud.",
                email, existing.role,
            )
        # else: already admin, no-op.
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Prod-guard: prod/staging TOLAK start bila config tak aman; dev → warn.
    _settings.assert_production_safe()
    init_db()  # dev: create tables. Prod: Alembic (backend-plan §10).
    _ensure_upload_dirs()
    _seed_admin_user()
    # v0.16.1: pre-warm catalog cache di tiap worker (lru_cache per-proses).
    # Tanpa ini, worker cold-cache parse 82 file per request pertama (~2s)
    # SAMBIL megang koneksi DB (dependency auth) -> pool exhaustion saat burst.
    try:
        from app.domains.cases.v2_catalog import list_v2_cases, specialties_present
        list_v2_cases()
        specialties_present()
        _log.info("[catalog] pre-warm OK")
    except Exception:
        _log.warning("[catalog] pre-warm gagal", exc_info=True)
    yield


app = FastAPI(title=_settings.app_name, version="0.15.0", lifespan=lifespan)

# Phase 12: correlation/version headers on EVERY response (innermost, so
# error responses built inside still pass through on the way out).
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth_router, users_router, cases_router, cases_admin_router, sessions_router, v2_router, v3_router, exam_router, scoring_router, ai_router, eye_photos_router, admin_router, billing_router, mentor_router, analytics_router, ops_router):
    app.include_router(r)


# v0.16.1: pool DB habis (burst) -> 503 cepat, bukan 500 + stacktrace.
# Frontend/CF function bisa retry; user dapat pesan jelas.
from sqlalchemy.exc import TimeoutError as SaTimeoutError


@app.exception_handler(SaTimeoutError)
async def _db_pool_timeout_handler(_request, _exc):
    return JSONResponse(
        status_code=503,
        content={"success": False, "data": None,
                 "error": "Server sibuk — coba lagi sebentar lagi."},
    )


# Phase 12: unhandled-exception envelope — stable client contract with a
# request ref for end-to-end tracing. Tracebacks never leave the server
# (they go to the server log only); secret-like tokens are redacted out of
# the echoed message. HTTPException keeps FastAPI's default shape.
import re as _re

_SECRET_PATTERNS = tuple(
    _re.compile(p, _re.IGNORECASE)
    for p in (r"api[_-]?key", r"apikey", r"secret", r"passwd", r"password",
              r"bearer", r"xendit", r"midtrans")
)


def _sanitize_error_text(text: str, limit: int = 200) -> str:
    try:
        out = str(text or "")
    except Exception:
        out = ""
    for rx in _SECRET_PATTERNS:
        out = rx.sub("[redacted]", out)
    out = " ".join(out.split())
    return out[:limit] if len(out) > limit else out


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request, exc: Exception):
    ref = request_id_of(request)
    try:
        path = request.url.path
    except Exception:
        path = "?"
    _log.exception("unhandled [%s] %s %s", ref,
                   getattr(request, "method", "?"), path)
    resp = JSONResponse(
        status_code=500,
        content={"success": False,
                 "error": f"{type(exc).__name__}: {_sanitize_error_text(exc)}",
                 "ref": ref},
    )
    stamp_response_headers(resp, request)
    return resp


# Eye-photo files are served by the authenticated route in
# `domains.eye_photos.router`; do not mount StaticFiles here, because that
# would bypass auth for anyone who knows a UUID filename.


@app.get("/health")
def health():
    return ok({"status": "up", "env": _settings.env})


# ── v0.16.0: serve built frontend (SPA) ──
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "sistemnya" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets"), check_dir=False),
        name="frontend_assets",
    )

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API routes handled by routers above; everything else → SPA
        if full_path.startswith("api/"):
            return JSONResponse({"error": "Not found"}, status_code=404)
        index = _FRONTEND_DIST / "index.html"
        if not index.exists():
            return JSONResponse({"error": "Frontend not built"}, status_code=503)
        return FileResponse(str(index))
    _log.info("[frontend] Serving SPA from %s", _FRONTEND_DIST)
