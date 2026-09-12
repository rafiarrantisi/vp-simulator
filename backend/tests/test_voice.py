"""Fase 4 voice endpoints — cek deterministik & offline (tanpa panggil
provider STT nyata; uji STT live = probe terpisah, lihat ringkasan)."""
import io

from fastapi.testclient import TestClient

from app.domains.ai.router import _DEDUP_WINDOW, _is_dup
from app.main import app

client = TestClient(app)


def _token() -> str:
    client.post("/api/auth/signup", json={
        "email": "voice@uni.ac.id", "password": "secret12", "full_name": "V",
    })
    return client.post("/api/auth/login", json={
        "email": "voice@uni.ac.id", "password": "secret12",
    }).json()["data"]["token"]


def test_transcribe_requires_auth():
    r = client.post("/api/ai/transcribe",
                     files={"audio": ("a.webm", b"x", "audio/webm")})
    assert r.status_code == 401


def test_transcribe_empty_audio_400():
    h = {"Authorization": f"Bearer {_token()}"}
    r = client.post("/api/ai/transcribe", headers=h,
                     files={"audio": ("a.webm", b"", "audio/webm")})
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_dedup_guard_logic():
    hsh = "deadbeef" * 4
    assert _is_dup(hsh) is False          # pertama → bukan duplikat
    assert _is_dup(hsh) is True           # ulang dalam window → duplikat
    assert _DEDUP_WINDOW == 5.0


def test_tts_not_configured_bad_provider(monkeypatch):
    # Deterministik & env-independent: provider tak dikenal → TtsNotConfigured.
    import app.voice.tts as tts_mod

    class _S:
        tts_provider = "elevenlabs"
        tts_gemini_model = "gemini-3.1-flash-tts-preview"
        tts_gemini_voice = "Gacrux"
        tts_gemini_language = "id-ID"

    monkeypatch.setattr(tts_mod, "get_settings", lambda: _S())
    import pytest
    with pytest.raises(tts_mod.TtsNotConfigured):
        tts_mod.synthesize("Halo")


def test_tts_empty_text_fails():
    # Teks kosong ditolak sebelum request (tidak bakar credit).
    import app.voice.tts as tts_mod
    import pytest
    with pytest.raises(tts_mod.TtsFailed):
        tts_mod.synthesize("   ")


def test_tts_endpoint_degrades_cleanly():
    # Tanpa ADC → 501 + envelope rapi. Dengan ADC/live → 200 audio/mpeg,
    # atau 502 + error jelas. Apa pun: tidak crash, envelope rapi.
    h = {"Authorization": f"Bearer {_token()}"}
    r = client.post("/api/ai/tts", headers=h, json={"text": "Halo"})
    if r.status_code == 501:
        assert r.json().get("error")
    else:
        assert r.status_code == 200 or (
            r.headers.get("content-type", "").startswith("application/json")
            and r.json().get("error")
        )


def test_tts_requires_auth():
    assert client.post("/api/ai/tts", json={"text": "Halo"}).status_code == 401


def test_tts_stream_validates_input():
    h = {"Authorization": f"Bearer {_token()}"}
    r = client.post("/api/ai/tts/stream", headers=h,
                    json={"text": "", "session_id": "nope"})
    assert r.status_code == 400
    r = client.post("/api/ai/tts/stream", headers=h,
                    json={"text": "Halo", "session_id": "no-such-session"})
    assert r.status_code == 404
    r = client.post("/api/ai/tts/stream", headers=h,
                    json={"text": "x" * 2001, "session_id": "nope"})
    assert r.status_code == 413


def test_tts_stream_no_auth():
    assert client.post("/api/ai/tts/stream",
                       json={"text": "Halo", "session_id": "x"}).status_code == 401


def test_tts_client_cache_name_separation():
    # Regression: module-global cache var must never be rebound by the
    # factory def (that made _client() return itself -> every TTS call 502).
    import inspect

    import app.voice.tts as tts_mod
    assert inspect.isfunction(tts_mod._get_client)
    assert not callable(tts_mod._cached_client)
