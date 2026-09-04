"""STEP-6 superseding rule 1 — v3 case runtime live HTTP API.

Parallel to the v2 flow but for case_v3 new-schema content. Reuses the existing
session storage, billing gate, owned/history helpers, ratelimit + analytics.

  POST /api/v3/sessions                 start (selection + persona + persist)
  GET  /api/v3/sessions/{id}            resume — SAME patient/truth (immutable)
  POST /api/v3/sessions/{id}/score      score/debrief using persisted variant
  GET  /api/v3/sessions/history         recent new-schema sessions
  GET  /api/v3/families                 SKD 2026 competency-filterable catalogue
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.domains.auth.models import User
from app.domains.sessions.models import SessionRow
from app.domains.sessions.v3_service import (
    latest_persisted_session, reload_v3_session, score_v3_session, start_v3_session,
)
from app.shared.dependencies import get_current_user
from app.shared.envelope import ok
from app.shared.ratelimit import rate_limit
from pipeline.case_v3.runtime import SelectionPolicy

router = APIRouter(prefix="/api/v3", tags=["v3"])
_ai_rl = Depends(rate_limit("ai", "rate_limit_ai"))


class V3StartReq(BaseModel):
    family_id: str | None = None
    specialty: str | None = None
    presentation: str | None = None
    learner_level: str = "koas"
    interaction_mode: str = "targeted"     # targeted | blind | random
    language: str = "en"
    difficulty: str | None = None
    released_only: bool = False


class V3ScoreReq(BaseModel):
    collected_items: dict = Field(default_factory=dict)
    stabilized: bool | None = None
    gave_referral: bool | None = None
    diagnosis_submitted: str = ""
    mode: str | None = None


class V3TurnReq(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    input_type: str | None = None


@router.post("/sessions", dependencies=[_ai_rl])
def v3_start(req: V3StartReq, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    released = None
    if req.released_only:
        released = set()   # nothing is clinically verified yet -> safe block
    return ok(start_v3_session(
        db, user, family_id=req.family_id, specialty=req.specialty,
        presentation=req.presentation, learner_level=req.learner_level,
        interaction_mode=req.interaction_mode, language=req.language,
        difficulty=req.difficulty, released_ids=released))


@router.get("/sessions/{session_id}")
def v3_get(session_id: str, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    return ok(reload_v3_session(db, session_id, user))


@router.post("/sessions/{session_id}/turns", dependencies=[_ai_rl])
def v3_turn(session_id: str, req: V3TurnReq, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    from app.domains.sessions.v3_service import turn_v3_session
    return ok(turn_v3_session(db, user, session_id, req.text))


@router.post("/sessions/{session_id}/score", dependencies=[_ai_rl])
def v3_score(session_id: str, req: V3ScoreReq, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    return ok(score_v3_session(
        db, session_id, user, collected_items=req.collected_items,
        stabilized=req.stabilized, gave_referral=req.gave_referral,
        diagnosis_submitted=req.diagnosis_submitted, mode=req.mode))


@router.get("/sessions")
def v3_history(limit: int = 20, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SessionRow).where(SessionRow.user_id == user.id,
                                 SessionRow.content_schema == "new")
        .order_by(SessionRow.started_at.desc()).limit(max(1, min(limit, 200)))
    ).all()
    return ok({"sessions": [
        {"sessionId": r.id, "variantId": r.variant_id, "familyId": r.family_id,
         "status": r.status, "score": r.total_score,
         "competencyCategory": r.competency_category,
         "interactionMode": r.interaction_mode,
         "startedAt": r.started_at.isoformat() if r.started_at else None}
        for r in rows], "total": len(rows)})


class V3AnotherPatientReq(BaseModel):
    family_id: str
    current_variant_id: str
    learner_level: str = "koas"
    difficulty: str | None = None
    released_only: bool = False
    seed: int = 0


@router.post("/another-patient", dependencies=[_ai_rl])
def v3_another_patient(req: V3AnotherPatientReq, user: User = Depends(get_current_user)):
    """Rule 5 — 'another patient with the same disease': returns a genuinely
    different ELIGIBLE clinical variant when one exists for this learner/mode/
    release state; otherwise flags an honest persona-replay (not a new case)."""
    from pipeline.case_v3.loader import CaseRegistry
    from pipeline.case_v3.runtime import SelectionRequest
    reg = CaseRegistry.from_dir()
    pol = SelectionPolicy(reg)
    released = None
    if req.released_only:
        released = set()
    sreq = SelectionRequest(mode="targeted", family_id=req.family_id,
                            learner_stage=req.learner_level,
                            difficulty=req.difficulty, seed=req.seed,
                            released_ids=released)
    return ok(pol.next_for_another_patient(sreq, req.current_variant_id))


@router.get("/families")
def v3_families(competency: str | None = None, specialty: str | None = None,
                learner_level: str = "koas",
                user: User = Depends(get_current_user)):
    """SKD 2026 competency-filterable catalogue (superseding rule 3).

    Rule 4: `eligibleVariantCount` counts variants actually available for this
    learner/mode/release state (draft/unreviewed/incompatible NOT counted).
    Badge metadata is available for filtering/detail but the frontend is NOT
    forced to show it on every card.
    """
    from pipeline.case_v3.loader import CaseRegistry
    from pipeline.case_v3.runtime import SelectionPolicy, SelectionRequest
    reg = CaseRegistry.from_dir()
    pol = SelectionPolicy(reg)
    families = []
    for fid, fam in reg.families.items():
        if specialty and fam.primary_specialty != specialty \
                and specialty not in fam.cross_specialty_tags:
            continue
        vs = reg.variants_for_family(fid)
        cats = sorted({v.competency.category for v in vs if v.competency and v.competency.category})
        # Rule 4 — eligible count for THIS learner level
        elig = pol.eligible_for(SelectionRequest(
            mode="targeted", family_id=fid, learner_stage=learner_level, released_ids=None))
        families.append({
            "id": fam.id, "familyType": fam.family_type.value,
            "titleId": fam.title_id, "titleEn": fam.title_en,
            "primarySpecialty": fam.primary_specialty,
            "crossSpecialtyTags": fam.cross_specialty_tags,
            "presentingComplaints": fam.presenting_complaints,
            "competencyCategories": cats,      # SKD 2026 filtering/detail metadata
            "eligibleVariantCount": len(elig),  # Rule 4: eligible, not all files
            "totalVariantFiles": len(vs),        # (diagnostic only)
        })
    if competency:
        families = [f for f in families if competency in f["competencyCategories"]]
    return ok({"families": families, "total": len(families),
               "competencyStandard": "SKD 2026"})


@router.get("/state")
def v3_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Latest persisted new-schema session state (resume on app open)."""
    return ok(latest_persisted_session(db, user) or {"none": True})