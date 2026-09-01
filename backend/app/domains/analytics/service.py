"""Pilot analytics aggregation (Fase 5 §35)."""
from statistics import median

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session as OrmSession

from app.domains.analytics.models import PilotEvent
from app.domains.auth.models import User
from app.domains.sessions.models import SessionRow, SessionTurn


def record_event(db: OrmSession, user_id: str, session_id: str | None,
                 event: str, stage: str | None, meta: dict) -> dict:
    case_id = (meta or {}).get("case_id") if isinstance(meta, dict) else None
    row = PilotEvent(user_id=user_id, session_id=session_id, event=event,
                     stage=stage, meta=meta or {}, case_id=case_id)
    db.add(row)
    db.commit()
    return {"id": row.id, "event": event, "recorded": True}


def build_analytics(db: OrmSession) -> dict:
    """Aggregate the pilot funnel answering the §35 questions. Pure DB reads."""
    out: dict = {}

    # --- reach & activation (§35.1-2) ---
    out["total_users"] = db.scalar(select(func.count(User.id))) or 0
    user_sessions = db.execute(
        select(SessionRow.user_id, func.count(SessionRow.id))
        .group_by(SessionRow.user_id)
    ).all()
    active_users = len(user_sessions)
    out["active_users"] = active_users  # have started ≥1 session (invited & practised)
    _users_with_completed = set(
        db.execute(
            select(SessionRow.user_id).where(SessionRow.status == "completed")
        ).scalars().all()
    )
    out["users_completed_first_case"] = len(_users_with_completed)
    out["completed_sessions"] = db.scalar(
        select(func.count(SessionRow.id)).where(SessionRow.status == "completed")
    ) or 0

    # --- engagement (§35.3-4) ---
    per_user_counts = [c for _, c in user_sessions]
    out["median_cases_per_active_user"] = round(median(per_user_counts), 1) if per_user_counts else 0
    # distinct calendar days with a session, per (already-active) user_indexed
    day_rows = db.execute(
        select(SessionRow.user_id, func.date(SessionRow.started_at))
        .group_by(SessionRow.user_id, func.date(SessionRow.started_at))
    ).all()
    from collections import Counter
    user_day_counts = Counter(u for u, _ in day_rows)
    out["users_returned_another_day"] = sum(1 for u, c in user_day_counts.items() if c >= 2)

    # --- session metrics ---
    total_sessions = db.scalar(select(func.count(SessionRow.id))) or 0
    completed = out["completed_sessions"]
    out["completion_rate"] = round(completed / total_sessions * 100, 1) if total_sessions else 0
    out["abandoned_sessions"] = total_sessions - completed  # never completed (≈ dropped)

    # --- voice vs text (§35.7) ---
    vt = {
        (r or "text"): n
        for r, n in db.execute(
            select(SessionTurn.input_type, func.count(SessionTurn.id))
            .where(SessionTurn.role == "user")
            .group_by(SessionTurn.input_type)
        ).all()
    }
    out["voice_turns"] = vt.get("voice", 0)
    out["text_turns"] = vt.get("text", 0)
    _tt = out["voice_turns"] + out["text_turns"]
    out["voice_vs_text"] = (round(out["voice_turns"] / _tt * 100, 1) if _tt else 0)

    # --- behavioural events (§35.9-11) ---
    ev = {
        e: n
        for e, n in db.execute(
            select(PilotEvent.event, func.count(PilotEvent.id))
            .group_by(PilotEvent.event)
        ).all()
    }
    out["events"] = ev
    out["debrief_opened_rate"] = round((ev.get("debrief_opened", 0) / completed * 100), 1) if completed else 0
    out["answer_key_revealed_rate"] = round((ev.get("answer_key_revealed", 0) / completed * 100), 1) if completed else 0
    out["retry_attempt_rate"] = round((ev.get("retry_attempt", 0) / completed * 100), 1) if completed else 0

    # --- language / mode distribution ---
    out["by_language"] = dict(db.execute(
        select(SessionRow.language, func.count(SessionRow.id)).group_by(SessionRow.language)).all() or {})
    out["by_mode"] = dict(db.execute(
        select(SessionRow.mode, func.count(SessionRow.id)).group_by(SessionRow.mode)).all() or {})

    # --- top specialties + presentations (§35.6) ---
    try:
        from app.domains.cases.v2_catalog import list_v2_cases
        cases = list(list_v2_cases() or [])
        spec_map = {getattr(c, "id", None): getattr(c, "specialty", "unknown") for c in cases}
        pres_map = {
            getattr(c, "id", None):
            (getattr(c, "presentation_id", None) or getattr(c, "presentation", None) or getattr(c, "id", None))
            for c in cases
        }
    except Exception:
        spec_map, pres_map = {}, {}
    spec_counts: dict[str, int] = {}
    pres_counts: dict[str, int] = {}
    for cid, n in db.execute(
        select(SessionRow.case_id, func.count(SessionRow.id))
        .where(SessionRow.status == "completed").group_by(SessionRow.case_id)
    ).all():
        sp = spec_map.get(cid, "unknown")
        spec_counts[sp] = spec_counts.get(sp, 0) + n
        pr = pres_map.get(cid, cid)
        pres_counts[pr] = pres_counts.get(pr, 0) + n
    out["top_specialties"] = dict(sorted(spec_counts.items(), key=lambda kv: -kv[1]))
    out["top_presentations"] = dict(sorted(pres_counts.items(), key=lambda kv: -kv[1]))

    # --- repeated learner weaknesses (§35.14) from stored reports ---
    dim_scores: dict[str, dict] = {}
    for report in db.execute(select(SessionRow.report).where(SessionRow.status == "completed")).scalars():
        if not isinstance(report, dict):
            continue
        for dim, d in (report.get("per_dimension") or {}).items():
            b = dim_scores.setdefault(dim, {"score": 0, "max": 0, "n": 0})
            try:
                b["score"] += float(d.get("score", 0))
                b["max"] += float(d.get("max", 0))
                b["n"] += 1
            except (TypeError, ValueError):
                continue
    _weak = []
    for dim, b in dim_scores.items():
        if b["max"] > 0 and b["n"] > 0:
            _weak.append({"dimension": dim, "avg_pct": round(b["score"] / b["max"] * 100, 1),
                          "n": b["n"]})
    out["weakest_dimensions"] = sorted(_weak, key=lambda x: x["avg_pct"])

    # --- pay intent (§35.16) from entitlements ---
    try:
        from app.domains.billing.models import Entitlement
        out["paying_users"] = db.scalar(
            select(func.count(distinct(Entitlement.user_id)))
            .where(Entitlement.plan != "free", Entitlement.status == "active")
        ) or 0
    except Exception:
        out["paying_users"] = 0

    return out