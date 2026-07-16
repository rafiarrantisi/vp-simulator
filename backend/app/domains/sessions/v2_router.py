"""Schema-v2 session API (pivot-v4 §6/§8) — parallel to the legacy flow so the
live ophthalmology product stays untouched. Uses the v2 patient engine + the
calibrated v2 judge, and reuses the billing gate/metering/cost guardrail.

  GET  /api/v2/cases                     catalogue (lint-clean v2 cases)
  GET  /api/v2/cases/{id}                case summary (no Part A)
  POST /api/v2/sessions                  start (freemium-gated)
  POST /api/v2/sessions/{id}/turns       patient turn (engine_v2)
  POST /api/v2/sessions/{id}/score       evaluate_v2 -> report + answer key (post-session reveal)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.domains.auth.models import User
from app.domains.billing import service as billing
from app.domains.cases.v2_catalog import (
    list_v2_cases,
    load_v2_case,
    specialties_present,
    summary,
)
from app.domains.sessions.models import SessionRow, SessionTurn
from app.domains.sessions.router import _history, _next_turn_no, _owned
from app.rag import engine_v2
from app.rag.judge_v2 import evaluate_v2
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/cases")
def v2_list_cases(specialty: str | None = None, user: User = Depends(get_current_user)):
    cases = list_v2_cases(specialty=specialty)
    return ok({"cases": [summary(c) for c in cases], "total": len(cases),
               "specialties": specialties_present()})


@router.get("/cases/{case_id}")
def v2_case_detail(case_id: str, user: User = Depends(get_current_user)):
    try:
        c = load_v2_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return ok(summary(c))


# Whitelisted media kinds so the viewer can pick an icon; anything else -> "image".
_MEDIA_TYPES = frozenset({"image", "photo", "scan", "xray", "ecg", "ultrasound", "fundus", "slitlamp"})


@router.get("/cases/{case_id}/media")
def v2_case_media(case_id: str, user: User = Depends(get_current_user)):
    """Examination media for the viewer (specialty-agnostic): images, scans,
    ECGs, etc. sourced from `physical_exam_findings.media` in the case. This is
    examination *findings* the candidate is entitled to see — never Part A
    scoring ground truth. Empty list when a case has no media (viewer hides)."""
    try:
        c = load_v2_case(case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    pef = c.frontmatter.get("physical_exam_findings") or {}
    raw = pef.get("media") if isinstance(pef, dict) else None
    media = []
    for m in raw or []:
        if not isinstance(m, dict):
            continue
        src = str(m.get("src") or "").strip()
        if not src:
            continue
        kind = str(m.get("type") or "image").strip().lower()
        media.append({
            "type": kind if kind in _MEDIA_TYPES else "image",
            "src": src,
            "label": str(m.get("label") or "").strip(),
            "caption": str(m.get("caption") or "").strip(),
        })
    return ok({"caseId": case_id, "media": media})


class V2StartReq(BaseModel):
    case_id: str


@router.post("/sessions")
def v2_start_session(req: V2StartReq, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    try:
        case = load_v2_case(req.case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    gate = billing.can_start_session(db, user.id)
    if not gate["allowed"]:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                            detail={"reason": gate.get("reason"), "usage": gate.get("usage"),
                                    "limit": gate.get("limit"),
                                    "message": "Free session limit reached — upgrade to continue."})
    s = SessionRow(user_id=user.id, institution_id=user.institution_id,
                   case_id=req.case_id, mode=case.frontmatter.get("mode_default", "anamnesis"))
    db.add(s)
    db.commit()
    db.refresh(s)
    try:
        billing.record_usage(db, user.id, "session_start", req.case_id)
        db.commit()
    except Exception:
        db.rollback()
    return ok({"sessionId": s.id, "caseId": s.case_id, "mode": s.mode,
               "openingLine": case.find_section("opening line")})


class V2TurnReq(BaseModel):
    text: str


@router.post("/sessions/{session_id}/turns")
def v2_turn(session_id: str, req: V2TurnReq, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    s = _owned(db, session_id, user)
    history = _history(db, session_id)
    n = _next_turn_no(db, session_id)
    db.add(SessionTurn(session_id=s.id, turn_number=n, role="user", content=req.text))
    try:
        reply = engine_v2.respond(s.case_id, history, req.text)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{s.case_id}' not found")
    db.add(SessionTurn(session_id=s.id, turn_number=n + 1, role="patient", content=reply))
    db.commit()
    try:  # best-effort cost guardrail
        tokens_in = (sum(len(h["content"]) for h in history) + len(req.text)) // 4
        billing.record_session_cost(db, s.id, user.id, tokens_in, len(reply) // 4)
        db.commit()
    except Exception:
        db.rollback()
    return ok({"reply": reply, "audioUrl": None})


class V2ScoreReq(BaseModel):
    ddx: dict | None = None
    management: dict | None = None


def _record_progress(user: User, case, report: dict) -> None:
    """Persist the session result to the user's profile (gamification). The JSON
    `extra` blob is replaced immutably so SQLAlchemy tracks the change."""
    prof = user.profile
    if prof is None:
        return
    overall = int(report.get("overall", 0) or 0)
    extra = dict(prof.extra or {})
    history = list(extra.get("scoreHistory") or [])
    history.insert(0, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "caseId": case.id,
        "specialty": case.frontmatter.get("specialty", ""),
        "overall": overall,
        "dims": {k: round((v.get("score", 0) / max(v.get("max", 1), 1)) * 100)
                 for k, v in (report.get("per_dimension") or {}).items()},
    })
    extra["scoreHistory"] = history[:200]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dates = dict(extra.get("sessionDates") or {})
    dates[today] = int(dates.get(today, 0)) + 1
    extra["sessionDates"] = dates
    done = set(extra.get("completedCaseIds") or [])
    done.add(case.id)
    extra["completedCaseIds"] = sorted(done)
    prof.extra = extra
    prof.xp = int(prof.xp or 0) + overall
    prof.total_sessions = int(prof.total_sessions or 0) + 1


@router.post("/sessions/{session_id}/score")
def v2_score(session_id: str, req: V2ScoreReq, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    s = _owned(db, session_id, user)
    try:
        case = load_v2_case(s.case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{s.case_id}' not found")
    transcript = _history(db, session_id)
    report = evaluate_v2(case, transcript, student_ddx=req.ddx, student_management=req.management)
    s.total_score = report.get("overall", 0)
    s.report = report
    s.status = "completed"
    _record_progress(user, case, report)
    db.commit()
    return ok(report)  # includes answer_key for the post-session reveal


@router.get("/progress")
def v2_progress(user: User = Depends(get_current_user)):
    """Gamification summary for the Qora flow: XP, sessions, per-dimension skill
    averages, and specialty coverage — from the user's profile."""
    prof = user.profile
    extra = (prof.extra if prof else {}) or {}
    history = extra.get("scoreHistory") or []
    sums, counts = {}, {}
    for h in history:
        for k, v in (h.get("dims") or {}).items():
            sums[k] = sums.get(k, 0) + (v or 0)
            counts[k] = counts.get(k, 0) + 1
    dim_avg = {k: round(sums[k] / counts[k], 1) for k in sums}
    spec = {}
    for h in history:
        sp = h.get("specialty") or "other"
        spec[sp] = spec.get(sp, 0) + 1
    return ok({
        "xp": int(prof.xp or 0) if prof else 0,
        "totalSessions": int(prof.total_sessions or 0) if prof else 0,
        "completedCases": len(extra.get("completedCaseIds") or []),
        "sessions": history[:50],
        "dimensionAverages": dim_avg,
        "specialtyCounts": spec,
    })
