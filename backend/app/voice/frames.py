"""Phase-2 voice transport — typed framed stream (ADR §4.2).

ONE POST streaming response per voice turn. Wire format (binary, no base64):

    type:u8 + length:u32be + payload[length]

Frame types (protocol VERSION 1):

    0x01 metadata    JSON  {v, route, turn_no, session_ref, reply_chars, ...}
    0x02 final-text  JSON  {text} — the ONE durable winner (persisted first)
    0x03 pcm         raw int16le mono 24kHz bytes (chunked, see MAX_PCM_CHUNK)
    0x04 error       JSON  {code, error} — terminal failure, no done follows
    0x05 done        JSON  {ok:true, pcm_bytes, pcm_chunks} — clean end

Ordering: metadata → final-text → pcm* → done. PCM is NEVER released
before the winner commit succeeds (the route buffers/starts TTS but holds
every pcm frame until commit returns). A stream with no `done` (and no
`error`) is truncated — the client falls back to text WITHOUT re-inference.

Incremental parsing is MANDATORY: one `reader.read()` is NOT one frame.
Use IncrementalParser.feed() (backend mirror) / qvParseVoiceFrames (JS) —
both enforce MAX_FRAME_LEN and split/merge arbitrarily.

Privacy: frames carry the turn's own reply audio/text to its owner only.
Perf logs carry timing/IDs/lengths only (never transcript/reply bytes).
"""
from __future__ import annotations

import json
import struct

VERSION = 1

METADATA = 0x01
FINAL_TEXT = 0x02
PCM = 0x03
ERROR = 0x04
DONE = 0x05

_KNOWN_TYPES = frozenset({METADATA, FINAL_TEXT, PCM, ERROR, DONE})

HEADER_LEN = 5  # u8 type + u32be length

# Largest single payload the parser accepts. PCM chunks are produced well
# below this (MAX_PCM_CHUNK); anything larger is a protocol violation.
MAX_FRAME_LEN = 1 << 20  # 1 MiB

# PCM payload size per emitted frame (~85ms of 24kHz int16 mono). Small
# enough for progressive playback, large enough to avoid frame spam.
MAX_PCM_CHUNK = 4096

# JSON control frames stay tiny; bound them tighter than PCM.
MAX_JSON_LEN = 1 << 16  # 64 KiB

_MIME = "application/octet-stream"


class FrameProtocolError(ValueError):
    """Oversize frame, unknown type, or truncated header/payload."""


def encode_frame(ftype: int, payload: bytes) -> bytes:
    """Encode one frame. Total, except oversize/unknown-type (raises)."""
    if ftype not in _KNOWN_TYPES:
        raise FrameProtocolError(f"unknown frame type {ftype!r}")
    payload = payload or b""
    if len(payload) > MAX_FRAME_LEN:
        raise FrameProtocolError(f"frame too large: {len(payload)}")
    if ftype in (METADATA, FINAL_TEXT, ERROR, DONE) and len(payload) > MAX_JSON_LEN:
        raise FrameProtocolError(f"control frame too large: {len(payload)}")
    return struct.pack(">BI", ftype, len(payload)) + payload


def _json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def encode_metadata(meta: dict) -> bytes:
    doc = {"v": VERSION}
    try:
        doc.update(dict(meta or {}))
    except Exception:
        pass
    return encode_frame(METADATA, _json_bytes(doc))


def encode_final_text(text: str) -> bytes:
    return encode_frame(FINAL_TEXT, _json_bytes({"text": text or ""}))


def encode_pcm_frames(pcm: bytes, chunk: int = MAX_PCM_CHUNK) -> list[bytes]:
    """Split raw PCM into one frame per chunk (empty input → no frames)."""
    data = bytes(pcm or b"")
    if not data:
        return []
    size = max(1, int(chunk or MAX_PCM_CHUNK))
    return [encode_frame(PCM, data[i:i + size])
            for i in range(0, len(data), size)]


def encode_error(code: str, message: str) -> bytes:
    return encode_frame(ERROR, _json_bytes(
        {"code": str(code or "error")[:48],
         "error": str(message or "failed")[:200]}))


def encode_done(pcm_bytes: int = 0, pcm_chunks: int = 0) -> bytes:
    return encode_frame(DONE, _json_bytes(
        {"ok": True, "pcm_bytes": int(pcm_bytes or 0),
         "pcm_chunks": int(pcm_chunks or 0)}))


def decode_json(payload: bytes) -> dict:
    try:
        obj = json.loads(bytes(payload or b"").decode("utf-8"))
    except Exception as exc:
        raise FrameProtocolError(f"bad json payload: {exc}") from exc
    return obj if isinstance(obj, dict) else {}


class IncrementalParser:
    """Byte-incremental frame parser: feed() any splits, get whole frames.

    Usage: parser.feed(chunk) → list[(ftype, payload)]. Raises
    FrameProtocolError on oversize/unknown (caller converts to an error
    frame / text fallback — never re-inference).
    """

    def __init__(self):
        self._buf = bytearray()

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        if data:
            self._buf += data
        out: list[tuple[int, bytes]] = []
        buf = self._buf
        while True:
            if len(buf) < HEADER_LEN:
                return out
            ftype = buf[0]
            if ftype not in _KNOWN_TYPES:
                raise FrameProtocolError(f"unknown frame type {ftype:#x}")
            (length,) = struct.unpack_from(">I", buf, 1)
            if length > MAX_FRAME_LEN:
                raise FrameProtocolError(f"frame too large: {length}")
            if ftype in (METADATA, FINAL_TEXT, ERROR, DONE) and length > MAX_JSON_LEN:
                raise FrameProtocolError(f"control frame too large: {length}")
            if len(buf) < HEADER_LEN + length:
                return out
            payload = bytes(buf[HEADER_LEN:HEADER_LEN + length])
            del buf[:HEADER_LEN + length]
            out.append((ftype, payload))

    def pending_bytes(self) -> int:
        return len(self._buf)
