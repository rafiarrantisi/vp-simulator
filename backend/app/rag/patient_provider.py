"""Phase-1 voice foundation — patient LLM provider seam (ADR §4.1, §4.4).

HARD CONSTRAINT (frozen for Run 1): NO provider/model migration. Patient
AND judge stay on OpenCode zen (LLM_BASE_URL=https://opencode.ai/zen/go/v1)
+ deepseek-v4-flash with identical params. This module builds the SEAM, it
does not cross it: the single implementation below reproduces the existing
OpenCode chat-completions behavior byte-for-byte (same URL/model/params/
headers/guards), so a future provider swap is config-only:

  future swap = new PatientLLMProvider subclass + PATIENT_LLM_* env
                (no engine/router/timing changes).

Contract:
  * PatientLLMProvider — Protocol: astream/agenerate with the SAME
    signature as the legacy async client, plus capability flags including
    the endpoint kind ("chat_completions" today).
  * OpenCodeChatCompletionsProvider — the ONE implementation: delegates to
    the existing OpenAI-compatible adapter in app.rag.llm (shared
    _chat_kwargs wire contract, thinking-disabled fast path, per-session
    x-opencode-session lane header, 7s TTFT / 20s total guards via
    astream_patient). Single deliberate delta vs the legacy client: SDK
    automatic retries are OFF (max_retries=0, ADR §4.3) so attempts are
    governed solely by the astream_patient fresh-lane policy — see the
    retry map in astream_patient. Timeouts (120s SDK, 7s/20s guards),
    temperature (0.5), max_tokens, headers and lane scheme are unchanged.
  * get_patient_provider() — per-worker persistent singleton (opened at
    lifespan startup, closed at shutdown; never per-request). No key
    material is ever logged; describe()/fingerprint() expose non-secret
    topology only.

The judge NEVER touches this module: judge_v2/judge_v3 keep using
get_llm_client()/get_async_llm_client() with LLM_* directly.
"""
from __future__ import annotations

import hashlib
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
        blob = "|".join([
            str(s.patient_provider() or ""),
            str(s.patient_base_url() or ""),
            str(s.patient_model() or ""),
            f"temp={PATIENT_TEMPERATURE}",
            f"persona_max_tokens={s.llm_persona_max_tokens}",
            f"sdk_retries={PATIENT_SDK_RETRIES}",
            "thinking=disabled",
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
            }
        except Exception:
            return {"model": "", "endpoint_kind": self._caps.endpoint_kind}

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
    serving a stale endpoint. Never includes key material (presence only)."""
    try:
        s = get_settings()
        return (
            str(s.patient_provider() or ""),
            str(s.patient_base_url() or ""),
            str(s.patient_model() or ""),
            bool(s.patient_api_key()),
        )
    except Exception:
        return ("", "", "", False)


def get_patient_provider() -> PatientLLMProvider:
    """Per-worker persistent patient provider (lifespan opens it eagerly).

    Config-keyed singleton: repeated calls with unchanged config return the
    same instance (no per-request builds, no duplication); a config change
    drops the old handle and builds fresh.
    """
    global _provider, _provider_key
    key = _current_key()
    if _provider is None or _provider_key != key:
        _provider = OpenCodeChatCompletionsProvider()
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
