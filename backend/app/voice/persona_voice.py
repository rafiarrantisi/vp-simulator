"""Server-side patient voice resolution (presentation layer only).

The frontend NEVER chooses persona/voice/style: given a session it owns, the
backend resolves the card's voice_profile (V3 variant field, V2 `Voice
profile` section) and returns (voice_name, style_instruction, language).
Clinical content is untouched — this only decides HOW the reply sounds.
"""
from __future__ import annotations

from app.config import get_settings

DEFAULT_LANGUAGE = "id-ID"


def resolve_voice(session_row, db=None) -> tuple[str, str, str]:
    """(voice_name, style_instruction, language) for a session row.

    Never raises for unknown content: falls back to configured defaults.
    """
    s = get_settings()
    default = (s.tts_gemini_voice, "", s.tts_gemini_language or DEFAULT_LANGUAGE)
    try:
        case_id = (getattr(session_row, "case_id", "") or "")
        if case_id.startswith("fam_"):
            return _from_variant(session_row, db, default)
        return _from_v2_case(case_id, default)
    except Exception:  # noqa: BLE001 — voice must never break a turn
        return default


def _from_variant(session_row, db, default):
    try:
        from app.domains.sessions.v3_compat_service import _frozen_variant
    except Exception:  # noqa: BLE001
        return default
    close = False
    if db is None:
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            close = True
        except Exception:  # noqa: BLE001
            return default
    try:
        _, v = _frozen_variant(db, session_row)
    except Exception:  # noqa: BLE001
        return default
    finally:
        if close:
            try:
                db.close()
            except Exception:  # noqa: BLE001
                pass
    if v is None:
        return default
    vp = getattr(v, "voice_profile", None) or {}
    if not isinstance(vp, dict):
        return default
    voice = str(vp.get("voice_name") or "").strip()
    if not voice:
        return default
    style = str(vp.get("style_instruction") or "").strip()
    lang = str(vp.get("language_code") or "").strip() or default[2]
    return voice, style, lang


def _from_v2_case(case_id: str, default):
    import re

    try:
        from app.domains.cases.v2_catalog import load_v2_case
        case = load_v2_case(case_id)
        sec = case.find_section("voice profile")
    except Exception:  # noqa: BLE001
        return default
    if not sec:
        return default
    voice = ""
    m = re.search(r"Voice:\s*([A-Za-z]+)", sec)
    if m:
        voice = m.group(1)
    if not voice:
        return default
    style = ""
    m = re.search(r"Style:\s*(.+)", sec, re.S)
    if m:
        style = " ".join(m.group(1).split())
        style = re.split(r"\bTraits:", style)[0].strip()
    lang = default[2]
    m = re.search(r"\(([a-z]{2}-[A-Z]{2})\)", sec)
    if m:
        lang = m.group(1)
    return voice, style, lang
