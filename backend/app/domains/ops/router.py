"""Phase 12 ops endpoints (plan §PHASE12) — public version/readiness probes
plus an authenticated client-error intake.

Privacy rules: version payloads carry version/category strings only (never
keys, URLs with credentials, or tokens — scanned by test); client errors
log screen/route/message-head + user id only (never email, transcripts, or
answer payloads); reported URLs are stripped of query/fragment before
anything is logged or echoed (tokens live in query strings).
"""
from __future__ import annotations

import logging
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.domains.auth.models import User
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok
from app.shared.feature_flags import snapshot as flag_snapshot

router = APIRouter(prefix="/api/ops", tags=["ops"])

_log = logging.getLogger("qora.ops")


def _strip_query(value: str | None) -> str:
    """Return the URL path without query/fragment (tokens live there).

    '' and None stay ''. Never raises.
    """
    try:
        text_value = (value or "").strip()
        if not text_value:
            return ""
        return urlsplit(text_value).path or ""
    except Exception:
        try:
            return str(value or "").split("#", 1)[0].split("?", 1)[0]
        except Exception:
            return ""


class ClientErrorIn(BaseModel):
    """Bounded critical-screen error report from the frontend."""

    screen: str = Field(default="", max_length=80)
    message: str = Field(default="", max_length=1000)
    url: str = Field(default="", max_length=500)
    stack: str = Field(default="", max_length=4000)

    @field_validator("url")
    @classmethod
    def _clean_url(cls, value: str) -> str:
        return _strip_query(value)[:500]


@router.get("/version")
def ops_version():
    """Pinned contract versions + effective flags. Public, no secrets."""
    from pipeline.clinical_contracts.versions import (
        CLINICAL_CONTENT_VERSION,
        EVIDENCE_PACK_VERSION,
        SCORING_VERSION,
    )
    return ok({
        "scoring_version": SCORING_VERSION,
        "evidence_pack_version": EVIDENCE_PACK_VERSION,
        "clinical_content_version": CLINICAL_CONTENT_VERSION,
        "flags": flag_snapshot(),
    })


def _check_db() -> tuple[bool, str]:
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("select 1"))
            return True, "select 1 ok"
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        return False, f"unreachable ({type(exc).__name__})"


def _check_uploads() -> tuple[bool, str]:
    try:
        from pathlib import Path
        base = Path(get_settings().upload_dir)
        if base.is_dir():
            return True, str(base)
        return False, f"missing dir {base}"
    except Exception as exc:  # noqa: BLE001
        return False, f"unreadable ({type(exc).__name__})"


def _check_catalog() -> tuple[bool, int]:
    try:
        from app.domains.cases.v2_catalog import list_v2_cases
        n = len(list(list_v2_cases() or []))
        return (n >= 1), n
    except Exception:  # noqa: BLE001
        return False, 0


def _check_llm() -> tuple[bool, bool]:
    try:
        configured = bool((get_settings().llm_api_key or "").strip())
        return True, configured
    except Exception:  # noqa: BLE001
        return False, False


@router.get("/readiness")
def ops_readiness():
    """Can this instance serve traffic? Per-check boring booleans only."""
    db_ok, db_detail = _check_db()
    up_ok, up_detail = _check_uploads()
    cat_ok, cat_n = _check_catalog()
    llm_ok, llm_configured = _check_llm()
    rollup = {"db": bool(db_ok), "uploads": bool(up_ok),
              "catalog": bool(cat_ok), "llm": bool(llm_ok)}
    return ok({
        "ready": bool(db_ok and up_ok and cat_ok and llm_ok),
        "checks": {
            "db": {"ok": bool(db_ok), "detail": str(db_detail)},
            "uploads": {"ok": bool(up_ok), "dir": str(up_detail)},
            "catalog": {"ok": bool(cat_ok), "v2_cases": int(cat_n)},
            "llm": {"ok": bool(llm_ok), "configured": bool(llm_configured)},
            "ok": dict(rollup),
        },
    })


@router.post("/client-errors")
def ops_client_errors(body: ClientErrorIn, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Authenticated critical-screen error intake (bounded + sanitized)."""
    route = _strip_query(body.url or "")[:120]
    try:
        _log.warning("client_error user=%s screen=%s route=%s msg=%.200s",
                     getattr(user, "id", "?"), (body.screen or "")[:80],
                     route, (body.message or ""))
    except Exception:
        pass
    return ok({"received": True, "route": route})
