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

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.sessions.hardening import ensure_turnable, find_duplicate_reply
from app.domains.sessions.models import SessionRow, SessionTurn
from app.domains.sessions.router import _history


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
