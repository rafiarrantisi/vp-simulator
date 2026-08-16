"""Qora Mentor — business logic (PRD_QORA_MENTOR §4.1, §4.4).

Journey lifecycle: proposed → active → completed | abandoned.
Case lifecycle: locked → available → in_progress → completed.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.cases.v2_catalog import list_v2_cases
from app.domains.mentor import journey_builder
from app.domains.mentor.case_selector import select_cases
from app.domains.mentor.models import JourneyCase, LearningJourney, ReasoningAutopsy

_log = logging.getLogger("mentor.service")

MAX_CUSTOMIZATIONS = 10


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Story → proposal
# ---------------------------------------------------------------------------

def create_journey(db: Session, user_id: str, institution_id: str, story: str) -> dict:
    """Phase 1: submit story → context → case selection → proposal."""
    context = journey_builder.extract_context(story)
    cases = list_v2_cases()
    selected = select_cases(context, cases)
    if not selected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Tidak ada kasus yang cocok dengan cerita kamu — coba ceritain lagi dengan "
            "spesialisasi atau topik yang lebih spesifik.",
        )
    proposal = journey_builder.generate_proposal(context, selected)

    journey = LearningJourney(
        user_id=user_id,
        institution_id=institution_id,
        user_story=story,
        extracted_context=context,
        proposed_plan=proposal,
        status="proposed",
        readiness_start=proposal.get("readiness_start"),
        readiness_target=proposal.get("readiness_target", 80),
    )
    db.add(journey)
    db.flush()
    for c in proposal["cases"]:
        db.add(JourneyCase(
            journey_id=journey.id,
            day_number=int(c["day"]),
            case_id=c["case_id"],
            focus_area=c.get("focus_area"),
            learning_objective=c.get("learning_objective"),
            estimated_minutes=int(c.get("estimated_minutes") or 45),
            status="locked",
        ))
    db.commit()
    db.refresh(journey)
    _log.info("journey created %s for user %s (%d cases)", journey.id, user_id,
              len(proposal["cases"]))
    return journey_detail(db, journey, include_proposal=True)


# ---------------------------------------------------------------------------
# Customize (proposed stage)
# ---------------------------------------------------------------------------

def customize_journey(db: Session, user_id: str, journey_id: str, feedback: str) -> dict:
    """Chat-based adjustment. Deterministic re-selection driven by the feedback
    (LLM refinement is applied on top when a key is present)."""
    journey = _owned(db, user_id, journey_id)
    if journey.status != "proposed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Journey sudah {journey.status} — customize hanya bisa sebelum mulai.",
        )

    ctx = dict(journey.extracted_context or {})
    old_days = {c["day"]: c["case_id"] for c in journey.proposed_plan.get("cases", [])}

    # Re-selection: feedback keywords feed the weakness pool.
    extra_ctx = journey_builder.extract_context(feedback)
    merged_weak = list(dict.fromkeys(
        (ctx.get("weaknesses") or []) + (extra_ctx.get("weaknesses") or [])
    ))
    ctx["weaknesses"] = merged_weak or ctx.get("weaknesses")
    if extra_ctx.get("timeline_days"):
        ctx["timeline_days"] = extra_ctx["timeline_days"]
    if extra_ctx.get("level") and extra_ctx["level"] != "general":
        ctx["level"] = extra_ctx["level"]

    cases = list_v2_cases()
    selected = select_cases(ctx, cases)
    if not selected:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Feedback tidak menghasilkan kasus yang cocok.")
    proposal = journey_builder.generate_proposal(ctx, selected)

    new_days = {c["day"]: c["case_id"] for c in proposal["cases"]}
    changes = [
        f"day_{d}: {old_days.get(d, '-')} → {new_days[d]}"
        for d in sorted(set(old_days) | set(new_days))
        if old_days.get(d) != new_days.get(d)
    ]
    if not changes:
        changes = ["proposal: struktur dipertahankan"]

    journey.extracted_context = ctx
    journey.proposed_plan = proposal
    journey.user_feedback = (journey.user_feedback or "") + f"\n{feedback}" if journey.user_feedback else feedback
    journey.updated_at = _now()
    db.commit()
    db.refresh(journey)
    return {"updated_proposal": journey_detail(db, journey, include_proposal=True),
            "changes": changes}


# ---------------------------------------------------------------------------
# Accept / abandon
# ---------------------------------------------------------------------------

def accept_journey(db: Session, user_id: str, journey_id: str) -> dict:
    journey = _owned(db, user_id, journey_id)
    if journey.status not in ("proposed", "active"):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Journey sudah {journey.status}.")
    if journey.status == "proposed":
        journey.status = "active"
        journey.started_at = _now()
        journey.final_plan = journey.proposed_plan
        journey.readiness_current = journey.readiness_start
    # Unlock the first case (earliest day).
    first = _unlock_next(db, journey)
    journey.updated_at = _now()
    db.commit()
    db.refresh(journey)
    data = journey_detail(db, journey, include_proposal=False)
    data["next_case"] = _case_view(first) if first else None
    return data


def abandon_journey(db: Session, user_id: str, journey_id: str) -> dict:
    journey = _owned(db, user_id, journey_id)
    if journey.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Journey sudah selesai.")
    journey.status = "abandoned"
    journey.updated_at = _now()
    db.commit()
    return {"id": journey.id, "status": journey.status}


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

def list_journeys(db: Session, user_id: str) -> list[dict]:
    rows = db.scalars(
        select(LearningJourney).where(LearningJourney.user_id == user_id)
        .order_by(LearningJourney.created_at.desc())
    ).all()
    return [journey_detail(db, j, include_proposal=False) for j in rows]


def get_journey(db: Session, user_id: str, journey_id: str, *, include_proposal: bool = False) -> dict:
    journey = _owned(db, user_id, journey_id)
    return journey_detail(db, journey, include_proposal=include_proposal)


def next_case(db: Session, user_id: str, journey_id: str) -> dict:
    """Next available (or in-progress) case for the active journey."""
    journey = _owned(db, user_id, journey_id)
    if journey.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Journey {journey.status} — hanya journey aktif punya case.")
    jc = db.scalars(
        select(JourneyCase).where(JourneyCase.journey_id == journey.id,
                                  JourneyCase.status.in_(("available", "in_progress")))
        .order_by(JourneyCase.day_number).limit(1)
    ).first()
    if jc is None:
        return {"case": None, "journey_status": "completed"}
    return {"case": _case_view(jc), "journey_status": journey.status}


def complete_case(db: Session, user_id: str, journey_id: str,
                  case_id: str, session_id: str, score: int) -> dict:
    journey = _owned(db, user_id, journey_id)
    jc = db.scalar(select(JourneyCase).where(
        JourneyCase.journey_id == journey.id, JourneyCase.case_id == case_id))
    if jc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case tidak ada di journey ini.")
    if jc.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Case ini sudah dikerjakan.")

    jc.status = "completed"
    jc.session_id = session_id
    jc.score = max(0, min(100, score))
    jc.completed_at = _now()
    if jc.day_number > journey.current_day:
        journey.current_day = jc.day_number
    journey.updated_at = _now()

    # Interim readiness (Phase 1): simple average of completed scores.
    # Phase 2 replaces this with the full readiness_calculator formula (§4.4.2).
    scores = [c.score for c in journey.cases if c.score is not None]
    journey.readiness_current = round(sum(scores) / len(scores)) if scores else journey.readiness_start

    nxt = _unlock_next(db, journey)
    if nxt is None:
        journey.status = "completed"
        journey.completed_at = _now()

    db.commit()
    db.refresh(journey)
    data = journey_detail(db, journey, include_proposal=False)
    data["next_case"] = _case_view(nxt) if nxt else None
    return data


def _unlock_next(db: Session, journey: LearningJourney) -> JourneyCase | None:
    """First locked case by day → available. Returns it (or None if all done)."""
    jc = db.scalars(
        select(JourneyCase).where(JourneyCase.journey_id == journey.id,
                                  JourneyCase.status == "locked")
        .order_by(JourneyCase.day_number).limit(1)
    ).first()
    if jc:
        jc.status = "available"
    return jc


# ---------------------------------------------------------------------------
# Reasoning autopsy (PRD §4.2)
# ---------------------------------------------------------------------------

def generate_autopsy_for_session(db: Session, user_id: str, session_id: str) -> dict:
    """Post-score: generate + store the autopsy, then check continuity trigger."""
    from app.domains.cases.v2_catalog import load_v2_case
    from app.domains.mentor.autopsy_generator import generate_autopsy
    from app.domains.mentor.continuity_engine import check_continuity_trigger
    from app.domains.sessions.models import SessionTurn
    from app.domains.sessions.router import _owned

    s = _owned(db, session_id, _fake_user(user_id))
    if s.status != "completed" or not s.report:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Autopsy hanya bisa dibuat setelah sesi selesai dinilai.")
    try:
        case = load_v2_case(s.case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Case tidak ditemukan.")

    rows = db.scalars(select(SessionTurn).where(SessionTurn.session_id == session_id)
                      .order_by(SessionTurn.turn_number)).all()
    transcript = [{"role": r.role, "content": r.content} for r in rows]

    data = generate_autopsy(case, transcript, s.report)

    # Existing autopsy for this session → update in place (idempotent).
    row = db.scalar(select(ReasoningAutopsy).where(
        ReasoningAutopsy.session_id == session_id))
    if row is None:
        row = ReasoningAutopsy(session_id=session_id)
        db.add(row)
    # Link to journey if the session belongs to one.
    jc = db.scalar(select(JourneyCase).where(JourneyCase.session_id == session_id))
    if jc:
        row.journey_id = jc.journey_id
    row.user_pathway = data.get("user_pathway")
    row.expert_pathway = data.get("expert_pathway")
    row.divergence_points = data.get("divergence_points")
    row.errors_detected = data.get("errors_detected")
    row.pearl = data.get("pearl")
    row.readiness_impact = data.get("readiness_impact", 0)

    continuity = check_continuity_trigger(db, data, s.case_id, user_id, session_id)
    db.commit()
    db.refresh(row)

    return {"autopsy": _autopsy_view(row), "continuity": continuity}


def get_autopsy(db: Session, user_id: str, session_id: str) -> dict | None:
    from app.domains.sessions.router import _owned
    _owned(db, session_id, _fake_user(user_id))
    row = db.scalar(select(ReasoningAutopsy).where(
        ReasoningAutopsy.session_id == session_id))
    return _autopsy_view(row) if row else None


def _autopsy_view(row) -> dict:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "journey_id": row.journey_id,
        "user_pathway": row.user_pathway or [],
        "expert_pathway": row.expert_pathway or [],
        "divergence_points": row.divergence_points or [],
        "errors_detected": row.errors_detected or [],
        "pearl": row.pearl,
        "readiness_impact": row.readiness_impact,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _fake_user(user_id: str):
    """Minimal User-like object for sessions.router._owned ownership checks."""
    from app.domains.auth.models import User
    u = User(id=user_id)
    return u


# ---------------------------------------------------------------------------
# Patient continuity (PRD §4.3)
# ---------------------------------------------------------------------------

def pending_continuity(db: Session, user_id: str) -> dict:
    from app.domains.mentor.continuity_engine import pending_continuity as _pending
    return {"pending": _pending(db, user_id)}


# ---------------------------------------------------------------------------
# Readiness (PRD §4.4)
# ---------------------------------------------------------------------------

def get_readiness(db: Session, user_id: str, journey_id: str | None = None) -> dict:
    from app.domains.mentor.readiness_calculator import calculate_readiness
    return calculate_readiness(db, user_id, journey_id)


def readiness_report(db: Session, user_id: str, journey_id: str | None = None) -> dict:
    """Full report: score + dimensions + weakest area + recommendations."""
    from app.domains.mentor.readiness_calculator import (
        _DIM_WEIGHTS, calculate_readiness, readiness_history)
    r = calculate_readiness(db, user_id, journey_id)
    if r.get("session_count", 0) == 0:
        return {"readiness": r, "history": [], "weakest": None, "recommendations": [],
                "disclaimer": _DISCLAIMER}

    dims = r.get("dimensions") or {}
    weakest = min(dims, key=dims.get) if dims else None
    weakest_pct = dims.get(weakest) if weakest else None

    recs: list[str] = []
    if weakest:
        recs.append(f"Fokus pada {weakest.replace('_', ' ')} — skor terendah ({weakest_pct}%).")
    if (r.get("error_penalty") or 0) > 0:
        recs.append("Kamu punya red flag kritis yang terlewat — ulangi skrining red flag.")
    if (r.get("trajectory_bonus") or 1.0) < 1.0:
        recs.append("Skor cenderung menurun — konsisten latihan, jangan skip hari.")
    if (r.get("consistency_bonus") or 1.0) < 0.95:
        recs.append("Latihan belum rutin — jadwalkan sesi harian.")
    if not recs:
        recs.append("Pertahankan konsistensi dan lanjut ke kasus yang lebih sulit.")
    if weakest and weakest_pct is not None and weakest_pct < 60:
        recs.append("Ulangi hari-hari yang membahas area terlemah di journey kamu.")

    return {
        "readiness": r,
        "history": readiness_history(db, user_id, journey_id)[-10:],
        "weakest": {"dimension": weakest, "pct": weakest_pct} if weakest else None,
        "recommendations": recs[:4],
        "disclaimer": _DISCLAIMER,
    }


_DISCLAIMER = (
    "Readiness score adalah estimasi berdasarkan rubrik OSCE dan performa latihan. "
    "Bukan guarantee kelulusan. Gunakan sebagai panduan, bukan pengganti persiapan "
    "resmi. Selalu konsultasikan dengan pembimbing klinis Anda."
)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def _owned(db: Session, user_id: str, journey_id: str) -> LearningJourney:
    journey = db.get(LearningJourney, journey_id)
    if journey is None or journey.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Journey tidak ditemukan.")
    return journey


def _case_view(jc: JourneyCase) -> dict:
    return {
        "day": jc.day_number,
        "case_id": jc.case_id,
        "focus_area": jc.focus_area,
        "learning_objective": jc.learning_objective,
        "estimated_minutes": jc.estimated_minutes,
        "status": jc.status,
        "score": jc.score,
    }


def journey_detail(db: Session, journey: LearningJourney, *, include_proposal: bool) -> dict:
    cases = journey.cases  # ordered by day_number (relationship)
    completed = [c for c in cases if c.status == "completed"]
    total = len(cases)
    percent = round(100 * len(completed) / total) if total else 0
    data = {
        "id": journey.id,
        "package_name": (journey.proposed_plan or {}).get("package_name", "Learning Journey"),
        "status": journey.status,
        "current_day": journey.current_day,
        "story": journey.user_story,
        "context": journey.extracted_context,
        "readiness": {
            "start": journey.readiness_start,
            "current": journey.readiness_current,
            "target": journey.readiness_target,
        },
        "progress": {"completed": len(completed), "total": total, "percent": percent},
        "cases": [_case_view(c) for c in cases],
        "created_at": journey.created_at.isoformat() if journey.created_at else None,
        "started_at": journey.started_at.isoformat() if journey.started_at else None,
    }
    if include_proposal:
        plan = journey.proposed_plan or {}
        data["proposal"] = {
            "package_name": plan.get("package_name"),
            "duration_days": plan.get("duration_days"),
            "reasoning": plan.get("reasoning"),
            "milestones": plan.get("milestones", []),
            "readiness_start": plan.get("readiness_start"),
            "readiness_target": plan.get("readiness_target"),
        }
    return data
