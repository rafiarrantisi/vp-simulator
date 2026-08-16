"""Schema-v2 patient engine (pivot-v4 §5.2) — parallel to the legacy RAG engine.

Patient context = Part B persona body + answer-restraint scaffold ONLY (via
prompt_v2.build_patient_prompt). Part A frontmatter NEVER enters the patient
context — the structural P1 guarantee. Reuses the legacy sliding-window message
builder for conversation memory.

Supports multilingual responses: the patient answers in the session's selected
language via the `language` parameter (defaults to English).
"""
from __future__ import annotations

from collections.abc import Iterator

from app.config import get_settings
from app.domains.cases.v2_catalog import load_v2_case
from app.rag.llm import get_llm_client
from app.rag.prompt import build_messages, is_first_turn
from app.rag.prompt_v2 import build_patient_prompt


def _prepare(case_id: str, history: list[dict], user_message: str,
             language: str = "en"):
    case = load_v2_case(case_id)  # raises FileNotFoundError if absent
    # Returning-patient cases declare `continuity:` frontmatter (PRD §4.3.4) —
    # the only frontmatter the patient prompt is allowed to see.
    continuity = case.frontmatter.get("continuity") if hasattr(case, "frontmatter") else None
    system = build_patient_prompt(case, is_first_turn=is_first_turn(history),
                                  language=language, continuity_context=continuity)
    messages = build_messages(history, user_message)
    return system, messages


def respond(case_id: str, history: list[dict], user_message: str,
            language: str = "en") -> str:
    system, messages = _prepare(case_id, history, user_message, language=language)
    return get_llm_client().generate(
        system, messages, max_tokens=get_settings().llm_persona_max_tokens
    ).strip()


def stream_respond(case_id: str, history: list[dict], user_message: str,
                   language: str = "en") -> Iterator[str]:
    system, messages = _prepare(case_id, history, user_message, language=language)
    yield from get_llm_client().stream(
        system, messages, max_tokens=get_settings().llm_persona_max_tokens
    )
