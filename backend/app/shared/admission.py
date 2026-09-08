"""Phase 2 — bounded admission for LLM-bound work (brief §7.1f/g, §14.4).

Per-worker-local semaphores (NOT a global correctness mechanism — cross-worker
hard requirements stay on authoritative DB state). Starting points from the
brief, tunable via env; production values must come from benchmark:

- conversation: 64 concurrent streams per worker (QORA_CONV_LIMIT);
- judge: 1 active generation per worker (QORA_JUDGE_LIMIT);
- DB bridge: bounded thread units for sync finalization (QORA_DB_THREADS).

Created lazily in the running loop; lifespan pre-builds them via
`init_admission()` so first request never pays construction.
"""
from __future__ import annotations

import logging
import os

import anyio

_log = logging.getLogger("qora.perf")

_CONV_DEFAULT = 64
_JUDGE_DEFAULT = 1
_DB_THREADS_DEFAULT = 8


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, default))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


_conv: anyio.Semaphore | None = None
_judge: anyio.Semaphore | None = None
_db_limiter: anyio.CapacityLimiter | None = None


def init_admission() -> None:
    """Build limiters in the worker loop (lifespan startup). Total, never raises."""
    global _conv, _judge, _db_limiter
    try:
        if _conv is None:
            _conv = anyio.Semaphore(_int_env("QORA_CONV_LIMIT", _CONV_DEFAULT))
        if _judge is None:
            _judge = anyio.Semaphore(_int_env("QORA_JUDGE_LIMIT", _JUDGE_DEFAULT))
        if _db_limiter is None:
            _db_limiter = anyio.CapacityLimiter(
                _int_env("QORA_DB_THREADS", _DB_THREADS_DEFAULT))
    except Exception:
        _log.warning("admission init failed", exc_info=True)


def conversation_limiter() -> anyio.Semaphore:
    global _conv
    if _conv is None:
        _conv = anyio.Semaphore(_int_env("QORA_CONV_LIMIT", _CONV_DEFAULT))
    return _conv


def judge_limiter() -> anyio.Semaphore:
    global _judge
    if _judge is None:
        _judge = anyio.Semaphore(_int_env("QORA_JUDGE_LIMIT", _JUDGE_DEFAULT))
    return _judge


def db_limiter() -> anyio.CapacityLimiter:
    global _db_limiter
    if _db_limiter is None:
        _db_limiter = anyio.CapacityLimiter(
            _int_env("QORA_DB_THREADS", _DB_THREADS_DEFAULT))
    return _db_limiter


def limits_snapshot() -> dict:
    """Current configured bounds (for evidence/debugging, no live counts)."""
    return {
        "conversation": _int_env("QORA_CONV_LIMIT", _CONV_DEFAULT),
        "judge": _int_env("QORA_JUDGE_LIMIT", _JUDGE_DEFAULT),
        "db_threads": _int_env("QORA_DB_THREADS", _DB_THREADS_DEFAULT),
    }


def admission_wait_s() -> float:
    """Bounded wait for an admission slot (§7.1g/n). Starting point 10 s."""
    try:
        return max(1.0, float(os.environ.get("QORA_ADMISSION_WAIT_S", 10)))
    except (TypeError, ValueError):
        return 10.0


def idle_timeout_s() -> float:
    """Max silence between upstream chunks before the turn fails (§7.1n).

    Starting point 60 s (healthy streams emit continuously; SDK total
    timeout still bounds the whole call).
    """
    try:
        return max(0.1, float(os.environ.get("QORA_IDLE_TIMEOUT_S", 60)))
    except (TypeError, ValueError):
        return 60.0
