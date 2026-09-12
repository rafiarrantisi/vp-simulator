"""Phase 12 — metadata-only LLM/judge logging helpers (plan §PHASE12).

Signature-level guarantee: these helpers accept outcome metadata ONLY —
never prompts, completions, transcripts, answer keys, rubrics, or any other
blind/clinical content. Nothing secret or clinical can flow through them by
construction. All helpers are total (never raise).

Phase-1 voice foundation: every record is ALSO appended to the queryable
JSONL sink (app.shared.perf_sink → backend/data/perf/) so attempt/TTFT
timelines can be reconstructed per route (ADR §4.5, §6 phase-0). Logger
output is unchanged.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

_log = logging.getLogger("qora.llm")
_jlog = logging.getLogger("qora.judge")
_plog = logging.getLogger("qora.patient")


def _safe(value, limit: int = 120) -> str:
    try:
        text = "" if value is None else str(value)
    except Exception:
        return ""
    return text[:limit]


def _sink(record: dict) -> None:
    """Best-effort append to the queryable sink. Total, never raises."""
    try:
        from app.shared.perf_sink import append_record
        append_record(record)
    except Exception:
        pass


def log_llm_event(*, role=None, outcome=None, session_id=None, model=None,
                  error=None, route=None, attempt=None, lane_hash=None,
                  ttft_ms=None, total_ms=None, output_chars=None,
                  endpoint_kind=None) -> dict:
    """Record an LLM-call outcome (persona/judge/mentor turns).

    Metadata only: which role, what happened, which session/model, and a
    SHORT error label (exception class or code — never messages, which may
    echo secrets). Optional timing/ID/length kwargs (TTFT, totals, attempt
    index, opaque lane hash, output length) feed the Phase-1 sink; they are
    all scalar-capped and carry no content. Returns the record (also
    debug-logged + sink-appended).
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
    # Optional Phase-1 timing/ID/length fields (dropped when None).
    try:
        from app.shared.perf_sink import lane_hash as _lh
        from app.shared.perf_sink import session_ref as _sr
        record["session_ref"] = _sr(session_id)
        if route is not None:
            record["route"] = _safe(route, 48)
        if attempt is not None:
            record["attempt"] = int(attempt)
        if lane_hash is not None:
            record["lane_hash"] = _safe(lane_hash, 32)
        if ttft_ms is not None:
            record["ttft_ms"] = float(ttft_ms)
        if total_ms is not None:
            record["total_ms"] = float(total_ms)
        if output_chars is not None:
            record["output_chars"] = int(output_chars)
        if endpoint_kind is not None:
            record["endpoint_kind"] = _safe(endpoint_kind, 32)
    except Exception:
        pass
    try:
        (_log.warning if record["error"] and record["error"] != "ok" else _log.info)(
            "llm_event role=%s outcome=%s session=%s model=%s error=%s",
            record["role"], record["outcome"], record["session_id"],
            record["model"], record["error"] or "-")
    except Exception:
        pass
    _sink(record)
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
    _sink(record)
    return record


_PATIENT_EVENTS = (
    "attempt_started",
    "retry_started",
    "first_content",
    "full_completion",
)


def log_patient_attempt(event: str, *, route=None, logical_turn_id=None,
                        session_id=None, attempt=None, lane_hash=None,
                        ttft_ms=None, total_ms=None, output_chars=None,
                        model=None, endpoint_kind=None, error=None) -> dict:
    """Phase-1 patient-streaming attempt timeline (ADR §1.4 event set, core).

    One record per attempt milestone: attempt_started → (retry_started →
    attempt_started) → first_content → full_completion. Timing, opaque IDs
    and lengths ONLY — never prompts, transcripts, keys or audio. Logger
    (`qora.patient`) + queryable sink. Unknown event names are recorded as
    "unknown_event" (never dropped silently, never raise).
    """
    try:
        name = str(event or "")
    except Exception:
        name = ""
    if name not in _PATIENT_EVENTS:
        name = "unknown_event"
    try:
        from app.shared.perf_sink import session_ref as _sr
    except Exception:
        def _sr(v):  # pragma: no cover - import never fails in practice
            try:
                return str(v or "")[:8]
            except Exception:
                return ""
    record = {
        "kind": "patient_attempt",
        "event": name,
        "route": _safe(route, 48),
        "logical_turn_id": _safe(logical_turn_id, 96),
        "session_ref": _sr(session_id),
        "model": _safe(model, 120),
        "endpoint_kind": _safe(endpoint_kind, 32),
        "error": _safe(error, 80),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    for key, value, cast in (
        ("attempt", attempt, int),
        ("ttft_ms", ttft_ms, float),
        ("total_ms", total_ms, float),
        ("output_chars", output_chars, int),
    ):
        try:
            if value is not None:
                record[key] = cast(value)
        except Exception:
            pass
    if lane_hash is not None:
        record["lane_hash"] = _safe(lane_hash, 32)
    try:
        _plog.info(
            "patient_attempt event=%s route=%s turn=%s attempt=%s ttft_ms=%s "
            "total_ms=%s out_chars=%s error=%s",
            record["event"], record["route"], record["logical_turn_id"],
            record.get("attempt", "-"), record.get("ttft_ms", "-"),
            record.get("total_ms", "-"), record.get("output_chars", "-"),
            record["error"] or "-")
    except Exception:
        pass
    _sink(record)
    return record
