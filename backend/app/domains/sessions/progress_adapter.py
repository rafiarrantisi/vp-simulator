"""FASE 8 wiring — DB rows <-> canonical longitudinal model.

Thin app-layer bridge (DB-aware) over the pure `pipeline.progress` data
layer. No scoring, no LLM, no report rewriting: reads completed sessions,
adapts them via `adapt_session`, and derives unified progress/readiness.

- specialty resolution: V2 from case frontmatter, V3 from family registry;
  unknown shapes fall back to "unknown" (never crash scoring paths).
- progress recording: single shared path for V2 AND V3 score handlers via
  `apply_progress_for_session` (fixes the V3 0-XP under-count).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.domains.sessions.models import SessionRow

_registry_cache = {}


def cached_registry():
    """Process-local memo of the V3 registry (386 YAML reads otherwise).

    Content only changes on deploy + backend restart (same contract as the
    V2 catalogue lru_cache), so caching per worker is safe and keeps
    per-session loops (progress, history) from re-parsing on every row.
    """
    reg = _registry_cache.get("reg")
    if reg is None:
        from app.domains.sessions.v3_compat_schemas import default_registry
        reg = default_registry()
        _registry_cache["reg"] = reg
    return reg


def specialty_for_session(row: SessionRow) -> str:
    """Best-effort specialty for longitudinal coverage (never raises)."""
    try:
        if (row.content_schema or "legacy") == "new":
            reg = cached_registry()
            fam_id = row.family_id or (row.case_id if (row.case_id or "").startswith("fam_") else None)
            if fam_id and fam_id in reg.families:
                return str(reg.families[fam_id].primary_specialty or "unknown")
            # Presentation families resolve cross-family variants; fall back
            # to the variant's family when the session case_id is the umbrella.
            if row.variant_id and row.variant_id in reg.variants:
                v = reg.variants[row.variant_id]
                fam = reg.families.get(v.family_id)
                if fam is not None:
                    return str(fam.primary_specialty or "unknown")
            return "unknown"
        from app.domains.cases.v2_catalog import load_v2_case
        c = load_v2_case(row.case_id)
        return str((c.frontmatter or {}).get("specialty") or "unknown")
    except Exception:
        return "unknown"


def row_to_normalized(row: SessionRow, *, specialty: str | None = None) -> dict:
    """Adapt one SessionRow to a NormalizedSession dict (pipeline stays app-free)."""
    from pipeline.progress.longitudinal import adapt_session
    spec = specialty if specialty else specialty_for_session(row)
    ended = row.ended_at.isoformat() if getattr(row, "ended_at", None) else None
    started = row.started_at.isoformat() if getattr(row, "started_at", None) else None
    ns = adapt_session({
        "id": row.id,
        "case_id": row.case_id,
        "mode": row.mode,
        "content_schema": row.content_schema or "legacy",
        "family_id": row.family_id,
        "variant_id": row.variant_id,
        "total_score": row.total_score,
        "report": row.report if isinstance(row.report, dict) else {},
        "ended_at": ended,
        "started_at": started,
    }, specialty=spec)
    return ns.to_dict()


def completed_normalized(db: OrmSession, user_id: str, *, journey_id: str | None = None) -> list[dict]:
    """All completed sessions with a stored report, oldest->newest, normalized."""
    q = (select(SessionRow)
         .where(SessionRow.user_id == user_id,
                SessionRow.status == "completed",
                SessionRow.report.isnot(None))
         .order_by(SessionRow.started_at.asc()))
    if journey_id:
        from app.domains.mentor.models import JourneyCase
        linked = select(JourneyCase.session_id).where(
            JourneyCase.journey_id == journey_id, JourneyCase.session_id.isnot(None))
        q = q.where(SessionRow.id.in_(linked))
    rows = list(db.scalars(q))
    out = []
    for r in rows:
        try:
            out.append(row_to_normalized(r))
        except Exception:
            continue
    return out


def record_progress_for_report(user, *, case_id: str, specialty: str,
                               report: dict, content_schema: str = "legacy") -> None:
    """Shared V2+V3 gamification writer (parity; idempotent-safe via caller).

    Uses the pure `apply_progress_for_session` so both engines contribute
    identically: XP, streak, total_sessions, scoreHistory, completedCaseIds.
    """
    from pipeline.progress.longitudinal import adapt_report
    from pipeline.progress.progress import apply_progress_for_session
    prof = getattr(user, "profile", None)
    if prof is None:
        return
    try:
        ns = adapt_report(report if isinstance(report, dict) else {},
                          content_schema=content_schema or "legacy")
        dim_pcts = dict(ns.dim_pcts or {})
    except Exception:
        dim_pcts = {}
        try:
            dim_pcts = {str(k): float((v or {}).get("score", 0))
                        for k, v in (report.get("per_dimension") or {}).items()
                        if isinstance(v, dict)}
        except Exception:
            dim_pcts = {}
    try:
        overall = int((report or {}).get("overall", 0) or 0)
    except (TypeError, ValueError):
        overall = 0
    new_extra, new_state = apply_progress_for_session(
        dict(prof.extra or {}),
        {"xp": int(prof.xp or 0), "streak": int(prof.streak or 0),
         "total_sessions": int(prof.total_sessions or 0)},
        case_id=case_id, specialty=specialty or "unknown",
        overall=overall, dim_pcts=dim_pcts,
    )
    prof.extra = new_extra
    prof.xp = int(new_state.get("xp") or 0)
    prof.streak = int(new_state.get("streak") or 0)
    prof.total_sessions = int(new_state.get("total_sessions") or 0)


def critical_errors_recent(db: OrmSession, session_ids: list[str]) -> int:
    """Count critical reasoning errors in autopsies for the given sessions."""
    if not session_ids:
        return 0
    try:
        from sqlalchemy import select as _select
        from app.domains.mentor.models import ReasoningAutopsy
        rows = db.scalars(_select(ReasoningAutopsy).where(
            ReasoningAutopsy.session_id.in_(session_ids))).all()
        n = 0
        for a in rows:
            for e in a.errors_detected or []:
                if isinstance(e, dict) and e.get("severity") == "critical":
                    n += 1
        return n
    except Exception:
        return 0
