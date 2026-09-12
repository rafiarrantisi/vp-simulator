"""Phase-1 voice foundation — backend seams (Run 1, zero paid calls).

Covers, with stub/fake transports only:
  (1) patient vs judge settings split (fallback identical, override scoped);
  (2) PatientLLMProvider seam (wire parity byte-for-byte + capability flags);
  (3) queryable JSONL sink (TurnClock/attempt events land, secrets dropped)
      + perf_summary CLI quantiles;
  (4) lifespan pre-warm (registry + patient provider) and separate
      patient/judge limiters;
  (5) retry map (guards frozen, SDK destack on patient client only,
      judge client untouched) + attempt timeline events;
  (6) TTS event-loop audit (measured: blocking stream stays off the loop).

Pre-existing failures elsewhere (stale goldens pinning the pre-migration
model/max_tokens) are NOT touched here; this module reads expected values
from settings so it tracks the frozen prod topology.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import struct
import time

import pytest
from fastapi.testclient import TestClient

from tests.test_refactor_phase0_baseline import (
    CANNED_TEXT, FakeAsyncOpenAI, FakeOpenAI,
)


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


@pytest.fixture(autouse=True)
def _clean_singletons():
    import app.rag.llm as llm_mod
    import app.rag.patient_provider as pp_mod
    import app.shared.admission as adm
    from app.config import get_settings
    llm_mod._client = None
    llm_mod._async_client = None
    pp_mod._provider = None
    pp_mod._provider_key = None
    adm._conv = None
    adm._patient = None
    adm._judge = None
    get_settings.cache_clear()
    yield
    llm_mod._client = None
    llm_mod._async_client = None
    pp_mod._provider = None
    pp_mod._provider_key = None
    adm._conv = None
    adm._patient = None
    adm._judge = None
    get_settings.cache_clear()


@pytest.fixture()
def _perf_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("QORA_PERF_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def _fake_sync_openai(monkeypatch):
    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    import app.rag.llm as llm_mod
    monkeypatch.setattr(llm_mod, "_client", None)
    from app.config import get_settings
    get_settings.cache_clear()
    FakeOpenAI.instances.clear()
    return FakeOpenAI


# ── (1) patient vs judge settings ─────────────────────────────────────────

def test_patient_settings_inherit_llm_by_default():
    from app.config import get_settings
    s = get_settings()
    assert s.patient_overrides() == {}
    assert s.patient_provider() == s.llm_provider
    assert s.patient_api_key() == s.llm_api_key
    assert s.patient_base_url() == s.llm_base_url
    assert s.patient_model() == s.llm_model


def test_patient_override_scoped_judge_untouched(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("PATIENT_LLM_MODEL", "future/model-x")
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", "https://example.invalid/v1")
    get_settings.cache_clear()
    s = get_settings()
    assert s.patient_model() == "future/model-x"
    assert s.patient_base_url() == "https://example.invalid/v1"
    assert s.patient_overrides() == {"base_url": True, "model": True}
    # Judge inputs unchanged by patient overrides.
    assert s.llm_model != "future/model-x"
    assert s.llm_judge_model != "future/model-x"


# ── (2) provider seam ─────────────────────────────────────────────────────

class _CapAsync(FakeAsyncOpenAI):
    """FakeAsyncOpenAI that also records constructor kwargs (SDK policy)."""
    ctor: list = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _CapAsync.ctor.append(kwargs)

    @property
    def base_url(self):
        import os as _os
        return _os.environ.get(
            "FAKE_BASE_URL", "https://opencode.ai/zen/go/v1")


def _frozen_env(monkeypatch):
    monkeypatch.setattr("openai.AsyncOpenAI", _CapAsync)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_BASE_URL", "https://opencode.ai/zen/go/v1")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("FAKE_BASE_URL", "https://opencode.ai/zen/go/v1")
    _CapAsync.ctor.clear()
    _CapAsync.instances.clear()
    from app.config import get_settings
    get_settings.cache_clear()


def _drain(agen):
    async def go():
        return [c async for c in agen]
    return asyncio.run(go())


def test_provider_wire_parity_with_legacy_client(monkeypatch):
    import app.rag.llm as llm_mod
    from app.rag.patient_provider import (
        ENDPOINT_KIND_CHAT_COMPLETIONS, OpenCodeChatCompletionsProvider,
    )
    _frozen_env(monkeypatch)
    legacy = llm_mod._openai_async_compatible(
        "https://opencode.ai/zen/go/v1")
    provider = OpenCodeChatCompletionsProvider()
    assert provider.capabilities.endpoint_kind == ENDPOINT_KIND_CHAT_COMPLETIONS
    assert provider.capabilities.supports_streaming is True
    assert provider.capabilities.lane_header == "x-opencode-session"
    assert provider.describe()["model"] == "deepseek-v4-flash"

    msgs = [{"role": "user", "content": "halo?"}]
    _drain(legacy.astream("sys", msgs, max_tokens=350, fast=True,
                          session_id="s1"))
    _drain(provider.astream("sys", msgs, max_tokens=350, fast=True,
                            session_id="s1"))
    legacy_kw = _CapAsync.instances[0].chat.completions.calls[-1]
    patient_kw = _CapAsync.instances[1].chat.completions.calls[-1]
    assert patient_kw == legacy_kw  # byte-for-byte wire parity
    assert patient_kw["model"] == "deepseek-v4-flash"
    assert patient_kw["temperature"] == 0.5
    assert patient_kw["max_tokens"] == 350
    assert patient_kw["stream"] is True
    assert patient_kw["extra_body"] == {"thinking": {"type": "disabled"}}
    assert patient_kw["extra_headers"] == {"x-opencode-session": "qora-s1"}

    asyncio.run(legacy.agenerate("sys", msgs, max_tokens=350, fast=True,
                                 session_id="s1"))
    asyncio.run(provider.agenerate("sys", msgs, max_tokens=350, fast=True,
                                   session_id="s1"))
    assert (_CapAsync.instances[1].chat.completions.calls[-1]
            == _CapAsync.instances[0].chat.completions.calls[-1])


def test_sdk_retries_off_on_patient_only(monkeypatch):
    import app.rag.llm as llm_mod
    from app.rag.patient_provider import OpenCodeChatCompletionsProvider
    _frozen_env(monkeypatch)
    llm_mod._openai_async_compatible("https://opencode.ai/zen/go/v1")
    OpenCodeChatCompletionsProvider()
    assert "max_retries" not in _CapAsync.ctor[0], \
        "shared/judge client must keep the SDK default (untouched)"
    assert _CapAsync.ctor[1].get("max_retries") == 0, \
        "patient client must disable SDK auto-retries (ADR §4.3)"


def test_provider_singleton_and_stub_default():
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import (
        ENDPOINT_KIND_STUB, get_patient_provider,
    )
    # conftest blanks LLM_API_KEY → stub behind the same seam, no network.
    p = get_patient_provider()
    assert p.capabilities.endpoint_kind == ENDPOINT_KIND_STUB
    assert get_patient_provider() is p
    assert pp_mod._provider is p


def test_fingerprint_and_describe_hold_no_secrets(monkeypatch):
    from app.config import get_settings
    from app.rag.patient_provider import (
        get_patient_provider, patient_config_fingerprint,
    )
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-test")
    get_settings.cache_clear()
    fp = patient_config_fingerprint()
    desc = get_patient_provider().describe()
    blob = fp + json.dumps(desc)
    assert "sk-super-secret-test" not in blob
    assert fp  # stable non-empty topology hash


# ── (3) sink + CLI ────────────────────────────────────────────────────────

def test_turnclock_sink_and_logger(_perf_tmp):
    import logging
    from app.shared.perf_marks import TurnClock
    from app.shared.perf_sink import iter_records
    c = TurnClock(route="v2_turn_stream", schema="legacy")
    c.mark("request_received")
    c.mark("llm_request_start")
    c.mark("llm_first_token")
    c.mark("request_complete")
    c.finish("complete")
    summary = c.log_summary()
    rows = iter_records("turn_perf", directory=_perf_tmp)
    assert len(rows) == 1
    row = rows[0]
    assert row["route"] == "v2_turn_stream"
    assert row["outcome"] == "complete"
    assert row["marks_ms"]["llm_first_token"] >= 0
    assert summary["marks_ms"].keys() <= row["marks_ms"].keys()


def test_sink_drops_secrets_and_unknown_keys(_perf_tmp):
    from app.shared.perf_sink import append_record, iter_records
    clean = append_record({
        "kind": "turn_perf", "route": "r",
        "api_key": "sk-SECRET", "prompt": "gejala...",
        "transcript": "saya demam", "mystery": 1,
    })
    assert "api_key" not in clean and "prompt" not in clean
    assert "transcript" not in clean and "mystery" not in clean
    rows = iter_records("turn_perf", directory=_perf_tmp)
    assert rows and "api_key" not in rows[0]


def test_cli_quantiles_nearest_rank(_perf_tmp, capsys):
    from scripts.perf_summary import main
    # n=10, ttft 100..1000 → nearest-rank p50=500, p90=900, p95=1000.
    day = "20990101"
    with open(_perf_tmp / f"turn_perf-{day}.jsonl", "w") as f:
        for i in range(1, 11):
            f.write(json.dumps({
                "kind": "turn_perf", "route": "v2_turn_stream",
                "outcome": "complete",
                "marks_ms": {"request_received": 0.0,
                             "request_complete": float(i * 100),
                             "llm_first_token": float(i * 100)},
            }) + "\n")
    rc = main(["--perf-dir", str(_perf_tmp), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    g = payload["by_route_turns"]["v2_turn_stream"]
    assert g["n"] == 10
    assert g["ttft_ms"] == {"p50": 500.0, "p90": 900.0, "p95": 1000.0}
    assert g["turn_total_ms"]["p95"] == 1000.0


# ── (4) lifespan + limiters ───────────────────────────────────────────────

def test_patient_judge_limiters_are_separate():
    from app.shared import admission
    from app.shared.admission import (
        judge_limiter, limits_snapshot, patient_limiter,
    )
    assert patient_limiter() is not judge_limiter()
    assert admission._patient is not admission._judge
    snap = limits_snapshot()
    assert snap["patient"] == 64 and snap["judge"] == 1


def test_lifespan_prewarms_registry_and_patient():
    from app.domains.sessions.progress_adapter import _registry_cache
    import app.rag.patient_provider as pp_mod
    from app.main import app
    _registry_cache.clear()
    pp_mod._provider = None
    with TestClient(app):
        assert _registry_cache.get("reg") is not None, \
            "cached_registry must be warm before readiness"
        assert pp_mod._provider is not None, \
            "patient provider must exist after lifespan startup"


# ── (5) retry map: frozen guards, destack, timeline ───────────────────────

def test_patient_guards_frozen():
    import app.rag.llm as llm_mod
    assert llm_mod._PATIENT_FIRST_TOKEN_S == 7.0
    assert llm_mod._PATIENT_TOTAL_S == 20.0


class _Scripted:
    """Duck-typed patient transport: scripted per-attempt behavior."""

    def __init__(self, modes):
        self.modes = list(modes)
        self.calls = 0
        self.lanes = []

    def describe(self):
        return {"model": "deepseek-v4-flash",
                "endpoint_kind": "chat_completions"}

    async def astream(self, system, messages, model=None, max_tokens=None,
                      fast=True, session_id=None):
        self.calls += 1
        self.lanes.append(session_id)
        mode = self.modes[min(self.calls - 1, len(self.modes) - 1)]
        if mode == "stall":
            raise TimeoutError("upstream stall")
        if mode == "empty":
            return
        yield "halo "
        yield "dunia "


def test_astream_patient_retry_then_success(_perf_tmp):
    import app.rag.llm as llm_mod
    from app.shared.perf_sink import iter_records
    client = _Scripted(["stall", "ok"])

    async def go():
        return [c async for c in llm_mod.astream_patient(
            client, "sys", [{"role": "user", "content": "hi"}],
            max_tokens=350, session_id="sess-abc-123",
            first_token_timeout=5.0, total_timeout=10.0,
            route="v2_turn_stream", logical_turn_id="sess-abc-123:t1")]
    out = asyncio.run(go())
    assert "".join(out) == "halo dunia "
    assert client.calls == 2  # exactly ONE fresh-lane retry
    assert client.lanes == ["sess-abc-123", "sess-abc-123-r0"]
    events = [r["event"] for r in
              iter_records("patient_attempt", directory=_perf_tmp)]
    assert events == ["attempt_started", "retry_started",
                      "attempt_started", "first_content", "full_completion"]
    rows = iter_records("patient_attempt", directory=_perf_tmp)
    full = [r for r in rows if r["event"] == "full_completion"][0]
    assert full["route"] == "v2_turn_stream"
    assert full["output_chars"] == len("halo dunia ")
    assert full["ttft_ms"] >= 0 and full["total_ms"] >= 0
    assert full["lane_hash"] and len(full["lane_hash"]) == 16
    assert "sess-abc-123" not in json.dumps(rows)  # opaque refs only
    import hashlib as _hl
    opaque = _hl.sha256(b"sess-abc-123:t1").hexdigest()[:16]
    assert {r["logical_turn_id"] for r in rows} == {opaque}


def test_astream_patient_empty_stream_retries(_perf_tmp):
    import app.rag.llm as llm_mod
    client = _Scripted(["empty", "ok"])

    async def go():
        return [c async for c in llm_mod.astream_patient(
            client, "sys", [{"role": "user", "content": "hi"}],
            max_tokens=350, session_id="s", first_token_timeout=5.0,
            total_timeout=10.0)]
    out = asyncio.run(go())
    assert "".join(out) == "halo dunia "
    assert client.calls == 2


def test_astream_patient_gives_up_after_two_attempts(_perf_tmp):
    import app.rag.llm as llm_mod
    from app.shared.perf_sink import iter_records
    client = _Scripted(["stall", "stall"])
    t0 = time.monotonic()

    async def go():
        return [c async for c in llm_mod.astream_patient(
            client, "sys", [{"role": "user", "content": "hi"}],
            max_tokens=350, session_id="s", first_token_timeout=0.05,
            total_timeout=0.2)]
    with pytest.raises(TimeoutError):
        asyncio.run(go())
    assert time.monotonic() - t0 < 5
    assert client.calls == 2
    events = [r["event"] for r in
              iter_records("patient_attempt", directory=_perf_tmp)]
    assert events.count("attempt_started") == 2
    assert events.count("retry_started") == 1
    assert "full_completion" not in events


def test_judge_outbound_untouched_by_patient_scope(monkeypatch,
                                                   _fake_sync_openai):
    from app.config import get_settings
    from app.domains.cases.v2_catalog import load_v2_case
    from app.rag import judge_v2
    monkeypatch.setenv("PATIENT_LLM_MODEL", "future/model-x")
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", "https://example.invalid/v1")
    get_settings.cache_clear()
    case = load_v2_case("em_anaphylaxis_001")
    judge_v2.evaluate_v2(case, [], mode="practice")
    kwargs = _fake_sync_openai.instances[-1].chat.completions.calls[-1]
    s = get_settings()
    assert kwargs["model"] == s.llm_judge_model
    assert kwargs["temperature"] == 0.1
    assert kwargs["max_tokens"] == s.llm_judge_max_tokens
    assert "future/model-x" not in json.dumps(kwargs)


# ── (6) TTS event-loop audit (measured) ───────────────────────────────────

def test_tts_stream_off_event_loop(monkeypatch):
    """Blocking gRPC iteration must never run on the event loop.

    Framework fact asserted: tts_stream is a sync `def` and _tts_frames is a
    sync generator → Starlette executes both in a worker thread. Measured
    below: consuming ~0.3s of blocking chunks via a worker thread (the
    Starlette model) keeps loop tick gaps <50ms, while the blocking cost is
    real (inline control ≥0.25s).
    """
    import app.voice.tts as tts_mod
    from app.domains.ai.router import _tts_frames, tts_stream
    assert not inspect.iscoroutinefunction(tts_stream)
    assert not inspect.isasyncgenfunction(_tts_frames)

    def fake_stream_pcm(text, *, voice=None, style=None, language=None):
        for _ in range(5):
            time.sleep(0.06)  # blocking gRPC-style wait
            yield b"\x00\x01" * 120

    monkeypatch.setattr(tts_mod, "stream_pcm", fake_stream_pcm)

    async def go():
        gaps = []
        tick = []

        async def ticker():
            last = time.monotonic()
            for _ in range(200):
                await asyncio.sleep(0.005)
                now = time.monotonic()
                gaps.append(now - last)
                last = now
            tick.append(True)

        task = asyncio.create_task(ticker())
        frames = await asyncio.to_thread(
            lambda: list(_tts_frames("halo", "Gacrux", None, "id-ID",
                                     "sess123456789")))
        await task
        return frames, max(gaps)

    frames, max_gap = asyncio.run(go())
    assert frames and frames[-1] == struct.pack(">I", 0)
    assert len(frames) == 6  # 5 PCM frames + EOF terminator
    assert max_gap < 0.05, f"event loop stalled {max_gap * 1000:.0f}ms"

    t0 = time.monotonic()
    list(_tts_frames("halo", "Gacrux", None, "id-ID", "sess123456789"))
    assert time.monotonic() - t0 >= 0.25  # blocking cost is real
