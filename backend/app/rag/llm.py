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
                        max_retries: int | None = None) -> str:
        return StubLlmClient().generate(
            system, messages, model=model, max_tokens=max_tokens,
            temperature=temperature, timeout=timeout, max_retries=max_retries)

    async def astream(self, system: str, messages: list[dict],
                      model: str | None = None,
                      max_tokens: int | None = None) -> AsyncIterator[str]:
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
                 max_retries: int | None = None) -> str:
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
               max_tokens: int | None = None) -> Iterator[str]:
        for tok in self.generate(system, messages).split(" "):
            yield tok + " "


def _openai_compatible(base_url: str | None):
    """OpenRouter & OpenAI sama-sama pakai SDK `openai`."""
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
    client = OpenAI(
        api_key=s.llm_api_key,
        base_url=base_url or None,
        default_headers=headers or None,
        timeout=120.0,  # judge/patient calls must not hang the UI forever
    )

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
                     timeout=None, max_retries=None):
            def _call():
                kwargs = _chat_kwargs(
                    model=model or s.llm_model, system=system, messages=messages,
                    temperature=0.5 if temperature is None else temperature,
                    max_tokens=max_tokens, timeout=timeout, stream=False,
                    extra_body=self._extra())
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

        def stream(self, system, messages, model=None, max_tokens=None):
            kwargs = _chat_kwargs(
                model=model or s.llm_model, system=system, messages=messages,
                temperature=0.5, max_tokens=max_tokens, timeout=None,
                stream=True, extra_body=self._extra())
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


def _openai_async_compatible(base_url: str | None):
    """OpenRouter & OpenAI via async SDK. One persistent client per worker,
    opened at lifespan startup and closed at shutdown (§7.1a)."""
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
    aclient = AsyncOpenAI(
        api_key=s.llm_api_key,
        base_url=base_url or None,
        default_headers=headers or None,
        timeout=120.0,
    )

    def _content_guard(content) -> str:
        content = content or ""
        if not re.sub(r"[^0-9A-Za-z]", "", str(content)):
            raise RuntimeError("LLM kembalikan konten kosong (overload/truncated?)")
        return content

    class _OAI_ASYNC:
        _sdk = aclient

        @staticmethod
        def _extra():
            try:
                bu = str(getattr(aclient, "base_url", "") or "")
                return _openrouter_extra(bu)
            except Exception:  # noqa: BLE001
                pass
            return None

        async def agenerate(self, system, messages, model=None, max_tokens=None,
                            temperature=None, timeout=None, max_retries=None):
            async def _call():
                kwargs = _chat_kwargs(
                    model=model or s.llm_model, system=system, messages=messages,
                    temperature=0.5 if temperature is None else temperature,
                    max_tokens=max_tokens, timeout=timeout, stream=False,
                    extra_body=self._extra())
                r = await aclient.chat.completions.create(**kwargs)
                if not getattr(r, "choices", None):
                    raise RuntimeError(
                        f"LLM tanpa choices: {str(getattr(r, 'error', None) or repr(r))[:200]}"
                    )
                msg = r.choices[0].message
                return _content_guard(msg.content)

            return await _with_retry_async(_call, retries=max_retries)

        async def astream(self, system, messages, model=None, max_tokens=None):
            kwargs = _chat_kwargs(
                model=model or s.llm_model, system=system, messages=messages,
                temperature=0.5, max_tokens=max_tokens, timeout=None,
                stream=True, extra_body=self._extra())
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
