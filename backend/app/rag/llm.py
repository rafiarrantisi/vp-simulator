"""LlmClient — abstraksi provider (kontrak §9 K2).

Default OpenRouter (OpenAI-compatible; satu key, banyak model `vendor/model`).
Tanpa `LLM_API_KEY` → `StubLlmClient` deterministik (pipeline tetap bisa
diverifikasi tanpa kredensial). SDK di-import lazy.

`generate`/`stream` menerima `model` opsional: default = model persona
(`settings.llm_model`, kuat); evaluator memakai `settings.llm_judge_model`
(murah, rag-plan §9.1) → pisah judge vs persona.
"""
from __future__ import annotations

import re
import time
from collections.abc import Iterator
from typing import Protocol

from app.config import get_settings

_RETRY = 3  # backoff utk 5xx/timeout (free tier sering flaky)


def _with_retry(fn):
    last = None
    for i in range(_RETRY):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - retry transient apa pun
            last = e
            msg = str(e).lower()
            transient = any(
                k in msg for k in ("timeout", "502", "503", "504", "rate", "overload")
            )
            if not transient or i == _RETRY - 1:
                raise
            time.sleep(1.5 * (i + 1))
    raise last  # pragma: no cover


class LlmClient(Protocol):
    def stream(self, system: str, messages: list[dict],
               model: str | None = None,
               max_tokens: int | None = None) -> Iterator[str]: ...

    def generate(self, system: str, messages: list[dict],
                 model: str | None = None,
                 max_tokens: int | None = None,
                 temperature: float | None = None) -> str: ...


class StubLlmClient:
    """Deterministik, ditandai jelas. BUKAN untuk evaluasi klinis —
    hanya membuktikan pipeline (prompt assembly, retrieval, streaming)."""

    PREFIX = "[STUB LLM] "

    def generate(self, system: str, messages: list[dict],
                 model: str | None = None,
                 max_tokens: int | None = None,
                 temperature: float | None = None) -> str:
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
                if "openrouter" in bu:
                    return {"reasoning": {"enabled": False}}
            except Exception:  # noqa: BLE001
                pass
            return None

        def generate(self, system, messages, model=None, max_tokens=None, temperature=None):
            def _call():
                kwargs = {
                    "model": model or s.llm_model,
                    "messages": [{"role": "system", "content": system}, *messages],
                    "temperature": 0.5 if temperature is None else temperature,
                }
                if max_tokens is not None:
                    kwargs["max_tokens"] = max_tokens
                extra = self._extra()
                if extra:
                    kwargs["extra_body"] = extra
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

            return _with_retry(_call)

        def stream(self, system, messages, model=None, max_tokens=None):
            kwargs = {
                "model": model or s.llm_model,
                "messages": [{"role": "system", "content": system}, *messages],
                "temperature": 0.5,
                "stream": True,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            extra = self._extra()
            if extra:
                kwargs["extra_body"] = extra
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
        def generate(self, system, messages, model=None, max_tokens=None, temperature=None):
            r = client.messages.create(
                model=model or s.llm_model, system=system,
                max_tokens=max_tokens or 1024,
                messages=messages, temperature=0.5 if temperature is None else temperature,
            )
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
