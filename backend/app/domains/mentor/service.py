"""Qora Mentor — business logic (PRD_QORA_MENTOR §4.1, §4.4; FASE 10 adaptive).

Journey lifecycle: proposed → active → completed | abandoned.
Case lifecycle: locked → available → in_progress → completed.

FASE 10 (Adaptive Mentor V1): the planning engine (planning_policy +
select_journey_cases) decides the curriculum deterministically; the LLM only
understands the story and explains. Slot metadata (slot_type,
selection_reason, mandatory) lives in the plan JSON columns
(proposed_plan/final_plan) — NO new tables or columns (STOP gate: alembic
count and model attrs are pinned by test).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.cases.v2_catalog import list_v2_cases
from app.domains.mentor import journey_builder
from app.domains.mentor.case_selector import select_cases, select_journey_cases
from app.domains.mentor.models import JourneyCase, LearningJourney, ReasoningAutopsy

_log = logging.getLogger("mentor.service")

MAX_CUSTOMIZATIONS = 10


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Story → proposal
# ---------------------------------------------------------------------------

def create_journey(db: Session, user_id: str, institution_id: str, story: str) -> dict:
    """Phase 1: submit story → context → case selection → proposal.

    FASE 10: unified deterministic planner (V3 eligible families + V2
    cases, one engine). Clarification questions (0–2) ride along when
    critical goal data is missing — intake stays free text.
    """
    context = journey_builder.extract_context(story)
    cases = list_v2_cases()
    selected = select_journey_cases(context, list(cases))
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
    data = journey_detail(db, journey, include_proposal=True)
    data["clarifications"] = journey_builder.needs_clarification(context)
    return data


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
    data["next_case"] = _case_view(first, _plan_slots(journey)) if first else None
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
    return {"case": _case_view(jc, _plan_slots(journey)), "journey_status": journey.status}


def complete_case(db: Session, user_id: str, journey_id: str,
                  case_id: str, session_id: str, score: int) -> dict:
    """Mark a journey case completed by ingesting the SERVER-scored session.

    FASE 10: the client `score` is accepted for compatibility but NEVER
    trusted — overall, safety and evidence come from the persisted session
    report (the judge's normalized output). Sessions that are not completed
    + scored are rejected (409): there is nothing honest to ingest.
    """
    journey = _owned(db, user_id, journey_id)
    jc = db.scalar(select(JourneyCase).where(
        JourneyCase.journey_id == journey.id, JourneyCase.case_id == case_id))
    if jc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case tidak ada di journey ini.")
    if jc.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Case ini sudah dikerjakan.")

    from app.domains.sessions.router import _owned as _owned_session
    s = _owned_session(db, session_id, _fake_user(user_id))
    report = s.report if isinstance(s.report, dict) else None
    if s.status != "completed" or not report:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Sesi belum selesai dinilai — selesaikan dan nilai sesi dulu.")

    try:
        server_overall = max(0, min(100, int(report.get("overall", 0) or 0)))
    except (TypeError, ValueError):
        server_overall = 0
    gates = report.get("safety_gates") or report.get("safety_flags") or []
    safety = bool(gates) if isinstance(gates, list) else bool(gates)
    dim_pcts = _report_dim_pcts(report)

    jc.status = "completed"
    jc.session_id = session_id
    jc.score = server_overall
    jc.completed_at = _now()
    if jc.day_number > journey.current_day:
        journey.current_day = jc.day_number
    journey.updated_at = _now()

    # Journey readiness: unified evidence engine scoped to this journey when
    # possible (FASE 8); falls back to the legacy simple average if the
    # engine has no evidence yet (keeps the field honest, never fabricated).
    try:
        jr = get_readiness(db, user_id, journey.id)
        if jr.get("session_count"):
            journey.readiness_current = int(jr.get("score", 0) or 0)
        else:
            raise ValueError("no journey evidence yet")
    except Exception:
        scores = [c.score for c in journey.cases if c.score is not None]
        journey.readiness_current = round(sum(scores) / len(scores)) if scores else journey.readiness_start

    # Stable core plan + adaptive slots: never regenerate the journey here.
    adaptation, coach_insight = _apply_adaptation(
        db, journey, jc, server_overall, safety, dim_pcts)
    try:
        plan = dict(journey.final_plan or {})
        plan["coach_insight"] = coach_insight
        journey.final_plan = plan
    except Exception:  # noqa: BLE001 — insight persistence is best-effort
        pass

    nxt = _unlock_next(db, journey)
    if nxt is None:
        journey.status = "completed"
        journey.completed_at = _now()

    db.commit()
    db.refresh(journey)
    data = journey_detail(db, journey, include_proposal=False)
    data["next_case"] = _case_view(nxt, _plan_slots(journey)) if nxt else None
    data["ingested"] = {"score": server_overall, "score_source": "server",
                        "safety_triggered": safety, "session_id": session_id}
    data["adaptation"] = adaptation
    data["coach_insight"] = coach_insight
    data["readiness"] = {"current": journey.readiness_current,
                         "start": journey.readiness_start,
                         "target": journey.readiness_target}
    return data


def _report_dim_pcts(report: dict) -> dict[str, float]:
    """Normalized dim percentages from a stored V2-shaped judge report."""
    out: dict[str, float] = {}
    for dim, entry in ((report or {}).get("per_dimension") or {}).items():
        if not isinstance(entry, dict):
            continue
        try:
            sc, mx = float(entry.get("score", 0) or 0), float(entry.get("max", 0) or 0)
        except (TypeError, ValueError):
            continue
        out[str(dim)] = round(100.0 * sc / mx, 1) if mx > 0 else round(sc, 1)
    return out


def _weakest_dim(dim_pcts: dict[str, float]) -> tuple[str | None, float | None]:
    if not dim_pcts:
        return None, None
    k = min(dim_pcts, key=lambda d: dim_pcts[d])
    return k, dim_pcts[k]


def _apply_adaptation(db: Session, journey: LearningJourney, jc: JourneyCase,
                      overall: int, safety: bool,
                      dim_pcts: dict[str, float]) -> tuple[dict, dict]:
    """Explicit remediation policy (FASE 10) — stable plan, adaptive slots.

    - safety-critical miss → mandatory remediation BEFORE advancing: the
      next incomplete day becomes a same-case reinforcement slot
      (same family/case → different variant at session start; persona-only
      repeats are never presented as new clinical cases).
    - poor score (<60) → reinforce (flagged; no slot churn on a single dip).
    - otherwise → advance.
    Feedback always cites real evidence, never LLM invention.
    """
    weak, weak_pct = _weakest_dim(dim_pcts)
    weak_txt = (f"{weak.replace('_', ' ')} ({weak_pct:.0f}%)"
                if weak else "key dimensions")
    if safety:
        nxt = db.scalars(select(JourneyCase).where(
            JourneyCase.journey_id == journey.id,
            JourneyCase.status != "completed",
            JourneyCase.day_number > jc.day_number)
            .order_by(JourneyCase.day_number).limit(1)).first()
        if nxt is None:
            max_day = max([c.day_number for c in journey.cases] or [jc.day_number])
            nxt = JourneyCase(journey_id=journey.id, day_number=max_day + 1,
                              case_id=jc.case_id, focus_area=jc.focus_area,
                              learning_objective=jc.learning_objective,
                              estimated_minutes=jc.estimated_minutes or 45,
                              status="locked")
            db.add(nxt)
            db.flush()
        nxt.focus_area = f"Remediation: {weak_txt} + red-flag review"
        nxt.learning_objective = (
            f"Close the safety gap from Day {jc.day_number}: re-elicit red flags "
            f"and stabilize before advancing")
        if nxt.status == "locked":
            nxt.status = "available"
        reason = (f"Safety-critical miss on Day {jc.day_number} ({weak_txt}) — "
                  f"mandatory reinforcement before advancing.")
        _upsert_plan_slot(journey, {"day": nxt.day_number, "case_id": nxt.case_id,
                                    "slot_type": "remediation", "slot_kind": "remediation",
                                    "mandatory": True, "selection_reason": reason,
                                    "estimated_minutes": nxt.estimated_minutes or 45})
        adaptation = {"action": "remediate", "slot_kind": "remediation",
                      "mandatory": True,
                      "slots": [{"day": nxt.day_number, "case_id": nxt.case_id,
                                 "slot_kind": "remediation"}]}
        insight = {"safety_flag": True,
                   "headline": f"Safety review needed: {weak_txt} caused a safety flag",
                   "detail": (f"Your Day {jc.day_number} session triggered a safety gate "
                              f"({weak_txt}). Complete the Day {nxt.day_number} remediation "
                              f"before advancing — same clinical family, a different patient.")}
        return adaptation, insight
    if overall < 60:
        adaptation = {"action": "reinforce", "slot_kind": "reinforcement",
                      "mandatory": False, "slots": []}
        insight = {"safety_flag": False,
                   "headline": f"Reinforce {weak_txt} before moving on",
                   "detail": (f"Score {overall} on Day {jc.day_number} with {weak_txt} weakest. "
                              f"Your next cases will revisit this area (spaced repetition).")}
        return adaptation, insight
    adaptation = {"action": "advance", "slot_kind": "core",
                  "mandatory": False, "slots": []}
    insight = {"safety_flag": False,
               "headline": f"Solid Day {jc.day_number} — {overall}",
               "detail": (f"Score {overall} with {weak_txt} as the relatively weakest area. "
                          f"Keep the pace; difficulty rises toward the mock.")}
    return adaptation, insight


# ---------------------------------------------------------------------------
# Today's Mission / rebalance / report / recap (FASE 10)
# ---------------------------------------------------------------------------

def get_mission(db: Session, user_id: str, journey_id: str) -> dict:
    """Today's Mission: focus, time, encounters, why, CTA (plan JSON only)."""
    journey = _owned(db, user_id, journey_id)
    if journey.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Journey {journey.status} — hanya journey aktif punya misi.")
    jc = db.scalars(
        select(JourneyCase).where(JourneyCase.journey_id == journey.id,
                                  JourneyCase.status.in_(("available", "in_progress")))
        .order_by(JourneyCase.day_number).limit(1)
    ).first()
    if jc is None:
        return {"state": "done", "day": None, "case_id": None, "focus": None,
                "expected_minutes": 0, "encounters": 0, "why": "",
                "cta": None}
    slots = _plan_slots(journey)
    slot = slots.get(int(jc.day_number or 0), {})
    day_rows = [c for c in journey.cases if c.day_number == jc.day_number
                and c.status in ("available", "in_progress")]
    expected = sum(int(c.estimated_minutes or 0) for c in day_rows) or 45
    why = str(slot.get("selection_reason") or "").strip()
    if not why:
        why = (f"Core practice for {str(jc.focus_area or jc.case_id).strip()} "
               f"(Day {jc.day_number}).")
    return {"state": "ready", "day": jc.day_number, "case_id": jc.case_id,
            "focus": jc.focus_area or jc.case_id,
            "expected_minutes": int(expected),
            "encounters": len(day_rows),
            "why": why,
            "cta": {"case_id": jc.case_id, "action": "start",
                    "label": "Start case"}}


def rebalance_journey(db: Session, user_id: str, journey_id: str,
                      missed_days: int) -> dict:
    """Missed days shift the remaining schedule — never "fail day".

    Every incomplete case moves +missed_days (descending update keeps the
    UNIQUE(journey_id, day_number) constraint satisfied); plan-slot days
    move with them. Completed history is untouched.
    """
    journey = _owned(db, user_id, journey_id)
    if journey.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Journey {journey.status} — hanya journey aktif bisa dijadwal ulang.")
    try:
        delta = max(0, int(missed_days or 0))
    except (TypeError, ValueError):
        delta = 0
    if delta:
        # Descending, one flush per row: the unit-of-work would otherwise
        # batch same-table UPDATEs in arbitrary order and trip the
        # UNIQUE(journey_id, day_number) constraint mid-shift.
        rows = db.scalars(select(JourneyCase).where(
            JourneyCase.journey_id == journey.id,
            JourneyCase.status != "completed")
            .order_by(JourneyCase.day_number.desc())).all()
        for jc in rows:
            jc.day_number = int(jc.day_number or 1) + delta
            db.flush()
        for key in ("final_plan", "proposed_plan"):
            plan = getattr(journey, key, None)
            if not isinstance(plan, dict) or not plan.get("cases"):
                continue
            shifted = []
            for c in plan["cases"]:
                if not isinstance(c, dict):
                    continue
                c = dict(c)
                try:
                    c["day"] = int(c.get("day", 1) or 1) + delta
                except (TypeError, ValueError):
                    pass
                shifted.append(c)
            plan = dict(plan)
            plan["cases"] = shifted
            setattr(journey, key, plan)
        journey.updated_at = _now()
        db.commit()
        db.refresh(journey)
    return journey_detail(db, journey, include_proposal=False)


def get_report(db: Session, user_id: str, journey_id: str) -> dict:
    """End-of-journey report: 'plan complete' ≠ 'ready'.

    verdict 'ready' only on real evidence (score ≥75, medium+ confidence);
    anything else is 'completed' with a concrete next recommendation — a
    finished plan may honestly end "not yet ready".
    """
    journey = _owned(db, user_id, journey_id)
    readiness = get_readiness(db, user_id, journey.id)
    cases = list(journey.cases or [])
    done = [c for c in cases if c.status == "completed"]
    score = int(readiness.get("score", 0) or 0)
    ready = score >= 75 and readiness.get("confidence") in ("medium", "high")
    verdict = "ready" if ready else "completed"
    needs = list(readiness.get("needs_work") or [])
    weakest = needs[-1] if needs else None
    dims = readiness.get("dimensions") or {}
    if ready:
        note = (f"Plan complete ({len(done)}/{len(cases)} cases) and readiness "
                f"{score} — exam-ready by current evidence.")
        nxt = "Keep a light spaced-repetition rhythm until exam day."
    elif done and len(done) == len(cases) and cases:
        note = (f"Plan complete ({len(done)}/{len(cases)} cases) but readiness "
                f"is {score} ({readiness.get('state')}) — not yet ready.")
        nxt = (f"Continue focused practice on "
               f"{str(weakest).replace('_', ' ') if weakest else 'your weakest area'}; "
               f"re-run safety-flagged families with new variants.")
    else:
        note = (f"Journey in progress ({len(done)}/{len(cases)} cases, "
                f"readiness {score}).")
        nxt = "Finish the remaining plan days, then re-check readiness."
    if weakest and dims.get(weakest) is not None:
        nxt += f" Weakest evidence: {str(weakest).replace('_', ' ')} ({dims[weakest]}%)."
    return {"verdict": verdict, "note": note, "next_recommendation": nxt,
            "evidence": {"sessions": int(readiness.get("session_count", 0) or 0)},
            "readiness": readiness,
            "progress": {"completed": len(done), "total": len(cases),
                         "percent": round(100 * len(done) / len(cases)) if cases else 0}}


def get_recap(db: Session, user_id: str, journey_id: str) -> dict:
    """End-of-day recap: cases/time/improvement/remaining weakness/tomorrow."""
    journey = _owned(db, user_id, journey_id)
    cases = list(journey.cases or [])
    done = [c for c in cases if c.status == "completed"]
    minutes = sum(int(c.estimated_minutes or 0) for c in done)
    try:
        from app.domains.sessions.progress_adapter import completed_normalized
        from pipeline.progress.readiness import compute_readiness
        normalized = completed_normalized(db, user_id)
        r = compute_readiness(normalized)
        needs = list(r.get("needs_work") or [])
        focus = needs[-1] if needs else (r.get("weakest") if isinstance(r.get("weakest"), str) else None)
        if not focus:
            dims = r.get("dimensions") or {}
            focus = min(dims, key=dims.get) if dims else None
        next_focus = (str(focus).replace("_", " ") if focus
                      else "Complete more cases to reveal your focus.")
    except Exception:  # noqa: BLE001 — recap never fails on analytics
        next_focus = "Complete more cases to reveal your focus."
    nxt = db.scalars(select(JourneyCase).where(
        JourneyCase.journey_id == journey.id,
        JourneyCase.status.in_(("available", "in_progress")))
        .order_by(JourneyCase.day_number).limit(1)).first()
    return {"cases_completed": len(done), "cases_total": len(cases),
            "minutes_practised": minutes,
            "next_focus": next_focus,
            "tomorrow": _case_view(nxt, _plan_slots(journey)) if nxt else None}


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
    """Unified evidence-based readiness (FASE 8).

    Same engine as Dashboard `/progress.readiness` over the same normalized
    sessions (§36: one performance can never produce contradictory claims).
    Legacy keys preserved (`score`, `confidence`, `session_count`,
    `base_score`, `trajectory_bonus`, `consistency_bonus`, `error_penalty`,
    `dimensions`, `interpretation`); explainable keys are additive
    (`version`, `state`, `core_dimensions`, `components`, `drivers`,
    `strengths`, `needs_work`, `evidence`).
    """
    from app.domains.sessions.progress_adapter import (
        completed_normalized,
        critical_errors_recent,
    )
    from pipeline.progress.readiness import compute_readiness
    try:
        normalized = completed_normalized(db, user_id, journey_id=journey_id)
    except Exception:
        normalized = []
    window = 5
    try:
        from pipeline.progress.readiness import READINESS_WEIGHTS
        window = int(READINESS_WEIGHTS.get("safety_window", 5))
    except Exception:
        pass
    # Critical-error penalty comes from recent reasoning autopsies (same
    # source as the legacy calculator: critical errors in scope).
    recent_ids = [s.get("session_id") for s in normalized[-window:] if s.get("session_id")]
    n_crit = critical_errors_recent(db, recent_ids)
    try:
        return compute_readiness(normalized, critical_errors=n_crit)
    except Exception:
        from app.domains.mentor.readiness_calculator import calculate_readiness
        return calculate_readiness(db, user_id, journey_id)


def readiness_report(db: Session, user_id: str, journey_id: str | None = None) -> dict:
    """Full report: score + dimensions + weakest area + recommendations."""
    r = get_readiness(db, user_id, journey_id)
    if r.get("session_count", 0) == 0:
        return {"readiness": r, "history": [], "weakest": None, "recommendations": [],
                "disclaimer": _DISCLAIMER}

    dims = r.get("dimensions") or {}
    # Prefer the engine's own needs_work (evidence-gated, min 2 observations);
    # fall back to the raw weakest dim for legacy parity.
    needs = r.get("needs_work") or []
    weakest = needs[-1] if needs else (min(dims, key=dims.get) if dims else None)
    weakest_pct = dims.get(weakest) if weakest else None

    recs: list[str] = []
    # Surface engine drivers first (explainable, strongest signal first).
    for d in (r.get("drivers") or []):
        if d.get("direction") in ("-", "cap") and d.get("factor") in (
                "safety", "safety_cap", "osce", "evidence", "recency",
                "critical_errors", "consistency", "trajectory"):
            recs.append(str(d.get("detail") or "").strip())
    if weakest:
        recs.append(f"Fokus pada {weakest.replace('_', ' ')} — skor terendah ({weakest_pct}%).")
    if (r.get("error_penalty") or 0) > 0:
        recs.append("Kamu punya red flag kritis yang terlewat — ulangi skrining red flag.")
    comps = r.get("components") or {}
    if comps.get("safety_capped"):
        recs.append("Safety failure membatasi readiness — remediasi red flag sebelum lanjut.")
    if not comps.get("osce_sessions"):
        recs.append("Belum ada sesi OSCE terintegrasi — Practice saja tidak cukup untuk kesiapan ujian.")
    if (r.get("trajectory_bonus") or 1.0) < 1.0:
        recs.append("Skor cenderung menurun — konsisten latihan, jangan skip hari.")
    if (r.get("consistency_bonus") or 1.0) < 0.95:
        recs.append("Latihan belum rutin — jadwalkan sesi harian.")
    if not recs:
        recs.append("Pertahankan konsistensi dan lanjut ke kasus yang lebih sulit.")
    if weakest and weakest_pct is not None and weakest_pct < 60:
        recs.append("Ulangi hari-hari yang membahas area terlemah di journey kamu.")

    try:
        from pipeline.progress.readiness import READINESS_WEIGHTS  # noqa: F401
        from app.domains.sessions.progress_adapter import completed_normalized
        normalized = completed_normalized(db, user_id, journey_id=journey_id)
        history = [{"session_id": s.get("session_id"), "case_id": s.get("case_id"),
                    "score": int(s.get("overall_0_100") or 0),
                    "rolling_avg": 0, "completed_at": s.get("completed_at")}
                   for s in normalized[-10:]]
        # Rolling average over overall scores (oldest->newest).
        running: list[float] = []
        for h, s in zip(history, normalized[-10:]):
            running.append(float(s.get("overall_0_100") or 0))
            h["rolling_avg"] = round(sum(running) / len(running))
    except Exception:
        from app.domains.mentor.readiness_calculator import readiness_history
        history = readiness_history(db, user_id, journey_id)[-10:]

    return {
        "readiness": r,
        "history": history,
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

def _plan_slots(journey: LearningJourney) -> dict[int, dict]:
    """Slot metadata by day, from the plan JSON (no new columns, STOP gate).

    final_plan wins once accepted; proposed_plan before that. Keys:
    slot_type ('core' | 'remediation'), selection_reason, mandatory.
    """
    plan = journey.final_plan or journey.proposed_plan or {}
    out: dict[int, dict] = {}
    cases = plan.get("cases") if isinstance(plan, dict) else None
    for c in cases or []:
        if not isinstance(c, dict):
            continue
        try:
            out[int(c.get("day"))] = c
        except (TypeError, ValueError):
            continue
    return out


def _upsert_plan_slot(journey: LearningJourney, slot: dict) -> None:
    """Insert/replace one day-slot in final_plan JSON (immutable replace so
    SQLAlchemy tracks the change)."""
    plan = dict(journey.final_plan or journey.proposed_plan or {})
    cases = [dict(c) for c in (plan.get("cases") or []) if isinstance(c, dict)]
    day = int(slot.get("day"))
    replaced = False
    for i, c in enumerate(cases):
        try:
            same = int(c.get("day")) == day
        except (TypeError, ValueError):
            same = False
        if same:
            merged = dict(c)
            merged.update({k: v for k, v in slot.items() if k != "day"})
            merged["day"] = day
            cases[i] = merged
            replaced = True
    if not replaced:
        cases.append(dict(slot))
    cases.sort(key=lambda c: int(c.get("day", 0) or 0))
    plan["cases"] = cases
    journey.final_plan = plan


def _shift_plan_slots(journey: LearningJourney, delta: int) -> None:
    """Shift every plan-slot day by delta (rebalance; JSON only)."""
    for key in ("final_plan", "proposed_plan"):
        plan = getattr(journey, key, None)
        if not isinstance(plan, dict) or not plan.get("cases"):
            continue
        cases = []
        for c in plan["cases"]:
            if not isinstance(c, dict):
                continue
            c = dict(c)
            try:
                c["day"] = int(c.get("day", 1) or 1) + delta
            except (TypeError, ValueError):
                pass
            cases.append(c)
        plan = dict(plan)
        plan["cases"] = cases
        setattr(journey, key, plan)


def _owned(db: Session, user_id: str, journey_id: str) -> LearningJourney:
    journey = db.get(LearningJourney, journey_id)
    if journey is None or journey.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Journey tidak ditemukan.")
    return journey


def _case_view(jc: JourneyCase, slots: dict[int, dict] | None = None) -> dict:
    slot = (slots or {}).get(int(jc.day_number or 0), {}) if slots else {}
    return {
        "day": jc.day_number,
        "case_id": jc.case_id,
        "focus_area": jc.focus_area,
        "learning_objective": jc.learning_objective,
        "estimated_minutes": jc.estimated_minutes,
        "status": jc.status,
        "score": jc.score,
        "slot_type": slot.get("slot_type", "core"),
        "selection_reason": slot.get("selection_reason", ""),
        "mandatory": bool(slot.get("mandatory", False)),
    }


def journey_detail(db: Session, journey: LearningJourney, *, include_proposal: bool) -> dict:
    cases = journey.cases  # ordered by day_number (relationship)
    completed = [c for c in cases if c.status == "completed"]
    total = len(cases)
    percent = round(100 * len(completed) / total) if total else 0
    slots = _plan_slots(journey)
    plan_cases = (journey.final_plan or journey.proposed_plan or {}).get("cases") \
        if isinstance(journey.final_plan or journey.proposed_plan, dict) else None
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
        "cases": [_case_view(c, slots) for c in cases],
        "slots": plan_cases if isinstance(plan_cases, list) else [],
        "coach_insight": ((journey.final_plan or {}) if isinstance(journey.final_plan, dict) else {}).get("coach_insight"),
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
