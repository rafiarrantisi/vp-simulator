"""Phase 12 — request correlation + version headers (plan §PHASE12).

Every response carries:
- X-Request-ID ......... client-supplied (echoed) or server-generated, so a
  chat/judge/Mentor error can be traced end-to-end;
- X-Qora-Scoring-Version / X-Qora-Evidence-Pack / X-Qora-Content-Version ...
  the exact contracts that scored the response (request/session/engine/
  schema/version correlation without logging any clinical content).

Header values are version/category strings only — never secrets. Handlers
for raised exceptions set the same headers explicitly (middleware cannot
decorate a response that was never built).
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "X-Request-ID"

VERSION_HEADERS: dict[str, str] = {}


def _version_headers() -> dict[str, str]:
    if not VERSION_HEADERS:
        try:
            from pipeline.clinical_contracts.versions import (
                CLINICAL_CONTENT_VERSION,
                EVIDENCE_PACK_VERSION,
                SCORING_VERSION,
            )
            VERSION_HEADERS.update({
                "X-Qora-Scoring-Version": str(SCORING_VERSION),
                "X-Qora-Evidence-Pack": str(EVIDENCE_PACK_VERSION),
                "X-Qora-Content-Version": str(CLINICAL_CONTENT_VERSION),
            })
        except Exception:
            VERSION_HEADERS.update({
                "X-Qora-Scoring-Version": "unknown",
                "X-Qora-Evidence-Pack": "unknown",
                "X-Qora-Content-Version": "unknown",
            })
    return VERSION_HEADERS


def new_request_id() -> str:
    return uuid.uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind/propagate X-Request-ID and stamp version headers on responses."""

    async def dispatch(self, request: Request, call_next):
        rid = (request.headers.get(REQUEST_ID_HEADER) or "").strip() or new_request_id()
        try:
            request.state.request_id = rid
        except Exception:
            pass
        resp = await call_next(request)
        resp.headers[REQUEST_ID_HEADER] = rid
        for k, v in _version_headers().items():
            resp.headers.setdefault(k, v)
        return resp


def request_id_of(request) -> str:
    """Best-effort request id for handlers (state → header → fresh)."""
    try:
        rid = getattr(getattr(request, "state", None), "request_id", "") or ""
        if rid:
            return str(rid)
    except Exception:
        pass
    try:
        rid = (request.headers.get(REQUEST_ID_HEADER) or "").strip()
        if rid:
            return rid
    except Exception:
        pass
    return new_request_id()


def stamp_response_headers(response, request=None) -> None:
    """Apply the correlation/version headers to a handler-built response."""
    try:
        rid = request_id_of(request) if request is not None else new_request_id()
        response.headers[REQUEST_ID_HEADER] = rid
        for k, v in _version_headers().items():
            response.headers.setdefault(k, v)
    except Exception:
        pass
