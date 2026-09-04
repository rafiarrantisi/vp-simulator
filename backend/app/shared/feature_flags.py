"""Phase 12 — feature-flag snapshot (plan §PHASE12).

Single, auditable view of the rollout seams so incremental rollout and
rollback never need a grand frontend revert:

- content_engine ... 'v2' (stable) | 'v3_compat' (V3 canary via backend facade)
- judge_engine ..... 'v2' (stable LLM judge) | 'hybrid' (upgraded judge canary;
  FASE 7 STOP: not wired into any scoring path until human calibration passes)
- judge_live ....... resolved live judge (mirrors judge_engine today; kept as
  a separate key so a future split-brain canary has a home)
- mentor_v1_enabled  Mentor write-paths kill-switch (reads stay open).

Unknown names are ignored; unknown VALUES fall back to safe defaults.
The snapshot never contains secrets — names and category values only.
"""
from __future__ import annotations

CONTENT_ENGINES = frozenset({"v2", "v3_compat"})

JUDGE_ENGINES = frozenset({"v2", "hybrid"})


def snapshot(settings=None) -> dict:
    """Resolve effective flags from settings (or global settings)."""
    if settings is None:
        from app.config import get_settings
        settings = get_settings()
    content = str(getattr(settings, "case_content_engine", "v2") or "v2").strip().lower()
    judge = str(getattr(settings, "judge_engine", "v2") or "v2").strip().lower()
    if content not in CONTENT_ENGINES:
        content = "v2"
    if judge not in JUDGE_ENGINES:
        judge = "v2"
    return {
        "content_engine": content,
        "judge_engine": judge,
        "judge_live": judge,
        "mentor_v1_enabled": bool(getattr(settings, "mentor_v1_enabled", True)),
    }
