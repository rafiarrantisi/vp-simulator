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

from fastapi import APIRouter, Depends, HTTPException, Request, status
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

from app.domains.sessions.hardening import ensure_turnable, find_duplicate_reply


def _is_v3_compat(*, user=None, email: str | None = None) -> bool:
    """Phase B flag (§K): which user sees the V3 family library + V3 dispatch.
    Global config OR canary email list. No new route / no UI change."""
    from app.config import get_settings
    st = get_settings()
    if (st.case_content_engine or "v2").lower() == "v3_compat":
        return True
    who = ((user.email if user is not None else "") or email or "").strip().lower()
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
        if spec is None:
            # FASE 9: V3-backed rows resolve their family card (same adapter
            # the catalogue uses) so history never shows raw `fam_*` ids.
            # Registry is process-cached (see progress_adapter).
            try:
                from app.domains.sessions.progress_adapter import cached_registry
                from app.domains.sessions.v3_compat_schemas import (
                    family_to_card,
                    family_variant_count,
                )
                reg = cached_registry()
                if r.case_id in reg.families:
                    fam = reg.families[r.case_id]
                    card = family_to_card(reg, fam, family_variant_count(reg, fam))
                    spec = card.get("specialty")
                    pres = card.get("presentation") or card.get("title")
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


@router.post("/sessions", dependencies=[_ai_rl])
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


class V2VoiceStreamReq(BaseModel):
    """Phase-2 server-orchestrated voice turn (ADR §4.2/§4.3).

    client_turn_id + transcript body-hash is the idempotency key: same key +
    same body replays the durable winner with NO new inference; same key +
    different body is rejected (409). client_telemetry is untrusted
    timing-only input (sanitized, never content).
    """
    client_turn_id: str = Field(min_length=1, max_length=128)
    transcript: str = Field(min_length=1, max_length=4000)
    client_telemetry: dict | None = None


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
async def v2_turn(session_id: str, req: V2TurnReq, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    from app.domains.sessions.turn_acceptance import (
        accept_turn, finalize_patient_turn,
    )
    snap = accept_turn(db, session_id=session_id, user_id=user.id,
                       text=req.text, input_type=req.input_type)
    if snap.content_schema == "new":  # Phase B: V3 turn (fallback, non-stream)
        from app.domains.sessions import v3_compat_service as v3c
        return ok(await v3c.turn(snap, user.id, req.text, req.input_type))
    history = [dict(h) for h in snap.history]
    # FASE 6: duplicate-send / stream→fallback retry returns stored reply.
    if snap.dup_reply is not None:
        return ok({"reply": snap.dup_reply, "audioUrl": None, "_deduped": True})
    n = snap.turn_no
    try:
        reply = await engine_v2.arespond(snap.case_id, history, req.text, language=snap.language,
                                                  session_id=session_id,
                                                  route="v2_turn",
                                                  logical_turn_id=f"{session_id}:t{n + 1}")
    except FileNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{snap.case_id}' not found")
    from app.database import SessionLocal as _SessionLocal

    def _record(db2):
        tokens_in = (sum(len(h["content"]) for h in history) + len(req.text)) // 4
        billing.record_session_cost(db2, snap.session_id, user.id, tokens_in, len(reply) // 4)

    try:  # best-effort cost guardrail (+ fencing, same durability as before)
        finalize_patient_turn(_SessionLocal, session_id=snap.session_id,
                              turn_no=n + 1, reply=reply, user_id=user.id,
                              record_cost=_record)
    except Exception:
        pass
    return ok({"reply": reply, "audioUrl": None})


@router.post("/sessions/{session_id}/turns/stream", dependencies=[_ai_rl])
async def v2_turn_stream(session_id: str, req: V2TurnReq, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """Token-by-token streaming patient turn (pivot-v4 §5 / instruksi §5). Returns
    a chunked text/plain stream consumed by the chat UI with `fetch` + a reader.

    Phase 2: async endpoint — no thread waits on the LLM. The user turn is
    persisted before streaming; the request session is closed before inference
    (no pool connection held during LLM wait); persist runs as a bounded
    thread unit. Wire contract unchanged (plain-text chunks, same errors).
    """
    import anyio

    from app.domains.sessions.turn_acceptance import accept_turn
    from app.shared.admission import admission_wait_s, idle_timeout_s, patient_limiter
    from app.shared.perf_marks import TurnClock
    clock = TurnClock(route="v2_turn_stream", schema="legacy")
    clock.mark("request_received")
    clock.mark("auth_done")
    # Phase 3: one atomic acceptance (lock + revalidate + history + number +
    # persist + commit). Same errors/messages as the previous inline preflight.
    snap = accept_turn(db, session_id=session_id, user_id=user.id,
                       text=req.text, input_type=req.input_type)
    if snap.content_schema == "new":  # Phase B: V3 streaming (exact V2 contract)
        from app.domains.sessions import v3_compat_service as v3c
        clock.mark("context_ready")
        db.close()
        return StreamingResponse(
            await v3c.stream_turn(snap, user.id, req.text, req.input_type),
            media_type="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    history = [dict(h) for h in snap.history]
    # FASE 6: duplicate-send retry on an interrupted stream replays stored text.
    if snap.dup_reply is not None:
        async def _replay():
            yield snap.dup_reply
        return StreamingResponse(
            _replay(),
            media_type="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    n = snap.turn_no
    user_id = snap.user_id
    case_id = snap.case_id
    language = snap.language
    clock.mark("context_ready")
    clock.mark("db_preflight_done")
    db.close()  # release pool connection before inference (H1 fix, Phase 2)

    limiter = patient_limiter()
    try:
        with anyio.fail_after(admission_wait_s()):
            await limiter.acquire()
    except TimeoutError:
        clock.mark("request_complete")
        clock.finish("rejected_admission")
        clock.log_summary()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "server busy — please retry in a moment")
    slot_held = True

    async def gen():
        nonlocal slot_held
        parts: list[str] = []
        outcome = "complete"
        clock.mark("llm_request_start")
        stream = engine_v2.astream_respond(case_id, history, req.text, language=language,
                                                 session_id=session_id,
                                                 route="v2_turn_stream",
                                                 logical_turn_id=f"{session_id}:t{n + 1}")
        aiter = stream.__aiter__()
        async def _close_upstream():
            try:
                await aiter.aclose()
            except Exception:  # noqa: BLE001 - cleanup must not fail
                pass
        try:
            first_sent = False
            while True:
                try:
                    with anyio.fail_after(idle_timeout_s()):
                        chunk = await aiter.__anext__()
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    outcome = "failed_idle"
                    raise
                if first_sent:
                    # Generator resumed => Starlette took the previous chunk.
                    # Approximation of ASGI send (see perf_marks docs).
                    clock.mark("first_content_sent")
                    first_sent = None
                if chunk:
                    if not parts:
                        clock.mark("llm_first_token")
                        clock.mark("first_chunk_yielded")
                    parts.append(chunk)
                    clock.count("chunks")
                    clock.count("chunk_bytes", len(chunk))
                    yield chunk
                    if first_sent is False:
                        first_sent = True
        except GeneratorExit:
            outcome = "cancelled"
            clock.mark("request_complete")
            clock.finish(outcome)
            clock.log_summary()
            await _close_upstream()
            raise
        except FileNotFoundError:
            outcome = "failed_case_missing"
            clock.mark("request_complete")
            clock.finish(outcome)
            clock.log_summary()
            yield f"(error: v2 case '{case_id}' not found)"
            return
        except Exception:
            if outcome == "complete":
                outcome = "failed_llm"
            clock.mark("request_complete")
            clock.finish(outcome)
            clock.log_summary()
            await _close_upstream()
            raise
        await _close_upstream()
        reply = "".join(parts).strip()
        clock.mark("stream_complete")

        # Phase 3: fenced finalization (stale worker cannot overwrite newer
        # results; same sequencing/billing as before).
        from app.database import SessionLocal as _SessionLocal
        from app.domains.sessions.turn_acceptance import finalize_patient_turn

        def _record(db2):
            tokens_in = (sum(len(h["content"]) for h in history) + len(req.text)) // 4
            billing.record_session_cost(db2, session_id, user_id, tokens_in, len(reply) // 4)

        try:
            from app.shared.admission import db_limiter

            def _finalize():
                return finalize_patient_turn(
                    _SessionLocal, session_id=session_id, turn_no=n + 1,
                    reply=reply, user_id=user_id, record_cost=_record)

            result = await anyio.to_thread.run_sync(_finalize, limiter=db_limiter())
            if result == "superseded":
                outcome = "superseded_stale"
            clock.mark("db_persist_complete")
        except Exception:
            outcome = "failed_persist"
        finally:
            clock.mark("request_complete")
            clock.finish(outcome)
            clock.log_summary()
            if slot_held:
                slot_held = False
                limiter.release()

    async def _gen_wrapped():
        it = gen()
        try:
            async for chunk in it:
                yield chunk
        finally:
            try:
                await it.aclose()
            except Exception:  # noqa: BLE001 - cleanup must not fail
                pass
            if slot_held:
                limiter.release()

    return StreamingResponse(
        _gen_wrapped(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/turns/voice-stream", dependencies=[_ai_rl])
async def v2_turn_voice_stream(session_id: str, req: V2VoiceStreamReq,
                               request: Request,
                               user: User = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    """Phase-2 server-orchestrated voice turn (ADR §4.2/§4.3).

    Single POST replaces the frontend-coordinated text-turn + TTS round
    trips for voice: atomic idempotent accept → ONE full patient reply via
    the frozen Phase-1 adapter (server-side buffering, no sentence
    pipelining) → fenced durable winner commit → ONE server-side TTS
    synthesis → ONE typed framed stream (see app.voice.frames).

    Contract notes:
    - Pre-accept failures are HTTP (401/404/400/409/503). Post-accept
      failures arrive as typed `error` frames on a 200 stream — the client
      falls back to text WITHOUT re-inference in both cases.
    - PCM is never released before the winner commit succeeds (commit runs
      first; TTS-after-commit trivially satisfies the gate — overlapping
      synthesis start is a future latency optimization, not v1 behavior).
    - Disconnect before commit cancels work (no patient row); the same
      client_turn_id then adopts and re-runs. After commit, recovery
      replays the stored winner with no new inference.
    - Text-chat send()/score() contracts are untouched (separate routes).
    """
    import time

    import anyio

    from app.domains.sessions import voice_stream as vs
    from app.domains.sessions.turn_acceptance import (
        accept_voice_turn, commit_voice_winner, read_voice_winner,
    )
    from app.shared.admission import admission_wait_s, db_limiter, patient_limiter
    from app.shared.perf_marks import TurnClock
    from app.voice import frames as vf

    clock = TurnClock(route="voice_stream", schema="legacy")
    clock.mark("request_received")
    clock.mark("auth_done")
    user_id = user.id
    cid = (req.client_turn_id or "").strip()
    transcript = (req.transcript or "").strip()
    telemetry = vs.sanitize_client_telemetry(req.client_telemetry)
    if telemetry:
        vs.voice_event(
            "client_endpoint", session_id=session_id, client_turn_id=cid,
            transcript_len=len(transcript),
            counts={k: v for k, v in telemetry.items()
                    if isinstance(v, (int, float))},
            outcome=str(telemetry.get("endpoint_reason", "")),
            mode="manual" if telemetry.get("manual") else "")
    vs.voice_event("received", session_id=session_id, client_turn_id=cid,
                   transcript_len=len(transcript))
    try:
        snap = accept_voice_turn(db, session_id=session_id, user_id=user_id,
                                 client_turn_id=cid, transcript=transcript)
    except HTTPException as e:
        clock.mark("request_complete")
        code = int(getattr(e, "status_code", 0) or 0)
        clock.finish("rejected_accept" if code == 409 else "rejected")
        clock.log_summary()
        vs.voice_event("rejected", session_id=session_id, client_turn_id=cid,
                       transcript_len=len(transcript),
                       error=f"http_{code}" if code else "accept_failed")
        raise
    if snap.replay_reply is not None:
        vs.voice_event("replayed", session_id=session_id, client_turn_id=cid,
                       transcript_len=len(transcript),
                       reply_len=len(snap.replay_reply))
    elif snap.adopted:
        vs.voice_event("adopted", session_id=session_id, client_turn_id=cid,
                       transcript_len=len(transcript))
    else:
        vs.voice_event("accepted", session_id=session_id, client_turn_id=cid,
                       transcript_len=len(transcript))
    history_len = sum(len(h.get("content") or "") for h in (snap.history or ()))
    case_id = snap.case_id
    language = snap.language
    turn_no = snap.turn_no
    clock.mark("context_ready")
    clock.mark("db_preflight_done")
    db.close()  # release pool connection before inference (same as text stream)

    limiter = patient_limiter()
    try:
        with anyio.fail_after(admission_wait_s()):
            await limiter.acquire()
    except TimeoutError:
        clock.mark("request_complete")
        clock.finish("rejected_admission")
        clock.log_summary()
        vs.voice_event("admission_rejected", session_id=session_id,
                       client_turn_id=cid, transcript_len=len(transcript),
                       error="admission_timeout")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "server busy — please retry in a moment")
    slot_held = True
    vs.voice_event("admission_ok", session_id=session_id, client_turn_id=cid,
                   transcript_len=len(transcript))

    async def gen():
        nonlocal slot_held
        outcome = "complete"
        # TurnClock milestones are text-path names; mapping for voice:
        # llm_request_start = inference begin, stream_complete = full reply
        # buffered, first_content_sent ≈ final-text frame, first_chunk_yielded
        # ≈ first PCM frame, db_persist_complete = winner commit. Missing
        # stages on failed/cancelled turns stay missing (never backfilled).
        reply = snap.replay_reply
        commit_status = "replayed" if reply is not None else ""
        try:
            if reply is None:
                # A racing worker may have committed between accept and here
                # — reread and skip new inference when the winner is durable.
                from app.database import SessionLocal as _SLRead
                stored = await anyio.to_thread.run_sync(
                    lambda: read_voice_winner(
                        _SLRead, session_id=session_id, client_turn_id=cid))
                if stored:
                    reply, commit_status = stored, "replayed"
                    vs.voice_event("replayed", session_id=session_id,
                                   client_turn_id=cid,
                                   transcript_len=len(transcript),
                                   reply_len=len(stored))
                else:
                    clock.mark("llm_request_start")
                    llm_t0 = time.monotonic()
                    reply = await vs.run_voice_llm(
                        snap, transcript, session_id=session_id,
                        client_turn_id=cid)
                    vs.voice_event("llm_full", session_id=session_id,
                                   client_turn_id=cid,
                                   transcript_len=len(transcript),
                                   reply_len=len(reply),
                                   total_ms=(time.monotonic() - llm_t0) * 1000.0)
                    clock.mark("stream_complete")
            try:
                gone = await request.is_disconnected()
            except Exception:  # noqa: BLE001
                gone = False
            if gone:
                # Disconnect BEFORE commit: cancel work, persist nothing.
                outcome = "cancelled"
                vs.voice_event("cancelled", session_id=session_id,
                               client_turn_id=cid,
                               transcript_len=len(transcript),
                               error="disconnect_before_commit")
                return
            if commit_status != "replayed":
                def _record(db2):
                    tokens_in = (history_len + len(transcript)) // 4
                    billing.record_session_cost(db2, session_id, user_id,
                                                tokens_in, len(reply) // 4)

                def _commit():
                    from app.database import SessionLocal as _SL
                    return commit_voice_winner(
                        _SL, session_id=session_id, client_turn_id=cid,
                        turn_no=turn_no, reply=reply, record_cost=_record)

                commit_status, reply = await anyio.to_thread.run_sync(
                    _commit, limiter=db_limiter())
                vs.voice_event("commit_ok", session_id=session_id,
                               client_turn_id=cid,
                               transcript_len=len(transcript),
                               reply_len=len(reply), outcome=commit_status)
            clock.mark("db_persist_complete")
            # ——— winner is durable from here: PCM may be released. ———
            from app.shared.perf_sink import session_ref as _sref
            yield vf.encode_metadata({
                "route": "voice_stream",
                "turn_no": turn_no + 1,
                "session_ref": _sref(session_id),
                "reply_chars": len(reply),
                "adopted": bool(snap.adopted),
                "commit": commit_status or "persisted",
            })
            yield vf.encode_final_text(reply)
            clock.mark("first_content_sent")
            if len(reply) > vs.TTS_STREAM_MAX_CHARS:
                outcome = "failed_tts_too_long"
                vs.voice_event("error", session_id=session_id,
                               client_turn_id=cid,
                               transcript_len=len(transcript),
                               reply_len=len(reply), error="tts_too_long")
                yield vf.encode_error("tts_too_long",
                                      "reply too long for one voice turn")
                return
            voice, style, lang = await anyio.to_thread.run_sync(
                lambda: vs.resolve_turn_voice(session_id))
            vs.voice_event("tts_start", session_id=session_id,
                           client_turn_id=cid, transcript_len=len(transcript),
                           reply_len=len(reply))
            tts_t0 = time.monotonic()
            from app.shared.admission import idle_timeout_s
            from app.voice.tts import TtsFailed, TtsNotConfigured
            pump = vs._PcmPump(reply, voice=voice, style=style, lang=lang,
                               session_ref=session_id)
            pump.start()
            pcm_bytes, pcm_chunks, attempts = 0, 0, 0
            first_pcm = False
            while True:
                try:
                    gone = await request.is_disconnected()
                except Exception:  # noqa: BLE001
                    gone = False
                if gone:
                    # Winner already durable — just stop streaming audio.
                    outcome = "cancelled"
                    vs.voice_event("cancelled", session_id=session_id,
                                   client_turn_id=cid,
                                   transcript_len=len(transcript),
                                   reply_len=len(reply),
                                   error="disconnect_after_commit")
                    return
                try:
                    chunk = await pump.next_chunk(idle_timeout_s())
                except StopAsyncIteration:
                    break
                except Exception as e:  # noqa: BLE001 - TTS/pump failure
                    if isinstance(e, TtsNotConfigured):
                        if vs.stub_tts_enabled():
                            stub_frames, stub_bytes = await vs.collect_stub_pcm()
                            for fr in stub_frames:
                                yield fr
                                pcm_chunks += 1
                            pcm_bytes += stub_bytes
                            if not first_pcm:
                                first_pcm = True
                                clock.mark("first_chunk_yielded")
                                vs.voice_event(
                                    "first_pcm", session_id=session_id,
                                    client_turn_id=cid,
                                    transcript_len=len(transcript),
                                    reply_len=len(reply),
                                    total_ms=(time.monotonic() - tts_t0) * 1000.0)
                            vs.voice_event("tts_stub", session_id=session_id,
                                           client_turn_id=cid,
                                           transcript_len=len(transcript),
                                           reply_len=len(reply),
                                           counts={"pcm_bytes": stub_bytes,
                                                   "pcm_chunks": len(stub_frames)})
                            break
                        outcome = "failed_tts_unavailable"
                        vs.voice_event("error", session_id=session_id,
                                       client_turn_id=cid,
                                       transcript_len=len(transcript),
                                       reply_len=len(reply),
                                       error="tts_not_configured")
                        yield vf.encode_error("tts_unavailable",
                                              "patient audio unavailable — "
                                              "reply text above is complete")
                        return
                    if pcm_chunks == 0 and attempts < 1 and isinstance(
                            e, TtsFailed):
                        # Early failure, nothing released: one fresh retry on
                        # the same remaining budget (no new 2s window).
                        attempts += 1
                        pump.restart()
                        continue
                    outcome = "failed_tts"
                    vs.voice_event("error", session_id=session_id,
                                   client_turn_id=cid,
                                   transcript_len=len(transcript),
                                   reply_len=len(reply),
                                   error=type(e).__name__[:80])
                    yield vf.encode_error("tts_failed",
                                          "patient audio unavailable — "
                                          "reply text above is complete")
                    return
                for fr in vf.encode_pcm_frames(chunk):
                    yield fr
                    pcm_chunks += 1
                pcm_bytes += len(chunk)
                clock.count("pcm_bytes", len(chunk))
                clock.count("pcm_chunks", 1)
                if not first_pcm:
                    first_pcm = True
                    clock.mark("first_chunk_yielded")
                    vs.voice_event("first_pcm", session_id=session_id,
                                   client_turn_id=cid,
                                   transcript_len=len(transcript),
                                   reply_len=len(reply),
                                   total_ms=(time.monotonic() - tts_t0) * 1000.0)
            vs.voice_event("tts_eof", session_id=session_id,
                           client_turn_id=cid, transcript_len=len(transcript),
                           reply_len=len(reply),
                           counts={"pcm_bytes": pcm_bytes,
                                   "pcm_chunks": pcm_chunks})
            yield vf.encode_done(pcm_bytes, pcm_chunks)
            vs.voice_event("done", session_id=session_id, client_turn_id=cid,
                           transcript_len=len(transcript),
                           reply_len=len(reply),
                           outcome=commit_status or "persisted",
                           counts={"pcm_bytes": pcm_bytes,
                                   "pcm_chunks": pcm_chunks})
        except GeneratorExit:
            outcome = "cancelled"
            vs.voice_event("cancelled", session_id=session_id,
                           client_turn_id=cid,
                           transcript_len=len(transcript), error="generator_exit")
            raise
        except Exception as e:  # noqa: BLE001 - post-accept → error frame
            outcome = "failed_llm" if reply is None else "failed_commit"
            vs.voice_event("error", session_id=session_id, client_turn_id=cid,
                           transcript_len=len(transcript),
                           error=type(e).__name__[:80])
            try:
                yield vf.encode_error(
                    "patient_failed",
                    "patient turn failed — retry audio (same turn) or "
                    "continue in text")
            except GeneratorExit:
                raise
            except Exception:  # noqa: BLE001
                pass
        finally:
            clock.mark("request_complete")
            clock.finish(outcome)
            clock.log_summary()
            if slot_held:
                slot_held = False
                limiter.release()

    async def _gen_wrapped():
        it = gen()
        try:
            async for chunk in it:
                yield chunk
        finally:
            try:
                await it.aclose()
            except Exception:  # noqa: BLE001 - cleanup must not fail
                pass
            if slot_held:
                limiter.release()

    return StreamingResponse(
        _gen_wrapped(), media_type="application/octet-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "X-Voice-Protocol": str(vf.VERSION)},
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


@router.post("/sessions/{session_id}/pf", dependencies=[_ai_rl])
def v2_pf(session_id: str, req: V2PFReq, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    """Structured physical-exam step (Aug 2026): the student states which areas
    they examine + what they expect; the endpoint reveals the patient's findings
    for those areas only. Stateless — the notes travel with the score request."""
    s = _owned(db, session_id, user)
    ensure_turnable(s.status)
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
    `extra` blob is replaced immutably so SQLAlchemy tracks the change.

    FASE 8: delegates to the shared `apply_progress_for_session` pure updater
    so V2 and V3 award XP/streak/history identically (parity fix). Legacy
    keys/rules preserved exactly.
    """
    from app.domains.sessions.progress_adapter import record_progress_for_report
    try:
        specialty = str((getattr(case, "frontmatter", None) or {}).get("specialty", ""))
    except Exception:
        specialty = ""
    try:
        case_id = getattr(case, "id", "") or ""
    except Exception:
        case_id = ""
    record_progress_for_report(user, case_id=case_id or "", specialty=specialty or "unknown",
                               report=report or {}, content_schema="legacy")


@router.post("/sessions/{session_id}/score", dependencies=[_ai_rl])
async def v2_score(session_id: str, req: V2ScoreReq, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    from app.domains.scoring.singleflight import run_singleflight
    from app.shared.perf_marks import TurnClock
    clock = TurnClock(route="v2_score", schema="legacy")
    clock.mark("request_received")
    clock.mark("auth_done")
    s = _owned(db, session_id, user)
    # Scoring may be retried by the browser/network after a slow judge call.
    # Return the stored report instead of awarding XP/progress twice.
    if s.status == "completed" and s.report:
        clock.count("stored_report_hit")
        clock.mark("request_complete")
        clock.finish("stored")
        clock.log_summary()
        return ok(s.report)
    clock.mark("context_ready")

    async def _do():
        if s.content_schema == "new":  # Phase B: V3 scoring -> V2 report shape
            from app.domains.sessions import v3_compat_service as v3c
            clock.count("judge_call")
            return await v3c.score(
                db, user, session_id, ddx=req.ddx, management=req.management,
                mode=req.mode, overtime=req.overtime,
                pf_notes=req.pf_notes, pf_areas=req.pf_areas)
        try:
            case = load_v2_case(s.case_id)
        except FileNotFoundError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"v2 case '{s.case_id}' not found")
        transcript = _history(db, session_id)
        user_id = user.id
        rubric_mode = _UI_MODE_TO_RUBRIC.get((req.mode or "").lower())
        req_mode, req_overtime = (req.mode or "practice"), bool(req.overtime)
        req_ddx, req_mgmt = req.ddx, req.management
        req_pf_notes, req_pf_areas = req.pf_notes, req.pf_areas
        # H1 (pool exhaustion): the judge holds 10-70s. Snapshot everything,
        # release the pool connection, judge, then persist on a fresh session
        # — same pattern as turns (v2_turn_stream db.close()).
        db.close()
        from app.rag.judge_v2 import aevaluate_v2
        clock.count("judge_call")
        report = await aevaluate_v2(case, transcript, mode=rubric_mode,
                                    student_ddx=req_ddx, student_management=req_mgmt,
                                    student_pf={"notes": req_pf_notes or "", "areas": req_pf_areas or []},
                                    session_id=session_id)
        if req_overtime:  # continued past the OSCE time limit (§4.3) -> small penalty
            orig = int(report.get("overall", 0) or 0)
            report["overall"] = max(0, orig - _OVERTIME_PENALTY)
            report["overtime_penalty"] = _OVERTIME_PENALTY
            report["summary"] = (report.get("summary", "") or "") + \
                f" (−{_OVERTIME_PENALTY} for continuing past the OSCE time limit.)"
        from app.domains.scoring.evidence_integration import maybe_enrich_report
        maybe_enrich_report(report, variant_id="", canonical_hash="",
                            rubric_items=[], mode=req_mode,
                            learner_stage="koas", clock=clock)
        from app.database import SessionLocal as _SessionLocal2
        db2 = _SessionLocal2()
        try:
            row = db2.get(SessionRow, session_id)
            if row is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
            if row.status == "completed" and row.report:
                return row.report  # cross-worker race: first persist wins
            row.total_score = report.get("overall", 0)
            row.report = report
            row.status = "completed"
            if row.ended_at is None:
                row.ended_at = datetime.now(timezone.utc)
            u2 = db2.get(User, user_id)
            _record_progress(u2, case, report)
            try:  # Phase 12: judge outcome correlation (metadata only, never content)
                from app.shared.observability import log_judge_event
                from pipeline.clinical_contracts.versions import SCORING_VERSION
                from app.rag.judge_v2 import is_stub as _judge_stub
                log_judge_event(engine="v2", outcome="stub" if _judge_stub() else "ok",
                                session_id=row.id, content_schema="legacy",
                                scoring_version=SCORING_VERSION)
            except Exception:
                pass
            db2.commit()
        finally:
            db2.close()
        clock.mark("db_persist_complete")
        return report  # includes answer_key for the post-session reveal

    # Phase 4: concurrent duplicate scoring shares one execution (§9.1d);
    # progress/XP therefore recorded exactly once.
    outcome = "complete"
    try:
        report, shared = await run_singleflight(f"score:{session_id}", _do)
        if shared:
            clock.count("singleflight_shared")
    except Exception:
        outcome = "failed"
        raise
    finally:
        clock.mark("request_complete")
        clock.finish(outcome)
        clock.log_summary()
    return ok(report)


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
def v2_progress(user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Gamification summary for the Qora flow: XP, streak, daily goal, badges,
    per-dimension skill averages, and specialty coverage.

    FASE 8 (unified): derived from completed sessions with stored reports
    (V2 + V3 via the canonical longitudinal model) so Result, Dashboard,
    Progress, and Mentor speak one vocabulary (§36). Legacy response keys
    are preserved; new explainable keys are additive:
    `readiness`, `coverage`, `dataSource`, `dimensionDetail`,
    `strongestSkill/weakestSkill`, `recentImprovement`, `definitions`.
    """
    from pipeline.progress.progress import compute_progress
    from pipeline.progress.readiness import compute_readiness
    prof = user.profile
    extra = (prof.extra if prof else {}) or {}
    try:
        from app.domains.sessions.progress_adapter import completed_normalized
        normalized = completed_normalized(db, user.id)
    except Exception:
        normalized = []
    prog = compute_progress(normalized)
    try:
        readiness = compute_readiness(normalized)
    except Exception:
        readiness = None
    # Legacy gamification state (XP/streak/bests) stays profile-authoritative.
    streak = int(prof.streak or 0) if prof else 0
    dates = extra.get("sessionDates") or {}
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    week = {(now.date() - timedelta(days=i)).isoformat() for i in range(7)}
    weekly = sum(int(v or 0) for k, v in dates.items() if k in week)
    completed_legacy = len(extra.get("completedCaseIds") or [])
    metrics = {"cases": prog["coverage"]["distinctCases"] or completed_legacy,
               "specialties": prog["coverage"]["specialties"],
               "avg_score": prog["avgScore"], "streak": streak,
               "sessions": prog["totalSessions"]}
    engines = sorted({s.get("engine") for s in normalized if s.get("engine")})
    return ok({
        "xp": int(prof.xp or 0) if prof else 0,
        "totalSessions": prog["totalSessions"],
        "completedCases": prog["coverage"]["distinctCases"] or completed_legacy,
        "streak": streak,
        "bestStreak": int(extra.get("bestStreak") or 0),
        "bestScore": int(extra.get("bestScore") or 0),
        "avgScore": prog["avgScore"],
        "dailyGoal": {"done": int(dates.get(today, 0) or 0), "target": 1},
        "weeklyCount": weekly,
        "sessions": prog["sessions"][:50],
        "dimensionAverages": prog["dimensionAverages"],
        "dimensionDetail": prog["dimensionDetail"],
        "strongestSkill": prog["strongestSkill"],
        "weakestSkill": prog["weakestSkill"],
        "recentImprovement": prog["recentImprovement"],
        "specialtyCounts": prog["specialtyCounts"],
        "coverage": prog["coverage"],
        "readiness": readiness,
        "badges": _compute_badges(metrics),
        "badgeMetrics": prog["badgeMetrics"],
        "dataSource": {"engines": engines,
                       "sessionsIncluded": prog["totalSessions"],
                       "excludedNoScore": prog["excludedNoScore"]},
        "definitions": prog["definitions"],
        "hasEvidence": prog["hasEvidence"],
    })
