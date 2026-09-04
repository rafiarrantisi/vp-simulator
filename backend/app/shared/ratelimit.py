"""Rate limiter in-memory sliding-window (kontrak v0.9.0).

CATATAN: per-proses — benar utk single instance. Multi-instance/scale =
Redis-backed (backend-plan §7.2), ditunda. Cukup utk hardening dasar
endpoint mahal (auth brute-force, LLM STT/judge abuse).
"""
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings

_hits: dict[tuple[str, str], list[float]] = defaultdict(list)

# Phase 12: hard bound so the table cannot grow without limit in a
# long-lived worker. Eviction is expiry-driven (stale buckets go first);
# only when genuinely full of live entries are the oldest dropped.
_MAX_BUCKETS = 2000


def _evict_expired(now: float, window: int) -> None:
    """Drop keys whose every hit is older than `window` (in place)."""
    dead = [k for k, arr in _hits.items()
            if not any(now - t < window for t in arr)]
    for k in dead:
        _hits.pop(k, None)


def _enforce_bound() -> None:
    """Cap live entries at _MAX_BUCKETS (oldest-inserted first)."""
    overflow = len(_hits) - _MAX_BUCKETS
    if overflow <= 0:
        return
    for k in list(_hits)[:overflow]:
        _hits.pop(k, None)


def _client_ip(request: Request) -> str:
    # Cloudflare Tunnel supplies the canonical client address. Do not trust
    # X-Forwarded-For from the public request body: clients can spoof it and
    # otherwise bypass the per-IP auth/AI buckets.
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    return request.client.host if request.client else "unknown"


def _check(bucket: str, key: str, limit: int, window: int) -> bool:
    now = time.time()
    _evict_expired(now, window)
    k = (bucket, key)
    arr = [t for t in _hits[k] if now - t < window]
    if len(arr) >= limit:
        _hits[k] = arr
        return False
    arr.append(now)
    _hits[k] = arr
    _enforce_bound()
    return True


def rate_limit(bucket: str, limit_attr: str):
    """Dependency factory. `limit_attr` = nama field limit di Settings."""

    def dep(request: Request, settings: Settings = Depends(get_settings)):
        if not settings.rate_limit_enabled:
            return
        limit = getattr(settings, limit_attr)
        window = settings.rate_limit_window_sec
        if not _check(bucket, _client_ip(request), limit, window):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Terlalu banyak permintaan. Coba lagi dalam {window}s.",
            )

    return dep
