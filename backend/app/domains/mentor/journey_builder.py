"""Qora Mentor — journey builder LLM pipeline (PRD_QORA_MENTOR §4.1.1, §4.1.2).

story → extracted context (JSON) → case selection → proposal (JSON).

Design rules:
- Uses `settings.llm_model` (deepseek/deepseek-v4-flash in prod; reasoning is
  disabled inside LlmClient for OpenRouter).
- Every LLM output is validated + clamped server-side; the server NEVER trusts
  the model's case ids or day assignments — the LLM enriches the deterministic
  selection, it does not replace it.
- No LLM key → StubLlmClient, and `extract_context` falls back to a
  deterministic keyword/heuristic parse so the whole flow is testable locally
  without paid API calls (Arran's constraint: don't burn paid API in dev).
"""
from __future__ import annotations

import json
import logging
import re

from app.config import get_settings
from app.rag.llm import get_llm_client

_log = logging.getLogger("mentor.journey_builder")

_CONTEXT_SYSTEM = """You are a medical education advisor for Indonesian medical students.
Extract learning context from the student's message. Return ONLY valid JSON,
no prose, no markdown fences:

{
  "timeline_days": 7 | 30 | 90 | null,
  "level": "preklinik" | "koas" | "ppds" | "general",
  "weaknesses": ["pediatrik", "bedah", ...],
  "goal": "osce" | "stase" | "general" | "mock_exam",
  "emotional_state": "panik" | "confident" | "overwhelmed" | "neutral",
  "special_needs": "string" | null,
  "confidence_score": 0-100
}

Rules:
- timeline_days: estimate from words like "besok" (1), "minggu" (7), "bulan" (30). null if unknown.
- level: default "koas" if unclear. "ppds" if resident/residen, "preklinik" if preclinical.
- weaknesses: list up to 3 specialty areas mentioned (Indonesian terms fine).
- confidence_score: self-reported confidence, 0-100 (low = anxious/bego)."""

_PROPOSAL_SYSTEM = """You are Qora Mentor, a supportive medical education advisor for Indonesian medical students.
Create a personalized learning journey proposal from the selected cases.

Rules:
1. Empathetic but professional — the student may be anxious.
2. Explain your reasoning: the student should understand WHY this sequence helps.
3. Use Indonesian medical education context (UKNPDPD, koas, stase, OSCE).
4. Keep focus labels and learning objectives in Indonesian, concise.
5. Return ONLY valid JSON, no prose, no markdown fences:

{
  "package_name": "string (e.g. 'Pediatrik Crash 7-Day')",
  "cases": [
    {"day": 1, "case_id": "...", "focus": "Anamnesis dasar anak",
     "estimated_minutes": 45, "learning_objective": "..."}
  ],
  "reasoning": "Explain WHY this sequence helps the student",
  "readiness_start": 0-100,
  "readiness_target": 0-100,
  "milestones": [{"day": 3, "checkpoint": "..."}]
}

IMPORTANT: use EXACTLY the case_ids given in the selection. You may reorder
focus/objectives but never invent case ids."""


def _extract_json(text: str):
    """Parse the FIRST complete JSON object in `text` (same pattern as judge_v2)."""
    if not text:
        return None
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Deterministic fallbacks (no LLM needed) — keep the flow testable + resilient
# ---------------------------------------------------------------------------

_TIME_RE = [
    (re.compile(r"(\d+)\s*(?:hari|day)", re.I), 1),
    (re.compile(r"(\d+)\s*(?:minggu|week)", re.I), 7),
    (re.compile(r"(\d+)\s*(?:bulan|month)", re.I), 30),
]
_NAMED_TIME = [
    (re.compile(r"bulan\s+depan|next\s+month|sebulan", re.I), 30),
    (re.compile(r"minggu\s+depan|next\s+week|seminggu", re.I), 7),
    (re.compile(r"besok|tomorrow|hari\s+ini|tonight|malam\s+ini", re.I), 1),
]
_LEVEL_RE = [
    (re.compile(r"ppds|residen|resident|spesialis", re.I), "ppds"),
    (re.compile(r"preklinik|preclinical|pre-klinik|mahasiswa\s+awal", re.I), "preklinik"),
    (re.compile(r"koas|kepaniteraan|clinical\s+student|stase", re.I), "koas"),
]
_GOAL_RE = [
    (re.compile(r"osce|uknpdpd|ukom|mock|try\s+out", re.I), "osce"),
    (re.compile(r"stase|rotasi|clerk", re.I), "stase"),
]
_EMOTION_RE = [
    (re.compile(r"panik|takut|nervous|stres|stress|bego|bodoh|khawatir", re.I), "panik"),
    (re.compile(r"overwhelm|kebanyakan|banyak\s+banget|buntu", re.I), "overwhelmed"),
    (re.compile(r"pede|yakin|confident|siap", re.I), "confident"),
]


def _heuristic_context(user_story: str) -> dict:
    """Keyword-based context extraction — deterministic fallback."""
    days = None
    for rx, mult in _TIME_RE:
        m = rx.search(user_story)
        if m:
            days = max(1, min(90, int(m.group(1)) * mult))
            break
    if days is None:
        for rx, val in _NAMED_TIME:
            if rx.search(user_story):
                days = val
                break

    level = "koas"
    for rx, val in _LEVEL_RE:
        if rx.search(user_story):
            level = val
            break

    goal = "general"
    for rx, val in _GOAL_RE:
        if rx.search(user_story):
            goal = val
            break

    emotion = "neutral"
    for rx, val in _EMOTION_RE:
        if rx.search(user_story):
            emotion = val
            break

    from app.domains.mentor.case_selector import SPECIALTY_ALIASES
    weaknesses: list[str] = []
    lower = user_story.lower()
    for alias in sorted(SPECIALTY_ALIASES, key=len, reverse=True):
        if alias in lower:
            sid = SPECIALTY_ALIASES[alias]
            if sid not in weaknesses:
                weaknesses.append(sid)
        if len(weaknesses) >= 3:
            break

    return {
        "timeline_days": days,
        "level": level,
        "weaknesses": weaknesses,
        "goal": goal,
        "emotional_state": emotion,
        "special_needs": None,
        "confidence_score": 30 if emotion == "panik" else 50,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_context(user_story: str) -> dict:
    """Story → normalized context dict. LLM first, heuristic fallback on failure."""
    ctx = _heuristic_context(user_story)  # baseline (always available)
    try:
        client = get_llm_client()
        from app.rag.llm import is_stub
        if not is_stub():
            raw = client.generate(
                _CONTEXT_SYSTEM,
                [{"role": "user", "content": f"Student: \"{user_story}\""}],
                model=get_settings().llm_model,
                max_tokens=600,
                temperature=0.2,
            )
            data = _extract_json(raw)
            if data:
                ctx = _normalize_context(data, ctx)
    except Exception:  # noqa: BLE001 — LLM failure never blocks journey creation
        _log.warning("extract_context LLM failed; using heuristic: %s", _log_short(user_story))
    return ctx


def _log_short(s: str) -> str:
    return (s or "")[:60]


def _normalize_context(data: dict, fallback: dict) -> dict:
    """Validate + clamp LLM output; fall back per-field on garbage."""
    out = dict(fallback)

    days = data.get("timeline_days")
    if isinstance(days, (int, float)) and days is not None:
        out["timeline_days"] = max(1, min(90, int(days)))
    elif data.get("timeline_days") is None:
        out["timeline_days"] = None

    level = str(data.get("level") or "").lower()
    if level in ("preklinik", "koas", "ppds", "general"):
        out["level"] = level

    w = data.get("weaknesses")
    if isinstance(w, list) and w:
        from app.domains.mentor.case_selector import map_weaknesses
        mapped = map_weaknesses([str(x) for x in w])
        out["weaknesses"] = mapped or out["weaknesses"]

    goal = str(data.get("goal") or "").lower()
    if goal in ("osce", "stase", "general", "mock_exam"):
        out["goal"] = goal

    emo = str(data.get("emotional_state") or "").lower()
    if emo in ("panik", "confident", "overwhelmed", "neutral"):
        out["emotional_state"] = emo

    cs = data.get("confidence_score")
    if isinstance(cs, (int, float)) and cs is not None:
        out["confidence_score"] = max(0, min(100, int(cs)))

    sn = data.get("special_needs")
    if isinstance(sn, str) and sn.strip():
        out["special_needs"] = sn.strip()
    return out


def generate_proposal(context: dict, selected: list[dict]) -> dict:
    """Selected cases + context → enriched proposal dict.

    The server enforces the case list: `selected` (deterministic) is the
    source of truth for day/case_id; LLM only adds focus/objective/reasoning
    polish. Falls back to `build_fallback_proposal` on any failure.
    """
    from app.domains.mentor.case_selector import build_fallback_proposal

    base = build_fallback_proposal(context, selected)
    try:
        client = get_llm_client()
        from app.rag.llm import is_stub
        if is_stub():
            return base
        selection = [
            {"day": d["day"], "case_id": d["case_id"], "specialty": d.get("specialty"),
             "presentation": d.get("presentation"), "focus": d.get("focus_area"),
             "estimated_minutes": d.get("estimated_minutes")}
            for d in selected
        ]
        raw = client.generate(
            _PROPOSAL_SYSTEM,
            [{"role": "user", "content": json.dumps(
                {"context": context, "selected_cases": selection}, ensure_ascii=False)}],
            model=get_settings().llm_model,
            max_tokens=1600,
            temperature=0.4,
        )
        data = _extract_json(raw)
        if not data:
            return base
        return _normalize_proposal(data, base, selected)
    except Exception:  # noqa: BLE001
        _log.warning("generate_proposal LLM failed; using template fallback")
        return base


def _normalize_proposal(data: dict, base: dict, selected: list[dict]) -> dict:
    out = dict(base)
    name = str(data.get("package_name") or "").strip()
    if name:
        out["package_name"] = name

    reasoning = str(data.get("reasoning") or "").strip()
    if reasoning:
        out["reasoning"] = reasoning

    # Readiness numbers: clamp to [0,100]; target must be > start.
    rs = data.get("readiness_start")
    if isinstance(rs, (int, float)):
        out["readiness_start"] = max(0, min(100, int(rs)))
    rt = data.get("readiness_target")
    if isinstance(rt, (int, float)):
        out["readiness_target"] = max(0, min(100, int(rt)))
    if out["readiness_target"] <= out["readiness_start"]:
        out["readiness_target"] = min(95, out["readiness_start"] + 20)

    # Milestones: keep only valid {day, checkpoint} entries.
    ms = []
    for m in data.get("milestones") or []:
        if isinstance(m, dict) and isinstance(m.get("day"), (int, float)) and m.get("checkpoint"):
            ms.append({"day": max(1, min(out["duration_days"], int(m["day"]))),
                       "checkpoint": str(m["checkpoint"]).strip()})
    if ms:
        out["milestones"] = ms

    # Case enrichment: merge LLM focus/objective onto the ENFORCED selection.
    by_id = {}
    for c in data.get("cases") or []:
        if isinstance(c, dict):
            by_id[str(c.get("case_id"))] = c
    enriched = []
    for d in selected:
        c = by_id.get(d["case_id"], {})
        focus = str(c.get("focus") or "").strip() or d.get("focus_area")
        obj = str(c.get("learning_objective") or "").strip() or d.get("learning_objective")
        minutes = c.get("estimated_minutes")
        if not isinstance(minutes, (int, float)) or minutes <= 0:
            minutes = d.get("estimated_minutes", 45)
        enriched.append({**d, "focus_area": focus, "learning_objective": obj,
                         "estimated_minutes": int(minutes)})
    out["cases"] = enriched
    return out
