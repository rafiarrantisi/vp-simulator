"""Phase 12 — metadata-only LLM/judge logging helpers (plan §PHASE12).

Signature-level guarantee: these helpers accept outcome metadata ONLY —
never prompts, completions, transcripts, answer keys, rubrics, or any other
blind/clinical content. Nothing secret or clinical can flow through them by
construction. All helpers are total (never raise).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

_log = logging.getLogger("qora.llm")
_jlog = logging.getLogger("qora.judge")


def _safe(value, limit: int = 120) -> str:
    try:
        text = "" if value is None else str(value)
    except Exception:
        return ""
    return text[:limit]


def log_llm_event(*, role=None, outcome=None, session_id=None, model=None,
                  error=None) -> dict:
    """Record an LLM-call outcome (persona/judge/mentor turns).

    Metadata only: which role, what happened, which session/model, and a
    SHORT error label (exception class or code — never messages, which may
    echo secrets). Returns the record (also debug-logged).
    """
    record = {
        "kind": "llm_event",
        "role": _safe(role, 40),
        "outcome": _safe(outcome, 40),
        "session_id": _safe(session_id, 64),
        "model": _safe(model, 120),
        "error": _safe(error, 80),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        (_log.warning if record["error"] and record["error"] != "ok" else _log.info)(
            "llm_event role=%s outcome=%s session=%s model=%s error=%s",
            record["role"], record["outcome"], record["session_id"],
            record["model"], record["error"] or "-")
    except Exception:
        pass
    return record


def log_judge_event(*, engine=None, outcome=None, session_id=None,
                    content_schema=None, scoring_version=None) -> dict:
    """Record a judge/scoring outcome (which engine, which contract version).

    Metadata only: engine name, outcome label, session, content schema and
    scoring-contract version. Never transcripts, rubrics, or answer keys.
    """
    record = {
        "kind": "judge_event",
        "engine": _safe(engine, 40),
        "outcome": _safe(outcome, 40),
        "session_id": _safe(session_id, 64),
        "content_schema": _safe(content_schema, 24),
        "scoring_version": _safe(scoring_version, 64),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _jlog.info(
            "judge_event engine=%s outcome=%s session=%s schema=%s scoring=%s",
            record["engine"], record["outcome"], record["session_id"],
            record["content_schema"], record["scoring_version"])
    except Exception:
        pass
    return record
