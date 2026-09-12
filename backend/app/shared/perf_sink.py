"""Phase-1 voice foundation — queryable performance sink (ADR §4.5, §6 phase-0).

`qora.perf` / `qora.llm` log records were logger-only: nothing queryable for
p50/p90/p95 per route. This module appends the SAME metadata-only records to
append-only JSONL files under ``backend/data/perf/`` (one file per record
kind per UTC day), while the existing logger calls stay untouched.

PRIVACY CONTRACT (same as perf_marks/observability): timing, opaque IDs,
lengths and bounded labels ONLY. Never prompts, transcripts, clinical
content, keys, audio, or raw session identity. The allowlist below is the
enforcement point: unknown keys are dropped, long strings truncated, and
any secret-looking key is dropped even if allowlisted by name.

Files (created on demand, never deleted here):
  turn_perf-YYYYMMDD.jsonl       TurnClock summaries (one line per turn)
  llm_event-YYYYMMDD.jsonl       log_llm_event records
  patient_attempt-YYYYMMDD.jsonl log_patient_attempt records
  tts_event-YYYYMMDD.jsonl       (reserved; TTS stage rows when wired)

Override the directory for tests with QORA_PERF_DIR. All helpers are total
(never raise) so instrumentation can never fail a turn.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

# backend/data/perf — resolved from this file, not CWD (workers/pytest/CLI
# run from different directories).
_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "perf"

# Field allowlist: kind-specific scalar fields that may reach the sink.
# Anything else is dropped. Limits are (max string length).
_ALLOW = {
    "kind": 32,
    "event": 32,
    "route": 48,
    "schema": 24,
    "mode": 24,
    "outcome": 40,
    "role": 40,
    "engine": 40,
    "model": 120,
    "endpoint_kind": 32,
    "error": 80,
    "session_ref": 16,       # opaque 8-char prefix, never the full id
    "logical_turn_id": 96,   # opaque correlation id (session:turn), no content
    "lane_hash": 32,         # sha256 hex prefix of the gateway lane, opaque
    "attempt": None,         # int
    "attempts": None,        # int
    "ttft_ms": None,         # float
    "total_ms": None,        # float
    "output_chars": None,    # int
    "input_chars": None,     # int
    "content_schema": 24,
    "scoring_version": 64,
    "marks_ms": None,        # dict[str, float] — stage durations only
    "counts": None,          # dict[str, int] — chunk/byte counters only
    "missing": None,         # list[str] — milestone names only
    "at": 32,                # iso timestamp
}

_SECRET_SUBSTRINGS = (
    "key", "secret", "passwd", "password", "token", "bearer",
    "prompt", "transcript", "content", "text", "audio", "message",
    "authorization", "cookie",
)

_lock = Lock()


def perf_dir() -> Path:
    """Sink directory (QORA_PERF_DIR override for tests/scratch)."""
    try:
        override = os.environ.get("QORA_PERF_DIR", "").strip()
        if override:
            return Path(override)
    except Exception:
        pass
    return _DEFAULT_DIR


def _clean_string(value, limit: int) -> str:
    try:
        text = "" if value is None else str(value)
    except Exception:
        return ""
    text = " ".join(text.split())
    return text[:limit] if len(text) > limit else text


def _clean_number(value):
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value if abs(value) < 10 ** 12 else 0
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                return 0
            return round(value, 3) if abs(value) < 10 ** 12 else 0
    except Exception:
        pass
    return 0


def sanitize(record: dict) -> dict:
    """Project a record onto the allowlist. Unknown/secret keys dropped."""
    out: dict = {}
    try:
        items = list((record or {}).items())
    except Exception:
        return out
    for key, value in items:
        try:
            name = str(key)
        except Exception:
            continue
        lowered = name.lower()
        if any(s in lowered for s in _SECRET_SUBSTRINGS):
            continue
        if name not in _ALLOW:
            continue
        limit = _ALLOW[name]
        if name == "logical_turn_id":
            # Raw session:turn identity stays out of the sink; the stable
            # hash preserves cross-row correlation (joins) without it.
            out[name] = _opaque(value)
        elif limit is None:
            if name in ("marks_ms", "counts"):
                if isinstance(value, dict):
                    clean = {}
                    for k, v in list(value.items())[:64]:
                        try:
                            clean[str(k)[:48]] = _clean_number(v)
                        except Exception:
                            continue
                    out[name] = clean
            elif name == "missing":
                try:
                    out[name] = [str(m)[:48] for m in list(value or [])[:32]]
                except Exception:
                    out[name] = []
            else:
                out[name] = _clean_number(value)
        else:
            out[name] = _clean_string(value, limit)
    return out


def lane_hash(lane: str | None) -> str:
    """Opaque correlation hash for a gateway lane (never the raw lane)."""
    try:
        if not lane:
            return ""
        return hashlib.sha256(str(lane).encode()).hexdigest()[:16]
    except Exception:
        return ""


def session_ref(session_id: str | None) -> str:
    """Opaque short ref (same 8-char-prefix precedent as the TTS log)."""
    try:
        text = str(session_id or "")
        return text[:8] if text else ""
    except Exception:
        return ""


def _opaque(value: str | None) -> str:
    """Stable opaque join key: sha256 hex prefix (raw identity never lands
    in the sink; equality joins across rows still work)."""
    try:
        if not value:
            return ""
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    except Exception:
        return ""


def append_record(record: dict) -> dict:
    """Append one sanitized record to today's kind file. Total, never raises.

    Returns the sanitized record (what was actually persisted).
    """
    clean = sanitize(record)
    kind = clean.get("kind") or "unknown"
    try:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        directory = perf_dir()
        with _lock:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                path = directory / f"{kind}-{day}.jsonl"
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(clean, ensure_ascii=False,
                                       separators=(",", ":")) + "\n")
            except Exception:
                pass
    except Exception:
        pass
    return clean


def iter_records(kind: str, *, days: int = 7,
                 directory: Path | None = None) -> list[dict]:
    """Read back records of one kind (for the CLI/tests). Never raises."""
    out: list[dict] = []
    try:
        base = Path(directory) if directory else perf_dir()
        if not base.is_dir():
            return out
        files = sorted(base.glob(f"{kind}-*.jsonl"))
        try:
            n = max(1, int(days))
        except (TypeError, ValueError):
            n = 7
        for path in files[-n:]:
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        if isinstance(obj, dict):
                            out.append(obj)
            except Exception:
                continue
    except Exception:
        pass
    return out


def nearest_rank(sorted_vals: list[float], pct: float) -> float | None:
    """Nearest-rank quantile (the ADR §7 estimator lock-in)."""
    try:
        if not sorted_vals:
            return None
        import math
        n = len(sorted_vals)
        p = min(100.0, max(0.0, float(pct))) / 100.0
        rank = max(1, int(math.ceil(p * n)))
        return float(sorted_vals[rank - 1])
    except Exception:
        return None
