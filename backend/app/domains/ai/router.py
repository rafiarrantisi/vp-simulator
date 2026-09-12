"""AI I/O — STT/TTS (Fase 4, kontrak v0.8.0).

/api/ai/transcribe : Whisper (OpenAI-compatible) + MD5 dedup guard, butuh
                     auth. Balas {transcript, is_duplicate}.
/api/ai/tts        : Gemini TTS → audio/mpeg; 501 jelas bila belum
                     dikonfigurasi.
/api/ai/tts/stream : Gemini TTS streaming → framed PCM chunks
                     (4-byte big-endian length + int16 mono 24kHz), zero-length
                     frame = clean end. Voice/style resolved SERVER-SIDE from
                     the session's patient card — the client never chooses them.
"""
import hashlib
import struct
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.domains.auth.models import User
from app.shared.dependencies import get_current_user
from app.shared.envelope import err, ok
from app.shared.ratelimit import rate_limit
from app.voice.stt import SttUnavailable
from app.voice.stt import is_configured as stt_configured
from app.voice.stt import transcribe
from app.voice.tts import TtsFailed, TtsNotConfigured, stream_pcm, synthesize
from app.database import get_db
from sqlalchemy.orm import Session as OrmSession

router = APIRouter(
    prefix="/api/ai",
    tags=["ai"],
    dependencies=[Depends(rate_limit("ai", "rate_limit_ai"))],
)

# Dedup guard in-memory (voice-plan §6): hash audio → ts terakhir.
_recent: dict[str, float] = {}
_DEDUP_WINDOW = 5.0  # detik


def _is_dup(h: str) -> bool:
    now = time.time()
    for k in [k for k, v in _recent.items() if now - v > _DEDUP_WINDOW * 2]:
        _recent.pop(k, None)
    last = _recent.get(h)
    _recent[h] = now
    return last is not None and (now - last) < _DEDUP_WINDOW


@router.get("/voice-status")
def voice_status(user: User = Depends(get_current_user)):
    """Readiness for the session-prep screen (instruksi §4.5): whether the
    speech-to-text and text-to-speech services are configured. Never reveals keys."""
    s = get_settings()
    return ok({
        "stt": stt_configured(),
        "tts": s.tts_provider == "gemini",
        # Entitlement placeholder (billing tahap berikutnya): server yang
        # memutuskan; room hanya membaca boolean ini. Dev: selalu True.
        "voice_enabled": s.tts_provider == "gemini",
        "language": s.stt_language,
    })


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    user: User = Depends(get_current_user),
):
    data = await audio.read()
    if not data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=err("Audio kosong")
        )
    if _is_dup(hashlib.md5(data).hexdigest()):
        return ok({"transcript": "", "is_duplicate": True})
    try:
        text = transcribe(data, audio.filename or "speech.webm")
    except SttUnavailable as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=err(str(e))
        )
    return ok({"transcript": text, "is_duplicate": False})


class TtsRequest(BaseModel):
    text: str


@router.post("/tts")
def tts(req: TtsRequest, user: User = Depends(get_current_user)):
    try:
        audio = synthesize(req.text)
    except TtsNotConfigured as e:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, content=err(str(e))
        )
    except TtsFailed as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY, content=err(str(e))
        )
    return Response(content=audio, media_type="audio/mpeg")


class TtsStreamRequest(BaseModel):
    text: str
    session_id: str


_EOF = struct.pack(">I", 0)
_TTS_STREAM_MAX_CHARS = 2000  # credit guard per request


def _tts_frames(text: str, voice: str | None, style: str | None,
                lang: str | None, session_ref: str):
    """Framed PCM generator for tts/stream (extracted for auditability).

    Phase-1 event-loop audit (Run 1, measured — see
    tests/test_voice_phase1_foundation.py::test_tts_stream_off_event_loop):
    `stream_pcm` is a BLOCKING gRPC generator, but this code never runs on
    the event loop. The route is a sync `def` (Starlette runs it in a worker
    thread) and the response body is a sync iterable (Starlette consumes it
    via iterate_in_threadpool). No bounded-thread offload was added: the
    framework already provides it. Do NOT convert this route to
    `async def` without re-auditing — an async route consuming a blocking
    generator inline WOULD stall the loop.
    """
    from app.voice.tts import _drop_client

    from app.voice.tts import stream_pcm as _stream_pcm
    for attempt in (0, 1):
        try:
            for chunk in _stream_pcm(text, voice=voice, style=style or None,
                                     language=lang):
                yield struct.pack(">I", len(chunk)) + chunk
            yield _EOF
            return
        except TtsFailed as e:
            import logging as _logging
            _logging.getLogger("qora.tts").warning(
                "tts stream attempt %d failed for session %s: %s",
                attempt, (session_ref or "")[:8], str(e)[:150])
            _drop_client()  # broken channel must not poison the next turn
        except Exception:  # noqa: BLE001
            _drop_client()
            return
    # both attempts failed: no terminator -> client falls back to text


@router.post("/tts/stream")
def tts_stream(req: TtsStreamRequest, user: User = Depends(get_current_user),
               db: OrmSession = Depends(get_db)):
    """Voice-mode audio: framed PCM straight from Gemini streaming.

    Voice/style come from the session's patient card on the server. Truncated
    stream (no zero-length terminator) = failure: client falls back to text.
    """
    from app.domains.sessions.models import SessionRow
    from app.voice.persona_voice import resolve_voice

    text = (req.text or "").strip()
    if not text:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=err("Teks kosong"))
    if len(text) > _TTS_STREAM_MAX_CHARS:
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content=err("Teks terlalu panjang untuk satu turn suara"))
    s = db.get(SessionRow, req.session_id)
    if s is None or s.user_id != user.id:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content=err("Session not found"))
    voice, style, lang = resolve_voice(s, db)

    def _frames():
        yield from _tts_frames(text, voice, style, lang, req.session_id)

    def _gen():
        yield from _frames()

    return StreamingResponse(
        _gen(), media_type="application/octet-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
