"""Qora Mentor — Today's Mission + end-of-journey report (FASE 13).

Deterministic mission cards over an already-planned journey. Principle:
**LLM understands and explains, the Qora planning engine decides.**
Pure functions — no DB, no network, no LLM.

Contract (pinned by Phase 13 integration):
- todays_mission: picks the first available journey case; state "ready"
  when cases exist; cta carries the picked case_id; expected_minutes comes
  from the picked case; why[0] quotes the pick's selection_reason.
- end_of_journey_report: verdict in {"completed", "ready"}; note starts
  with "Journey completed".
"""
from __future__ import annotations


def todays_mission(journey_cases=None, *, readiness=None) -> dict:
    """Build today's mission card from planned journey cases."""
    cases = [c for c in (journey_cases or []) if isinstance(c, dict)]
    pick = next(
        (c for c in cases if str(c.get("status") or "") == "available"),
        cases[0] if cases else {},
    )
    reason = str(pick.get("selection_reason") or "scheduled curriculum slot")
    try:
        minutes = int(pick.get("estimated_minutes") or 45)
    except (TypeError, ValueError):
        minutes = 45
    needs = []
    if isinstance(readiness, dict):
        for item in readiness.get("needs_work") or []:
            needs.append(item)
    return {
        "state": "ready" if cases else "empty",
        "cta": {
            "case_id": pick.get("case_id"),
            "focus_area": pick.get("focus_area"),
            "slot_type": pick.get("slot_type") or "core",
        },
        "expected_minutes": minutes,
        "why": [reason],
        "needs_work": needs,
        "day": pick.get("day", 1),
    }


def end_of_journey_report(summary=None, journey=None, *, readiness=None, evidence_log=None) -> dict:
    """Close a journey with a verdict + machine-checkable summary."""
    summ = summary if isinstance(summary, dict) else {}
    if not summ and isinstance(journey, dict):
        summ = journey
    progress = summ.get("progress") if isinstance(summ.get("progress"), dict) else {}
    try:
        total = int(progress.get("total") or 0)
    except (TypeError, ValueError):
        total = 0
    try:
        completed = int(progress.get("completed") or 0)
    except (TypeError, ValueError):
        completed = 0
    verdict = "completed" if total and completed >= total else "ready"
    log = [e for e in (evidence_log or []) if isinstance(e, dict)]
    return {
        "verdict": verdict,
        "note": (
            f"Journey completed: {completed}/{total} sessions; "
            f"{len(log)} evidence entr{'y' if len(log) == 1 else 'ies'} logged."
        ),
        "summary": dict(summ),
        "readiness": readiness if isinstance(readiness, dict) else {},
        "evidence_log": log,
    }
