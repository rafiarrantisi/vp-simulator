"""Pilot analytics API (Fase 5 §35)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from app.domains.analytics.schemas import PilotEventIn
from app.domains.analytics.service import build_analytics, record_event
from app.domains.auth.models import User
from app.database import get_db
from app.shared.dependencies import get_current_user, require_admin
from app.shared.envelope import ok

router = APIRouter(prefix="/api/v2/pilot", tags=["pilot-analytics"])


@router.post("/events")
def post_event(req: PilotEventIn, user: User = Depends(get_current_user),
               db: OrmSession = Depends(get_db)):
    try:
        req.validate_event()
    except ValueError as e:
        raise HTTPException(422, str(e))
    return ok(record_event(db, user.id, req.session_id, req.event, req.stage, req.meta))


@router.get("/analytics")
def analytics(db: OrmSession = Depends(get_db), _admin: User = Depends(require_admin)):
    """Pilot funnel answering the §35 questions. Admin-only."""
    return ok(build_analytics(db))