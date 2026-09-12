"""Phase 3 — atomic turn acceptance (brief §4, §8.1).

One transaction per accepted turn: ownership/status revalidation, history
read, duplicate check, in-transaction numbering, user-turn persist, commit.
A `SELECT ... FOR UPDATE` on the session row serializes concurrent accepts
on the SAME session; different sessions never contend. No schema change:
fencing uses the row lock (short-lived, released at commit — never held
during LLM) plus an advisory lock at finalization.

Behavior preserved exactly (same errors, same messages, same ordering):
- missing/foreign session → 404 "Session not found" (ownership included);
- non-turnable status → existing `ensure_turnable` error;
- duplicate text → dedup reply (no insert), same as FASE 6;
- numbering = max(turn_number)+1 read INSIDE the lock (no extra COUNT).

Legacy V1 (`sessions/router.py`) and native `v3_service` writers keep their
own semantics and are NOT routed here (different error mapping/status
rules); mixed-path same-session concurrency is a documented residual.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.sessions.hardening import ensure_turnable, find_duplicate_reply
from app.domains.sessions.models import SessionRow, SessionTurn, VoiceTurnLedger
from app.domains.sessions.router import _history

_VOICE_CLIENT_ID_MAX = 128
_VOICE_TRANSCRIPT_MAX = 4000


@dataclass(frozen=True)
class TurnSnapshot:
    """Immutable pre-LLM snapshot: DTOs only, no ORM escapes the boundary."""

    session_id: str
    user_id: str
    status: str
    content_schema: str
    case_id: str
    language: str
    variant_id: str | None = None
    variant_canonical_hash: str | None = None
    persona: dict | None = None
    turn_no: int = 0
    history: tuple = ()
    dup_reply: str | None = None


def _snapshot_history(history: list[dict]) -> tuple:
    return tuple(
        {"role": h.get("role"), "content": h.get("content")} for h in history
    )


def accept_turn(db: Session, *, session_id: str, user_id: str, text: str,
                input_type: str = "text") -> TurnSnapshot:
    """Accept one user turn atomically; returns the immutable snapshot.

    Single transaction: lock session row → revalidate → read history →
    duplicate check → number → persist user turn → commit. Raises the same
    HTTP errors with the same messages as the previous inline preflight.
    """
    row = db.execute(
        select(SessionRow).where(SessionRow.id == session_id).with_for_update()
    ).scalar_one_or_none()
    if row is None or row.user_id != user_id:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    ensure_turnable(row.status)
    history = _history(db, session_id)
    dup = find_duplicate_reply(history, text)
    persona = _persona_dict(row.persona)
    if dup is not None:
        db.rollback()
        return TurnSnapshot(
            session_id=row.id, user_id=user_id, status=row.status,
            content_schema=row.content_schema or "legacy",
            case_id=row.case_id or "", language=row.language or "en",
            variant_id=row.variant_id, variant_canonical_hash=row.variant_canonical_hash,
            persona=persona, turn_no=0,
            history=_snapshot_history(history), dup_reply=dup,
        )
    max_no = db.scalar(
        select(func.max(SessionTurn.turn_number)).where(
            SessionTurn.session_id == session_id)
    )
    n = int(max_no or 0) + 1
    db.add(SessionTurn(session_id=row.id, turn_number=n, role="user",
                       content=text, input_type=input_type))
    db.commit()
    return TurnSnapshot(
        session_id=row.id, user_id=user_id, status=row.status,
        content_schema=row.content_schema or "legacy",
        case_id=row.case_id or "", language=row.language or "en",
        variant_id=row.variant_id, variant_canonical_hash=row.variant_canonical_hash,
            persona=persona, turn_no=n,
        history=_snapshot_history(history), dup_reply=None,
    )


def _persona_dict(raw) -> dict | None:
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            import json as _json

            return _json.loads(raw)
        except Exception:  # noqa: BLE001
            return None
    return dict(raw)


# ── Phase-2 voice acceptance (ADR §4.3) ──────────────────────────────────

def voice_body_hash(transcript: str) -> str:
    """Idempotency body hash: sha256 of the stripped transcript."""
    try:
        return hashlib.sha256((transcript or "").strip().encode("utf-8")).hexdigest()
    except Exception:  # noqa: BLE001
        return ""


@dataclass(frozen=True)
class VoiceTurnSnapshot:
    """Immutable pre-LLM snapshot for one voice turn (DTOs only)."""

    session_id: str
    user_id: str
    status: str
    content_schema: str
    case_id: str
    language: str
    variant_id: str | None = None
    variant_canonical_hash: str | None = None
    persona: dict | None = None
    turn_no: int = 0          # the persisted user turn_number
    history: tuple = ()       # history BEFORE the user turn (for the engine)
    replay_reply: str | None = None  # set when the winner is already durable
    adopted: bool = False     # True when retry adopted a pre-commit row


def accept_voice_turn(db: Session, *, session_id: str, user_id: str,
                      client_turn_id: str, transcript: str) -> VoiceTurnSnapshot:
    """Atomically accept one voice turn keyed by client_turn_id.

    One transaction: lock session row → revalidate → validate key/body →
    ledger check → (new: number + persist user turn + insert ledger) → commit.

    Outcomes (same HTTP semantics as the text path where they overlap):
    - missing/foreign session → 404; completed session → existing guard;
    - bad key/body → 400; same key + different body hash → 409;
    - same key + committed winner → snapshot with replay_reply (NO new
      inference, NO new rows — caller streams the stored winner);
    - same key + accepted (pre-commit) row + same hash → snapshot with
      adopted=True reusing turn_no (NO second user turn — caller re-runs
      inference; the commit fence still yields exactly one winner).
    The UNIQUE(session_id, client_turn_id) insert is the cross-worker fence:
    concurrent same-key accepts serialize here, never as process-local locks.
    """
    cid = (client_turn_id or "").strip()
    text_in = (transcript or "").strip()
    if not cid or len(cid) > _VOICE_CLIENT_ID_MAX:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "client_turn_id required (max 128 chars)")
    if not text_in or len(text_in) > _VOICE_TRANSCRIPT_MAX:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "transcript required (max 4000 chars)")
    row = db.execute(
        select(SessionRow).where(SessionRow.id == session_id).with_for_update()
    ).scalar_one_or_none()
    if row is None or row.user_id != user_id:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    ensure_turnable(row.status)
    bhash = voice_body_hash(text_in)
    existing = db.scalar(
        select(VoiceTurnLedger).where(
            VoiceTurnLedger.session_id == session_id,
            VoiceTurnLedger.client_turn_id == cid)
    )
    if existing is not None:
        if (existing.body_hash or "") != bhash:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "client_turn_id already used with a different transcript")
        if (existing.status or "") == "committed" and (existing.reply or "").strip():
            db.rollback()
            return VoiceTurnSnapshot(
                session_id=row.id, user_id=user_id, status=row.status,
                content_schema=row.content_schema or "legacy",
                case_id=row.case_id or "", language=row.language or "en",
                variant_id=row.variant_id,
                variant_canonical_hash=row.variant_canonical_hash,
                persona=_persona_dict(row.persona), turn_no=int(existing.turn_no or 0),
                history=(), replay_reply=(existing.reply or "").strip(),
                adopted=False,
            )
        # Pre-commit retry: adopt the existing turn_no. History may already
        # contain the adopted user turn — exclude it so the engine prompt is
        # identical to the first attempt's (history-before + transcript).
        history = _history(db, session_id)
        if (history and history[-1].get("role") == "user"
                and (history[-1].get("content") or "").strip() == text_in):
            history = history[:-1]
        db.rollback()
        return VoiceTurnSnapshot(
            session_id=row.id, user_id=user_id, status=row.status,
            content_schema=row.content_schema or "legacy",
            case_id=row.case_id or "", language=row.language or "en",
            variant_id=row.variant_id,
            variant_canonical_hash=row.variant_canonical_hash,
            persona=_persona_dict(row.persona),
            turn_no=int(existing.turn_no or 0),
            history=_snapshot_history(history), replay_reply=None,
            adopted=True,
        )
    history = _history(db, session_id)
    max_no = db.scalar(
        select(func.max(SessionTurn.turn_number)).where(
            SessionTurn.session_id == session_id)
    )
    n = int(max_no or 0) + 1
    db.add(SessionTurn(session_id=row.id, turn_number=n, role="user",
                       content=text_in, input_type="voice"))
    db.add(VoiceTurnLedger(session_id=row.id, client_turn_id=cid,
                           body_hash=bhash, transcript_len=len(text_in),
                           turn_no=n, status="accepted"))
    snap = VoiceTurnSnapshot(
        session_id=row.id, user_id=user_id, status=row.status,
        content_schema=row.content_schema or "legacy",
        case_id=row.case_id or "", language=row.language or "en",
        variant_id=row.variant_id,
        variant_canonical_hash=row.variant_canonical_hash,
        persona=_persona_dict(row.persona), turn_no=n,
        history=_snapshot_history(history), replay_reply=None,
        adopted=False,
    )
    try:
        db.commit()
    except IntegrityError:
        # Lost the cross-worker insert race: the winner's row is now
        # visible — reread under a fresh transaction and follow it.
        db.rollback()
        loser = db.scalar(
            select(VoiceTurnLedger).where(
                VoiceTurnLedger.session_id == session_id,
                VoiceTurnLedger.client_turn_id == cid)
        )
        if loser is None or (loser.body_hash or "") != bhash:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "client_turn_id already used with a different transcript")
        if (loser.status or "") == "committed" and (loser.reply or "").strip():
            return VoiceTurnSnapshot(
                session_id=session_id, user_id=user_id,
                status=snap.status, content_schema=snap.content_schema,
                case_id=snap.case_id, language=snap.language,
                variant_id=snap.variant_id,
                variant_canonical_hash=snap.variant_canonical_hash,
                persona=snap.persona, turn_no=int(loser.turn_no or 0),
                history=(), replay_reply=(loser.reply or "").strip(),
                adopted=False,
            )
        return VoiceTurnSnapshot(
            session_id=session_id, user_id=user_id,
            status=snap.status, content_schema=snap.content_schema,
            case_id=snap.case_id, language=snap.language,
            variant_id=snap.variant_id,
            variant_canonical_hash=snap.variant_canonical_hash,
            persona=snap.persona, turn_no=int(loser.turn_no or 0),
            history=snap.history, replay_reply=None, adopted=True,
        )
    return snap


def commit_voice_winner(db_factory, *, session_id: str, client_turn_id: str,
                        turn_no: int, reply: str,
                        record_cost=None) -> tuple[str, str]:
    """Persist the ONE durable winner for a voice turn (ADR §4.2 step 5).

    Final transaction (holds across workers via the DB, never a
    process-local lock): advisory xact lock per session (PostgreSQL; skipped
    elsewhere) → reread ledger → committed already? return ("replayed",
    stored) with NO insert → else insert patient turn_no+1 + mark ledger
    committed + reply in the same commit. Returns ("persisted"|"replayed",
    reply_text). A disconnect/crash before this commit leaves the ledger
    `accepted` with no patient row — recovery adopts and re-runs, and this
    fence still yields exactly one patient row.
    """
    from sqlalchemy import inspect as _sa_inspect

    clean = (reply or "").strip()
    if not clean:
        raise ValueError("commit_voice_winner: empty reply is never durable")
    db = db_factory()
    try:
        dialect = _sa_inspect(db.bind).dialect.name if db.bind is not None else ""
        if dialect == "postgresql":
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:sid))"),
                {"sid": session_id},
            )
        row = db.scalar(
            select(VoiceTurnLedger).where(
                VoiceTurnLedger.session_id == session_id,
                VoiceTurnLedger.client_turn_id == (client_turn_id or "").strip())
        )
        if row is None:
            db.rollback()
            raise LookupError("voice ledger row missing for client_turn_id")
        if (row.status or "") == "committed" and (row.reply or "").strip():
            db.rollback()
            return "replayed", (row.reply or "").strip()
        patient_no = int(turn_no or row.turn_no or 0) + 1
        conflict = db.scalar(
            select(func.count(SessionTurn.id)).where(
                SessionTurn.session_id == session_id,
                SessionTurn.turn_number >= patient_no,
            )
        )
        if conflict:
            # Reached only when the ledger holds NO winner (committed+reply
            # returned above): a foreign turn (e.g. text-path interleave)
            # took our number. Append the single winner at a fresh number so
            # the reply the client hears is still the durable one. A racing
            # voice worker can never reach here: it either sees the committed
            # ledger above, or serializes behind us on the advisory lock and
            # then sees it. Same-session text finalization takes the same
            # advisory lock, so fresh-number allocation cannot collide.
            fresh = db.scalar(
                select(func.max(SessionTurn.turn_number)).where(
                    SessionTurn.session_id == session_id)
            )
            patient_no = max(patient_no, int(fresh or 0) + 1)
        db.add(SessionTurn(session_id=session_id, turn_number=patient_no,
                           role="patient", content=clean))
        row.status = "committed"
        row.reply = clean
        db.commit()
        if record_cost is not None:
            # Same durability posture as finalize_patient_turn: cost runs in
            # a best-effort follow-up unit, never inside the winner commit.
            try:
                record_cost(db)
                db.commit()
            except Exception:  # noqa: BLE001
                try:
                    db.rollback()
                except Exception:  # noqa: BLE001
                    pass
        return "persisted", clean
    except Exception:
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        raise
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


def read_voice_winner(db_factory, *, session_id: str,
                      client_turn_id: str) -> str | None:
    """Return the durable winner text for a key, or None (total, never raises).

    Lets a racing/second worker skip new inference when the winner is already
    committed. Timing-safe: callers still commit through commit_voice_winner
    (the fence), never by trusting this read alone.
    """
    try:
        db = db_factory()
    except Exception:  # noqa: BLE001
        return None
    try:
        row = db.scalar(
            select(VoiceTurnLedger).where(
                VoiceTurnLedger.session_id == session_id,
                VoiceTurnLedger.client_turn_id == (client_turn_id or "").strip())
        )
        if row is not None and (row.status or "") == "committed":
            text_out = (row.reply or "").strip()
            return text_out or None
        return None
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


def finalize_patient_turn(db_factory, *, session_id: str, turn_no: int,
                          reply: str, history_text_len: int = 0,
                          text_len: int = 0, user_id: str = "",
                          record_cost=None) -> str:
    """Persist the canonical patient reply with fencing (brief §8.1k/l).

    Final transaction: advisory xact lock per session (PostgreSQL; skipped
    elsewhere) → skip insert when a turn >= turn_no already exists (stale
    worker must not overwrite newer results) → insert + commit. Returns
    'persisted' | 'superseded'. `record_cost(db, ...)` runs in the same unit
    when provided. Never regenerates LLM output.
    """
    from sqlalchemy import inspect as _sa_inspect

    db = db_factory()
    try:
        dialect = _sa_inspect(db.bind).dialect.name if db.bind is not None else ""
        if dialect == "postgresql":
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:sid))"),
                {"sid": session_id},
            )
        newer = db.scalar(
            select(func.count(SessionTurn.id)).where(
                SessionTurn.session_id == session_id,
                SessionTurn.turn_number >= turn_no,
            )
        )
        if newer:
            db.rollback()
            return "superseded"
        db.add(SessionTurn(session_id=session_id, turn_number=turn_no,
                           role="patient", content=reply))
        db.commit()
        if record_cost is not None:
            record_cost(db)
            db.commit()
        return "persisted"
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            db.close()
        except Exception:
            pass
