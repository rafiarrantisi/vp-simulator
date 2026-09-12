"""Phase 2 — lightweight turn milestone clock (brief §11).

One monotonic-clock recorder per logical turn. Records DURATIONS, COUNTS and
bounded outcome labels ONLY — never prompts, transcripts, rubrics, diagnoses,
answer keys, secrets, or any clinical payload (same guarantee as
`observability.log_llm_event`: structural types admit only str labels and
numbers, so clinical content cannot flow through by construction).

Milestones (§11.2): request_received, auth_done, context_ready,
db_preflight_done, llm_request_start, llm_first_token, first_chunk_yielded,
first_content_sent, stream_complete, db_persist_complete, request_complete.
Missing stages on failed/cancelled turns are recorded explicitly, never
backfilled. All helpers are total (never raise).
"""
from __future__ import annotations

import logging
import time

_log = logging.getLogger("qora.perf")

MILESTONES = (
    "request_received",
    "auth_done",
    "context_ready",
    "db_preflight_done",
    "llm_request_start",
    "llm_first_token",
    "first_chunk_yielded",
    "first_content_sent",
    "stream_complete",
    "db_persist_complete",
    "request_complete",
)


def _label(value, limit: int = 48) -> str:
    try:
        text = "" if value is None else str(value)
    except Exception:
        return ""
    return text[:limit]


class TurnClock:
    """Monotonic milestone recorder for one logical turn."""

    def __init__(self, *, route: str = "", schema: str = "", mode: str = ""):
        self.route = _label(route)
        self.schema = _label(schema)
        self.mode = _label(mode)
        self._t0 = time.perf_counter_ns()
        self._marks: dict[str, int] = {}
        self._counts: dict[str, int] = {}
        self.outcome = ""

    def mark(self, name: str) -> None:
        try:
            if name in MILESTONES and name not in self._marks:
                self._marks[name] = time.perf_counter_ns()
        except Exception:
            pass

    def count(self, name: str, n: int = 1) -> None:
        try:
            key = _label(name, 32)
            self._counts[key] = self._counts.get(key, 0) + max(0, int(n))
        except Exception:
            pass

    def finish(self, outcome: str) -> dict:
        try:
            self.outcome = _label(outcome, 32)
        except Exception:
            self.outcome = ""
        return self.summary()

    def elapsed_ms(self, name: str) -> float | None:
        try:
            ts = self._marks.get(name)
            if ts is None:
                return None
            return round((ts - self._t0) / 1e6, 1)
        except Exception:
            return None

    def summary(self) -> dict:
        try:
            marks = {m: self.elapsed_ms(m) for m in MILESTONES if m in self._marks}
            return {
                "kind": "turn_perf",
                "route": self.route,
                "schema": self.schema,
                "mode": self.mode,
                "outcome": self.outcome,
                "marks_ms": marks,
                "counts": dict(self._counts),
                "missing": [m for m in MILESTONES if m not in self._marks],
            }
        except Exception:
            return {"kind": "turn_perf", "outcome": "summary_failed"}

    def log_summary(self) -> dict:
        summary = self.summary()
        try:
            _log.info(
                "turn_perf route=%s schema=%s outcome=%s marks=%s",
                summary.get("route"), summary.get("schema"),
                summary.get("outcome"), summary.get("marks_ms"),
            )
        except Exception:
            pass
        # Phase-1: same record ALSO goes to the queryable JSONL sink
        # (backend/data/perf/turn_perf-*.jsonl) for p50/p90/p95 per route.
        # Logger output is unchanged; sink write is total (never raises).
        try:
            from app.shared.perf_sink import append_record
            append_record(summary)
        except Exception:
            pass
        return summary
