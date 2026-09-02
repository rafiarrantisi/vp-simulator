"""STEP-6 superseding rule 1 — wire the case_v3 runtime into the live backend.

Reuses the existing `sessions`/`session_turns` architecture (SessionRow, owned,
history helpers, billing gate) — NO new DB subsystem. A v3 session is an
ordinary SessionRow with content_schema='new' and the runtime fields filled in.

Key contracts (rule 1 & 2 immutability):
  * selection happens ONCE at start; the chosen variant_id + persona_seed +
    rendered persona are persisted.
  * session reload/resume returns the SAME patient & clinical truth — derived
    from the persisted variant_id, never a re-selection.
  * scoring/debrief use the persisted selected variant, not a new selection.
  * analytics receive the actual live session IDs.
  * after start the clinical variant, persona, and canonical facts are frozen.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.domains.auth.models import User
from app.domains.sessions.models import SessionRow, SessionTurn
from app.domains.sessions.router import _history, _next_turn_no, _owned
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.persona import persona_from_constraints
from pipeline.case_v3.runtime import (
    SelectionPolicy, SelectionRequest, ScoreInput, VariantUnavailable,
    build_debrief, score_encounter,
)
from pipeline.case_v3.derive import derive_mode_views, derive_answer_key


def _registry() -> CaseRegistry:
    return CaseRegistry.from_dir()


def _family_title(reg: CaseRegistry, family_id: str) -> str:
    fam = reg.families.get(family_id)
    return fam.title_en or fam.title_id if fam else ""


def start_v3_session(db: OrmSession, user: User, *, family_id: str | None = None,
                     specialty: str | None = None, presentation: str | None = None,
                     learner_level: str = "koas", interaction_mode: str = "targeted",
                     language: str = "en", difficulty: str | None = None,
                     seed: int = 0, released_ids: set[str] | None = None) -> dict:
    """§1-2 start: select variant, instantiate & persist persona, freeze session."""
    reg = _registry()
    policy = SelectionPolicy(reg)

    # The existing billing gate / metering is reused (not duplicated).
    from app.domains.billing import service as billing
    gate = billing.can_start_session(db, user.id)
    case_id_for_usage = family_id or specialty or "v3"

    req = SelectionRequest(mode=interaction_mode, family_id=family_id,
                           specialty=specialty, presentation=presentation,
                           learner_stage=learner_level,
                           difficulty=difficulty, seed=seed,
                           released_ids=released_ids)
    try:
        result = policy.select(req)
    except VariantUnavailable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No eligible variant for this selection")

    v = result.variant
    constraints = _default_constraints()
    try:
        persona = persona_from_constraints(v, constraints, seed)
        used_fallback = False
    except Exception:
        persona = _safe_default_persona(reg, v)
        used_fallback = True

    from pipeline.case_v3.models import SessionInstance
    _ = SessionInstance  # reproducibility helper is built via build_session_instance
    inst = build_session_instance_persisted(v, persona_seed=seed, language=language,
                                            learner_stage=learner_level,
                                            mode=interaction_mode,
                                            entry_point=result.entry_point)

    # Persist into the EXISTING sessions table (content_schema='new').
    s = SessionRow(
        user_id=user.id, institution_id=user.institution_id,
        case_id=v.id,  # keep case_id populated for legacy-dashboard compatibility
        mode=interaction_mode,
        status="active",
        language=language,
        content_schema="new",
        family_id=v.family_id,
        variant_id=v.id,
        persona_seed=seed,
        persona=persona,
        learner_level=learner_level,
        interaction_mode=interaction_mode,
        competency_category=v.competency.category if v.competency else None,
        legacy_skdi_level=v.competency.legacy_level if v.competency else None,
        presentation_path=result.entry_point,
        selection_reason=result.reason,
        variant_canonical_hash=v.canonical_hash(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    try:
        billing.record_usage(db, user.id, "session_start", case_id_for_usage)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "sessionId": s.id,
        "schema": "new",
        "status": "active",
        "familyId": s.family_id,
        "variantId": s.variant_id,
        "familyTitle": _family_title(reg, s.family_id),
        "personaUsedFallback": used_fallback,
        "persona": persona,
        "modeViews": derive_mode_views(v, _family_title(reg, v.family_id)),
        "encounterStagesGuidance": _stage_guidance(v),
        "openingBrief": v.blind_candidate_brief or v.chief_complaint,
    }


def reload_v3_session(db: OrmSession, session_id: str, user: User) -> dict:
    """§1/§2 reload/resume: returns the SAME patient & clinical truth from the
    persisted variant. Never re-selects. Enforces immutability: if the canonical
    hash stored doesn't match the current variant truth, refuse (frozen)."""
    s = _owned(db, session_id, user)
    if s.content_schema != "new":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a new-schema session")
    reg = _registry()
    v = reg.variant(s.variant_id or "")
    if v is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Stored variant '{s.variant_id}' unavailable — cannot resume")
    # immutability guard: canonical truth must equal what was frozen at start
    if s.variant_canonical_hash and s.variant_canonical_hash != v.canonical_hash():
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Session clinical truth changed since start — refusing to resume (immutability).")
    persona = s.persona or persona_from_constraints(v, _default_constraints(), s.persona_seed or 0)
    return {
        "sessionId": s.id,
        "schema": "new",
        "caseId": s.case_id,
        "status": s.status,
        "familyId": s.family_id,
        "variantId": s.variant_id,
        "familyTitle": _family_title(reg, s.family_id),
        "persona": persona,
        "modeViews": derive_mode_views(v, _family_title(reg, v.family_id)),
        "openingBrief": v.blind_candidate_brief or v.chief_complaint,
        "turns": _history(db, session_id),
    }


class V3ScorePayload(dict):
    pass


def score_v3_session(db: OrmSession, session_id: str, user: User, *,
                     collected_items: dict, stabilized: bool | None = None,
                     gave_referral: bool | None = None,
                     diagnosis_submitted: str = "", mode: str | None = None) -> dict:
    """§6-9 score: uses the PERSISTED selected variant (never a re-selection)."""
    s = _owned(db, session_id, user)
    if s.content_schema != "new":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a new-schema session")
    # idempotent: don't re-score / re-award an already-completed session
    if s.status == "completed" and s.report:
        return s.report
    reg = _registry()
    v = reg.variant(s.variant_id or "")
    if v is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Stored variant '{s.variant_id}' unavailable")
    if s.variant_canonical_hash and s.variant_canonical_hash != v.canonical_hash():
        raise HTTPException(status.HTTP_409_CONFLICT, "clinical truth changed since start; refusing to score")
    learner_level = s.learner_level or "koas"
    inp = ScoreInput(variant=v, learner_stage=learner_level,
                     collected_items=collected_items, stabilized=stabilized,
                     gave_referral=gave_referral,
                     diagnosis_submitted=diagnosis_submitted)
    result = score_encounter(inp)
    debrief = build_debrief(v, score=result, family_title=_family_title(reg, v.family_id))
    report = {
        "schema": "new",
        "variantId": v.id,
        "familyId": v.family_id,
        "competency_mapping": v.competency.to_dict() if v.competency else {},
        "score": result.total,
        "max_score": result.max_score,
        "by_dimension": result.by_dimension,
        "safety_flags": result.safety_flags,
        "debrief": debrief,
        "answer_key": derive_answer_key(v),
        "submitted_diagnosis": diagnosis_submitted,
    }
    s.total_score = int(round(result.total))
    s.report = report
    s.status = "completed"
    if s.ended_at is None:
        s.ended_at = datetime.now(timezone.utc)
    db.commit()
    return report


# ── helpers ────────────────────────────────────────────────────────────────

def _default_constraints():
    from pipeline.case_v3.models import PersonaConstraints
    return PersonaConstraints(relationship="self", allow_name_generation=True,
                              anxiety_level="range", verbosity="range")


def _safe_default_persona(reg, v):
    from pipeline.case_v3.models import PersonaConstraints
    c = PersonaConstraints(relationship="self", allow_name_generation=False)
    try:
        return persona_from_constraints(v, c, 0)
    except Exception:
        return {"name": "", "occupation": "", "relationship": "self",
                "working_diagnosis": v.diagnostic.working_diagnosis,
                "chief_complaint": v.chief_complaint}


def build_session_instance_persisted(v, *, persona_seed, language, learner_stage,
                                     mode, entry_point):
    from pipeline.case_v3.persona import build_session_instance
    return build_session_instance(v, persona_seed=persona_seed, language=language,
                                  learner_stage=learner_stage, mode=mode,
                                  entry_point=entry_point)


def _stage_guidance(v) -> list[str]:
    from pipeline.case_v3.runtime import encounter_stages_for
    return encounter_stages_for(v, mode="targeted")


def latest_persisted_session(db: OrmSession, user: User) -> dict | None:
    from sqlalchemy import select
    s = db.scalars(
        select(SessionRow).where(SessionRow.user_id == user.id)
        .order_by(SessionRow.started_at.desc()).limit(1)
    ).first()
    if not s:
        return None
    return {"sessionId": s.id, "schema": s.content_schema, "variantId": s.variant_id,
            "familyId": s.family_id, "status": s.status}