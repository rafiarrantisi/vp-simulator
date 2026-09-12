"""Phase-3 honest old-vs-new voice benchmark (SAME provider, SMALL sample).

Old flow = POST turns/stream (collect full text) + POST /api/ai/tts/stream
  (2 round trips, frontend-coordinated).
New flow = POST turns/voice-stream (1 round trip, server-orchestrated,
  Phase-1 adapter, guards unchanged, flag qora.voice.adaptive default OFF).

Provider is FROZEN: OpenCode zen deepseek-v4-flash throughout, NO migration.
Guards/timeouts/temperature/max_tokens unchanged (asserted at startup).

Modes (one-command re-runnable — see Usage):
  transport : STUBBED inference over localhost ephemeral-port HTTP (free).
              N=10 old (2-RTT) vs N=10 new (1-RTT). Measures submit->first-byte
              and total. Test users only, rows deleted afterwards, cleanup
              proof in output + JSONL.
  segments  : Real-provider segments IN-PROCESS (paid, capped). Same 10 short
              Indonesian inputs + frozen case/em_anaphylaxis_001/lang=id.
              Old orchestration (adapter stream + collect + stream_pcm on the
              ACTUAL reply) vs new orchestration (voice-stream service path:
              same adapter with route=voice_stream + accept/commit fence +
              same stream_pcm). Per turn: endpointing-constant, LLM TTFT,
              LLM full, transition gap (full-ready -> TTS-start, THE
              eliminated-RTT metric in-process), TTS TTFA, TTS full.
              Timings + lengths ONLY, never content/keys.
              HARD CAP: max 12 logical turns per flow (this run uses 10).
              Requires --allow-paid (explicit opt-in, no accidental billing).
  analyze   : Summarize existing JSONL under backend/data/voice_bench/
              (p50/p90 nearest-rank; n=10 INSUFFICIENT for p95 — never emits
              p95).
  all       : transport + (segments only if --allow-paid, else skipped).

Usage (re-runnable via one command, from repo root):
  backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode transport
  backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode segments --allow-paid
  backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode all --allow-paid
  backend/.venv/bin/python backend/scripts/voice_bench_phase3.py --mode analyze

Results: backend/data/voice_bench/phase3_*.jsonl (timings/lengths only).
Privacy: no transcript/reply bytes, prompts, keys, audio, or raw session
  identity in code output/logs/results. Opaque hashes only.
Forbidden: no provider/model/endpoint/timeout/guard changes, no new infra,
  no prod restart/deploy, no files outside repo except /tmp, no leftover rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO_ROOT / "backend" / "data" / "voice_bench"

# Frozen benchmark contract (small-sample precedent: N=10).
CASE_ID = "em_anaphylaxis_001"
LANGUAGE = "id"
N_TURNS = 10
MAX_PAID_TURNS_PER_FLOW = 12
# 10 short Indonesian anamnesis openers (synthetic, generic — no PII, no keys).
# Frozen for this phase; lengths only are recorded in results.
INPUTS = [
    "Sudah tiga hari demam naik turun.",
    "Kepala pusing sejak pagi tadi.",
    "Batuk kering sudah seminggu.",
    "Mual sejak kemarin sore.",
    "Nyeri perut bagian kanan bawah.",
    "Sesak napas saat naik tangga.",
    "Tenggorokan sakit saat menelan.",
    "Diare tiga kali sejak semalam.",
    "Nyeri dada saat batuk.",
    "Badan lemas dan nafsu makan turun.",
]
ENDPOINTING_APPLIED = "baseline_1200_3000_flagOFF"
BASELINE_INTERIM_MS = 3000
BASELINE_FINAL_MS = 1200

# Frozen provider topology (asserted, never changed here).
EXPECT_BASE_SUBSTR = "opencode.ai"
EXPECT_MODEL = "deepseek-v4-flash"
EXPECT_TEMP = 0.5
EXPECT_MAX_TOKENS = 350
EXPECT_TTFT_S = 7.0
EXPECT_TOTAL_S = 20.0


def _opaque(value: str) -> str:
    try:
        return hashlib.sha256(str(value or "").encode()).hexdigest()[:16]
    except Exception:
        return ""


def nearest_rank(sorted_vals: list[float], pct: float):
    try:
        if not sorted_vals:
            return None
        n = len(sorted_vals)
        p = min(100.0, max(0.0, float(pct))) / 100.0
        rank = max(1, int(math.ceil(p * n)))
        return float(sorted_vals[rank - 1])
    except Exception:
        return None


def summarize(vals: list[float]) -> dict:
    s = sorted(float(v) for v in vals if v is not None)
    if not s:
        return {"n": 0, "p50": None, "p90": None}
    return {
        "n": len(s),
        "p50": nearest_rank(s, 50),
        "p90": nearest_rank(s, 90),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _bench_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_backend_env() -> None:
    """Load backend/.env for CWD-independent runs (repo-root safe).

    pydantic-settings resolves env_file=".env" relative to CWD, so running
    from repo root would otherwise fall back to defaults (openrouter) instead
    of the frozen backend/.env (opencode zen). This loader mirrors .env into
    os.environ via setdefault (explicit env always wins, e.g. the stub
    server's LLM_API_KEY="" override). Values are never logged.
    """
    try:
        env_path = REPO_ROOT / "backend" / ".env"
        if not env_path.is_file():
            return
        with open(env_path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def assert_frozen_topology() -> dict:
    """Verify SAME-provider + frozen guards without logging secrets."""
    _load_backend_env()
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.config import get_settings

    try:
        get_settings.cache_clear()
    except Exception:
        pass
    s = get_settings()
    base = str(s.patient_base_url() or "")
    model = str(s.patient_model() or "")
    assert EXPECT_BASE_SUBSTR in base, f"provider drift: base={base[:40]}"
    assert model == EXPECT_MODEL, f"model drift: {model!r}"
    assert int(s.llm_persona_max_tokens) == EXPECT_MAX_TOKENS, "max_tokens drift"
    import app.rag.llm as llm_mod
    import app.rag.patient_provider as pp_mod

    assert float(llm_mod._PATIENT_FIRST_TOKEN_S) == EXPECT_TTFT_S, "TTFT guard drift"
    assert float(llm_mod._PATIENT_TOTAL_S) == EXPECT_TOTAL_S, "total guard drift"
    assert float(pp_mod.PATIENT_TEMPERATURE) == EXPECT_TEMP, "temperature drift"
    assert int(pp_mod.PATIENT_SDK_RETRIES) == 0, "sdk-retries drift"
    assert s.patient_overrides() == {}, "patient overrides must be empty (inherit)"
    # Flag default OFF: baseline timers are the shipped behavior.
    assert BASELINE_INTERIM_MS == 3000 and BASELINE_FINAL_MS == 1200
    try:
        fp = pp_mod.patient_config_fingerprint()
    except Exception:
        fp = ""
    return {
        "base_host": "opencode.ai/zen",
        "model": model,
        "max_tokens": EXPECT_MAX_TOKENS,
        "temperature": EXPECT_TEMP,
        "ttft_guard_s": EXPECT_TTFT_S,
        "total_guard_s": EXPECT_TOTAL_S,
        "endpointing": ENDPOINTING_APPLIED,
        "config_fingerprint": str(fp or "")[:16],
    }


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        sk.bind(("127.0.0.1", 0))
        return int(sk.getsockname()[1])


_STUB_SERVER_WRAPPER = r'''
import sys
sys.path.insert(0, "BACKEND_DIR")
# Deterministic stub TTS for BOTH old (/tts/stream) and new (voice-stream)
# transports: free, fast, no network, no billing. Audio bytes are synthetic;
# only transport/accept overhead is compared here (never audio quality).
import math as _math
import struct as _struct
def _stub_pcm(seconds=0.2, freq=440.0, sr=24000):
    n = max(1, int(seconds * sr))
    out = bytearray(n * 2)
    for i in range(n):
        v = int(8000.0 * _math.sin(2.0 * _math.pi * freq * i / sr))
        _struct.pack_into("<h", out, i * 2, v)
    return bytes(out)
_STUB = _stub_pcm()
def _fake_stream_pcm(text, *, voice=None, style=None, language=None):
    # Yield in small chunks to exercise progressive framing.
    step = 4096
    for i in range(0, len(_STUB), step):
        yield _STUB[i:i+step]
import app.voice.tts as _tts
_tts.stream_pcm = _fake_stream_pcm
import uvicorn
uvicorn.run("app.main:app", host="127.0.0.1", port=PORT_INT,
            workers=1, log_level="warning")
'''


def run_transport(n: int = N_TURNS) -> dict:
    """Stubbed localhost HTTP transport benchmark (free, N=10 each)."""
    import httpx

    assert n <= MAX_PAID_TURNS_PER_FLOW, "transport N exceeds cap"
    topo = assert_frozen_topology()
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _bench_stamp()
    out_path = BENCH_DIR / f"phase3_transport_{stamp}.jsonl"

    port = _free_port()
    db_path = f"/tmp/qora_voice_bench_transport_{os.getpid()}_{uuid.uuid4().hex[:8]}.db"
    perf_dir = f"/tmp/qora_voice_bench_perf_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    os.makedirs(perf_dir, exist_ok=True)
    wrapper_src = (
        _STUB_SERVER_WRAPPER.replace("BACKEND_DIR", str(REPO_ROOT / "backend"))
        .replace("PORT_INT", str(port))
    )
    wrapper_path = f"/tmp/qora_voice_bench_srv_{os.getpid()}_{uuid.uuid4().hex[:8]}.py"
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(wrapper_src)

    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["ENV"] = "test"
    env["LLM_API_KEY"] = ""  # force AsyncStubLlmClient (no network, no billing)
    env["PATIENT_LLM_API_KEY"] = ""
    env["QORA_VOICE_STUB_TTS"] = "1"
    env["QORA_PERF_DIR"] = perf_dir
    # Isolated bench server only (never prod): disable per-IP rate limiting so
    # N=10 old (20 ai calls) + N=10 new (10 ai calls) + 2 session creates from
    # one localhost IP do not 429. Documented; prod limiter untouched.
    env["RATE_LIMIT_ENABLED"] = "false"
    env["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/nonexistent-adc-bench.json"
    env.pop("QORA_ALLOW_LIVE_DB", None)
    env.pop("QORA_LIVE_TURNS", None)
    env.pop("RUN_LLM_QA", None)

    proc = subprocess.Popen(
        [sys.executable, wrapper_path],
        cwd=str(REPO_ROOT / "backend"),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    cleanup: dict = {
        "mode": "transport",
        "at": _now_iso(),
        "provider": "stub (no paid calls)",
        "endpointing": ENDPOINTING_APPLIED,
        "topology": topo,
        "n_per_flow": n,
    }
    rows: list[dict] = []
    created: dict = {"users": [], "sessions": []}
    try:
        # Wait for readiness (poll openapi, localhost only).
        ready = False
        for _ in range(100):
            try:
                r = httpx.get(f"{base}/openapi.json", timeout=2.0)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.3)
        if not ready:
            raise RuntimeError("stub server did not become ready on ephemeral port")

        client = httpx.Client(base_url=base, timeout=30.0)

        def signup() -> dict:
            tag = uuid.uuid4().hex[:10]
            email = f"bench-transport-{tag}@example.com"
            r = client.post(
                "/api/auth/signup",
                json={"email": email, "password": "secret12",
                      "full_name": "Bench"},
            )
            assert r.status_code == 200, r.text[:200]
            r = client.post(
                "/api/auth/login",
                json={"email": email, "password": "secret12"},
            )
            assert r.status_code == 200, r.text[:200]
            token = r.json()["data"]["token"]
            headers = {"Authorization": "Bearer " + token}
            created["users"].append(email)
            return headers

        def mk_session(headers: dict) -> str:
            r = client.post(
                "/api/v2/sessions",
                json={"case_id": CASE_ID, "language": LANGUAGE},
                headers=headers,
            )
            assert r.status_code == 200, r.text[:300]
            sid = r.json()["data"]["sessionId"]
            created["sessions"].append(sid)
            return sid

        h_old = signup()
        h_new = signup()
        sid_old = mk_session(h_old)
        sid_new = mk_session(h_new)
        sid_old_ref = _opaque(sid_old)
        sid_new_ref = _opaque(sid_new)

        # Warmup (unmeasured, one per flow) so the first MEASURED turn does not
        # pay registry/connection cold start. Warmup rows are in the same
        # isolated sessions and are deleted by the same cleanup below.
        try:
            with client.stream(
                "POST", f"/api/v2/sessions/{sid_old}/turns/stream",
                json={"text": "pemanasan transport", "input_type": "voice"},
                headers=h_old,
            ) as _w:
                assert _w.status_code == 200
                _wtxt = b"".join(list(_w.iter_bytes(chunk_size=4096))).decode(
                    "utf-8", errors="ignore").strip()
            if _wtxt:
                with client.stream(
                    "POST", "/api/ai/tts/stream",
                    json={"text": _wtxt[:500], "session_id": sid_old},
                    headers=h_old,
                ) as _w2:
                    for _ in _w2.iter_bytes(chunk_size=4096):
                        pass
        except Exception:
            pass
        try:
            with client.stream(
                "POST", f"/api/v2/sessions/{sid_new}/turns/voice-stream",
                json={"client_turn_id": "ct-warm-" + uuid.uuid4().hex[:12],
                      "transcript": "pemanasan transport"},
                headers=h_new,
            ) as _w3:
                for _ in _w3.iter_bytes(chunk_size=4096):
                    pass
        except Exception:
            pass

        # OLD: 2-RTT frontend-coordinated (turns/stream + tts/stream).
        for i, text_in in enumerate(INPUTS[:n]):
            t0 = time.monotonic()
            llm_first = None
            parts: list[str] = []
            with client.stream(
                "POST", f"/api/v2/sessions/{sid_old}/turns/stream",
                json={"text": text_in, "input_type": "voice"},
                headers=h_old,
            ) as resp:
                assert resp.status_code == 200, resp.read().decode()[:300]
                t_first_byte_llm = None
                for chunk in resp.iter_bytes(chunk_size=1024):
                    if not chunk:
                        continue
                    now = time.monotonic()
                    if t_first_byte_llm is None:
                        t_first_byte_llm = now
                    if llm_first is None:
                        llm_first = now
                    try:
                        parts.append(chunk.decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
                t_llm_done = time.monotonic()
            full_text = "".join(parts).strip()
            assert full_text, "stub LLM returned empty (transport)"
            # Second round trip (frontend-coordinated TTS).
            t_tts_submit = time.monotonic()
            tts_first = None
            tts_bytes = 0
            with client.stream(
                "POST", "/api/ai/tts/stream",
                json={"text": full_text, "session_id": sid_old},
                headers=h_old,
            ) as resp2:
                assert resp2.status_code == 200, resp2.read().decode()[:300]
                for chunk in resp2.iter_bytes(chunk_size=1024):
                    if not chunk:
                        continue
                    now = time.monotonic()
                    if tts_first is None:
                        tts_first = now
                    tts_bytes += len(chunk)
                t_tts_done = time.monotonic()
            rows.append({
                "kind": "transport_turn",
                "flow": "old_2rtt",
                "turn_index": i,
                "session_ref": sid_old_ref,
                "input_chars": len(text_in),
                "llm_reply_chars": len(full_text),
                "submit_to_first_llm_byte_ms": round((t_first_byte_llm - t0) * 1000.0, 2) if t_first_byte_llm else None,
                "llm_full_ms": round((t_llm_done - t0) * 1000.0, 2),
                "client_handoff_gap_ms": round((t_tts_submit - t_llm_done) * 1000.0, 2),
                "submit_to_first_audio_ms": round((tts_first - t0) * 1000.0, 2) if tts_first else None,
                "total_ms": round((t_tts_done - t0) * 1000.0, 2),
                "tts_bytes": int(tts_bytes),
                "endpointing": ENDPOINTING_APPLIED,
            })

        # NEW: 1-RTT server-orchestrated (voice-stream).
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from app.voice.frames import FINAL_TEXT, METADATA, PCM, DONE, ERROR, IncrementalParser, decode_json

        for i, text_in in enumerate(INPUTS[:n]):
            cid = "ct-bench-" + uuid.uuid4().hex[:16]
            t0 = time.monotonic()
            t_first_byte = None
            t_first_pcm = None
            t_final_text = None
            meta_chars = 0
            reply_chars = 0
            pcm_bytes = 0
            outcome = "unknown"
            with client.stream(
                "POST", f"/api/v2/sessions/{sid_new}/turns/voice-stream",
                json={"client_turn_id": cid, "transcript": text_in},
                headers=h_new,
            ) as resp:
                assert resp.status_code == 200, resp.read().decode()[:300]
                parser = IncrementalParser()
                for chunk in resp.iter_bytes(chunk_size=1024):
                    if not chunk:
                        continue
                    now = time.monotonic()
                    if t_first_byte is None:
                        t_first_byte = now
                    for ftype, payload in parser.feed(chunk):
                        now2 = time.monotonic()
                        if ftype == METADATA:
                            try:
                                meta_chars = int(decode_json(payload).get("reply_chars", 0) or 0)
                            except Exception:
                                pass
                        elif ftype == FINAL_TEXT:
                            t_final_text = now2
                            try:
                                reply_chars = len(str(decode_json(payload).get("text", "") or ""))
                            except Exception:
                                pass
                        elif ftype == PCM:
                            if t_first_pcm is None:
                                t_first_pcm = now2
                            pcm_bytes += len(payload)
                        elif ftype == DONE:
                            outcome = "done"
                        elif ftype == ERROR:
                            outcome = "error"
                t_done = time.monotonic()
            rows.append({
                "kind": "transport_turn",
                "flow": "new_1rtt",
                "turn_index": i,
                "session_ref": sid_new_ref,
                "input_chars": len(text_in),
                "llm_reply_chars": int(reply_chars or meta_chars or 0),
                "submit_to_first_byte_ms": round((t_first_byte - t0) * 1000.0, 2) if t_first_byte else None,
                "submit_to_first_pcm_ms": round((t_first_pcm - t0) * 1000.0, 2) if t_first_pcm else None,
                "submit_to_final_text_ms": round((t_final_text - t0) * 1000.0, 2) if t_final_text else None,
                "total_ms": round((t_done - t0) * 1000.0, 2),
                "pcm_bytes": int(pcm_bytes),
                "outcome": outcome,
                "endpointing": ENDPOINTING_APPLIED,
            })

        # Persist rows (timings/lengths only — already sanitized above).
        with open(out_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False,
                                   separators=(",", ":")) + "\n")

        # Cleanup: DELETE created rows from the ISOLATED stub DB (never prod),
        # then verify zero remain. Proof recorded in JSONL-adjacent summary.
        proof: dict = {"rows_before": {}, "rows_after": {}, "db_file_removed": False}
        try:
            import sqlite3

            # Query before delete (isolated file only).
            con = sqlite3.connect(db_path)
            try:
                def _count(table: str) -> int:
                    try:
                        cur = con.execute(f"SELECT COUNT(*) FROM {table}")
                        return int(cur.fetchone()[0])
                    except Exception:
                        return -1
                proof["rows_before"] = {
                    "sessions": _count("sessions"),
                    "session_turns": _count("session_turns"),
                    "voice_turn_ledger": _count("voice_turn_ledger"),
                }
                sids = list(created["sessions"])
                if sids:
                    q = ",".join("?" for _ in sids)
                    try:
                        con.execute(
                            f"DELETE FROM session_turns WHERE session_id IN ({q})", sids)
                    except Exception:
                        pass
                    try:
                        con.execute(
                            f"DELETE FROM voice_turn_ledger WHERE session_id IN ({q})", sids)
                    except Exception:
                        pass
                    try:
                        con.execute(
                            f"DELETE FROM sessions WHERE id IN ({q})", sids)
                    except Exception:
                        pass
                    # Test users by email pattern.
                    try:
                        con.execute(
                            "DELETE FROM users WHERE email LIKE 'bench-transport-%'")
                    except Exception:
                        pass
                    try:
                        con.execute(
                            "DELETE FROM profiles WHERE user_id NOT IN (SELECT id FROM users)")
                    except Exception:
                        pass
                    con.commit()
                proof["rows_after"] = {
                    "sessions": _count("sessions"),
                    "session_turns": _count("session_turns"),
                    "voice_turn_ledger": _count("voice_turn_ledger"),
                }
            finally:
                con.close()
        except Exception as e:
            proof["cleanup_error"] = str(type(e).__name__)[:80]

        cleanup.update({
            "results": str(out_path),
            "rows_written": len(rows),
            "cleanup_proof": proof,
            "db_path": "(isolated /tmp file, removed below)",
            "prod_rows_touched": 0,
        })
    finally:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
        except Exception:
            pass
        for p in (wrapper_path, db_path):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        try:
            import shutil
            shutil.rmtree(perf_dir, ignore_errors=True)
        except Exception:
            pass
        # Mark file removal in proof when possible.
        try:
            cleanup.setdefault("cleanup_proof", {})["db_file_removed"] = not os.path.exists(db_path)
        except Exception:
            pass
    return cleanup


def run_segments(n: int = N_TURNS) -> dict:
    """Real-provider in-process segments (paid, capped at 12/flow)."""
    if n > MAX_PAID_TURNS_PER_FLOW:
        raise RuntimeError(f"paid-call cap: requested {n} > {MAX_PAID_TURNS_PER_FLOW}")
    topo = assert_frozen_topology()
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _bench_stamp()

    # Isolated DB file (never prod). Set BEFORE app.database engine import
    # takes effect: clear settings cache so DATABASE_URL override wins.
    db_path = f"/tmp/qora_voice_bench_seg_{os.getpid()}_{uuid.uuid4().hex[:8]}.db"
    perf_dir = f"/tmp/qora_voice_bench_segperf_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    os.makedirs(perf_dir, exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ENV"] = "test"
    os.environ["QORA_PERF_DIR"] = perf_dir
    os.environ.pop("QORA_ALLOW_LIVE_DB", None)
    # Real LLM key comes from backend/.env via Settings (not blanked here).
    # ADC for real TTS: use the runtime credential file when present.
    adc = "/home/ubuntu/.secrets/google/qora-tts-runtime.json"
    if os.path.exists(adc) and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = adc

    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.config import get_settings

    try:
        get_settings.cache_clear()
    except Exception:
        pass
    s = get_settings()
    if not str(s.patient_api_key() or ""):
        raise RuntimeError("real LLM key missing (backend/.env) — segments need paid provider")
    # Re-assert after env switch (same provider, still frozen).
    topo = assert_frozen_topology()

    import asyncio

    from app.database import SessionLocal, engine, init_db

    init_db()

    from fastapi.testclient import TestClient

    from app.main import app

    paid: dict = {"old_llm": 0, "old_tts": 0, "new_llm": 0, "new_tts": 0,
                  "old_failures": 0, "new_failures": 0}
    old_rows: list[dict] = []
    new_rows: list[dict] = []
    created: dict = {"users": [], "sessions": []}

    with TestClient(app) as h:
        def signup(tag: str):
            email = f"bench-seg-{tag}-{uuid.uuid4().hex[:8]}@example.com"
            r = h.post("/api/auth/signup",
                       json={"email": email, "password": "secret12",
                             "full_name": "Bench"})
            assert r.status_code == 200, r.text[:200]
            r = h.post("/api/auth/login",
                       json={"email": email, "password": "secret12"})
            assert r.status_code == 200, r.text[:200]
            headers = {"Authorization": "Bearer " + r.json()["data"]["token"]}
            created["users"].append(email)
            return headers

        h_old = signup("old")
        h_new = signup("new")

        def mk_session(headers: dict) -> str:
            r = h.post("/api/v2/sessions",
                       json={"case_id": CASE_ID, "language": LANGUAGE},
                       headers=headers)
            assert r.status_code == 200, r.text[:300]
            sid = r.json()["data"]["sessionId"]
            created["sessions"].append(sid)
            return sid

        sid_old = mk_session(h_old)
        sid_new = mk_session(h_new)
        sid_old_ref = _opaque(sid_old)
        sid_new_ref = _opaque(sid_new)

        from app.domains.sessions.turn_acceptance import (
            accept_turn,
            accept_voice_turn,
            commit_voice_winner,
            finalize_patient_turn,
        )
        from app.rag import engine_v2

        async def _old_turn(idx: int, text_in: str):
            from app.database import SessionLocal as _SL

            db = _SL()
            try:
                # Resolve user id from the session row (test user only).
                from app.domains.sessions.models import SessionRow

                row = db.get(SessionRow, sid_old)
                assert row is not None
                uid = row.user_id
                snap = accept_turn(db, session_id=sid_old, user_id=uid,
                                   text=text_in, input_type="voice")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            history = [dict(x) for x in (snap.history or ())]
            paid["old_llm"] += 1
            if paid["old_llm"] > MAX_PAID_TURNS_PER_FLOW:
                raise RuntimeError("paid-call cap exceeded (old LLM)")
            t0 = time.monotonic()
            t_first = None
            parts: list[str] = []
            try:
                async for ch in engine_v2.astream_respond(
                        snap.case_id or CASE_ID, history, text_in,
                        language=snap.language or LANGUAGE,
                        session_id=sid_old, route="v2_turn_stream",
                        logical_turn_id=f"{sid_old}:seg-old-{idx}"):
                    now = time.monotonic()
                    if t_first is None:
                        t_first = now
                    parts.append(ch)
            except Exception as e:
                paid["old_failures"] += 1
                old_rows.append({
                    "kind": "segment_turn", "flow": "old",
                    "turn_index": idx, "session_ref": sid_old_ref,
                    "input_chars": len(text_in), "status": "llm_failed",
                    "error": type(e).__name__[:40],
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            t_full = time.monotonic()
            reply = "".join(parts).strip()
            if not reply:
                paid["old_failures"] += 1
                old_rows.append({
                    "kind": "segment_turn", "flow": "old",
                    "turn_index": idx, "session_ref": sid_old_ref,
                    "input_chars": len(text_in), "status": "llm_empty",
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            # Persist (outside timed LLM/TTS spans).
            try:
                def _record(db2):
                    from app.domains.billing import service as billing

                    tokens_in = (sum(len(x.get("content", "")) for x in history) + len(text_in)) // 4
                    billing.record_session_cost(db2, sid_old, uid, tokens_in, len(reply) // 4)
                finalize_patient_turn(
                    _SL, session_id=sid_old, turn_no=snap.turn_no + 1,
                    reply=reply, user_id=uid, record_cost=_record)
            except Exception:
                pass
            # TTS on the ACTUAL reply (paid, only for this reply).
            from app.voice.tts import stream_pcm

            t_tts_start = time.monotonic()
            gap = (t_tts_start - t_full) * 1000.0
            paid["old_tts"] += 1
            if paid["old_tts"] > MAX_PAID_TURNS_PER_FLOW:
                raise RuntimeError("paid-call cap exceeded (old TTS)")
            try:
                import anyio as _anyio

                def _tts_timed():
                    # One billed synthesis; timing inside the worker thread so
                    # first-chunk (TTFA) and total are both true RPC timings
                    # without a second call.
                    _s = time.monotonic()
                    _first = None
                    _bytes = 0
                    _n = 0
                    for c in stream_pcm(reply, voice=None, style=None,
                                        language="id-ID"):
                        if not c:
                            continue
                        _now = time.monotonic()
                        if _first is None:
                            _first = _now
                        _bytes += len(c)
                        _n += 1
                    _e = time.monotonic()
                    return (_bytes, _n,
                            ((_first - _s) * 1000.0 if _first else None),
                            ((_e - _s) * 1000.0))

                pcm_bytes, _pcm_n, _ttfa, _tfull = await _anyio.to_thread.run_sync(_tts_timed)
                t_tts_first_ms = _ttfa
                t_tts_full_ms = _tfull
            except Exception as e:
                paid["old_failures"] += 1
                old_rows.append({
                    "kind": "segment_turn", "flow": "old",
                    "turn_index": idx, "session_ref": sid_old_ref,
                    "input_chars": len(text_in),
                    "output_chars": len(reply),
                    "llm_ttft_ms": round((t_first - t0) * 1000.0, 1) if t_first else None,
                    "llm_full_ms": round((t_full - t0) * 1000.0, 1),
                    "status": "tts_failed",
                    "error": type(e).__name__[:40],
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            old_rows.append({
                "kind": "segment_turn", "flow": "old",
                "turn_index": idx, "session_ref": sid_old_ref,
                "input_chars": len(text_in),
                "output_chars": len(reply),
                "pcm_bytes": int(pcm_bytes),
                "llm_ttft_ms": round((t_first - t0) * 1000.0, 1) if t_first else None,
                "llm_full_ms": round((t_full - t0) * 1000.0, 1),
                "transition_gap_ms": round(gap, 1),
                "tts_ttfa_ms": round(t_tts_first_ms, 1) if t_tts_first_ms is not None else None,
                "tts_full_ms": round(t_tts_full_ms, 1) if t_tts_full_ms is not None else None,
                "status": "ok",
                "endpointing": ENDPOINTING_APPLIED,
            })

        async def _new_turn(idx: int, text_in: str):
            from app.database import SessionLocal as _SL

            from app.domains.sessions.models import SessionRow

            db = _SL()
            try:
                row = db.get(SessionRow, sid_new)
                assert row is not None
                uid = row.user_id
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            cid = f"ct-seg-new-{idx}-" + uuid.uuid4().hex[:12]
            db2 = _SL()
            try:
                snap = accept_voice_turn(db2, session_id=sid_new, user_id=uid,
                                         client_turn_id=cid,
                                         transcript=text_in)
            finally:
                try:
                    db2.close()
                except Exception:
                    pass
            if snap.replay_reply is not None:
                new_rows.append({
                    "kind": "segment_turn", "flow": "new",
                    "turn_index": idx, "session_ref": sid_new_ref,
                    "input_chars": len(text_in), "status": "unexpected_replay",
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            history = [dict(x) for x in (snap.history or ())]
            paid["new_llm"] += 1
            if paid["new_llm"] > MAX_PAID_TURNS_PER_FLOW:
                raise RuntimeError("paid-call cap exceeded (new LLM)")
            t0 = time.monotonic()
            t_first = None
            parts: list[str] = []
            try:
                # Voice-stream service path: same Phase-1 adapter/guards as
                # run_voice_llm (arespond), with route=voice_stream so the
                # attempt timeline labels the new flow. run_voice_llm itself
                # buffers via arespond (hiding TTFT); timing the identical
                # streaming primitive preserves the TTFT segment honestly
                # without a second billed call.
                async for ch in engine_v2.astream_respond(
                        snap.case_id or CASE_ID, history, text_in,
                        language=snap.language or LANGUAGE,
                        session_id=sid_new, route="voice_stream",
                        logical_turn_id=f"{sid_new}:{cid}"):
                    now = time.monotonic()
                    if t_first is None:
                        t_first = now
                    parts.append(ch)
            except Exception as e:
                paid["new_failures"] += 1
                new_rows.append({
                    "kind": "segment_turn", "flow": "new",
                    "turn_index": idx, "session_ref": sid_new_ref,
                    "input_chars": len(text_in), "status": "llm_failed",
                    "error": type(e).__name__[:40],
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            t_full = time.monotonic()
            reply = "".join(parts).strip()
            if not reply:
                paid["new_failures"] += 1
                new_rows.append({
                    "kind": "segment_turn", "flow": "new",
                    "turn_index": idx, "session_ref": sid_new_ref,
                    "input_chars": len(text_in), "status": "llm_empty",
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            try:
                def _record(dbx):
                    from app.domains.billing import service as billing

                    tokens_in = (sum(len(x.get("content", "")) for x in history) + len(text_in)) // 4
                    billing.record_session_cost(dbx, sid_new, uid, tokens_in, len(reply) // 4)
                commit_voice_winner(
                    _SL, session_id=sid_new, client_turn_id=cid,
                    turn_no=snap.turn_no, reply=reply, record_cost=_record)
            except Exception as e:
                paid["new_failures"] += 1
                new_rows.append({
                    "kind": "segment_turn", "flow": "new",
                    "turn_index": idx, "session_ref": sid_new_ref,
                    "input_chars": len(text_in),
                    "output_chars": len(reply),
                    "status": "commit_failed",
                    "error": type(e).__name__[:40],
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            from app.voice.tts import stream_pcm

            t_tts_start = time.monotonic()
            gap = (t_tts_start - t_full) * 1000.0
            paid["new_tts"] += 1
            if paid["new_tts"] > MAX_PAID_TURNS_PER_FLOW:
                raise RuntimeError("paid-call cap exceeded (new TTS)")
            try:
                import anyio as _anyio

                def _tts_timed2():
                    _s = time.monotonic()
                    _first = None
                    _bytes = 0
                    _n = 0
                    for c in stream_pcm(reply, voice=None, style=None,
                                        language="id-ID"):
                        if not c:
                            continue
                        _now = time.monotonic()
                        if _first is None:
                            _first = _now
                        _bytes += len(c)
                        _n += 1
                    _e = time.monotonic()
                    return (_bytes, _n,
                            ((_first - _s) * 1000.0 if _first else None),
                            ((_e - _s) * 1000.0))

                pcm_bytes, _pcm_n2, _ttfa2, _tfull2 = await _anyio.to_thread.run_sync(_tts_timed2)
            except Exception as e:
                paid["new_failures"] += 1
                new_rows.append({
                    "kind": "segment_turn", "flow": "new",
                    "turn_index": idx, "session_ref": sid_new_ref,
                    "input_chars": len(text_in),
                    "output_chars": len(reply),
                    "llm_ttft_ms": round((t_first - t0) * 1000.0, 1) if t_first else None,
                    "llm_full_ms": round((t_full - t0) * 1000.0, 1),
                    "status": "tts_failed",
                    "error": type(e).__name__[:40],
                    "endpointing": ENDPOINTING_APPLIED,
                })
                return
            new_rows.append({
                "kind": "segment_turn", "flow": "new",
                "turn_index": idx, "session_ref": sid_new_ref,
                "input_chars": len(text_in),
                "output_chars": len(reply),
                "pcm_bytes": int(pcm_bytes),
                "llm_ttft_ms": round((t_first - t0) * 1000.0, 1) if t_first else None,
                "llm_full_ms": round((t_full - t0) * 1000.0, 1),
                "transition_gap_ms": round(gap, 1),
                "tts_ttfa_ms": round(_ttfa2, 1) if _ttfa2 is not None else None,
                "tts_full_ms": round(_tfull2, 1) if _tfull2 is not None else None,
                "status": "ok",
                "endpointing": ENDPOINTING_APPLIED,
            })

        async def _run_all():
            for i, text_in in enumerate(INPUTS[:n]):
                await _old_turn(i, text_in)
            for i, text_in in enumerate(INPUTS[:n]):
                await _new_turn(i, text_in)

        asyncio.run(_run_all())

    # Persist (timings/lengths only).
    old_path = BENCH_DIR / f"phase3_segments_old_{stamp}.jsonl"
    new_path = BENCH_DIR / f"phase3_segments_new_{stamp}.jsonl"
    with open(old_path, "w", encoding="utf-8") as f:
        for row in old_rows:
            f.write(json.dumps(row, ensure_ascii=False,
                               separators=(",", ":")) + "\n")
    with open(new_path, "w", encoding="utf-8") as f:
        for row in new_rows:
            f.write(json.dumps(row, ensure_ascii=False,
                               separators=(",", ":")) + "\n")

    # Cleanup isolated DB (never prod): delete test rows, verify zero.
    proof: dict = {}
    try:
        import sqlite3

        con = sqlite3.connect(db_path)
        try:
            def _count(t: str) -> int:
                try:
                    return int(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                except Exception:
                    return -1
            proof["rows_before"] = {
                "sessions": _count("sessions"),
                "session_turns": _count("session_turns"),
                "voice_turn_ledger": _count("voice_turn_ledger"),
            }
            sids = list(created["sessions"])
            if sids:
                q = ",".join("?" for _ in sids)
                for stmt in (
                    f"DELETE FROM session_turns WHERE session_id IN ({q})",
                    f"DELETE FROM voice_turn_ledger WHERE session_id IN ({q})",
                    f"DELETE FROM sessions WHERE id IN ({q})",
                ):
                    try:
                        con.execute(stmt, sids)
                    except Exception:
                        pass
                try:
                    con.execute("DELETE FROM users WHERE email LIKE 'bench-seg-%'")
                except Exception:
                    pass
                con.commit()
            proof["rows_after"] = {
                "sessions": _count("sessions"),
                "session_turns": _count("session_turns"),
                "voice_turn_ledger": _count("voice_turn_ledger"),
            }
        finally:
            con.close()
    except Exception as e:
        proof["cleanup_error"] = str(type(e).__name__)[:80]
    try:
        engine.dispose()
    except Exception:
        pass
    for p in (db_path,):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    try:
        import shutil
        shutil.rmtree(perf_dir, ignore_errors=True)
    except Exception:
        pass
    try:
        proof["db_file_removed"] = not os.path.exists(db_path)
    except Exception:
        pass

    return {
        "mode": "segments",
        "at": _now_iso(),
        "provider": "real OpenCode zen deepseek-v4-flash (paid, capped)",
        "topology": topo,
        "case_id": CASE_ID,
        "language": LANGUAGE,
        "n_per_flow": n,
        "paid_calls": dict(paid),
        "results_old": str(old_path),
        "results_new": str(new_path),
        "rows_written": {"old": len(old_rows), "new": len(new_rows)},
        "cleanup_proof": proof,
        "prod_rows_touched": 0,
        "tts_note": ("One billed stream_pcm per reply; TTFA = first yielded "
                     "PCM chunk inside the worker thread, full = synthesis "
                     "end. No second call."),
    }


def analyze(bench_dir: Path | None = None) -> dict:
    base = Path(bench_dir) if bench_dir else BENCH_DIR
    files = sorted(base.glob("phase3_*.jsonl"))
    per_flow: dict[str, list[dict]] = {}
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    flow = str(obj.get("flow") or "unknown")
                    per_flow.setdefault(flow, []).append(obj)
        except Exception:
            continue
    summary: dict = {"at": _now_iso(), "files": [str(p) for p in files],
                     "note": "n=10 INSUFFICIENT for p95 — p50/p90 only, no p95 claims."}
    for flow, rows in sorted(per_flow.items()):
        keys = ("llm_ttft_ms", "llm_full_ms", "transition_gap_ms",
                "tts_ttfa_ms", "tts_full_ms", "total_ms",
                "submit_to_first_audio_ms", "submit_to_first_byte_ms",
                "submit_to_first_pcm_ms")
        out: dict = {"n": len(rows)}
        for k in keys:
            vals = [r[k] for r in rows
                    if isinstance(r.get(k), (int, float))]
            if vals:
                out[k] = summarize(vals)
        summary[flow] = out
    print(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True))
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase-3 old-vs-new voice benchmark")
    ap.add_argument("--mode", default="transport",
                    choices=["transport", "segments", "analyze", "all"])
    ap.add_argument("--allow-paid", action="store_true",
                    help="Explicit opt-in for real-LLM/TTS billed calls (segments).")
    ap.add_argument("--n", type=int, default=N_TURNS)
    args = ap.parse_args(argv)
    n = max(1, min(int(args.n or N_TURNS), MAX_PAID_TURNS_PER_FLOW))
    if args.mode in ("segments", "all") and args.mode == "segments" and not args.allow_paid:
        print("REFUSED: segments need --allow-paid (paid-call guard). "
              "Run --mode transport (free) or add --allow-paid.", file=sys.stderr)
        return 2
    if args.mode == "transport":
        out = run_transport(n=n)
        print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    if args.mode == "segments":
        out = run_segments(n=n)
        print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    if args.mode == "analyze":
        analyze()
        return 0
    # all
    out_t = run_transport(n=n)
    print(json.dumps(out_t, ensure_ascii=False, indent=1, sort_keys=True))
    if args.allow_paid:
        out_s = run_segments(n=n)
        print(json.dumps(out_s, ensure_ascii=False, indent=1, sort_keys=True))
    else:
        print("SKIPPED segments (needs --allow-paid). Transport only.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
