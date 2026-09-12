"""Phase-1 voice foundation — patient LLM provider seam (ADR §4.1, §4.4).

HARD CONSTRAINT (frozen for Run 1): NO provider/model migration. Patient
AND judge stay on OpenCode zen (LLM_BASE_URL=https://opencode.ai/zen/go/v1)
+ deepseek-v4-flash with identical params. This module builds the SEAM, it
does not cross it: the single implementation below reproduces the existing
OpenCode chat-completions behavior byte-for-byte (same URL/model/params/
headers/guards), so a future provider swap is config-only:

  future swap = new PatientLLMProvider subclass + PATIENT_LLM_* env
                (no engine/router/timing changes).

Phase-2 (OpenRouter patient runtime, evaluated + APPROVED by owner):
  * OpenRouterChatCompletionsProvider — second implementation behind the
    SAME seam, with the EXACT evaluated params: base
    https://openrouter.ai/api/v1, model deepseek/deepseek-v4-flash-0731,
    temperature 0.5, max_tokens 350 (via engine), stream, extra_body
    {"reasoning": {"enabled": False}}; NO x-opencode-session lane header,
    NO thinking-disabled param (OpenRouter-appropriate only); same
    meaningful-content guard semantics as the OpenCode path; same 7s TTFT /
    20s total guards via the SHARED astream_patient path (untouched).
  * Selection is pure config on the RESOLVED patient base_url:
    "openrouter.ai" substring → OpenRouter adapter; "opencode.ai"
    substring → existing OpenCode adapter; anything else (with a key set)
    → fail closed with a clear 501, never silent wrong-model. When ALL
    PATIENT_LLM_* are unset, resolution inherits LLM_* so prod stays on
    the frozen OpenCode zen topology with ZERO behavior change.
  * Rollback = unset PATIENT_LLM_* (one line: unset PATIENT_LLM_BASE_URL
    PATIENT_LLM_API_KEY PATIENT_LLM_MODEL PATIENT_LLM_EXTRA).

Contract:
  * PatientLLMProvider — Protocol: astream/agenerate with the SAME
    signature as the legacy async client, plus capability flags including
    the endpoint kind ("chat_completions" for both real gateways).
  * OpenCodeChatCompletionsProvider — the Phase-1 implementation: delegates
    to the existing OpenAI-compatible adapter in app.rag.llm (shared
    _chat_kwargs wire contract, thinking-disabled fast path, per-session
    x-opencode-session lane header, 7s TTFT / 20s total guards via
    astream_patient). Single deliberate delta vs the legacy client: SDK
    automatic retries are OFF (max_retries=0, ADR §4.3) so attempts are
    governed solely by the astream_patient fresh-lane policy — see the
    retry map in astream_patient. Timeouts (120s SDK, 7s/20s guards),
    temperature (0.5), max_tokens, headers and lane scheme are unchanged.
  * OpenRouterChatCompletionsProvider — the Phase-2 implementation (see
    above). No engine/router/timing changes; guards stay 7s/20s.
  * get_patient_provider() — per-worker persistent singleton (opened at
    lifespan startup, closed at shutdown; never per-request). No key
    material is ever logged; describe()/fingerprint() expose non-secret
    topology only.

The judge NEVER touches this module: judge_v2/judge_v3 keep using
get_llm_client()/get_async_llm_client() with LLM_* directly (pinned by
test — patient env is ignored by judge construction).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings

ENDPOINT_KIND_CHAT_COMPLETIONS = "chat_completions"
ENDPOINT_KIND_STUB = "stub"

# Frozen Phase-1 patient sampling/wire values (mirrors llm.py; asserted by
# tests — any change here is a provider migration and needs an ADR revision).
PATIENT_TEMPERATURE = 0.5
PATIENT_SDK_TIMEOUT_S = 120.0
PATIENT_SDK_RETRIES = 0  # ADR §4.3: SDK auto-retries off on patient clients

# Phase-2 evaluated OpenRouter contract (APPROVED by owner; asserted by
# tests — any change here is a provider migration and needs re-evaluation).
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_EVALUATED_MODEL = "deepseek/deepseek-v4-flash-0731"
OPENROUTER_REASONING_OFF: dict = {"reasoning": {"enabled": False}}


def resolve_patient_adapter_kind(base_url: str | None) -> str:
    """Pure-config adapter selection (no I/O, no keys).

    Returns "openrouter" when the resolved patient base_url contains
    "openrouter.ai", "opencode" when it contains "opencode.ai", else
    "unknown". Case-insensitive substring match. Callers fail closed on
    "unknown" (clear 501) when a key is set — never silent wrong-model.
    With no key set the factory returns the stub (no network) regardless.
    """
    try:
        bu = (base_url or "").lower()
    except Exception:
        return "unknown"
    if "openrouter.ai" in bu:
        return "openrouter"
    if "opencode.ai" in bu:
        return "opencode"
    return "unknown"


def _openrouter_extra_body() -> dict:
    """Evaluated OpenRouter extra_body: reasoning OFF, plus future knobs.

    Merges PATIENT_LLM_EXTRA (optional JSON object) then FORCES
    reasoning.enabled=False (other reasoning sub-keys are preserved) and
    drops any "thinking" key (OpenRouter-appropriate only — the gateway
    must never see the OpenCode thinking-disabled param). Invalid EXTRA
    JSON raises with a clear 501 (fail closed).
    """
    s = get_settings()
    try:
        extra = dict(s.patient_extra() or {})
    except RuntimeError:
        raise
    except Exception:
        extra = {}
    extra.pop("thinking", None)
    reasoning = extra.get("reasoning")
    if isinstance(reasoning, dict):
        merged = dict(reasoning)
        merged["enabled"] = False
        extra["reasoning"] = merged
    else:
        extra["reasoning"] = {"enabled": False}
    return extra


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capability flags for a patient provider (endpoint kind included)."""
    endpoint_kind: str = ENDPOINT_KIND_CHAT_COMPLETIONS
    supports_streaming: bool = True
    thinking_disabled: bool = True
    lane_header: str = "x-opencode-session"
    sdk_retries: int = PATIENT_SDK_RETRIES


class PatientLLMProvider(Protocol):
    """Transport seam for the patient persona. Same call shape as the
    legacy async client so astream_patient() accepts either."""

    @property
    def capabilities(self) -> ProviderCapabilities: ...

    def describe(self) -> dict:
        """Non-secret topology labels for the attempt timeline."""
        ...

    async def astream(self, system: str, messages: list[dict],
                      model: str | None = None,
                      max_tokens: int | None = None,
                      fast: bool = True,
                      session_id: str | None = None): ...

    async def agenerate(self, system: str, messages: list[dict],
                        model: str | None = None,
                        max_tokens: int | None = None,
                        temperature: float | None = None,
                        timeout: float | None = None,
                        max_retries: int | None = None,
                        fast: bool = True,
                        session_id: str | None = None) -> str: ...


def patient_config_fingerprint() -> str:
    """Non-secret config hash for topology logging (no key material)."""
    try:
        s = get_settings()
        try:
            kind = resolve_patient_adapter_kind(s.patient_base_url())
        except Exception:
            kind = "unknown"
        try:
            extra_keys = ",".join(sorted((s.patient_extra() or {}).keys()))
        except RuntimeError:
            extra_keys = "invalid"
        except Exception:
            extra_keys = ""
        guard = ("reasoning=off" if kind == "openrouter"
                 else "thinking=disabled")
        blob = "|".join([
            str(s.patient_provider() or ""),
            str(s.patient_base_url() or ""),
            str(s.patient_model() or ""),
            f"temp={PATIENT_TEMPERATURE}",
            f"persona_max_tokens={s.llm_persona_max_tokens}",
            f"sdk_retries={PATIENT_SDK_RETRIES}",
            guard,
            f"kind={kind}",
            f"extra={extra_keys or '-'}",
        ])
        return hashlib.sha256(blob.encode()).hexdigest()[:16]
    except Exception:
        return ""


class OpenCodeChatCompletionsProvider:
    """Existing OpenCode chat-completions behavior, behind the seam."""

    def __init__(self, client=None):
        from app.rag.llm import AsyncStubLlmClient, _openai_async_compatible
        s = get_settings()
        if client is not None:
            self._client = client
        elif not s.patient_api_key():
            self._client = AsyncStubLlmClient()
        else:
            built = _openai_async_compatible(
                s.patient_base_url(),
                sdk_retries=PATIENT_SDK_RETRIES,
                api_key=s.patient_api_key(),
                default_model=s.patient_model(),
            )
            from app.rag.llm import AsyncStubLlmClient as _Stub
            self._client = built if built is not None else _Stub()
        self._caps = ProviderCapabilities(
            endpoint_kind=(ENDPOINT_KIND_STUB if type(
                self._client).__name__ == "AsyncStubLlmClient"
                else ENDPOINT_KIND_CHAT_COMPLETIONS),
            sdk_retries=PATIENT_SDK_RETRIES,
        )

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def describe(self) -> dict:
        try:
            s = get_settings()
            return {
                "model": str(s.patient_model() or ""),
                "endpoint_kind": self._caps.endpoint_kind,
                "gateway": "opencode",
            }
        except Exception:
            return {"model": "", "endpoint_kind": self._caps.endpoint_kind,
                    "gateway": "opencode"}

    async def astream(self, system, messages, model=None, max_tokens=None,
                      fast=True, session_id=None):
        # Identical delegation: same adapter, same kwargs, same headers.
        # The default model resolves inside the adapter to the patient model.
        async for tok in self._client.astream(
                system, messages, model=model, max_tokens=max_tokens,
                fast=fast, session_id=session_id):
            yield tok

    async def agenerate(self, system, messages, model=None, max_tokens=None,
                        temperature=None, timeout=None, max_retries=None,
                        fast=True, session_id=None) -> str:
        return await self._client.agenerate(
            system, messages, model=model, max_tokens=max_tokens,
            temperature=temperature, timeout=timeout,
            max_retries=max_retries, fast=fast, session_id=session_id)


def _build_openrouter_async_client():
    """OpenRouter async transport: OpenAI-compatible, OpenRouter-appropriate
    only (no gateway lane header, no thinking param). Shared _chat_kwargs
    wire contract + same meaningful-content guard semantics as llm.py."""
    from app.rag.llm import _chat_kwargs, _with_retry_async
    s = get_settings()
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return None
    headers: dict = {}
    # OpenRouter attribution only (safe to leave empty). Deliberately NO
    # x-opencode-session default header — that lane belongs to the OpenCode
    # gateway and must never leak to OpenRouter.
    if s.llm_site_url:
        headers["HTTP-Referer"] = s.llm_site_url
    if s.llm_app_title:
        headers["X-Title"] = s.llm_app_title
    aclient = AsyncOpenAI(
        api_key=s.patient_api_key(),
        base_url=s.patient_base_url() or None,
        default_headers=headers or None,
        timeout=PATIENT_SDK_TIMEOUT_S,
        max_retries=PATIENT_SDK_RETRIES,
    )
    default_model = s.patient_model()

    def _guard(content) -> str:
        content = content or ""
        if not re.sub(r"[^0-9A-Za-z]", "", str(content)):
            raise RuntimeError("LLM kembalikan konten kosong (overload/truncated?)")
        return content

    class _OAI_OR_ASYNC:
        _sdk = aclient
        _default_model = default_model

        async def agenerate(self, system, messages, model=None, max_tokens=None,
                            temperature=None, timeout=None, max_retries=None,
                            fast=True, session_id=None):
            # session_id accepted for Protocol compat but NEVER sent as a
            # header (OpenRouter-appropriate only). fast is accepted but
            # ignored: there is no thinking param on this gateway.
            async def _call():
                kwargs = _chat_kwargs(
                    model=model or self._default_model or s.llm_model,
                    system=system, messages=messages,
                    temperature=(PATIENT_TEMPERATURE if temperature is None
                                 else temperature),
                    max_tokens=max_tokens, timeout=timeout, stream=False,
                    extra_body=_openrouter_extra_body() or None)
                # NO extra_headers here — OpenRouter must never see the
                # x-opencode-session lane header.
                r = await aclient.chat.completions.create(**kwargs)
                if not getattr(r, "choices", None):
                    raise RuntimeError(
                        f"LLM tanpa choices: {str(getattr(r, 'error', None) or repr(r))[:200]}"
                    )
                return _guard(r.choices[0].message.content)

            return await _with_retry_async(_call, retries=max_retries)

        async def astream(self, system, messages, model=None, max_tokens=None,
                          fast=True, session_id=None):
            # Same: session_id/fast accepted, never emitted as headers/params.
            kwargs = _chat_kwargs(
                model=model or self._default_model or s.llm_model,
                system=system, messages=messages,
                temperature=PATIENT_TEMPERATURE, max_tokens=max_tokens,
                timeout=None, stream=True,
                extra_body=_openrouter_extra_body() or None)
            # NO extra_headers — see above.
            st = await aclient.chat.completions.create(**kwargs)
            try:
                async for ch in st:
                    if not getattr(ch, "choices", None):
                        continue
                    d = ch.choices[0].delta.content
                    if d:
                        yield d
            finally:
                aclose = getattr(st, "aclose", None)
                if aclose is not None:
                    try:
                        await aclose()
                    except Exception:  # noqa: BLE001 - cleanup must not fail
                        pass

    return _OAI_OR_ASYNC()


class OpenRouterChatCompletionsProvider:
    """Evaluated OpenRouter patient behavior, behind the same seam.

    Wire contract (APPROVED): base https://openrouter.ai/api/v1, model
    deepseek/deepseek-v4-flash-0731 (via PATIENT_LLM_MODEL), temperature
    0.5, max_tokens from the caller (350 via the engine), stream,
    extra_body {"reasoning": {"enabled": False}} (+ future PATIENT_LLM_EXTRA
    knobs, reasoning forced OFF); NO x-opencode-session header, NO thinking
    param. Guards (7s TTFT / 20s total / one fresh-lane retry) live in the
    SHARED astream_patient path and are unchanged.

    Rollback = unset PATIENT_LLM_* (one line: unset PATIENT_LLM_BASE_URL
    PATIENT_LLM_API_KEY PATIENT_LLM_MODEL PATIENT_LLM_EXTRA).
    """

    def __init__(self, client=None):
        from app.rag.llm import AsyncStubLlmClient
        s = get_settings()
        if client is not None:
            self._client = client
        elif not s.patient_api_key():
            self._client = AsyncStubLlmClient()
        else:
            _openrouter_extra_body()  # fail fast on invalid EXTRA (clear 501)
            built = _build_openrouter_async_client()
            self._client = built if built is not None else AsyncStubLlmClient()
        self._caps = ProviderCapabilities(
            endpoint_kind=(ENDPOINT_KIND_STUB if type(
                self._client).__name__ == "AsyncStubLlmClient"
                else ENDPOINT_KIND_CHAT_COMPLETIONS),
            thinking_disabled=False,  # no thinking param on this gateway
            lane_header="",  # no lane header on this gateway
            sdk_retries=PATIENT_SDK_RETRIES,
        )

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def describe(self) -> dict:
        try:
            s = get_settings()
            return {
                "model": str(s.patient_model() or ""),
                "endpoint_kind": self._caps.endpoint_kind,
                "gateway": "openrouter",
            }
        except Exception:
            return {"model": "", "endpoint_kind": self._caps.endpoint_kind,
                    "gateway": "openrouter"}

    async def astream(self, system, messages, model=None, max_tokens=None,
                      fast=True, session_id=None):
        # session_id is consumed by the shared astream_patient retry/lane
        # accounting only — never forwarded as a transport header here.
        async for tok in self._client.astream(
                system, messages, model=model, max_tokens=max_tokens,
                fast=fast, session_id=session_id):
            yield tok

    async def agenerate(self, system, messages, model=None, max_tokens=None,
                        temperature=None, timeout=None, max_retries=None,
                        fast=True, session_id=None) -> str:
        return await self._client.agenerate(
            system, messages, model=model, max_tokens=max_tokens,
            temperature=temperature, timeout=timeout,
            max_retries=max_retries, fast=fast, session_id=session_id)


class StubPatientProvider(OpenCodeChatCompletionsProvider):
    """Deterministic stub behind the same seam (no key → no network)."""

    def __init__(self):
        from app.rag.llm import AsyncStubLlmClient
        super().__init__(client=AsyncStubLlmClient())


_provider = None
_provider_key: tuple | None = None


def _current_key() -> tuple:
    """Non-secret identity of the patient endpoint config. The singleton is
    keyed on this (not just None-checked) so a config change — or a test
    swapping env/fakes with a cleared settings cache — rebuilds instead of
    serving a stale endpoint. Never includes key material (presence only;
    EXTRA raw string included so knob changes rebuild — EXTRA is documented
    as future non-secret knobs; values never leave this process)."""
    try:
        s = get_settings()
        try:
            extra_raw = str(s.patient_llm_extra or "")
        except Exception:
            extra_raw = ""
        return (
            str(s.patient_provider() or ""),
            str(s.patient_base_url() or ""),
            str(s.patient_model() or ""),
            bool(s.patient_api_key()),
            extra_raw,
        )
    except Exception:
        return ("", "", "", False, "")


def get_patient_provider() -> PatientLLMProvider:
    """Per-worker persistent patient provider (lifespan opens it eagerly).

    Config-keyed singleton: repeated calls with unchanged config return the
    same instance (no per-request builds, no duplication); a config change
    drops the old handle and builds fresh.

    Selection is pure config on the RESOLVED patient base_url (see
    resolve_patient_adapter_kind): openrouter.ai → OpenRouter adapter,
    opencode.ai → existing OpenCode adapter. With NO key set (stub env,
    tests, dev) the stub is returned regardless (no network, safe). With a
    key set and an unknown base_url, fail closed with a clear 501 — never
    silent wrong-model.

    Rollback = unset PATIENT_LLM_* (one line: unset PATIENT_LLM_BASE_URL
    PATIENT_LLM_API_KEY PATIENT_LLM_MODEL PATIENT_LLM_EXTRA).
    """
    global _provider, _provider_key
    key = _current_key()
    if _provider is None or _provider_key != key:
        s = get_settings()
        if not s.patient_api_key():
            _provider = StubPatientProvider()
        else:
            kind = resolve_patient_adapter_kind(s.patient_base_url())
            if kind == "openrouter":
                _provider = OpenRouterChatCompletionsProvider()
            elif kind == "opencode":
                _provider = OpenCodeChatCompletionsProvider()
            else:
                raise RuntimeError(
                    "[patient provider 501] unknown PATIENT_LLM_BASE_URL "
                    f"{str(s.patient_base_url() or '')[:80]!r}: expected a "
                    "base_url containing 'openrouter.ai' or 'opencode.ai'. "
                    "Refusing to guess a gateway/model (never silent "
                    "wrong-model). Rollback: unset PATIENT_LLM_BASE_URL "
                    "PATIENT_LLM_API_KEY PATIENT_LLM_MODEL PATIENT_LLM_EXTRA."
                )
        _provider_key = key
    return _provider


async def open_patient_provider() -> None:
    """Lifespan startup: build the patient provider outside request path."""
    get_patient_provider()


async def close_patient_provider() -> None:
    """Lifespan shutdown: close the patient SDK transport (§7.1a).

    Only the patient-owned SDK client is closed; the shared judge/sync
    client is owned by app.rag.llm.close_async_llm and is never touched.
    """
    global _provider, _provider_key
    provider, _provider = _provider, None
    _provider_key = None
    try:
        sdk = getattr(getattr(provider, "_client", None), "_sdk", None)
        close = getattr(sdk, "close", None)
        if close is not None:
            import asyncio as _asyncio
            result = close()
            if _asyncio.iscoroutine(result):
                await result
    except Exception:  # noqa: BLE001 - shutdown must not fail
        pass
