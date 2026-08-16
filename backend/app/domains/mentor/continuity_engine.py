"""Qora Mentor — patient memory & continuity engine (PRD_QORA_MENTOR §4.3).

A critical missed red flag triggers a "returning patient" case in a future
session — the student sees the consequence of their reasoning error.

Flow:
1. `check_continuity_trigger(autopsy, case_id, user_id)` — critical
   missed_red_flag → find matching patient_series → advance user_patient_history
   → return the next visit descriptor.
2. `pending_continuity(user_id)` — the queued next visit for the dashboard
   ("Returning patient: Ibu Siti (Visit 2)").
3. `build_patient_continuity_context(series, visit)` — the context block
   injected into the patient prompt for the continuity case.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.mentor.models import PatientSeries, UserPatientHistory

_log = logging.getLogger("mentor.continuity")

MAX_VISITS = 3  # PRD §12: max 3 visits per series (safety against confusion)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _case_red_flags(case) -> list[str]:
    """Normalized red-flag ids/items for the case."""
    out: list[str] = []
    for rf in case.red_flag_items():
        out.append(str(rf.get("id") or rf.get("item") or "").strip().lower())
        out.append(str(rf.get("item") or "").strip().lower())
    return [x for x in out if x]


def find_series_by_trigger(db: Session, case_id: str, trigger_value: str) -> PatientSeries | None:
    """A series whose case_sequence contains `case_id` and whose triggers match
    `trigger_value` (red-flag id/item, lowercased)."""
    trigger_value = (trigger_value or "").strip().lower()
    series_rows = db.scalars(select(PatientSeries)).all()
    for s in series_rows:
        seq = [str(x).lower() for x in (s.case_sequence or [])]
        if case_id.lower() not in seq:
            continue
        for tr in s.triggers or []:
            val = str(tr.get("value") or "").strip().lower()
            if val and (val == trigger_value or val in trigger_value or trigger_value in val):
                return s
    return None


def check_continuity_trigger(db: Session, autopsy: dict, case_id: str, user_id: str,
                             session_id: str | None = None) -> dict | None:
    """Critical missed red flag → queue the next visit. Returns a descriptor
    (or None when no series matches). Idempotent per session via last_session_id."""
    critical = [e for e in (autopsy.get("errors_detected") or [])
                if e.get("severity") == "critical" and e.get("type") == "missed_red_flag"]
    if not critical:
        return None

    # Match by the case's red-flag id first; fall back to item text.
    values = {str(e.get("value") or "").strip().lower() for e in critical}
    series = None
    for v in values:
        series = find_series_by_trigger(db, case_id, v)
        if series:
            break
    if series is None:
        return None

    history = db.scalar(select(UserPatientHistory).where(
        UserPatientHistory.user_id == user_id,
        UserPatientHistory.series_id == series.id))
    if history is None:
        history = UserPatientHistory(user_id=user_id, series_id=series.id,
                                     current_visit=1, status="active")
        db.add(history)

    seq = [str(x) for x in (series.case_sequence or [])]
    # Don't double-advance when the same session re-runs the autopsy — but do
    # return the same pending descriptor (idempotent POST, same response).
    if session_id and history.last_session_id == session_id:
        return _descriptor(db, series, history, seq)
    # current_visit = the visit the user is ON (1-based). Completing the case
    # of the current visit advances to the next visit.
    history.current_visit = min(history.current_visit + 1, len(seq) + 1)
    history.last_session_id = session_id
    history.errors_detected = autopsy.get("errors_detected") or []
    history.status = "active"
    history.updated_at = _now()
    db.commit()
    return _descriptor(db, series, history, seq)


def _descriptor(db: Session, series: PatientSeries, history: UserPatientHistory,
                seq: list[str]) -> dict | None:
    """Pending-visit descriptor; None when the series is finished."""
    visit = history.current_visit
    if visit > len(seq):
        if history.status != "completed":
            history.status = "completed"
            history.updated_at = _now()
            db.commit()
            _log.info("continuity series %s completed (user %s)",
                      series.id, history.user_id)
        return None
    nxt = seq[visit - 1]  # 0-indexed: current_visit 2 → seq[1] (visit 2's case)
    ctx = series.next_visit_context or {}
    return {
        "series_id": series.id,
        "next_case_id": nxt,
        "visit_number": visit,
        "total_visits": len(seq),
        "context": {
            "days_since_last": ctx.get("days_later", 3),
            "previous_diagnosis": series.base_condition,
            "previous_treatment": ctx.get("previous_treatment", "obat sesuai diagnosis"),
            "current_concern": ctx.get("reason", "gejala tidak membaik"),
            "new_symptoms": ctx.get("new_symptoms", []),
        },
    }


def pending_continuity(db: Session, user_id: str) -> dict | None:
    """The queued continuity case (if any) for the user's next session."""
    histories = db.scalars(select(UserPatientHistory).where(
        UserPatientHistory.user_id == user_id,
        UserPatientHistory.status == "active")).all()
    for h in histories:
        series = db.get(PatientSeries, h.series_id)
        if series is None:
            continue
        seq = [str(x) for x in (series.case_sequence or [])]
        # Queued only after a trigger session happened, and only while visits remain.
        if h.last_session_id is None or h.current_visit > len(seq):
            continue
        nxt = seq[h.current_visit - 1]
        ctx = series.next_visit_context or {}
        return {
            "series_id": series.id,
            "name": series.name,
            "age": series.age,
            "gender": series.gender,
            "visit_number": h.current_visit,
            "total_visits": len(seq),
            "next_case_id": nxt,
            "story_so_far": {
                "previous_diagnosis": series.base_condition,
                "reason": ctx.get("reason", "gejala tidak membaik"),
                "new_symptoms": ctx.get("new_symptoms", []),
            },
        }
    return None


def build_patient_continuity_context(series: PatientSeries, visit: int, ctx: dict | None = None) -> dict:
    """Context block injected into the patient prompt for a continuity case
    (PRD §4.3.5 — the patient remembers the previous visit)."""
    ctx = ctx or series.next_visit_context or {}
    return {
        "is_returning_patient": True,
        "days_since_last": ctx.get("days_later", 3),
        "previous_diagnosis": series.base_condition,
        "previous_treatment": ctx.get("previous_treatment", "obat sesuai diagnosis"),
        "current_concern": ctx.get("reason", "sesuatu memburuk"),
        "new_symptoms": ctx.get("new_symptoms", []),
        "visit_number": visit,
    }
