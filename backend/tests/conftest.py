"""Shared pytest fixtures + FASE 0 safety gate (test DB isolation).

INVARIANT (FASE 0):
- Normal `pytest` MUST NEVER touch production Postgres, even if
  `backend/.env` contains a prod `DATABASE_URL` (Supabase pooler).
- Default: force an isolated sqlite DB (`/tmp/qora_test_isolated.db`).
- Live DB access requires explicit opt-in: `QORA_ALLOW_LIVE_DB=1`.
- Live/paid LLM requires explicit opt-in: `QORA_LIVE_TURNS=1` / `RUN_LLM_QA=1`.
  Otherwise `LLM_API_KEY` is blanked so `StubLlmClient` is used.

Ordering matters: this file is imported by pytest BEFORE any `tests/test_*.py`
module, so setting `os.environ` here happens before `app.database` creates its
engine (engine is bound at import time from `get_settings().database_url`).
pydantic-settings prioritises real env vars over `.env` file values, so this
override wins over `backend/.env`.
"""
import os

_LIVE_DB = os.environ.get("QORA_ALLOW_LIVE_DB") == "1"
_LIVE_LLM = (
    os.environ.get("QORA_LIVE_TURNS") == "1"
    or os.environ.get("RUN_LLM_QA") == "1"
)

if not _LIVE_DB:
    # Force isolated test DB. Never trust a leftover exported DATABASE_URL.
    os.environ["DATABASE_URL"] = "sqlite:////tmp/qora_test_isolated.db"
    # Use a non-prod ENV so `assert_production_safe()` can never fail-fast here.
    os.environ["ENV"] = "test"

if not _LIVE_LLM:
    # Force deterministic stub LLM (no paid calls, no network).
    os.environ["LLM_API_KEY"] = ""

# Clear any cached Settings so the overrides above take effect even if
# something imported app.config before conftest finished loading.
try:
    from app.config import get_settings as _get_settings

    _get_settings.cache_clear()
except Exception:
    pass

import pytest

from app.shared import ratelimit


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter is an in-memory per-process sliding window. Clear it
    before each test so the suite's many auth/AI calls don't accumulate and
    trip a flaky 429 in unrelated tests."""
    ratelimit._hits.clear()
    yield


@pytest.fixture(autouse=True)
def _guard_no_prod_db():
    """Fail-fast if any test path is bound to a non-sqlite DB without opt-in."""
    if os.environ.get("QORA_ALLOW_LIVE_DB") == "1":
        yield
        return
    from app.database import engine

    url = str(engine.url)
    assert url.startswith("sqlite"), (
        f"[FASE0-GUARD] Test engine is not isolated sqlite: {url.split('@')[-1][:60]} "
        "(set QORA_ALLOW_LIVE_DB=1 only for explicit live-DB runs)"
    )
    yield
