"""Shared pytest fixtures."""
import pytest

from app.shared import ratelimit


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter is an in-memory per-process sliding window. Clear it
    before each test so the suite's many auth/AI calls don't accumulate and
    trip a flaky 429 in unrelated tests."""
    ratelimit._hits.clear()
    yield
