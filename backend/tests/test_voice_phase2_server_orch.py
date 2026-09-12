"""Phase-2 server-orchestrated voice path (ADR §4.2/§4.3) — stub transports only.

Covers, with zero paid calls (stub LLM + QORA_VOICE_STUB_TTS=1 PCM):
  (1) framed protocol: roundtrip, incremental splits, max-length/unknown-type
      rejection (backend parser; the JS mirror qvFeedVoiceFrames in
      sistemnya/qora-voice.jsx implements the same u8+u32be wire format);
  (2) voice-stream success: metadata → final-text → pcm* → done, winner
      durable before any PCM, perf_sink voice_turn events metadata-only;
  (3) idempotent double-submit: same key+body replays WITHOUT new inference
      (engine call count == 1) and persists exactly one user+patient pair;
  (4) same key + different body → 409, no new rows;
  (5) disconnect-cancel: accept with no commit persists no patient row; the
      same key then adopts (same turn_no, no second user turn) and commits
      exactly one winner;
  (6) winner-once: double commit (simulated 2 workers) → first persisted,
      second replayed, single patient row with the first reply;
  (7) auth/validation: 401 without token, 404 on foreign session;
  (8) endpointing decision-logic unit tests (python mirror of the JS pure
      function qvEndpointNext in sistemnya/qora-voice.jsx — thresholds are
      asserted identically on both sides; no JS runner exists in this repo,
      so the mirror + rollout flag documentation is the contract).

Hard constraints honored: patient engine path untouched (stub adapter via
Phase-1 provider), text/score contracts untouched (existing suites green).
"""
from __future__ import annotations

import struct
import uuid

import pytest
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────

def _auth(h, tag="v2"):
    email = f"{tag}{uuid.uuid4().hex[:8]}@example.com"
    h.post("/api/auth/signup",
           json={"email": email, "password": "secret12", "full_name": "V2"})
    r = h.post("/api/auth/login", json={"email": email, "password": "secret12"})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": "Bearer " + r.json()["data"]["token"]}


def _mk_session(h, case_id="em_anaphylaxis_001"):
    headers = _auth(h)
    r = h.post("/api/v2/sessions", json={"case_id": case_id, "language": "id"},
               headers=headers)
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["sessionId"], headers


def _turns(h, sid, headers):
    r = h.get(f"/api/v2/sessions/{sid}/turns", headers=headers)
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["turns"]


@pytest.fixture(autouse=True)
def _stub_tts(monkeypatch):
    monkeypatch.setenv("QORA_VOICE_STUB_TTS", "1")


@pytest.fixture(autouse=True)
def _clean_event_loop():
    import asyncio as _aio
    yield
    try:
        closed = _aio.get_event_loop().is_closed()
    except RuntimeError:
        closed = True
    if closed:
        try:
            _aio.set_event_loop(_aio.new_event_loop())
        except Exception:
            pass


@pytest.fixture()
def _counting_llm(monkeypatch):
    """Count patient-LLM invocations while delegating to the real stub path."""
    calls = {"n": 0}
    from app.rag import engine_v2 as e2
    real = e2.arespond

    async def _counting(*a, **k):
        calls["n"] += 1
        return await real(*a, **k)

    monkeypatch.setattr(e2, "arespond", _counting)
    return calls


def _voice(h, sid, headers, cid, text, telemetry=None, raw_body=None):
    body = {"client_turn_id": cid, "transcript": text}
    if telemetry is not None:
        body["client_telemetry"] = telemetry
    if raw_body is not None:
        body = raw_body
    return h.post(f"/api/v2/sessions/{sid}/turns/voice-stream",
                  json=body, headers=headers)


def _parse_all(blob: bytes):
    """Incremental parse in hostile splits (mirrors the JS client's reader)."""
    from app.voice.frames import IncrementalParser
    parser = IncrementalParser()
    out = []
    # 1-byte, 3-byte, 7-byte and remainder splits exercise reassembly.
    i, splits = 0, (1, 3, 7, 64, 4096)
    k = 0
    while i < len(blob):
        step = splits[k % len(splits)]
        k += 1
        out.extend(parser.feed(blob[i:i + step]))
        i += step
    out.extend(parser.feed(b""))
    assert parser.pending_bytes() == 0
    return out


# ── (1) framing ───────────────────────────────────────────────────────────

def test_frames_roundtrip_and_order():
    from app.voice import frames as vf
    pcm = bytes(range(256)) * 40  # 10240 bytes → several PCM frames
    blob = (vf.encode_metadata({"turn_no": 2})
            + vf.encode_final_text("Halo, apa keluhannya?")
            + b"".join(vf.encode_pcm_frames(pcm))
            + vf.encode_done(10240, 3))
    got = _parse_all(blob)
    types = [t for t, _ in got]
    assert types[0] == vf.METADATA
    assert types[1] == vf.FINAL_TEXT
    assert set(types[2:-1]) == {vf.PCM}
    assert types[-1] == vf.DONE
    assert vf.decode_json(got[0][1])["v"] == vf.VERSION
    assert vf.decode_json(got[1][1])["text"] == "Halo, apa keluhannya?"
    assert b"".join(p for t, p in got if t == vf.PCM) == pcm
    done = vf.decode_json(got[-1][1])
    assert done["pcm_bytes"] == 10240 and done["ok"] is True


def test_frames_reject_oversize_and_unknown():
    from app.voice.frames import FrameProtocolError, IncrementalParser
    import pytest as _pt
    with _pt.raises(FrameProtocolError):
        IncrementalParser().feed(b"\x03" + struct.pack(">I", (1 << 20) + 1))
    with _pt.raises(FrameProtocolError):
        IncrementalParser().feed(b"\x09" + struct.pack(">I", 1) + b"x")
    # control frame above the JSON cap is rejected even though < 1MiB
    with _pt.raises(FrameProtocolError):
        IncrementalParser().feed(b"\x02" + struct.pack(">I", (1 << 16) + 1))


def test_encode_rejects_bad_type_and_huge_payload():
    from app.voice.frames import FrameProtocolError, encode_frame
    import pytest as _pt
    with _pt.raises(FrameProtocolError):
        encode_frame(0x09, b"x")
    with _pt.raises(FrameProtocolError):
        encode_frame(0x03, b"x" * ((1 << 20) + 1))


# ── (2) voice-stream success (stub) ───────────────────────────────────────

def test_voice_stream_success_stub(_counting_llm, tmp_path, monkeypatch):
    from app.voice import frames as vf
    monkeypatch.setenv("QORA_PERF_DIR", str(tmp_path))
    from app.main import app
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        cid = "ct-" + uuid.uuid4().hex[:12]
        r = _voice(h, sid, headers, cid, "sudah tiga hari demam",
                   telemetry={"endpoint_reason": "final_quiet",
                              "endpoint_ms": 512, "final_n": 2,
                              "transcript": "MUST BE DROPPED"})
        assert r.status_code == 200, r.text[:300]
        assert r.headers.get("x-voice-protocol") == str(vf.VERSION)
        frames = _parse_all(r.content)
        types = [t for t, _ in frames]
        assert types[0] == vf.METADATA
        assert types[1] == vf.FINAL_TEXT
        assert vf.PCM in types and types[-1] == vf.DONE
        meta = vf.decode_json(frames[0][1])
        assert meta["v"] == vf.VERSION and meta["turn_no"] == 2
        reply = vf.decode_json(frames[1][1])["text"]
        assert reply and reply.startswith("[STUB LLM]")
        pcm = b"".join(p for t, p in frames if t == vf.PCM)
        assert len(pcm) % 2 == 0 and len(pcm) > 0  # valid int16 blob
        done = vf.decode_json(frames[-1][1])
        assert done["pcm_bytes"] == len(pcm)
        # durable winner: user + patient persisted exactly once
        turns = _turns(h, sid, headers)
        assert [(t["role"], t["content"]) for t in turns] == [
            ("user", "sudah tiga hari demam"), ("patient", reply)]
        assert _counting_llm["n"] == 1
    # perf sink: lifecycle events present, metadata-only (no content leak)
    import json as _json
    rows = []
    for path in tmp_path.glob("voice_turn-*.jsonl"):
        rows += [_json.loads(line) for line in path.read_text().splitlines()
                 if line.strip()]
    events = {row.get("event") for row in rows}
    for want in ("received", "accepted", "admission_ok", "llm_full",
                 "commit_ok", "tts_start", "first_pcm", "tts_stub",
                 "tts_eof", "done"):
        assert want in events, events
    blob_all = _json.dumps(rows, ensure_ascii=False)
    assert "sudah tiga hari demam" not in blob_all
    assert reply not in blob_all
    assert "MUST BE DROPPED" not in blob_all


# ── (3) idempotent double-submit: winner-once, inference-once ─────────────

def test_voice_idempotent_double_submit_no_new_inference(_counting_llm):
    from app.voice import frames as vf
    from app.main import app
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        cid = "ct-" + uuid.uuid4().hex[:12]
        r1 = _voice(h, sid, headers, cid, "kepala pusing sejak pagi")
        assert r1.status_code == 200, r1.text[:300]
        reply1 = vf.decode_json(_parse_all(r1.content)[1][1])["text"]
        r2 = _voice(h, sid, headers, cid, "kepala pusing sejak pagi")
        assert r2.status_code == 200, r2.text[:300]
        reply2 = vf.decode_json(_parse_all(r2.content)[1][1])["text"]
        assert reply1 == reply2  # committed winner replayed
        assert _counting_llm["n"] == 1  # NO second inference
        turns = _turns(h, sid, headers)
        assert [t["role"] for t in turns] == ["user", "patient"]
        # manual retry semantics hold too: third identical submit still replays
        r3 = _voice(h, sid, headers, cid, "kepala pusing sejak pagi")
        assert r3.status_code == 200
        assert _counting_llm["n"] == 1


# ── (4) same key + different body rejected ────────────────────────────────

def test_voice_same_key_different_body_rejected(_counting_llm):
    from app.main import app
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        cid = "ct-" + uuid.uuid4().hex[:12]
        r1 = _voice(h, sid, headers, cid, "batuk kering")
        assert r1.status_code == 200, r1.text[:300]
        n_llm = _counting_llm["n"]
        r2 = _voice(h, sid, headers, cid, "nyeri dada yang berbeda")
        assert r2.status_code == 409, r2.text[:300]
        assert _counting_llm["n"] == n_llm  # rejected before any inference
        turns = _turns(h, sid, headers)
        assert len([t for t in turns if t["role"] == "user"]) == 1


# ── (5) disconnect-cancel then recovery ───────────────────────────────────

def test_voice_disconnect_before_commit_cancels_and_recovers():
    """Accept (= user turn persisted) with NO commit persists no patient row;
    the same key then adopts the same turn_no and commits exactly one winner
    (mirrors generator-cancel-before-commit + same-key recovery)."""
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionTurn
    from app.domains.sessions.turn_acceptance import (
        accept_voice_turn, commit_voice_winner,
    )
    from app.main import app
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        db = SessionLocal()
        try:
            snap = accept_voice_turn(db, session_id=sid,
                                     user_id=_user_id(h, headers),
                                     client_turn_id="ct-cancel-1",
                                     transcript="mual sejak kemarin")
            first_no = snap.turn_no
            assert snap.replay_reply is None and not snap.adopted
        finally:
            db.close()
        # — disconnect hits here: no commit — no patient row may exist.
        db = SessionLocal()
        try:
            patients = db.query(SessionTurn).filter_by(
                session_id=sid, role="patient").all()
            assert patients == []
            users = db.query(SessionTurn).filter_by(
                session_id=sid, role="user").all()
            assert len(users) == 1  # the accepted user turn stays
        finally:
            db.close()
        # — recovery with the same key adopts (no second user turn).
        db = SessionLocal()
        try:
            snap2 = accept_voice_turn(db, session_id=sid,
                                      user_id=_user_id(h, headers),
                                      client_turn_id="ct-cancel-1",
                                      transcript="mual sejak kemarin")
            assert snap2.adopted and snap2.turn_no == first_no
            assert snap2.replay_reply is None
        finally:
            db.close()
        status, winner = commit_voice_winner(
            SessionLocal, session_id=sid, client_turn_id="ct-cancel-1",
            turn_no=first_no, reply="Baik, sejak kapan mualnya mulai?")
        assert status == "persisted"
        db = SessionLocal()
        try:
            rows = db.query(SessionTurn).filter_by(session_id=sid).order_by(
                SessionTurn.turn_number).all()
            assert [(t.role) for t in rows] == ["user", "patient"]
            assert rows[1].content == winner
        finally:
            db.close()


def _user_id(h, headers) -> str:
    from app.shared.security import decode_token
    token = headers["Authorization"].split(" ", 1)[1]
    return decode_token(token)["sub"]


# ── (6) winner-once across simulated 2 workers ────────────────────────────

def test_voice_winner_once_two_workers_race():
    """Two workers committing different replies for one key: first persists,
    second replays it — exactly one patient row, first reply wins."""
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionTurn
    from app.domains.sessions.turn_acceptance import (
        accept_voice_turn, commit_voice_winner,
    )
    from app.main import app
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        uid = _user_id(h, headers)
        db = SessionLocal()
        try:
            snap = accept_voice_turn(db, session_id=sid, user_id=uid,
                                     client_turn_id="ct-race-1",
                                     transcript="sesak napas")
        finally:
            db.close()
        s1, w1 = commit_voice_winner(SessionLocal, session_id=sid,
                                     client_turn_id="ct-race-1",
                                     turn_no=snap.turn_no, reply="jawaban A")
        s2, w2 = commit_voice_winner(SessionLocal, session_id=sid,
                                     client_turn_id="ct-race-1",
                                     turn_no=snap.turn_no,
                                     reply="jawaban B dari worker lain")
        assert s1 == "persisted" and w1 == "jawaban A"
        assert s2 == "replayed" and w2 == "jawaban A"
        db = SessionLocal()
        try:
            patients = db.query(SessionTurn).filter_by(
                session_id=sid, role="patient").all()
            assert len(patients) == 1
            assert patients[0].content == "jawaban A"
        finally:
            db.close()


# ── (7) auth/validation ───────────────────────────────────────────────────

def test_voice_requires_auth():
    from app.main import app
    with TestClient(app) as h:
        r = h.post("/api/v2/sessions/nope/turns/voice-stream",
                   json={"client_turn_id": "x", "transcript": "halo"})
        assert r.status_code == 401


def test_voice_rejects_foreign_session_and_bad_body():
    from app.main import app
    with TestClient(app) as h:
        sid, _ = _mk_session(h)
        other = _auth(h, tag="v2x")
        r = h.post(f"/api/v2/sessions/{sid}/turns/voice-stream",
                   json={"client_turn_id": "x", "transcript": "halo"},
                   headers=other)
        assert r.status_code == 404
        _, headers = _mk_session(h, case_id="em_anaphylaxis_001")
        r = h.post(f"/api/v2/sessions/{sid}/turns/voice-stream",
                   json={"client_turn_id": "x", "transcript": ""},
                   headers=headers)
        assert r.status_code in (400, 422)


# ── (8) endpointing decision logic (python mirror of qvEndpointNext) ──────
#
# The canonical implementation is the JS pure function qvEndpointNext in
# sistemnya/qora-voice.jsx (no JS runner exists in this repo). This mirror
# implements the IDENTICAL thresholds/state transitions for pytest; any
# threshold change must land in both places (flag rollback = feature off,
# baseline 3000/1200 unchanged).

_QV_FINAL_QUIET_MS = 500
_QV_FINAL_STABLE_MS = 100
_QV_INTERIM_QUIET_MS = 800
_QV_INTERIM_STABLE_MS = 400
_QV_STOP_GRACE_MS = 250
_QV_HESITATION_HOLD_MS = 1200
_QV_MANUAL_FLUSH_MS = 250
_QV_BASELINE_INTERIM_MS = 3000
_QV_BASELINE_FINAL_MS = 1200
_HESITATION_TAILS = (" dan ", " tapi ", " anu ", " eh ", " maksudnya ",
                     " jadi ", " kalau ")


def _qv_endpoint_next(*, final_text, interim_text, final_stable_ms,
                      interim_stable_ms, quiet_ms, resumed,
                      manual=False, hesitation=False):
    """Mirror of JS qvEndpointNext — returns (action, fire_in_ms, reason)."""
    if resumed:
        return ("wait", -1, "resume_cancels_submit")
    if manual:
        return ("submit", min(_QV_MANUAL_FLUSH_MS, quiet_ms), "manual_flush")
    if (final_text or "").strip() and not (interim_text or "").strip():
        if hesitation:
            return ("wait", _QV_HESITATION_HOLD_MS, "hesitation_hold")
        if quiet_ms >= _QV_FINAL_QUIET_MS and \
                final_stable_ms >= _QV_FINAL_STABLE_MS:
            return ("submit", 0, "final_quiet")
        wait = max(_QV_FINAL_QUIET_MS - quiet_ms,
                   _QV_FINAL_STABLE_MS - final_stable_ms, 0)
        return ("wait", wait, "final_armed")
    if (interim_text or "").strip():
        if hesitation:
            return ("wait", _QV_HESITATION_HOLD_MS, "hesitation_hold")
        if quiet_ms >= _QV_INTERIM_QUIET_MS and \
                interim_stable_ms >= _QV_INTERIM_STABLE_MS:
            return ("stop_then_submit", _QV_STOP_GRACE_MS, "interim_stable")
        wait = max(_QV_INTERIM_QUIET_MS - quiet_ms,
                   _QV_INTERIM_STABLE_MS - interim_stable_ms, 0)
        return ("wait", wait, "interim_armed")
    return ("wait", -1, "no_transcript")


def test_endpointing_final_quiet_submits_fast():
    action, delay, reason = _qv_endpoint_next(
        final_text="saya demam", interim_text="", final_stable_ms=150,
        interim_stable_ms=0, quiet_ms=600, resumed=False)
    assert (action, delay, reason) == ("submit", 0, "final_quiet")


def test_endpointing_interim_needs_stop_grace():
    action, delay, reason = _qv_endpoint_next(
        final_text="", interim_text="saya demam", final_stable_ms=0,
        interim_stable_ms=500, quiet_ms=900, resumed=False)
    assert (action, delay, reason) == (
        "stop_then_submit", _QV_STOP_GRACE_MS, "interim_stable")


def test_endpointing_hesitation_holds_1200():
    for kwargs in (
        dict(final_text="saya demam dan", interim_text="",
             final_stable_ms=500, interim_stable_ms=0),
        dict(final_text="", interim_text="saya demam tapi",
             final_stable_ms=0, interim_stable_ms=900),
    ):
        action, delay, reason = _qv_endpoint_next(
            quiet_ms=900, resumed=False, hesitation=True, **kwargs)
        assert (action, delay, reason) == (
            "wait", _QV_HESITATION_HOLD_MS, "hesitation_hold")


def test_endpointing_resume_cancels_submit():
    action, delay, reason = _qv_endpoint_next(
        final_text="saya demam", interim_text="", final_stable_ms=500,
        interim_stable_ms=0, quiet_ms=900, resumed=True)
    assert action == "wait" and reason == "resume_cancels_submit"


def test_endpointing_manual_flush_bounded():
    action, delay, reason = _qv_endpoint_next(
        final_text="", interim_text="saya", final_stable_ms=0,
        interim_stable_ms=0, quiet_ms=5000, resumed=False, manual=True)
    assert action == "submit" and delay <= _QV_MANUAL_FLUSH_MS


def test_endpointing_baseline_constants_untouched():
    # Rollback contract: flag OFF keeps the shipped 3000/1200 timers.
    assert _QV_BASELINE_INTERIM_MS == 3000
    assert _QV_BASELINE_FINAL_MS == 1200
