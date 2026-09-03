"""Schema-v2 session API (pivot-v4 §6/§8) — parallel to the legacy flow so the
live ophthalmology product stays untouched. Uses the v2 patient engine + the
calibrated v2 judge, and reuses the billing gate/metering/cost guardrail.

  GET  /api/v2/cases                     catalogue (lint-clean v2 cases)
  GET  /api/v2/cases/{id}                case summary (no Part A)
  POST /api/v2/sessions                  start (freemium-gated)
  POST /api/v2/sessions/{id}/turns       patient turn (engine_v2)
  POST /api/v2/sessions/{id}/score       evaluate_v2 -> report + answer key (post-session reveal)
"""
from datetime import datetime, timedelta, timezone
import json
import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
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
from app.shared.ratelimit import rate_limit


def _is_v3_compat(*, user=None, email: str | None = None) -> bool:
    """Phase B flag (§K): which user sees the V3 family library + V3 dispatch.
    Global config OR canary email list. No new route / no UI change."""
    from app.config import get_settings
    st = get_settings()
    if (st.case_content_engine or "v2").lower() == "v3_compat":
        return True
    who = (user.email if user is not None else "") or email or ""
    if not who or not st.v3_compat_test_emails:
        return False
    return who in [w.strip().lower() for w in st.v3_compat_test_emails.split(",") if w.strip()]

# Cap the LLM-hitting turns/score endpoints per IP (cost + abuse guard).
_ai_rl = Depends(rate_limit("ai", "rate_limit_ai"))

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/cases")
def v2_list_cases(specialty: str | None = None, status: str | None = None,
                  scope: str | None = None, user: User = Depends(get_current_user)):
    # Phase B (§4/K): if this user is flagged v3_compat, the V2 frontend
    # (`QV2Catalogue`) receives V3 family cards in exact CaseCard shape. The
    # flag only changes the CONTENT SOURCE — QoraV2Screen / routes / shell stay
    # identical. Flip to v2 (global or canary removal) restores old content.
    from app.domains.sessions import v3_compat_service as v3c
    if _is_v3_compat(user=user):
        cards = v3c.library_cards()
        specs = sorted({c.get("specialty") for c in cards if c.get("specialty")})
        return ok({"cases": cards, "total": len(cards), "specialties": specs,
                   "contentEngine": "v3_compat"})
    # The rebuilt bank (STEP 2+) filters EXCLUSIVELY to verified, non-legacy
    # content. The default (no scope / status) preserves the existing live flow
    # so the current catalogue keeps working untouched.
    exclude_legacy = scope in ("verified", "pilot")
    cases = list_v2_cases(specialty=specialty, status=status, exclude_legacy=exclude_legacy)
    if scope == "pilot":  # kurasi pre-pilot: hanya kasus yang ditandai pilot_candidate
        cases = [c for c in cases if c.pilot_candidate]
    elif scope == "verified":  # STEP 1: hanya kasus yang sudah released & non-legacy
        cases = [c for c in cases if c.is_released() and not c.is_legacy()]
    elif scope == "released":
        cases = [c for c in cases if c.is_released() and not c.is_legacy()]
    return ok({"cases": [summary(c) for c in cases], "total": len(cases),
               "specialties": specialties_present()})


@router.get("/cases/{case_id}")
def v2_case_detail(case_id: str, user: User = Depends(get_current_user)):
    from app.domains.sessions import v3_compat_service as v3c
    from app.domains.sessions.v3_compat_schemas import (
        default_registry, family_to_card, family_variant_count,
    )
    reg = default_registry()
    if case_id in reg.families:
        fam = reg.families[case_id]
        return ok(family_to_card(reg, fam, family_variant_count(reg, fam)))
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
    language: str = "en"  # en | id | ms | tl | vi | th | ...


@router.get("/sessions")
def v2_list_sessions(limit: int = 50, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """Session history list (most-recent first). Feeds the dashboard "Recent
    sessions" and the /sessions page. Shape expected by the frontend:
    {sessions: [{sessionId, caseId, mode, status, score, specialty,
    presentation, startedAt}]}. score is null until the session is assessed.
    """
    rows = db.scalars(
        select(SessionRow)
        .where(SessionRow.user_id == user.id)
        .order_by(SessionRow.started_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    sessions = []
    for r in rows:
        spec = None
        pres = None
        try:
            c = load_v2_case(r.case_id)
            spec = c.frontmatter.get("specialty")
            pres = c.frontmatter.get("presentation_id") or c.frontmatter.get("presentation")
        except Exception:
            pass
        sessions.append({
            "sessionId": r.id,
            "caseId": r.case_id,
            "mode": r.mode,
            "status": r.status,
            "score": r.total_score,
            "specialty": spec,
            "presentation": pres,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
        })
    return ok({"sessions": sessions, "total": len(sessions)})


@router.post("/sessions")
def v2_start_session(req: V2StartReq, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    # Phase B (§E/§G): a V3 family public ref dispatches into the V3 runtime,
    # returning the exact V2 session DTO. Variant selection happens HERE (at
    # creation), not at card click. Diagnostics are never in the candidate DTO.
    from app.domains.sessions.v3_compat_schemas import is_v3_family_ref
    if is_v3_family_ref(req.case_id):
        from app.domains.sessions import v3_compat_service as v3c
        return ok(v3c.start(db, user, case_id=req.case_id, language=req.language))
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
                   case_id=req.case_id, mode=case.frontmatter.get("mode_default", "anamnesis"),
                   language=req.language)
    db.add(s)
    db.commit()
    db.refresh(s)
    try:
        billing.record_usage(db, user.id, "session_start", req.case_id)
        db.commit()
    except Exception:
        db.rollback()
    return ok({"sessionId": s.id, "caseId": s.case_id, "mode": s.mode,
               "language": s.language,
               "openingLine": case.find_section("opening line")})


class V2TurnReq(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    input_type: str = "text"  # 'text' | 'voice' (Fase 5 §35.7)


@router.get("/sessions/{session_id}/turns")
def v2_get_turns(session_id: str, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """Chat turn history — used to restore an in-flight session after a refresh
    (hash-routing, Aug 2026). Returns the transcript + session metadata."""
    s = _owned(db, session_id, user)
    if s.content_schema == "new":  # Phase B: V3-backed session -> compat path
        from app.domains.sessions import v3_compat_service as v3c
        return ok(v3c.get_turns(db, session_id, user))
    return ok({
        "turns": _history(db, session_id),
        "case_id": s.case_id,
        "language": s.language,
        "status": s.status,
        "opening_line": load_v2_case(s.case_id).find_section("opening line"),
    })


@router.post("/sessions/{session_id}/turns", dependencies=[_ai_rl])
def v2_turn(session_id: str, req: V2TurnReq, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    s = _owned(db, session_id, user)
    if s.content_schema == "new":  # Phase B: V3 turn (fallback, non-stream)
        from app.domains.sessions import v3_compat_service as v3c
        return ok(v3c.turn(db, user, session_id, req.text, req.input_type))
    history = _history(db, session_id)
    n = _next_turn_no(db, session_id)
    db.add(SessionTurn(session_id=s.id, turn_number=n, role="user", content=req.text, input_type=req.input_type))
    try:
        reply = engine_v2.respond(s.case_id, history, req.text, language=s.language)
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


@router.post("/sessions/{session_id}/turns/stream", dependencies=[_ai_rl])
def v2_turn_stream(session_id: str, req: V2TurnReq, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """Token-by-token streaming patient turn (pivot-v4 §5 / instruksi §5). Returns
    a chunked text/plain stream consumed by the chat UI with `fetch` + a reader.

    The user turn is persisted before streaming; the patient turn + cost guardrail
    are persisted on a FRESH session inside the generator, because the request-scoped
    `db` is closed by the time the streaming body runs.
    """
    s = _owned(db, session_id, user)
    if s.content_schema == "new":  # Phase B: V3 streaming (exact V2 contract)
        from app.domains.sessions import v3_compat_service as v3c
        return StreamingResponse(
            v3c.stream_turn(db, user, session_id, req.text, req.input_type),
            media_type="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    history = _history(db, session_id)
    n = _next_turn_no(db, session_id)
    user_id = user.id
    case_id = s.case_id
    db.add(SessionTurn(session_id=s.id, turn_number=n, role="user", content=req.text, input_type=req.input_type))
    db.commit()

    def gen():
        parts: list[str] = []
        try:
            for chunk in engine_v2.stream_respond(case_id, history, req.text, language=s.language):
                if chunk:
                    parts.append(chunk)
                    yield chunk
        except FileNotFoundError:
            yield f"(error: v2 case '{case_id}' not found)"
            return
        reply = "".join(parts).strip()
        db2 = SessionLocal()
        try:
            db2.add(SessionTurn(session_id=session_id, turn_number=n + 1, role="patient", content=reply))
            db2.commit()
            tokens_in = (sum(len(h["content"]) for h in history) + len(req.text)) // 4
            billing.record_session_cost(db2, session_id, user_id, tokens_in, len(reply) // 4)
            db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()

    return StreamingResponse(
        gen(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class V2ScoreReq(BaseModel):
    ddx: dict | None = None
    management: dict | None = None
    mode: str | None = None       # UI session mode: "practice" | "osce"
    overtime: bool = False        # continued past the OSCE timer -> score penalty
    pf_notes: str | None = Field(default=None, max_length=4000)   # free-text physical exam the student performed
    pf_areas: list[str] | None = Field(default=None, max_length=20)  # areas examined (general/skin/head_neck/chest/abdomen/limbs/neuro)

    @field_validator("ddx", "management")
    @classmethod
    def _bound_structured_payload(cls, value):
        if value is not None and len(json.dumps(value, ensure_ascii=False)) > 12000:
            raise ValueError("structured assessment payload is too large")
        return value


class V2PFReq(BaseModel):
    notes: str = Field(default="", max_length=4000)               # what the student examined / expected to find
    areas: list[str] = Field(default_factory=list, max_length=20)         # examined areas; only these get revealed


# Part B `## Physical findings` bullet labels -> canonical area keys.
_PF_AREA_PATTERNS = {
    "general": ["general"],
    "skin": ["skin"],
    "head_neck": ["head", "neck"],
    "chest": ["chest", "thorax", "cardio", "respir"],
    "abdomen": ["abdomen", "abdo", "belly"],
    "limbs": ["limb", "extremit"],
    "neuro": ["neuro"],
}


def parse_pf_findings(case) -> dict[str, str]:
    """Parse the patient's `## Physical findings` (Part B) into area -> text.

    The patient LLM narrates these in lay terms; the PF step reveals ONLY the
    areas the student examined (isolation rule — same contract as the chat)."""
    section = case.find_section("physical findings")
    if not section:
        return {}
    out: dict[str, str] = {}
    for line in section.splitlines():
        line = line.strip()
        # Pattern is `- **Label:** text` — the colon sits INSIDE the bold
        # (`**Label:**` = `**` + "Label:" + `**`), so match `:**` not `**:`.
        m = re.match(r"^-\s*\*\*(.+?):\*\*\s*(.*)$", line)
        if not m:
            continue
        label, text = m.group(1).strip(), m.group(2).strip()
        lk = label.lower()
        key = next((k for k, pats in _PF_AREA_PATTERNS.items() if any(p in lk for p in pats)), None)
        if key and text:
            out[key] = (out[key] + " " + text) if key in out else text
    return out


@router.post("/sessions/{session_id}/pf")
def v2_pf(session_id: str, req: V2PFReq, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    """Structured physical-exam step (Aug 2026): the student states which areas
    they examine + what they expect; the endpoint reveals the patient's findings
    for those areas only. Stateless — the notes travel with the score request."""
    s = _owned(db, session_id, user)
    if s.content_schema == "new":  # Phase B: V3 physical exam (isolation rule)
        from app.domains.sessions import v3_compat_service as v3c
        return ok(v3c.pf(db, user, session_id, notes=req.notes, areas=req.areas))
    try:
        case = load_v2_case(s.case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{s.case_id}' not found")
    all_findings = parse_pf_findings(case)
    examined = [a for a in (req.areas or []) if a in all_findings]
    return ok({
        "findings": {a: all_findings[a] for a in examined},
        "examined": examined,
        "available_areas": sorted(all_findings.keys()),
    })


# UI session mode -> scoring rubric mode. "practice" scores history only;
# "osce" scores the full OSCE arc. Unknown/None -> the case's mode_default.
_UI_MODE_TO_RUBRIC = {"osce": "osce_full", "practice": "anamnesis"}
_OVERTIME_PENALTY = 10


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
    # Daily streak: consecutive calendar days with >=1 completed session (§14).
    last = extra.get("lastActiveDate")
    if last != today:
        try:
            prev = datetime.strptime(last, "%Y-%m-%d").date() if last else None
        except (ValueError, TypeError):
            prev = None
        today_d = datetime.now(timezone.utc).date()
        prof.streak = (int(prof.streak or 0) + 1) if (prev and (today_d - prev).days == 1) else 1
    extra["lastActiveDate"] = today
    extra["bestStreak"] = max(int(extra.get("bestStreak") or 0), int(prof.streak or 0))
    extra["bestScore"] = max(int(extra.get("bestScore") or 0), overall)
    prof.extra = extra
    prof.xp = int(prof.xp or 0) + overall
    prof.total_sessions = int(prof.total_sessions or 0) + 1


@router.post("/sessions/{session_id}/score", dependencies=[_ai_rl])
def v2_score(session_id: str, req: V2ScoreReq, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    s = _owned(db, session_id, user)
    # Scoring may be retried by the browser/network after a slow judge call.
    # Return the stored report instead of awarding XP/progress twice.
    if s.status == "completed" and s.report:
        return ok(s.report)
    if s.content_schema == "new":  # Phase B: V3 scoring -> V2 report shape
        from app.domains.sessions import v3_compat_service as v3c
        return ok(v3c.score(
            db, user, session_id, ddx=req.ddx, management=req.management,
            mode=req.mode, overtime=req.overtime,
            pf_notes=req.pf_notes, pf_areas=req.pf_areas))
    try:
        case = load_v2_case(s.case_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{s.case_id}' not found")
    transcript = _history(db, session_id)
    rubric_mode = _UI_MODE_TO_RUBRIC.get((req.mode or "").lower())
    report = evaluate_v2(case, transcript, mode=rubric_mode,
                         student_ddx=req.ddx, student_management=req.management,
                         student_pf={"notes": req.pf_notes or "", "areas": req.pf_areas or []})
    if req.overtime:  # continued past the OSCE time limit (§4.3) -> small penalty
        orig = int(report.get("overall", 0) or 0)
        report["overall"] = max(0, orig - _OVERTIME_PENALTY)
        report["overtime_penalty"] = _OVERTIME_PENALTY
        report["summary"] = (report.get("summary", "") or "") + \
            f" (−{_OVERTIME_PENALTY} for continuing past the OSCE time limit.)"
    s.total_score = report.get("overall", 0)
    s.report = report
    s.status = "completed"
    if s.ended_at is None:
        s.ended_at = datetime.now(timezone.utc)
    _record_progress(user, case, report)
    db.commit()
    return ok(report)  # includes answer_key for the post-session reveal


# Gamification badges (§14). Derived from stats on each request — not stored.
_BADGES = [
    {"id": "first_case", "name": "First steps", "icon": "🎯", "metric": "cases", "goal": 1},
    {"id": "cases_5", "name": "Getting serious", "icon": "📚", "metric": "cases", "goal": 5},
    {"id": "cases_10", "name": "Dedicated", "icon": "🔥", "metric": "cases", "goal": 10},
    {"id": "cases_25", "name": "Prolific", "icon": "🏆", "metric": "cases", "goal": 25},
    {"id": "spec_3", "name": "Explorer", "icon": "🧭", "metric": "specialties", "goal": 3},
    {"id": "spec_6", "name": "Polymath", "icon": "🧠", "metric": "specialties", "goal": 6},
    {"id": "spec_10", "name": "Completionist", "icon": "👑", "metric": "specialties", "goal": 10},
    {"id": "score_70", "name": "Sharp", "icon": "⭐", "metric": "avg_score", "goal": 70},
    {"id": "score_85", "name": "Excellent", "icon": "💎", "metric": "avg_score", "goal": 85},
    {"id": "streak_3", "name": "On a roll", "icon": "🔥", "metric": "streak", "goal": 3},
    {"id": "streak_7", "name": "Unstoppable", "icon": "⚡", "metric": "streak", "goal": 7},
    {"id": "sessions_50", "name": "Half-century", "icon": "💯", "metric": "sessions", "goal": 50},
]


def _compute_badges(metrics: dict) -> list[dict]:
    out = []
    for b in _BADGES:
        val = float(metrics.get(b["metric"], 0) or 0)
        goal = float(b["goal"])
        out.append({
            "id": b["id"], "name": b["name"], "icon": b["icon"],
            "goal": b["goal"], "metric": b["metric"], "value": round(val, 1),
            "earned": val >= goal,
            "progress": round(min(val / goal, 1.0), 2) if goal else 1.0,
        })
    return out


@router.get("/progress")
def v2_progress(user: User = Depends(get_current_user)):
    """Gamification summary for the Qora flow: XP, streak, daily goal, badges,
    per-dimension skill averages, and specialty coverage — from the user's profile."""
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
    overalls = [int(h.get("overall", 0) or 0) for h in history]
    avg_score = round(sum(overalls) / len(overalls), 1) if overalls else 0
    completed = len(extra.get("completedCaseIds") or [])
    streak = int(prof.streak or 0) if prof else 0
    total_sessions = int(prof.total_sessions or 0) if prof else 0
    dates = extra.get("sessionDates") or {}
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    week = {(now.date() - timedelta(days=i)).isoformat() for i in range(7)}
    weekly = sum(int(v or 0) for k, v in dates.items() if k in week)
    metrics = {"cases": completed, "specialties": len(spec),
               "avg_score": avg_score, "streak": streak, "sessions": total_sessions}
    return ok({
        "xp": int(prof.xp or 0) if prof else 0,
        "totalSessions": total_sessions,
        "completedCases": completed,
        "streak": streak,
        "bestStreak": int(extra.get("bestStreak") or 0),
        "bestScore": int(extra.get("bestScore") or 0),
        "avgScore": avg_score,
        "dailyGoal": {"done": int(dates.get(today, 0) or 0), "target": 1},
        "weeklyCount": weekly,
        "sessions": history[:50],
        "dimensionAverages": dim_avg,
        "specialtyCounts": spec,
        "badges": _compute_badges(metrics),
    })
