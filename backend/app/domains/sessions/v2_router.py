"""Schema-v2 session API (pivot-v4 §6/§8) — parallel to the legacy flow so the
live ophthalmology product stays untouched. Uses the v2 patient engine + the
calibrated v2 judge, and reuses the billing gate/metering/cost guardrail.

  GET  /api/v2/cases                     catalogue (lint-clean v2 cases)
  GET  /api/v2/cases/{id}                case summary (no Part A)
  POST /api/v2/sessions                  start (freemium-gated)
  POST /api/v2/sessions/{id}/turns       patient turn (engine_v2)
  POST /api/v2/sessions/{id}/score       evaluate_v2 -> report + answer key (post-session reveal)
"""
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
    db.commit()
    return ok(report)  # includes answer_key for the post-session reveal
