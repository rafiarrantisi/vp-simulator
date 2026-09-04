"""Qora Mentor — API router (PRD_QORA_MENTOR §5.3, Phase 1 subset).

  POST /api/v2/mentor/story                     story → proposal
  POST /api/v2/mentor/journeys/{id}/customize   chat-based adjustment
  POST /api/v2/mentor/journeys/{id}/accept      start journey
  POST /api/v2/mentor/journeys/{id}/abandon     abandon journey
  GET  /api/v2/mentor/journeys                  list journeys
  GET  /api/v2/mentor/journeys/{id}             journey detail + progress
  GET  /api/v2/mentor/journeys/{id}/next-case   next available case
  POST /api/v2/mentor/journeys/{id}/complete-case  mark case completed
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.domains.auth.models import User
from app.domains.mentor import service
from app.domains.mentor.schemas import (
    AcceptRequest,
    CompleteCaseRequest,
    CustomizeRequest,
    RebalanceRequest,
    StoryRequest,
)
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok
from app.shared.ratelimit import rate_limit

router = APIRouter(prefix="/api/v2/mentor", tags=["mentor"])

# Story/customize hit the LLM — rate limit like other AI endpoints.
_ai_rl = Depends(rate_limit("ai", "rate_limit_ai"))


def _require_mentor_enabled() -> None:
    """Phase 12 Mentor canary kill-switch: writes 503 when disabled while
    reads stay open, so rollback needs no frontend revert."""
    from app.shared.feature_flags import snapshot
    if not snapshot().get("mentor_v1_enabled", True):
        raise HTTPException(status_code=503,
                            detail="Mentor is temporarily disabled — please retry shortly.")


_mentor_write = Depends(_require_mentor_enabled)


@router.post("/story")
def mentor_story(req: StoryRequest, _: None = _ai_rl, _w: None = _mentor_write,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    data = service.create_journey(db, user.id, user.institution_id, req.story)
    return ok(data)


@router.post("/journeys/{journey_id}/customize")
def mentor_customize(journey_id: str, req: CustomizeRequest, _: None = _ai_rl, _w: None = _mentor_write,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    data = service.customize_journey(db, user.id, journey_id, req.feedback)
    return ok(data)


@router.post("/journeys/{journey_id}/accept")
def mentor_accept(journey_id: str, _req: AcceptRequest | None = None, _w: None = _mentor_write,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    data = service.accept_journey(db, user.id, journey_id)
    return ok(data)


@router.post("/journeys/{journey_id}/abandon")
def mentor_abandon(journey_id: str, user: User = Depends(get_current_user), _w: None = _mentor_write,
                   db: Session = Depends(get_db)):
    data = service.abandon_journey(db, user.id, journey_id)
    return ok(data)


@router.get("/journeys")
def mentor_list(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok({"journeys": service.list_journeys(db, user.id)})


@router.get("/journeys/{journey_id}")
def mentor_detail(journey_id: str, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return ok(service.get_journey(db, user.id, journey_id))


@router.get("/journeys/{journey_id}/next-case")
def mentor_next_case(journey_id: str, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return ok(service.next_case(db, user.id, journey_id))


@router.post("/journeys/{journey_id}/complete-case")
def mentor_complete_case(journey_id: str, req: CompleteCaseRequest, _w: None = _mentor_write,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    data = service.complete_case(db, user.id, journey_id,
                                 req.case_id, req.session_id, req.score)
    return ok(data)


@router.get("/journeys/{journey_id}/mission")
def mentor_mission(journey_id: str, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return ok(service.get_mission(db, user.id, journey_id))


@router.post("/journeys/{journey_id}/rebalance")
def mentor_rebalance(journey_id: str, req: RebalanceRequest, _w: None = _mentor_write,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return ok(service.rebalance_journey(db, user.id, journey_id, req.missed_days))


@router.get("/journeys/{journey_id}/report")
def mentor_journey_report(journey_id: str, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    return ok(service.get_report(db, user.id, journey_id))


@router.get("/journeys/{journey_id}/recap")
def mentor_journey_recap(journey_id: str, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    return ok(service.get_recap(db, user.id, journey_id))


# ---------------------------------------------------------------------------
# Reasoning autopsy (PRD §4.2)
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/autopsy")
def mentor_autopsy_generate(session_id: str, _: None = _ai_rl, _w: None = _mentor_write,
                            user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    data = service.generate_autopsy_for_session(db, user.id, session_id)
    return ok(data)


@router.get("/sessions/{session_id}/autopsy")
def mentor_autopsy_get(session_id: str, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    data = service.get_autopsy(db, user.id, session_id)
    return ok({"autopsy": data})


# ---------------------------------------------------------------------------
# Patient continuity (PRD §4.3)
# ---------------------------------------------------------------------------

@router.get("/continuity/pending")
def mentor_continuity_pending(user: User = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    return ok(service.pending_continuity(db, user.id))


# ---------------------------------------------------------------------------
# Readiness (PRD §4.4)
# ---------------------------------------------------------------------------

@router.get("/readiness")
def mentor_readiness(journey_id: str | None = None,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return ok(service.get_readiness(db, user.id, journey_id))


@router.get("/readiness/report")
def mentor_readiness_report(journey_id: str | None = None,
                            user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    return ok(service.readiness_report(db, user.id, journey_id))
