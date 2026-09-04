"""FASE 6 — Session hardening helpers (additive, no contract change).

Covers the audit findings without touching the V2 external shapes:
  * completed-session guard — turns/stream/pf reject on `completed`
    (reopening must go through score/report, not new turns);
  * duplicate-send idempotency — an identical user text that already has a
    patient reply returns the stored reply instead of persisting a duplicate
    pair (covers double-Enter, retry after interrupted stream, and the
    frontend stream→fallback path which would otherwise persist twice);
  * canonical vitals formatter — single source for vitals text so PF result,
    answer key, judge ground truth and scorer all read the exact same
    persisted variant values (no duplicate/conflicting vitals).

All helpers are pure w.r.t. the persisted SessionRow/variant — V3 engine
still receives only transcript/text and never knows about microphones.
"""
from __future__ import annotations

from fastapi import HTTPException, status


def ensure_turnable(session_status: str | None) -> None:
    """Reject turns/stream/pf on completed sessions (reopen via report)."""
    if (session_status or "") == "completed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "session already completed — reopen the report instead of sending turns",
        )


def find_duplicate_reply(history: list[dict], text: str) -> str | None:
    """Return the stored patient reply when `text` duplicates the last user turn.

    `history` is the `_history()` list [{role, content}]. When the last two
    entries are user(text)+patient(reply) and the incoming text matches the
    last user text (exact, trimmed), the caller should return the stored
    reply instead of calling the LLM + persisting a duplicate pair.
    """
    t = (text or "").strip()
    if not t or len(history) < 2:
        return None
    last, prev = history[-1], history[-2]
    if last.get("role") != "patient" or prev.get("role") != "user":
        return None
    if (prev.get("content") or "").strip() != t:
        return None
    reply = (last.get("content") or "").strip()
    return reply or None


def format_vitals_canonical(variant) -> str:
    """Single canonical vitals string from the persisted variant.

    Used by PF fallback text; answer key / judge ground truth read the same
    `variant.physical_exam.vitals` objects so values can never diverge.
    Format: `name valueunit; ...` (e.g. `HR 98bpm; Temp 37.9C`).
    """
    try:
        pe = getattr(variant, "physical_exam", None)
        vitals = getattr(pe, "vitals", None) or []
    except Exception:
        return ""
    parts: list[str] = []
    for vt in vitals:
        try:
            name = getattr(vt, "name", "") or ""
            value = getattr(vt, "value", None)
            if value is None or str(value).strip() == "":
                continue
            unit = getattr(getattr(vt, "unit", None), "value", "") or ""
            parts.append(f"{name} {value}{unit}".strip())
        except Exception:
            continue
    return "; ".join(parts)


def general_with_vitals(variant) -> str:
    """Canonical `general` fallback text (appearance + vitals)."""
    try:
        pe = getattr(variant, "physical_exam", None)
        appearance = (getattr(pe, "general_appearance", None) or "").strip()
    except Exception:
        appearance = ""
    vitals_txt = format_vitals_canonical(variant)
    if appearance and vitals_txt:
        return f"{appearance} — {vitals_txt}"
    return appearance or vitals_txt
