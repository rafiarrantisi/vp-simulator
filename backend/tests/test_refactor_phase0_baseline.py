"""Phase 0 — deterministic LLM replay harness + golden outbound contracts.

Brief §5.1d/h: record V2/V3 outbound LLM requests (messages, role order,
model, params, reasoning guards, token handling) WITHOUT paid calls, and
prove stream replay equivalence. The fake transport replaces
`openai.OpenAI` before the adapter builds its client, so the REAL adapter
code (kwarg construction, guards, retry, chunk iteration) is exercised.

Golden files live in tests/fixtures/perf_phase0/. Written on first run,
asserted afterwards. No secrets, no transcript PII beyond repo fixtures.
"""
from __future__ import annotations

import hashlib
import json
import os

import pytest

FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "perf_phase0")

CANNED_TEXT = "Baik, coba ceritakan sejak kapan demamnya mulai?"


class _FakeDelta:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, text=None, delta=None):
        if text is not None:
            self.message = type("M", (), {"content": text})()
        if delta is not None:
            self.delta = _FakeDelta(delta)


class _FakeCompletion:
    def __init__(self, text):
        self.choices = [_FakeChoice(text=text)]


class _FakeStreamChunk:
    def __init__(self, delta):
        self.choices = [_FakeChoice(delta=delta)]


class FakeCompletions:
    """Mimics openai resources.chat.completions (create only)."""

    def __init__(self, script):
        self.script = script
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        mode = self.script["mode"]
        if mode == "ok":
            return _FakeCompletion(self.script["text"])
        if mode == "stream":
            words = self.script["text"].split(" ")
            return iter([_FakeStreamChunk(w + " ") for w in words])
        if mode == "empty":
            return _FakeCompletion(self.script.get("text", "...."))
        raise AssertionError("unknown script mode")


class FakeChat:
    def __init__(self, script):
        self.completions = FakeCompletions(script)


class FakeOpenAI:
    instances: list = []
    default_script: dict = {"mode": "ok", "text": CANNED_TEXT}

    def __init__(self, script=None, **kwargs):
        self.script = script or dict(FakeOpenAI.default_script)
        self.chat = FakeChat(self.script)
        FakeOpenAI.instances.append(self)

    @property
    def base_url(self):
        return "https://openrouter.ai/api/v1"


@pytest.fixture(autouse=True)
def _clean_llm_singletons():
    """LLM settings/client singletons leak across tests (lru_cache + module
    globals). Reset before/after so stub isolation from conftest holds."""
    import app.rag.llm as llm_mod
    from app.config import get_settings

    llm_mod._client = None
    llm_mod._async_client = None
    get_settings.cache_clear()
    yield
    llm_mod._client = None
    llm_mod._async_client = None
    get_settings.cache_clear()



@pytest.fixture()
def fake_openai(monkeypatch):
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


def _golden(name: str, payload: dict) -> dict:
    os.makedirs(FIX_DIR, exist_ok=True)
    path = os.path.join(FIX_DIR, name)
    blob = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(blob + "\n")
    with open(path) as f:
        assert f.read() == blob + "\n", f"golden {name} diverged"
    return payload


def _summarize_request(kwargs: dict) -> dict:
    msgs = kwargs.get("messages") or []
    return {
        "model": kwargs.get("model"),
        "temperature": kwargs.get("temperature"),
        "max_tokens": kwargs.get("max_tokens"),
        "timeout": kwargs.get("timeout", None),
        "extra_body": kwargs.get("extra_body"),
        "stream": kwargs.get("stream", False),
        "roles": [m.get("role") for m in msgs],
        "system_sha256": hashlib.sha256(
            (msgs[0].get("content") or "").encode()).hexdigest() if msgs else None,
        "system_chars": len(msgs[0].get("content") or "") if msgs else 0,
        "n_messages": len(msgs),
    }


def test_v2_outbound_request_shape(fake_openai):
    from app.rag import engine_v2

    out = engine_v2.respond(
        "em_anaphylaxis_001", [], "kenapa datang ke dokter?", language="id")
    assert out and not out.startswith("[STUB")
    kwargs = FakeOpenAI.instances[-1].chat.completions.calls[-1]
    summary = _summarize_request(kwargs)
    assert summary["roles"][0] == "system"
    assert summary["roles"][-1] == "user"
    assert summary["model"] == "deepseek/deepseek-v4-flash"
    assert summary["temperature"] == 0.5
    assert summary["max_tokens"] == 1024
    assert summary["extra_body"] == {"reasoning": {"enabled": False}}
    _golden("v2_outbound.json", summary)


def test_v3_outbound_request_shape(fake_openai):
    from pipeline.case_v3.loader import default_registry
    from app.rag import engine_v3

    reg = default_registry()
    v = reg.variants["dengue_001_mild"]
    out = engine_v3.respond(v, [], "kenapa demam?", language="id")
    assert out and not out.startswith("[STUB")
    kwargs = FakeOpenAI.instances[-1].chat.completions.calls[-1]
    summary = _summarize_request(kwargs)
    assert summary["roles"][0] == "system"
    assert summary["roles"][-1] == "user"
    assert summary["extra_body"] == {"reasoning": {"enabled": False}}
    assert summary["max_tokens"] == 1024
    _golden("v3_outbound.json", summary)


def test_stream_replay_equivalence(fake_openai, monkeypatch):
    from app.rag import engine_v2

    monkeypatch.setattr(FakeOpenAI, "default_script",
                        {"mode": "stream", "text": CANNED_TEXT})
    FakeOpenAI.instances.clear()
    chunks = list(engine_v2.stream_respond(
        "em_anaphylaxis_001", [], "kenapa datang ke dokter?", language="id"))
    assert chunks, "stream must yield at least one chunk"
    streamed = "".join(chunks)
    assert streamed.strip() == CANNED_TEXT
    kwargs = FakeOpenAI.instances[-1].chat.completions.calls[-1]
    assert kwargs.get("stream") is True
    _golden("v2_stream.json", {
        "n_chunks": len(chunks),
        "joined_sha256": hashlib.sha256(streamed.encode()).hexdigest(),
        "stream_flag": True,
    })


def test_empty_content_guard_raises_without_sleep(fake_openai, monkeypatch):
    import app.rag.llm as llm_mod

    monkeypatch.setattr(FakeOpenAI, "default_script",
                        {"mode": "empty", "text": "...."})
    monkeypatch.setattr(llm_mod, "_client", None)
    client = llm_mod.get_llm_client()
    with pytest.raises(RuntimeError, match="konten kosong"):
        client.generate("sys", [{"role": "user", "content": "hi"}],
                        max_tokens=16, max_retries=1)


def test_reasoning_guard_never_falls_back_to_cot(fake_openai):
    from app.rag import engine_v2

    out = engine_v2.respond(
        "em_anaphylaxis_001", [], "apa diagnosis saya?", language="id")
    # canned transport returns plain content; adapter must surface it as-is
    assert out.strip() == CANNED_TEXT


def test_yield_dependency_teardown_after_stream_body():
    """Framework fact (FastAPI/Starlette installed): does a yield dependency
    close before or after a StreamingResponse body is consumed? Decides
    whether the request Session holds its pool connection during LLM wait."""
    from fastapi import Depends, FastAPI
    from fastapi.responses import StreamingResponse
    from fastapi.testclient import TestClient

    events: list[str] = []

    def dep():
        events.append("setup")
        yield "db"
        events.append("teardown")

    async def gen():
        events.append("first_chunk")
        yield b"x"
        events.append("second_chunk")
        yield b"y"

    app = FastAPI()

    @app.get("/s", dependencies=[])
    def route(db=Depends(dep)):
        assert db == "db"
        return StreamingResponse(gen(), media_type="text/plain")

    with TestClient(app) as client:
        r = client.get("/s")
        assert r.content == b"xy"
    assert events[0] == "setup", events
    _golden("dependency_lifecycle.json", {
        "order": events,
        "teardown_after_body": events[-1] == "teardown",
        "fastapi": __import__("fastapi").__version__,
        "starlette": __import__("starlette").__version__,
    })
    assert events[-1] == "teardown", events


class _FakeAsyncStream:
    def __init__(self, words):
        self._words = words
        self.aclosed = False

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for w in self._words:
            yield _FakeStreamChunk(w + " ")

    async def aclose(self):
        self.aclosed = True


class FakeAsyncCompletions:
    def __init__(self):
        self.calls: list[dict] = []
        self.streams: list = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            st = _FakeAsyncStream(FakeAsyncOpenAI.default_text.split(" "))
            self.streams.append(st)
            return st
        return _FakeCompletion(FakeAsyncOpenAI.default_text)


class FakeAsyncChat:
    def __init__(self):
        self.completions = FakeAsyncCompletions()


class FakeAsyncOpenAI:
    instances: list = []
    default_text: str = CANNED_TEXT

    def __init__(self, **kwargs):
        self.chat = FakeAsyncChat()
        FakeAsyncOpenAI.instances.append(self)

    @property
    def base_url(self):
        return "https://openrouter.ai/api/v1"

    async def close(self):
        pass


def test_async_outbound_matches_sync_golden(monkeypatch):
    """Async adapter builds byte-identical wire kwargs (shared builder)."""
    import asyncio

    import app.rag.llm as llm_mod
    from app.rag import engine_v2

    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(llm_mod, "_async_client", None)
    from app.config import get_settings

    get_settings.cache_clear()
    FakeAsyncOpenAI.instances.clear()

    async def go():
        return await engine_v2.arespond(
            "em_anaphylaxis_001", [], "kenapa datang ke dokter?", language="id")

    out = asyncio.run(go())
    assert out.strip() == CANNED_TEXT
    kwargs = FakeAsyncOpenAI.instances[-1].chat.completions.calls[-1]
    assert kwargs["model"] == "deepseek/deepseek-v4-flash"
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_tokens"] == 1024
    assert kwargs["extra_body"] == {"reasoning": {"enabled": False}}
    assert [m["role"] for m in kwargs["messages"]][0] == "system"
    with open("tests/fixtures/perf_phase0/v2_outbound.json") as f:
        golden = json.load(f)
    assert kwargs["model"] == golden["model"]
    assert kwargs["temperature"] == golden["temperature"]
    assert kwargs["max_tokens"] == golden["max_tokens"]
    assert kwargs["extra_body"] == golden["extra_body"]


def test_async_stream_replay_and_cleanup(monkeypatch):
    import asyncio

    import app.rag.llm as llm_mod
    from app.rag import engine_v2

    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(llm_mod, "_async_client", None)
    from app.config import get_settings

    get_settings.cache_clear()
    FakeAsyncOpenAI.instances.clear()

    async def go():
        return [c async for c in engine_v2.astream_respond(
            "em_anaphylaxis_001", [], "kenapa datang ke dokter?", language="id")]

    chunks = asyncio.run(go())
    assert "".join(chunks).strip() == CANNED_TEXT
    st = FakeAsyncOpenAI.instances[-1].chat.completions.streams[-1]
    assert st.aclosed is True, "upstream stream must be closed after consume"
