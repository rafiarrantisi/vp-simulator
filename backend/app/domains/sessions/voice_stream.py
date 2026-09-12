"""Phase-2 server-orchestrated voice turn (ADR §4.2, §4.3).

Pipeline per POST /api/v2/sessions/{id}/turns/voice-stream:

    accept (idempotent, via turn_acceptance) → buffer ONE full reply through
    the Phase-1 patient adapter (OpenCode zen deepseek-v4-flash, identical
    params/guards/timeouts incl. the 7s TTFT guard — NO provider migration)
    → fenced winner commit (durable BEFORE any PCM) → server-side Gemini TTS
    (existing tts + persona_voice.resolve_voice) → ONE typed framed stream.

HARD CONSTRAINTS (frozen):
- No provider/model/endpoint/timeout/guard change: the LLM call is
  engine_v2/engine_v3.arespond() — the same guarded astream_patient path the
  text route uses. No sentence pipelining, no speculative segmentation, no
  token-to-TTS: the full reply is selected first, then ONE synthesis.
- PCM is NEVER yielded before commit_voice_winner succeeds. TTS synthesis
  may overlap the commit (progressive pump starts early) but every PCM byte
  is held until the winner is durable; on commit failure the buffered audio
  is dropped and an error frame goes out — never audible-but-unlogged audio.
- Disconnect before commit cancels work (no winner persisted); the same
  client_turn_id then adopts the accepted row and re-runs. After commit,
  recovery streams the stored winner with NO new inference.
- Perf/telemetry rows carry timing, opaque IDs and lengths ONLY (never
  transcript/reply bytes, keys, or audio). Client endpoint telemetry is
  untrusted: numeric ranges clamped, reason label truncated, content ignored.
- Zero paid calls in stub env: LLM is the Phase-1 stub provider when no key;
  TTS stub PCM is emitted ONLY with QORA_VOICE_STUB_TTS=1 (explicit opt-in,
  tests/E2E) — a misconfigured prod (TTS down, flag off) gets an error frame,
  never synthetic audio.
"""
from __future__ import annotations

import math
import os
import queue
import threading
import time

from app.domains.sessions.models import VoiceTurnLedger  # noqa: F401 (registry)
from app.domains.sessions.turn_acceptance import (
    VoiceTurnSnapshot,
    commit_voice_winner,
    read_voice_winner,
)
from app.voice import frames as vf

_ROUTE = "voice_stream"
TTS_STREAM_MAX_CHARS = 2000  # same credit guard as /api/ai/tts/stream

# Client endpoint telemetry allowlist (timing/counts/labels only — the body
# text, if ever sent, is dropped here, never logged or persisted).
_TELEMETRY_NUM_KEYS = ("time_to_submit_ms", "endpoint_ms", "quiet_ms",
                       "interim_n", "final_n", "restart_n")
_TELEMETRY_NUM_MAX = 10 ** 9


def voice_event(event: str, *, session_id: str = "", client_turn_id: str = "",
                transcript_len: int = 0, reply_len: int = 0,
                route: str = _ROUTE, error: str = "",
                ttft_ms: float | None = None, total_ms: float | None = None,
                counts: dict | None = None, outcome: str = "",
                mode: str = "") -> dict:
    """Append one metadata-only voice_turn row to the queryable sink."""
    try:
        from app.shared.perf_sink import append_record, session_ref
        record: dict = {
            "kind": "voice_turn",
            "event": str(event or "")[:32],
            "route": str(route or "")[:48],
            "logical_turn_id": f"{session_id}:{client_turn_id}",
            "session_ref": session_ref(session_id),
            "input_chars": max(0, int(transcript_len or 0)),
            "output_chars": max(0, int(reply_len or 0)),
        }
        if error:
            record["error"] = str(error)[:80]
        if outcome:
            record["outcome"] = str(outcome)[:40]
        if mode:
            record["mode"] = str(mode)[:24]
        for key, value in (("ttft_ms", ttft_ms), ("total_ms", total_ms)):
            try:
                if value is not None:
                    record[key] = float(value)
            except (TypeError, ValueError):
                pass
        if isinstance(counts, dict) and counts:
            clean = {}
            for k, v in list(counts.items())[:16]:
                try:
                    clean[str(k)[:32]] = max(0, int(v or 0))
                except (TypeError, ValueError):
                    continue
            if clean:
                record["counts"] = clean
        return append_record(record)
    except Exception:  # noqa: BLE001 - telemetry never fails a turn
        return {}


def sanitize_client_telemetry(raw) -> dict:
    """Project untrusted endpoint telemetry onto timing/counts/labels only."""
    out: dict = {}
    if not isinstance(raw, dict):
        return out
    try:
        items = list(raw.items())[:16]
    except Exception:  # noqa: BLE001
        return out
    for key, value in items:
        try:
            name = str(key)
        except Exception:  # noqa: BLE001
            continue
        if name in _TELEMETRY_NUM_KEYS:
            try:
                num = float(value)
            except (TypeError, ValueError):
                continue
            if num != num or num in (float("inf"), float("-inf")):
                continue
            out[name] = max(0, min(_TELEMETRY_NUM_MAX, num))
        elif name in ("endpoint_reason", "reason"):
            try:
                out["endpoint_reason"] = " ".join(str(value).split())[:32]
            except Exception:  # noqa: BLE001
                pass
        elif name == "manual":
            out["manual"] = 1 if value else 0
        # everything else (notably any text/transcript) is dropped.
    return out


async def run_voice_llm(snap: VoiceTurnSnapshot, transcript: str,
                        *, session_id: str, client_turn_id: str) -> str:
    """Buffer ONE full patient reply via the Phase-1 adapter.

    Identical engine/guards to the text path (7s TTFT + 20s total via
    astream_patient, one fresh-lane retry). Raises on transport failure or
    empty output — empty/format-invalid output is never a playable winner.
    """
    from app.rag import engine_v2

    history = [dict(h) for h in (snap.history or ())]
    logical = f"{session_id}:{client_turn_id}"
    language = snap.language or "en"
    if (snap.content_schema or "legacy") == "new":
        from app.domains.sessions import v3_compat_service as v3c
        from app.rag import engine_v3
        variant = v3c._resolve_frozen(snap)
        reply = await engine_v3.arespond(
            variant, history, transcript, language=language,
            persona=snap.persona, session_id=session_id,
            route=_ROUTE, logical_turn_id=logical)
    else:
        reply = await engine_v2.arespond(
            snap.case_id, history, transcript, language=language,
            session_id=session_id, route=_ROUTE, logical_turn_id=logical)
    clean = (reply or "").strip()
    if not clean:
        raise RuntimeError("patient LLM returned empty output")
    return clean


def _stub_pcm_bytes(seconds: float = 0.5, freq_hz: float = 440.0,
                    sample_rate: int = 24000) -> bytes:
    """Deterministic stub PCM (int16le mono 24kHz sine, tests/E2E only)."""
    import struct as _struct

    n = max(1, int(seconds * sample_rate))
    out = bytearray(n * 2)
    for i in range(n):
        sample = int(12000.0 * math.sin(2.0 * math.pi * freq_hz * i / sample_rate))
        _struct.pack_into("<h", out, i * 2, sample)
    return bytes(out)


def stub_tts_enabled() -> bool:
    """Explicit stub-audio opt-in (never on by accident in prod)."""
    try:
        return os.environ.get("QORA_VOICE_STUB_TTS", "") == "1"
    except Exception:  # noqa: BLE001
        return False


class _PcmPump:
    """Progressive bridge: blocking stream_pcm (thread) → async byte pulls.

    Synthesis may start alongside the winner commit, but the caller MUST NOT
    release any pumped byte until commit succeeds (buffer-then-gate). One
    retry is allowed ONLY while zero PCM bytes have been released and the
    failure happened early (mirrors /api/ai/tts/stream two-attempt policy;
    after the first PCM byte there is no restart — text fallback instead).
    """

    def __init__(self, text: str, *, voice: str | None, style: str | None,
                 lang: str | None, session_ref: str):
        self._text = text
        self._voice = voice
        self._style = style
        self._lang = lang
        self._session_ref = (session_ref or "")[:8]
        self._queue: queue.Queue = queue.Queue()
        self._eof = object()
        self._started = False

    def _pump_once(self) -> None:
        from app.voice.tts import TtsFailed, TtsNotConfigured, stream_pcm

        q = self._queue
        try:
            for chunk in stream_pcm(self._text, voice=self._voice,
                                    style=self._style or None,
                                    language=self._lang):
                if chunk:
                    q.put(bytes(chunk))
            q.put(self._eof)
        except (TtsFailed, TtsNotConfigured) as e:
            q.put(e)
        except ImportError as e:
            # stream_pcm imports the google client lazily at call time; a
            # missing/broken google lib surfaces as a bare ImportError, not
            # TtsNotConfigured (tts.py contract gap, left untouched here).
            # Treat "no google TTS transport" as not-configured so the stub
            # opt-in and the clean unavailable-error both trigger correctly.
            if "texttospeech" in str(e).lower() or "google" in str(e).lower():
                q.put(TtsNotConfigured(f"Google TTS transport missing: {e}"))
            else:  # pragma: no cover - unrelated import failure
                q.put(TtsFailed(f"tts pump failed: {type(e).__name__}"))
        except Exception as e:  # noqa: BLE001 - never strand the puller
            try:
                from app.voice.tts import TtsFailed as _TF
                q.put(_TF(f"tts pump failed: {type(e).__name__}"))
            except Exception:  # noqa: BLE001
                q.put(self._eof)

    def start(self) -> None:
        if self._started:
            return
        self._started = True

        def _run():
            self._pump_once()

        thread = threading.Thread(target=_run, daemon=True,
                                  name="qora-voice-tts-pump")
        thread.start()

    def restart(self) -> None:
        """Fresh pump for the early-failure retry (drops the old queue)."""
        self._queue = queue.Queue()
        self._started = False
        try:
            from app.voice.tts import _drop_client
            _drop_client()  # broken channel must not poison the retry
        except Exception:  # noqa: BLE001
            pass
        self.start()

    async def next_chunk(self, timeout_s: float):
        """Next pumped item: bytes | EOF-sentinel | Exception (raises Stop)."""
        import anyio

        with anyio.fail_after(timeout_s):
            item = await anyio.to_thread.run_sync(self._queue.get)
        if item is self._eof:
            raise StopAsyncIteration
        if isinstance(item, Exception):
            raise item
        return item


async def collect_stub_pcm() -> tuple[list[bytes], int]:
    """Stub PCM frames for QORA_VOICE_STUB_TTS=1 (no network, no billing).

    Returns (frames, total_pcm_bytes).
    """
    import anyio

    data = await anyio.to_thread.run_sync(_stub_pcm_bytes)
    return vf.encode_pcm_frames(data), len(data)


def resolve_turn_voice(session_id: str) -> tuple[str | None, str | None, str | None]:
    """Server-resolved (voice, style, lang) for the session; never raises."""
    try:
        from app.database import SessionLocal
        from app.domains.sessions.models import SessionRow
        from app.voice.persona_voice import resolve_voice

        db = SessionLocal()
        try:
            row = db.get(SessionRow, session_id)
            if row is None:
                return None, None, None
            return resolve_voice(row, db)
        finally:
            try:
                db.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001 - voice must never break a turn
        return None, None, None
