"""Phase-2 OpenRouter patient runtime — adapter + selection + judge pinning.

Zero paid calls: stub/fake transports only (dummy keys, FakeAsyncOpenAI).

Covers:
  (1) adapter param-contract: EXACT evaluated wire params (base
      https://openrouter.ai/api/v1, model deepseek/deepseek-v4-flash-0731,
      temperature 0.5, max_tokens 350, stream, reasoning.enabled=False; NO
      x-opencode-session lane header anywhere, NO thinking-disabled param;
      same meaningful-content guard semantics as the OpenCode path);
  (2) selection logic: pure-config matrix (unset / partial / unknown) —
      base_url containing openrouter.ai → OpenRouter adapter, opencode.ai →
      existing adapter, unknown (+key) → fail closed with clear 501, never
      silent wrong-model; no-key → stub regardless (no network);
  (3) judge pinning: judge sync+async client construction ignores PATIENT_*
      vars entirely (LLM_* only).

Rollback = unset PATIENT_LLM_* (unset PATIENT_LLM_BASE_URL
PATIENT_LLM_API_KEY PATIENT_LLM_MODEL PATIENT_LLM_EXTRA).
"""
from __future__ import annotations

import asyncio
import json

import pytest

EVAL_BASE = "https://openrouter.ai/api/v1"
EVAL_MODEL = "deepseek/deepseek-v4-flash-0731"
OPENCODE_BASE = "https://opencode.ai/zen/go/v1"
OPENCODE_MODEL = "deepseek-v4-flash"
CANNED = "Baik, coba ceritakan sejak kapan demamnya mulai?"


@pytest.fixture(autouse=True)
def _clean_singletons():
    import app.rag.llm as llm_mod
    import app.rag.patient_provider as pp_mod
    from app.config import get_settings
    llm_mod._client = None
    llm_mod._async_client = None
    pp_mod._provider = None
    pp_mod._provider_key = None
    get_settings.cache_clear()
    yield
    llm_mod._client = None
    llm_mod._async_client = None
    pp_mod._provider = None
    pp_mod._provider_key = None
    get_settings.cache_clear()


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


# ── fakes (record wire, no network) ──────────────────────────────────────

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
    def __init__(self, text):
        self.calls: list[dict] = []
        self.streams: list = []
        self._text = text

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            st = _FakeAsyncStream(self._text.split(" "))
            self.streams.append(st)
            return st
        return _FakeCompletion(self._text)


class FakeAsyncChat:
    def __init__(self, text):
        self.completions = FakeAsyncCompletions(text)


class FakeAsyncOpenAI:
    """Mimics openai.AsyncOpenAI ctor + chat.completions.create."""
    instances: list = []
    text: str = CANNED

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.chat = FakeAsyncChat(type(self).text)
        FakeAsyncOpenAI.instances.append(self)

    @property
    def base_url(self):
        return self.kwargs.get("base_url", "")

    async def close(self):
        pass


def _patch_async(monkeypatch, text=CANNED):
    FakeAsyncOpenAI.instances.clear()
    FakeAsyncOpenAI.text = text
    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)
    return FakeAsyncOpenAI


def _drain(agen):
    async def go():
        return [c async for c in agen]
    return asyncio.run(go())


def _openrouter_env(monkeypatch):
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", EVAL_BASE)
    monkeypatch.setenv("PATIENT_LLM_API_KEY", "sk-test-patient-dummy")
    monkeypatch.setenv("PATIENT_LLM_MODEL", EVAL_MODEL)
    # Judge stays on the frozen OpenCode topology regardless.
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", "sk-test-judge-dummy")
    monkeypatch.setenv("LLM_BASE_URL", OPENCODE_BASE)
    monkeypatch.setenv("LLM_MODEL", OPENCODE_MODEL)
    monkeypatch.setenv("LLM_JUDGE_MODEL", OPENCODE_MODEL)
    from app.config import get_settings
    get_settings.cache_clear()


# ── (1) param contract ───────────────────────────────────────────────────

def test_openrouter_param_contract_exact(monkeypatch):
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import (
        ENDPOINT_KIND_CHAT_COMPLETIONS, OpenRouterChatCompletionsProvider,
        PATIENT_SDK_RETRIES, PATIENT_TEMPERATURE,
    )
    _patch_async(monkeypatch)
    _openrouter_env(monkeypatch)

    p = OpenRouterChatCompletionsProvider()
    assert isinstance(p, OpenRouterChatCompletionsProvider)
    assert p.capabilities.endpoint_kind == ENDPOINT_KIND_CHAT_COMPLETIONS
    assert p.capabilities.supports_streaming is True
    assert p.capabilities.thinking_disabled is False
    assert p.capabilities.lane_header == ""
    assert p.capabilities.sdk_retries == PATIENT_SDK_RETRIES
    assert p.describe()["model"] == EVAL_MODEL
    assert PATIENT_TEMPERATURE == 0.5

    # ctor: OpenRouter base, dummy patient key, 120s SDK timeout, no retries,
    # NO gateway lane header in default_headers.
    assert len(FakeAsyncOpenAI.instances) == 1
    ctor = FakeAsyncOpenAI.instances[0].kwargs
    assert EVAL_BASE in str(ctor.get("base_url", ""))
    assert ctor.get("api_key") == "sk-test-patient-dummy"
    assert ctor.get("timeout") == 120.0
    assert ctor.get("max_retries") == 0
    default_headers = ctor.get("default_headers") or {}
    assert "x-opencode-session" not in default_headers

    # stream: exact evaluated wire params.
    msgs = [{"role": "user", "content": "halo?"}]
    toks = _drain(p.astream("sys", msgs, max_tokens=350, fast=True,
                            session_id="s1"))
    assert "".join(toks).strip() == CANNED
    kw = FakeAsyncOpenAI.instances[0].chat.completions.calls[-1]
    assert kw["model"] == EVAL_MODEL
    assert kw["temperature"] == 0.5
    assert kw["max_tokens"] == 350
    assert kw.get("stream") is True
    assert kw.get("extra_body") == {"reasoning": {"enabled": False}}
    assert "thinking" not in json.dumps(kw.get("extra_body") or {})
    assert "extra_headers" not in kw, \
        "OpenRouter must never see the x-opencode-session lane header"
    assert "x-opencode-session" not in json.dumps(kw)

    # non-stream: same reasoning-off, no headers, temperature default 0.5.
    out = asyncio.run(p.agenerate("sys", msgs, max_tokens=350, fast=True,
                                  session_id="s1"))
    assert CANNED.split(" ")[0] in out
    kw2 = FakeAsyncOpenAI.instances[0].chat.completions.calls[-1]
    assert kw2.get("stream", False) is not True
    assert kw2["model"] == EVAL_MODEL
    assert kw2["temperature"] == 0.5
    assert kw2["max_tokens"] == 350
    assert kw2.get("extra_body") == {"reasoning": {"enabled": False}}
    assert "extra_headers" not in kw2


def test_openrouter_content_guard_matches_opencode(monkeypatch):
    """Same meaningful-content semantics: bare '....' raises like llm.py."""
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch, text="....")
    _openrouter_env(monkeypatch)
    p = OpenRouterChatCompletionsProvider()
    with pytest.raises(RuntimeError, match="konten kosong"):
        asyncio.run(p.agenerate("sys", [{"role": "user", "content": "hi"}],
                                max_tokens=350))


def test_openrouter_extra_merges_but_reasoning_stays_off(monkeypatch):
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch)
    _openrouter_env(monkeypatch)
    monkeypatch.setenv("PATIENT_LLM_EXTRA",
                       '{"top_p": 0.9, "reasoning": {"max_tokens": 0, "enabled": true}}')
    from app.config import get_settings
    get_settings.cache_clear()
    p = OpenRouterChatCompletionsProvider()
    _drain(p.astream("sys", [{"role": "user", "content": "hi"}],
                     max_tokens=350, session_id="s"))
    kw = FakeAsyncOpenAI.instances[0].chat.completions.calls[-1]
    assert kw["extra_body"]["top_p"] == 0.9
    assert kw["extra_body"]["reasoning"]["enabled"] is False
    assert kw["extra_body"]["reasoning"]["max_tokens"] == 0
    assert "thinking" not in kw["extra_body"]


def test_openrouter_thinking_key_in_extra_is_dropped(monkeypatch):
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch)
    _openrouter_env(monkeypatch)
    monkeypatch.setenv("PATIENT_LLM_EXTRA", '{"thinking": {"type": "disabled"}}')
    from app.config import get_settings
    get_settings.cache_clear()
    p = OpenRouterChatCompletionsProvider()
    _drain(p.astream("sys", [{"role": "user", "content": "hi"}],
                     max_tokens=350, session_id="s"))
    kw = FakeAsyncOpenAI.instances[0].chat.completions.calls[-1]
    assert "thinking" not in kw["extra_body"]
    assert kw["extra_body"] == {"reasoning": {"enabled": False}}


# ── (2) selection matrix ─────────────────────────────────────────────────

def test_resolve_kind_pure_config():
    from app.rag.patient_provider import resolve_patient_adapter_kind
    assert resolve_patient_adapter_kind(EVAL_BASE) == "openrouter"
    assert resolve_patient_adapter_kind("https://openrouter.ai/api/v1/extra") == "openrouter"
    assert resolve_patient_adapter_kind("HTTPS://OPENROUTER.AI/API/V1") == "openrouter"
    assert resolve_patient_adapter_kind(OPENCODE_BASE) == "opencode"
    assert resolve_patient_adapter_kind("https://opencode.ai/zen/go/v1") == "opencode"
    assert resolve_patient_adapter_kind("https://example.invalid/v1") == "unknown"
    assert resolve_patient_adapter_kind("") == "unknown"
    assert resolve_patient_adapter_kind(None) == "unknown"


def test_selection_unset_inherits_llm_opencode(monkeypatch):
    """ALL PATIENT_* unset + LLM_*=OpenCode zen → existing adapter, zero change."""
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import OpenCodeChatCompletionsProvider
    _patch_async(monkeypatch)
    for v in ("PATIENT_LLM_PROVIDER", "PATIENT_LLM_API_KEY",
              "PATIENT_LLM_BASE_URL", "PATIENT_LLM_MODEL", "PATIENT_LLM_EXTRA"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_BASE_URL", OPENCODE_BASE)
    monkeypatch.setenv("LLM_MODEL", OPENCODE_MODEL)
    from app.config import get_settings
    get_settings.cache_clear()
    assert get_settings().patient_overrides() == {}
    p = pp_mod.get_patient_provider()
    assert isinstance(p, OpenCodeChatCompletionsProvider)
    assert p.describe()["model"] == OPENCODE_MODEL


def test_selection_unset_inherits_llm_openrouter(monkeypatch):
    """ALL PATIENT_* unset + LLM_*=OpenRouter defaults → OpenRouter adapter."""
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch)
    for v in ("PATIENT_LLM_PROVIDER", "PATIENT_LLM_API_KEY",
              "PATIENT_LLM_BASE_URL", "PATIENT_LLM_MODEL", "PATIENT_LLM_EXTRA"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_BASE_URL", EVAL_BASE)
    monkeypatch.setenv("LLM_MODEL", EVAL_MODEL)
    from app.config import get_settings
    get_settings.cache_clear()
    p = pp_mod.get_patient_provider()
    assert isinstance(p, OpenRouterChatCompletionsProvider)


def test_selection_full_patient_env_routes_openrouter(monkeypatch):
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch)
    _openrouter_env(monkeypatch)
    p = pp_mod.get_patient_provider()
    assert isinstance(p, OpenRouterChatCompletionsProvider)
    assert p.describe()["model"] == EVAL_MODEL
    # singleton: same instance while config unchanged.
    assert pp_mod.get_patient_provider() is p


def test_selection_partial_model_only_stays_opencode(monkeypatch):
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import OpenCodeChatCompletionsProvider
    _patch_async(monkeypatch)
    for v in ("PATIENT_LLM_PROVIDER", "PATIENT_LLM_API_KEY",
              "PATIENT_LLM_BASE_URL", "PATIENT_LLM_EXTRA"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_BASE_URL", OPENCODE_BASE)
    monkeypatch.setenv("LLM_MODEL", OPENCODE_MODEL)
    monkeypatch.setenv("PATIENT_LLM_MODEL", "future/model-x")
    from app.config import get_settings
    get_settings.cache_clear()
    p = pp_mod.get_patient_provider()
    assert isinstance(p, OpenCodeChatCompletionsProvider)
    assert p.describe()["model"] == "future/model-x"


def test_selection_partial_base_only_switches_gateway(monkeypatch):
    """Only PATIENT_LLM_BASE_URL=openrouter (+LLM key) → OpenRouter adapter."""
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import OpenRouterChatCompletionsProvider
    _patch_async(monkeypatch)
    for v in ("PATIENT_LLM_PROVIDER", "PATIENT_LLM_API_KEY",
              "PATIENT_LLM_MODEL", "PATIENT_LLM_EXTRA"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("LLM_BASE_URL", OPENCODE_BASE)
    monkeypatch.setenv("LLM_MODEL", OPENCODE_MODEL)
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", EVAL_BASE)
    from app.config import get_settings
    get_settings.cache_clear()
    p = pp_mod.get_patient_provider()
    assert isinstance(p, OpenRouterChatCompletionsProvider)


def test_selection_unknown_fails_closed_501(monkeypatch):
    import app.rag.patient_provider as pp_mod
    _patch_async(monkeypatch)
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("PATIENT_LLM_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("PATIENT_LLM_MODEL", "some/model")
    from app.config import get_settings
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="501"):
        pp_mod.get_patient_provider()


def test_selection_invalid_extra_fails_closed_501(monkeypatch):
    import app.rag.patient_provider as pp_mod
    _patch_async(monkeypatch)
    _openrouter_env(monkeypatch)
    monkeypatch.setenv("PATIENT_LLM_EXTRA", "{not-json")
    from app.config import get_settings
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="501"):
        pp_mod.get_patient_provider()


def test_selection_no_key_returns_stub_even_for_unknown(monkeypatch):
    """No key → stub (no network, safe); 501 only matters with a live key."""
    import app.rag.patient_provider as pp_mod
    from app.rag.patient_provider import ENDPOINT_KIND_STUB
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.delenv("PATIENT_LLM_API_KEY", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    p = pp_mod.get_patient_provider()
    assert p.capabilities.endpoint_kind == ENDPOINT_KIND_STUB


def test_guards_stay_frozen():
    import app.rag.llm as llm_mod
    assert llm_mod._PATIENT_FIRST_TOKEN_S == 7.0
    assert llm_mod._PATIENT_TOTAL_S == 20.0


# ── (3) judge pinning ────────────────────────────────────────────────────

class _FakeSyncCompletions:
    def __init__(self):
        self.calls: list[dict] = []

    def create(self, **kwargs):
        from tests.test_refactor_phase0_baseline import _FakeCompletion, CANNED_TEXT
        self.calls.append(kwargs)
        return _FakeCompletion(CANNED_TEXT)


class _FakeSyncChat:
    def __init__(self):
        self.completions = _FakeSyncCompletions()


class _FakeSyncOpenAI:
    instances: list = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.chat = _FakeSyncChat()
        _FakeSyncOpenAI.instances.append(self)

    @property
    def base_url(self):
        return self.kwargs.get("base_url", "")


def test_judge_construction_ignores_patient_env(monkeypatch):
    """Judge sync+async clients are built from LLM_* ONLY (PINNED)."""
    import app.rag.llm as llm_mod
    import openai
    _FakeSyncOpenAI.instances.clear()
    FakeAsyncOpenAI.instances.clear()
    monkeypatch.setattr(openai, "OpenAI", _FakeSyncOpenAI)
    monkeypatch.setattr(openai, "AsyncOpenAI", FakeAsyncOpenAI)
    # Judge on OpenCode zen; patient on OpenRouter evaluated — judge must not move.
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", "sk-judge-key")
    monkeypatch.setenv("LLM_BASE_URL", OPENCODE_BASE)
    monkeypatch.setenv("LLM_MODEL", OPENCODE_MODEL)
    monkeypatch.setenv("LLM_JUDGE_MODEL", OPENCODE_MODEL)
    monkeypatch.setenv("PATIENT_LLM_BASE_URL", EVAL_BASE)
    monkeypatch.setenv("PATIENT_LLM_API_KEY", "sk-patient-key-DIFFERENT")
    monkeypatch.setenv("PATIENT_LLM_MODEL", EVAL_MODEL)
    from app.config import get_settings
    get_settings.cache_clear()
    llm_mod._client = None
    llm_mod._async_client = None

    sync_client = llm_mod._build_client()
    assert len(_FakeSyncOpenAI.instances) == 1
    assert _FakeSyncOpenAI.instances[0].kwargs.get("api_key") == "sk-judge-key"
    assert OPENCODE_BASE in str(_FakeSyncOpenAI.instances[0].kwargs.get("base_url") or "")

    async_client = llm_mod._build_async_client()
    assert len(FakeAsyncOpenAI.instances) == 1
    assert FakeAsyncOpenAI.instances[0].kwargs.get("api_key") == "sk-judge-key"
    assert OPENCODE_BASE in str(FakeAsyncOpenAI.instances[0].kwargs.get("base_url") or "")

    # Judge outbound uses the judge model, never the patient model.
    sync_client.generate("sys", [{"role": "user", "content": "hi"}],
                         model=get_settings().llm_judge_model, max_tokens=16)
    kwargs = _FakeSyncOpenAI.instances[0].chat.completions.calls[-1]
    assert kwargs["model"] == OPENCODE_MODEL
    assert EVAL_MODEL not in json.dumps(kwargs)
    assert "sk-patient-key-DIFFERENT" not in json.dumps(kwargs)
    assert EVAL_BASE not in json.dumps(kwargs)
