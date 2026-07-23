"""STT — Whisper via endpoint OpenAI-compatible (Fase 4, kontrak v0.8.0).

Default base+key = OpenRouter (sama spt LLM). CAVEAT: OpenRouter router
LLM-chat; bila tak dukung /audio/transcriptions → set STT_BASE_URL ke
endpoint Whisper OpenAI-compatible lain (mis. Groq). Provider-agnostic.
"""
from __future__ import annotations

from app.config import get_settings

# Seed the transcriber with medical vocabulary → better accuracy on specialist
# terms (voice-plan §6). Language-aware: the product pivoted to English, so the
# prompt tracks STT_LANGUAGE (app-level localization, not model/provider config).
_MEDICAL_PROMPT_ID = (
    "Percakapan dokter dan pasien dalam bahasa Indonesia. Istilah medis: "
    "anamnesis, konjungtivitis, glaukoma, blefaritis, keratitis, uveitis, "
    "visus, tonometri, slit lamp, funduskopi, preaurikular, fotofobia."
)
_MEDICAL_PROMPT_EN = (
    "A doctor-and-patient clinical interview in English. Medical terms may include: "
    "history taking, palpitations, dyspnoea, haemoptysis, syncope, paraesthesia, "
    "photophobia, auscultation, differential diagnosis, safety-netting."
)


def _medical_prompt(language: str) -> str:
    return _MEDICAL_PROMPT_EN if (language or "").lower().startswith("en") else _MEDICAL_PROMPT_ID


class SttUnavailable(RuntimeError):
    pass


def is_configured() -> bool:
    """True when STT can be attempted (a key is present)."""
    return bool(get_settings().stt_key())


def transcribe(audio_bytes: bytes, filename: str = "speech.webm") -> str:
    s = get_settings()
    key = s.stt_key()
    if not key:
        raise SttUnavailable("STT belum dikonfigurasi (STT/LLM API key kosong)")
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise SttUnavailable(f"SDK openai tak tersedia: {e}") from e
    try:
        client = OpenAI(api_key=key, base_url=s.stt_base() or None)
        r = client.audio.transcriptions.create(
            model=s.stt_model,
            file=(filename, audio_bytes, "application/octet-stream"),
            language=s.stt_language,
            prompt=_medical_prompt(s.stt_language),
            temperature=0.0,
        )
        return (getattr(r, "text", None) or "").strip()
    except Exception as e:  # provider tak dukung audio / error jaringan
        raise SttUnavailable(
            f"Transkripsi gagal di {s.stt_base()}: {e}. "
            f"Jika OpenRouter tak dukung audio, set STT_BASE_URL ke endpoint "
            f"Whisper OpenAI-compatible (mis. Groq)."
        ) from e
