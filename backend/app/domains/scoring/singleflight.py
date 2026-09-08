"""Phase 4 — in-worker single-flight for scoring (brief §9.1d).

One worker deduplicates concurrent identical scoring operations: the first
request runs, the rest await the same result. Bounded by construction (entry
removed in `finally`; no queues, no threads). Cross-worker duplicates remain
possible (documented residual) — the stored-report fast path still makes
retries idempotent.

Cancellation: owner disconnect never hangs waiters (future always settles);
a cancelled waiter affects only itself. No hang in any path.
"""
from __future__ import annotations

import asyncio

_flights: dict[str, asyncio.Future] = {}


async def run_singleflight(key: str, fn):
    """Run `fn()` once per key; concurrent callers share the outcome.

    Returns (result, shared) where shared=True for waiters. Raises the
    owner's exception (or CancelledError-derived failure) for waiters when
    the owner fails or disconnects — callers must map that to a retryable
    error; a retry then hits the stored-report fast path when available.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return await fn(), False
    fut = loop.create_future()
    existing = _flights.setdefault(key, fut)
    if existing is not fut:
        result = await existing
        return result, True
    try:
        result = await fn()
    except BaseException as e:  # noqa: BLE001 - must settle waiters
        if not fut.done():
            fut.set_exception(e)
        raise
    else:
        if not fut.done():
            fut.set_result(result)
        return result, False
    finally:
        _flights.pop(key, None)
