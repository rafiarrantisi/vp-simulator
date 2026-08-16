"""Qora Mentor — readiness score calculator (PRD_QORA_MENTOR §4.4.2).

Weighted dimension averages from completed session reports, adjusted by
trajectory (improving vs declining), consistency (regular practice) and an
error penalty for unresolved critical reasoning errors. Always returns an
interpretation + confidence level; NOT a guarantee (disclaimer required in UI).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.mentor.models import ReasoningAutopsy
from app.domains.sessions.models import SessionRow

# PRD §4.4.2 weights (sum = 1.00)
_DIM_WEIGHTS = {
    "history_coverage": 0.20,
    "red_flags": 0.15,
    "diagnostic_reasoning": 0.15,
    "management": 0.15,
    "physical_exam": 0.10,
    "communication": 0.10,
    "ice_fife": 0.10,
    "questioning_technique": 0.05,
}
_ERROR_PENALTY_CAP = 10
_TRAJECTORY_WINDOW = 5


def _dim_pct(report: dict) -> dict[str, float]:
    """Normalize a session report's per_dimension scores to 0-100."""
    out: dict[str, float] = {}
    for dim, entry in (report.get("per_dimension") or {}).items():
        if not isinstance(entry, dict):
            continue
        mx = entry.get("max")
        sc = entry.get("score")
        try:
            mx, sc = float(mx), float(sc)
        except (TypeError, ValueError):
            continue
        if mx > 0:
            out[dim] = max(0.0, min(100.0, 100.0 * sc / mx))
    return out


def _completed_sessions(db: Session, user_id: str,
                        journey_id: str | None = None) -> list[SessionRow]:
    q = select(SessionRow).where(
        SessionRow.user_id == user_id, SessionRow.status == "completed",
        SessionRow.report.isnot(None))
    if journey_id:
        from app.domains.mentor.models import JourneyCase
        linked = select(JourneyCase.session_id).where(JourneyCase.journey_id == journey_id,
                                                      JourneyCase.session_id.isnot(None))
        q = q.where(SessionRow.id.in_(linked))
    rows = list(db.scalars(q.order_by(SessionRow.started_at.asc())))
    # ended_at may be NULL for sessions completed before the v2 fix — fall back
    # to started_at as the completion-time proxy (same practice day anyway).
    for r in rows:
        if r.ended_at is None:
            r.ended_at = r.started_at
    return [r for r in rows if r.ended_at is not None]


def _unresolved_critical_errors(db: Session, user_id: str, session_ids: list[str]) -> int:
    """Critical errors from autopsies of the sessions in scope (recent window)."""
    if not session_ids:
        return 0
    rows = db.scalars(select(ReasoningAutopsy).where(
        ReasoningAutopsy.session_id.in_(session_ids))).all()
    n = 0
    for a in rows:
        for e in a.errors_detected or []:
            if isinstance(e, dict) and e.get("severity") == "critical":
                n += 1
    return n


def calculate_readiness(db: Session, user_id: str,
                        journey_id: str | None = None) -> dict:
    """PRD §4.4.2 — full formula."""
    sessions = _completed_sessions(db, user_id, journey_id)
    if not sessions:
        return {"score": 0, "confidence": "insufficient_data", "session_count": 0,
                "base_score": 0, "trajectory_bonus": 1.0, "consistency_bonus": 1.0,
                "error_penalty": 0, "dimensions": {}, "interpretation": None}

    # Base score: weighted dimension averages across all sessions.
    dim_accum: dict[str, list[float]] = {}
    for s in sessions:
        for dim, pct in _dim_pct(s.report or {}).items():
            dim_accum.setdefault(dim, []).append(pct)
    dims = {d: round(sum(v) / len(v), 1) for d, v in dim_accum.items()}

    active_w = {d: w for d, w in _DIM_WEIGHTS.items() if d in dims}
    if not active_w:
        return {"score": 0, "confidence": "low", "session_count": len(sessions),
                "base_score": 0, "trajectory_bonus": 1.0, "consistency_bonus": 1.0,
                "error_penalty": 0, "dimensions": dims,
                "interpretation": interpret_score(0)}
    wsum = sum(active_w.values())
    base_score = sum(dims[d] * (w / wsum) for d, w in active_w.items())

    # Trajectory bonus from the last N overall scores.
    scores = [int(s.total_score or 0) for s in sessions[-_TRAJECTORY_WINDOW:]]
    if len(scores) >= 3:
        trajectory = (scores[-1] - scores[0]) / len(scores)
        trajectory_bonus = min(1.1, max(0.9, 1.0 + trajectory / 100))
    else:
        trajectory_bonus = 1.0

    # Consistency bonus: fraction of distinct days practised.
    dates = {s.ended_at.date() for s in sessions}
    span = (max(dates) - min(dates)).days + 1
    consistency = min(1.0, len(dates) / max(1, span))
    consistency_bonus = 0.9 + 0.1 * consistency

    # Error penalty: unresolved critical errors (recent autopsies).
    recent_ids = [s.id for s in sessions[-_TRAJECTORY_WINDOW:]]
    n_crit = _unresolved_critical_errors(db, user_id, recent_ids)
    error_penalty = min(_ERROR_PENALTY_CAP, n_crit * 2)

    raw = base_score * trajectory_bonus * consistency_bonus
    final_score = max(0, min(100, round(raw - error_penalty)))

    n = len(sessions)
    confidence = "high" if n >= 10 else "medium" if n >= 5 else "low"
    return {
        "score": final_score,
        "confidence": confidence,
        "session_count": n,
        "base_score": round(base_score),
        "trajectory_bonus": round(trajectory_bonus, 2),
        "consistency_bonus": round(consistency_bonus, 2),
        "error_penalty": error_penalty,
        "dimensions": dims,
        "interpretation": interpret_score(final_score),
    }


def interpret_score(score: int) -> dict:
    """PRD §4.4.2 interpretation tiers (design tokens for colors)."""
    if score >= 90:
        return {"level": "distinction", "label": "Exam ready — predicted distinction",
                "color": "var(--teal)"}
    if score >= 75:
        return {"level": "pass", "label": "Ready — predicted clear pass",
                "color": "var(--green)"}
    if score >= 60:
        return {"level": "borderline",
                "label": "Borderline — needs targeted improvement", "color": "var(--amber)"}
    if score >= 40:
        return {"level": "not_ready", "label": "Not ready — significant gaps",
                "color": "var(--red)"}
    return {"level": "foundation", "label": "Foundation needed — repeat basics",
            "color": "var(--red-d)"}


def readiness_history(db: Session, user_id: str,
                      journey_id: str | None = None) -> list[dict]:
    """Per-session readiness over time (for the trend line)."""
    sessions = _completed_sessions(db, user_id, journey_id)
    out = []
    running: list[float] = []
    for s in sessions:
        running.append(float(s.total_score or 0))
        out.append({
            "session_id": s.id,
            "case_id": s.case_id,
            "score": int(s.total_score or 0),
            "rolling_avg": round(sum(running) / len(running)),
            "completed_at": s.ended_at.isoformat(),
        })
    return out
