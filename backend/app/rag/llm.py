"""LlmClient — abstraksi provider (kontrak §9 K2).

Default OpenRouter (OpenAI-compatible; satu key, banyak model `vendor/model`).
Tanpa `LLM_API_KEY` → `StubLlmClient` deterministik (pipeline tetap bisa
diverifikasi tanpa kredensial). SDK di-import lazy.

`generate`/`stream` menerima `model` opsional: default = model persona
(`settings.llm_model`, kuat); evaluator memakai `settings.llm_judge_model`
(murah, rag-plan §9.1) → pisah judge vs persona.
"""
from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncIterator, Iterator
from typing import Protocol

from app.config import get_settings

_RETRY = 3  # backoff utk 5xx/timeout (free tier sering flaky)


def _is_transient(e: Exception) -> bool:
    msg = str(e).lower()
    return any(k in msg for k in ("timeout", "502", "503", "504", "rate", "overload"))


def _with_retry(fn, retries: int | None = None):
    last = None
    n = _RETRY if retries is None else max(1, retries)
    for i in range(n):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - retry transient apa pun
            last = e
            if not _is_transient(e) or i == n - 1:
                raise
            time.sleep(1.5 * (i + 1))
    raise last  # pragma: no cover


async def _with_retry_async(fn, retries: int | None = None):
    """Async twin of `_with_retry`: identical budget Predicates, nonblocking wait."""
    last = None
    n = _RETRY if retries is None else max(1, retries)
    for i in range(n):
        try:
            return await fn()
        except Exception as e:  # noqa: BLE001 - retry transient apa pun
            last = e
            if not _is_transient(e) or i == n - 1:
                raise
            await asyncio.sleep(1.5 * (i + 1))
    raise last  # pragma: no cover


_PATIENT_FIRST_TOKEN_S = 7.0  # stall yang terobservasi = tak ada token sama sekali
_PATIENT_TOTAL_S = 20.0  # pengaman hang mid-stream (tak pernah terobservasi)


def _stream_transient_types():
    try:
        from openai import (APIConnectionError, APIStatusError,
                            APITimeoutError, RateLimitError)
        return (APIConnectionError, APITimeoutError, RateLimitError,
                APIStatusError, TimeoutError)
    except ImportError:  # pragma: no cover
        return (TimeoutError,)


async def _iter_guarded(agen, first_timeout: float, total_timeout: float):
    """Yield child tokens with TTFT + total caps; always release upstream."""
    start = time.monotonic()
    it = agen.__aiter__()
    first = True
    try:
        while True:
            budget = total_timeout - (time.monotonic() - start)
            if budget <= 0:
                raise TimeoutError(
                    f"patient turn exceeded {total_timeout}s total")
            try:
                tok = await asyncio.wait_for(
                    it.__anext__(), min(first_timeout if first else budget, budget))
            except StopAsyncIteration:
                return
            first = False
            yield tok
    finally:
        aclose = getattr(agen, "aclose", None)
        if aclose is not None:
            try:
                await aclose()
            except Exception:  # noqa: BLE001 - cleanup must not fail
                pass


async def astream_patient(client, system, messages, *, max_tokens,
                          session_id: str | None = None,
                          first_token_timeout: float = _PATIENT_FIRST_TOKEN_S,
                          total_timeout: float = _PATIENT_TOTAL_S,
                          route: str = "patient_turn",
                          logical_turn_id: str | None = None):
    """Patient turn with TTFT + total guardrails; ONE retry on a fresh gateway
    lane (stall terobservasi = lane-specific). Yields tokens progressively.
    Patient-only: thinking off. Raises TimeoutError/RuntimeError bila 2
    attempt gagal (router mengubahnya jadi pesan retry yang ramah).

    Phase-1 retry map (patient streaming path — the stacking audit):
      L0 SDK automatic retries ... DISABLED on the patient client
         (max_retries=0 via the patient provider; ADR §4.3). The shared
         judge/sync client keeps the SDK default (2) — judge untouched.
         Previously L0 stacked invisibly under L2/L4 on setup failures.
      L1 _with_retry/_with_retry_async (module, up to 3 tries, 1.5/3/4.5s
         sleeps) ... generate/agenerate ONLY (sync respond + judge paths).
         NOT on this streaming path. Unchanged.
      L2 THIS loop ................ max 2 attempts (0,1); 7.0s TTFT guard +
         20.0s total guard unchanged. Attempt 1 uses a fresh lane
         ("{session}-r0"); zero-content clean streams retry like stalls.
      L3 router stream (v2_turn_stream / v3c.stream_turn) ... NO retry:
         raises (v2) or yields one in-stream error string (v3). Unchanged.
      L4 frontend send() (sistemnya/qora-v2.jsx) ... stream failure → ONE
         non-stream POST /turns fallback (server dedupes via dup_reply).
         NOT edited in Run 1 (frontend out of scope) — documented here.
    Worst case per user send: 2 (L2 stream) + 2 (L2 via L4 fallback) = 4 LLM
    attempts. `client` may be a legacy async client or a PatientLLMProvider
    (duck-typed: a `describe()` hook supplies model/endpoint labels for the
    attempt timeline; transport signature is identical).

    Emits attempt_started / retry_started / first_content / full_completion
    timeline events (timing/IDs/lengths only) via observability.
    """
    from app.shared.observability import log_patient_attempt
    transient = _stream_transient_types()
    lane = session_id
    try:
        _describe = client.describe()  # type: ignore[attr-defined]
    except Exception:
        _describe = {}
    try:
        _model = _describe.get("model", "")
        _endpoint = _describe.get("endpoint_kind", "chat_completions")
    except Exception:
        _model, _endpoint = "", "chat_completions"
    try:
        from app.shared.perf_sink import lane_hash as _lane_hash
    except Exception:
        def _lane_hash(v):
            return ""
    last_exc: Exception | None = None
    for attempt in (0, 1):
        if attempt == 1:
            try:
                log_patient_attempt(
                    "retry_started", route=route,
                    logical_turn_id=logical_turn_id, session_id=session_id,
                    attempt=attempt, lane_hash=_lane_hash(lane),
                    model=_model, endpoint_kind=_endpoint,
                    error=type(last_exc).__name__ if last_exc else "")
            except Exception:
                pass
        try:
            log_patient_attempt(
                "attempt_started", route=route,
                logical_turn_id=logical_turn_id, session_id=session_id,
                attempt=attempt, lane_hash=_lane_hash(lane),
                model=_model, endpoint_kind=_endpoint)
        except Exception:
            pass
        attempt_t0 = time.monotonic()
        try:
            got_any = False
            first_at: float | None = None
            out_chars = 0
            async for tok in _iter_guarded(
                    client.astream(system, messages, max_tokens=max_tokens,
                                   fast=True, session_id=lane),
                    first_token_timeout, total_timeout):
                if not got_any:
                    got_any = True
                    first_at = time.monotonic()
                    try:
                        log_patient_attempt(
                            "first_content", route=route,
                            logical_turn_id=logical_turn_id,
                            session_id=session_id, attempt=attempt,
                            lane_hash=_lane_hash(lane), model=_model,
                            endpoint_kind=_endpoint,
                            ttft_ms=(first_at - attempt_t0) * 1000.0)
                    except Exception:
                        pass
                try:
                    out_chars += len(str(tok))
                except Exception:
                    pass
                yield tok
            if not got_any:
                # Clean stream with zero content tokens (transient upstream
                # truncation observed Sep 2026) — retry once like a stall.
                raise TimeoutError("patient turn returned no content")
            try:
                log_patient_attempt(
                    "full_completion", route=route,
                    logical_turn_id=logical_turn_id, session_id=session_id,
                    attempt=attempt, lane_hash=_lane_hash(lane), model=_model,
                    endpoint_kind=_endpoint,
                    ttft_ms=((first_at - attempt_t0) * 1000.0
                             if first_at else 0.0),
                    total_ms=(time.monotonic() - attempt_t0) * 1000.0,
                    output_chars=out_chars)
            except Exception:
                pass
            return
        except transient as e:
            last_exc = e
            lane = (f"{session_id}-r{attempt}" if session_id
                    else f"qora-retry-{attempt}")
    assert last_exc is not None  # noqa: S101 - loop selalu set atau return
    raise last_exc


class LlmClient(Protocol):
    def stream(self, system: str, messages: list[dict],
               model: str | None = None,
               max_tokens: int | None = None) -> Iterator[str]: ...

    def generate(self, system: str, messages: list[dict],
                 model: str | None = None,
                 max_tokens: int | None = None,
                 temperature: float | None = None,
                 timeout: float | None = None,
                 max_retries: int | None = None) -> str: ...


class AsyncLlmClient(Protocol):
    async def astream(self, system: str, messages: list[dict],
                      model: str | None = None,
                      max_tokens: int | None = None) -> AsyncIterator[str]: ...

    async def agenerate(self, system: str, messages: list[dict],
                        model: str | None = None,
                        max_tokens: int | None = None,
                        temperature: float | None = None,
                        timeout: float | None = None,
                        max_retries: int | None = None) -> str: ...


class AsyncStubLlmClient:
    """Async twin of the stub: deterministic, clearly marked, no network."""

    PREFIX = "[STUB LLM] "  # must match StubLlmClient.PREFIX below

    async def agenerate(self, system: str, messages: list[dict],
                        model: str | None = None,
                        max_tokens: int | None = None,
                        temperature: float | None = None,
                        timeout: float | None = None,
                        max_retries: int | None = None,
                        fast: bool = False,
                        session_id: str | None = None) -> str:
        return StubLlmClient().generate(
            system, messages, model=model, max_tokens=max_tokens,
            temperature=temperature, timeout=timeout, max_retries=max_retries)

    async def astream(self, system: str, messages: list[dict],
                      model: str | None = None,
                      max_tokens: int | None = None,
                      fast: bool = False,
                      session_id: str | None = None) -> AsyncIterator[str]:
        for tok in StubLlmClient().stream(system, messages):
            yield tok


def _openrouter_extra(base_url: str | None) -> dict | None:
    """Reasoning-disabled guard (OpenRouter-only), shared sync/async."""
    try:
        if base_url and "openrouter" in str(base_url):
            return {"reasoning": {"enabled": False}}
    except Exception:  # noqa: BLE001
        pass
    return None


def _thinking_off_extra(base_url: str | None) -> dict | None:
    """Thinking-disabled guard for the OpenCode Go gateway (patient persona
    only): measured Sep 2026 — TTFT 2.4s -> 1.6s, zero reasoning tokens,
    persona quality unchanged. Other providers: no-op (param ignored)."""
    try:
        if base_url and "opencode.ai" in str(base_url):
            return {"thinking": {"type": "disabled"}}
    except Exception:  # noqa: BLE001
        pass
    return None


def _gateway_headers(base_url: str | None, headers: dict) -> dict:
    """Provider-specific required headers, shared sync/async."""
    try:
        if base_url and "opencode.ai" in str(base_url):
            # OpenCode Go gateway refuses requests without a stable session
            # id (400 MissingSessionID). Deployment-stable value keeps
            # routing working; per-conversation ids would improve caching.
            headers.setdefault("x-opencode-session", "qora-prod")
    except Exception:  # noqa: BLE001
        pass
    return headers


def _chat_kwargs(*, model: str, system: str, messages: list[dict],
                 temperature: float, max_tokens: int | None,
                 timeout: float | None, stream: bool,
                 extra_body: dict | None) -> dict:
    """Single kwarg construction shared by sync + async adapters.

    Any divergence here changes the wire contract; pinned by golden tests.
    """
    kwargs: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": temperature,
    }
    if stream:
        kwargs["stream"] = True
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if timeout is not None and not stream:
        kwargs["timeout"] = timeout
    if extra_body:
        kwargs["extra_body"] = extra_body
    return kwargs


class StubLlmClient:
    """Deterministik, ditandai jelas. BUKAN untuk evaluasi klinis —
    hanya membuktikan pipeline (prompt assembly, retrieval, streaming)."""

    PREFIX = "[STUB LLM] "

    def generate(self, system: str, messages: list[dict],
                 model: str | None = None,
                 max_tokens: int | None = None,
                 temperature: float | None = None,
                 timeout: float | None = None,
                 max_retries: int | None = None,
                 fast: bool = False,
                 session_id: str | None = None) -> str:
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        return (
            self.PREFIX
            + "respons dihasilkan dari prompt ber-answer-restraint "
            + "(set env LLM_API_KEY utk provider nyata). Pertanyaan: "
            + (last_user[:80] if last_user else "(kosong)")
        )

    def stream(self, system: str, messages: list[dict],
               model: str | None = None,
               max_tokens: int | None = None,
               fast: bool = False,
               session_id: str | None = None) -> Iterator[str]:
        for tok in self.generate(system, messages).split(" "):
            yield tok + " "


def _openai_compatible(base_url: str | None, sdk_retries: int | None = None,
                       api_key: str | None = None):
    """OpenRouter & OpenAI sama-sama pakai SDK `openai`.

    Phase-1: `sdk_retries` disables the SDK's invisible automatic retries on
    patient clients (ADR §4.3 — SDK retries used to stack under the
    astream_patient fresh-lane policy and _with_retry). None (default) =
    historical behavior: the kwarg is not passed at all, so the SDK default
    applies. The judge/shared path NEVER passes it (judge untouched).
    """
    s = get_settings()
    try:
        from openai import OpenAI
    except ImportError:
        return None
    headers = {}
    if s.llm_site_url:
        headers["HTTP-Referer"] = s.llm_site_url
    if s.llm_app_title:
        headers["X-Title"] = s.llm_app_title
    headers = _gateway_headers(base_url, headers)
    _cli_kwargs: dict = {
        "api_key": api_key if api_key is not None else s.llm_api_key,
        "base_url": base_url or None,
        "default_headers": headers or None,
        "timeout": 120.0,  # judge/patient calls must not hang the UI forever
    }
    if sdk_retries is not None:
        _cli_kwargs["max_retries"] = sdk_retries
    client = OpenAI(**_cli_kwargs)

    def _err(r):
        e = getattr(r, "error", None)
        if e is None and getattr(r, "model_extra", None):
            e = r.model_extra.get("error")
        return e

    class _OAI:
        # deepseek-v4-flash on OpenRouter is a reasoning model: with reasoning
        # ENABLED it burns the ENTIRE max_tokens budget on chain-of-thought and
        # returns ZERO content (measured Aug 2026: finish=length, reasoning=4000,
        # content=0 — the cause of empty/"...." replies AND empty judge reports).
        # Disable reasoning so output is direct content. OpenRouter-only param.
        @staticmethod
        def _extra():
            try:
                bu = str(getattr(client, "base_url", "") or "")
                return _openrouter_extra(bu)
            except Exception:  # noqa: BLE001
                pass
            return None

        def generate(self, system, messages, model=None, max_tokens=None, temperature=None,
                     timeout=None, max_retries=None, fast=False, session_id=None):
            def _extra_fast():
                extra = dict(self._extra() or {})
                if fast:
                    bu = str(getattr(client, "base_url", "") or "")
                    extra.update(_thinking_off_extra(bu) or {})
                return extra or None

            def _call():
                kwargs = _chat_kwargs(
                    model=model or s.llm_model, system=system, messages=messages,
                    temperature=0.5 if temperature is None else temperature,
                    max_tokens=max_tokens, timeout=timeout, stream=False,
                    extra_body=_extra_fast())
                if session_id:
                    kwargs["extra_headers"] = {
                        "x-opencode-session": f"qora-{session_id}"}
                r = client.chat.completions.create(**kwargs)
                if not getattr(r, "choices", None):
                    raise RuntimeError(
                        f"LLM tanpa choices: {_err(r) or repr(r)[:200]}"
                    )
                msg = r.choices[0].message
                # Reasoning model (gpt-oss) menaruh chain-of-thought di
                # `reasoning` — JANGAN pernah fallback ke situ utk output
                # user-facing (bocor CoT ke mahasiswa). Content kosong =
                # transient (truncated/overload) → retry via _with_retry.
                content = msg.content or ""
                # Meaningful-content guard (Aug 2026): deepseek-v4-flash can
                # emit a bare "...."/"…" or stray punctuation when overloaded.
                # Strip non-alphanumerics — "Hmm." / "Yes." stay, "...." is
                # treated as empty and retried like other transient failures.
                if not re.sub(r"[^0-9A-Za-z]", "", str(content)):
                    raise RuntimeError("LLM kembalikan konten kosong (overload/truncated?)")
                return content

            return _with_retry(_call, retries=max_retries)

        def stream(self, system, messages, model=None, max_tokens=None, fast=False,
                   session_id=None):
            extra = dict(self._extra() or {})
            if fast:
                bu = str(getattr(client, "base_url", "") or "")
                extra.update(_thinking_off_extra(bu) or {})
            kwargs = _chat_kwargs(
                model=model or s.llm_model, system=system, messages=messages,
                temperature=0.5, max_tokens=max_tokens, timeout=None,
                stream=True, extra_body=extra or None)
            if session_id:
                kwargs["extra_headers"] = {
                    "x-opencode-session": f"qora-{session_id}"}
            st = client.chat.completions.create(**kwargs)
            for ch in st:
                if not getattr(ch, "choices", None):
                    continue
                d = ch.choices[0].delta.content
                if d:
                    yield d

    return _OAI()


def _anthropic():  # pragma: no cover - butuh SDK + key
    s = get_settings()
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    client = Anthropic(api_key=s.llm_api_key)

    class _Anth:
        def generate(self, system, messages, model=None, max_tokens=None, temperature=None,
                     timeout=None, max_retries=None):
            kwargs = dict(
                model=model or s.llm_model, system=system,
                max_tokens=max_tokens or 1024,
                messages=messages, temperature=0.5 if temperature is None else temperature,
            )
            if timeout is not None:
                kwargs["timeout"] = timeout
            r = client.messages.create(**kwargs)
            return "".join(b.text for b in r.content if b.type == "text")

        def stream(self, system, messages, model=None, max_tokens=None):
            with client.messages.stream(
                model=model or s.llm_model, system=system,
                max_tokens=max_tokens or 1024,
                messages=messages, temperature=0.5,
            ) as st:
                yield from st.text_stream

    return _Anth()


def _build_client() -> LlmClient:
    s = get_settings()
    if not s.llm_api_key:
        return StubLlmClient()
    provider = (s.llm_provider or "").lower()
    if provider == "openrouter":
        return _openai_compatible(s.llm_base_url) or StubLlmClient()
    if provider == "openai":
        return _openai_compatible(None) or StubLlmClient()
    if provider == "anthropic":
        return _anthropic() or StubLlmClient()
    return StubLlmClient()


_client: LlmClient | None = None


def get_llm_client() -> LlmClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def is_stub() -> bool:
    return isinstance(get_llm_client(), StubLlmClient)


def _openai_async_compatible(base_url: str | None, sdk_retries: int | None = None,
                               api_key: str | None = None,
                               default_model: str | None = None):
    """OpenRouter & OpenAI via async SDK. One persistent client per worker,
    opened at lifespan startup and closed at shutdown (§7.1a).

    Phase-1: `sdk_retries` — see `_openai_compatible`. The patient provider
    passes 0 (ADR §4.3 destack); every other caller leaves None (SDK
    default, historical behavior, judge untouched).
    """
    s = get_settings()
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return None
    headers = {}
    if s.llm_site_url:
        headers["HTTP-Referer"] = s.llm_site_url
    if s.llm_app_title:
        headers["X-Title"] = s.llm_app_title
    headers = _gateway_headers(base_url, headers)
    _cli_kwargs: dict = {
        "api_key": api_key if api_key is not None else s.llm_api_key,
        "base_url": base_url or None,
        "default_headers": headers or None,
        "timeout": 120.0,
    }
    if sdk_retries is not None:
        _cli_kwargs["max_retries"] = sdk_retries
    aclient = AsyncOpenAI(**_cli_kwargs)

    def _content_guard(content) -> str:
        content = content or ""
        if not re.sub(r"[^0-9A-Za-z]", "", str(content)):
            raise RuntimeError("LLM kembalikan konten kosong (overload/truncated?)")
        return content

    class _OAI_ASYNC:
        _sdk = aclient
        # Phase-1: patient provider may override the default model (None =
        # historical s.llm_model). Explicit per-call `model=` still wins.
        _default_model = default_model

        @staticmethod
        def _extra():
            try:
                bu = str(getattr(aclient, "base_url", "") or "")
                return _openrouter_extra(bu)
            except Exception:  # noqa: BLE001
                pass
            return None

        async def agenerate(self, system, messages, model=None, max_tokens=None,
                            temperature=None, timeout=None, max_retries=None, fast=False,
                            session_id=None):
            async def _call():
                extra = dict(self._extra() or {})
                if fast:
                    bu = str(getattr(aclient, "base_url", "") or "")
                    extra.update(_thinking_off_extra(bu) or {})
                kwargs = _chat_kwargs(
                    model=model or self._default_model or s.llm_model,
                    system=system, messages=messages,
                    temperature=0.5 if temperature is None else temperature,
                    max_tokens=max_tokens, timeout=timeout, stream=False,
                    extra_body=extra or None)
                if session_id:
                    kwargs["extra_headers"] = {
                        "x-opencode-session": f"qora-{session_id}"}
                r = await aclient.chat.completions.create(**kwargs)
                if not getattr(r, "choices", None):
                    raise RuntimeError(
                        f"LLM tanpa choices: {str(getattr(r, 'error', None) or repr(r))[:200]}"
                    )
                msg = r.choices[0].message
                return _content_guard(msg.content)

            return await _with_retry_async(_call, retries=max_retries)

        async def astream(self, system, messages, model=None, max_tokens=None, fast=False,
                          session_id=None):
            extra = dict(self._extra() or {})
            if fast:
                bu = str(getattr(aclient, "base_url", "") or "")
                extra.update(_thinking_off_extra(bu) or {})
            kwargs = _chat_kwargs(
                model=model or self._default_model or s.llm_model,
                system=system, messages=messages,
                temperature=0.5, max_tokens=max_tokens, timeout=None,
                stream=True, extra_body=extra or None)
            if session_id:
                kwargs["extra_headers"] = {
                    "x-opencode-session": f"qora-{session_id}"}
            st = await aclient.chat.completions.create(**kwargs)
            try:
                async for ch in st:
                    if not getattr(ch, "choices", None):
                        continue
                    d = ch.choices[0].delta.content
                    if d:
                        yield d
            finally:
                # Release the upstream connection on normal end AND on
                # cancellation (Starlette cancels the generator) — §7.1k/l.
                aclose = getattr(st, "aclose", None)
                if aclose is not None:
                    try:
                        await aclose()
                    except Exception:  # noqa: BLE001 - cleanup must not fail
                        pass

    return _OAI_ASYNC()


def _build_async_client() -> AsyncLlmClient:
    s = get_settings()
    if not s.llm_api_key:
        return AsyncStubLlmClient()
    provider = (s.llm_provider or "").lower()
    if provider == "openrouter":
        return _openai_async_compatible(s.llm_base_url) or AsyncStubLlmClient()
    if provider == "openai":
        return _openai_async_compatible(None) or AsyncStubLlmClient()
    return AsyncStubLlmClient()


_async_client: AsyncLlmClient | None = None


def get_async_llm_client() -> AsyncLlmClient:
    """Per-worker persistent async client (lifespan opens it eagerly)."""
    global _async_client
    if _async_client is None:
        _async_client = _build_async_client()
    return _async_client


async def open_async_llm() -> None:
    """Lifespan startup: build the async client outside request path."""
    get_async_llm_client()


async def close_async_llm() -> None:
    """Lifespan shutdown: close the persistent HTTP transport (§7.1a)."""
    global _async_client
    client, _async_client = _async_client, None
    sdk = getattr(client, "_sdk", None)
    close = getattr(sdk, "close", None)
    if close is not None:
        try:
            result = close()
            if asyncio.iscoroutine(result):
                await result
        except Exception:  # noqa: BLE001 - shutdown must not fail
            pass


def is_async_stub() -> bool:
    return isinstance(get_async_llm_client(), AsyncStubLlmClient)
