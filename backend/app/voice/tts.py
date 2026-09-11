"""TTS — Google Cloud Gemini TTS (Cloud Text-to-Speech API).

Env-driven, Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS
points at the service-account JSON; set for the worker process, never in Git
or .env). No keys in code. Return audio mp3 bytes.

Style control is the reason for this provider: `style` steers delivery
(age, affect, pace) via the model prompt; text stays pure content.
"""
from __future__ import annotations

from app.config import get_settings

DEFAULT_STYLE = (
    "Speak in a calm, neutral way, like a patient plainly describing "
    "a symptom. Normal pace. Speak in Indonesian."
)


class TtsNotConfigured(RuntimeError):
    pass


class TtsFailed(RuntimeError):
    pass


def _client():
    try:
        from google.cloud import texttospeech
    except ImportError as e:
        raise TtsNotConfigured(
            "google-cloud-texttospeech belum terinstal "
            "(pip install google-cloud-texttospeech>=2.29)"
        ) from e
    try:
        return texttospeech.TextToSpeechClient()
    except Exception as e:  # noqa: BLE001 — mis. ADC file hilang
        raise TtsNotConfigured(f"Google TTS auth gagal: {e}") from e


def synthesize(text: str, style: str | None = None) -> bytes:
    s = get_settings()
    if s.tts_provider != "gemini":
        raise TtsNotConfigured(f"TTS provider '{s.tts_provider}' belum didukung")
    if not (text or "").strip():
        raise TtsFailed("Teks kosong")
    from google.cloud import texttospeech

    client = _client()
    try:
        resp = client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=text, prompt=style or DEFAULT_STYLE),
            voice=texttospeech.VoiceSelectionParams(
                language_code=s.tts_gemini_language,
                name=s.tts_gemini_voice,
                model_name=s.tts_gemini_model,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3),
            timeout=60.0,
        )
    except Exception as e:  # noqa: BLE001
        raise TtsFailed(f"Google TTS gagal: {type(e).__name__}: {str(e)[:200]}") from e
    return bytes(resp.audio_content)
