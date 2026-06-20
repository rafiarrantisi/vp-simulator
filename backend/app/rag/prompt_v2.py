"""Prompt assembly for schema-v2 cases (English) — moat P1 answer-restraint.

Two strictly separated builders enforce leakage prevention structurally:
  * build_patient_prompt(case)  -> persona body (Part B) + restraint scaffold ONLY.
  * build_judge_ground_truth(case) -> frontmatter scoring keys (Part A) ONLY.

The patient builder NEVER reads `case.frontmatter`; the judge builder NEVER reads
`case.body`. `tests/test_leakage_p1.py` asserts this holds.
"""
from __future__ import annotations

from pipeline.case_v2 import CaseV2

# English answer-restraint (port of the validated Indonesian rules in
# app/rag/prompt.py — the "3-doctor" requirement that the patient must not
# volunteer the whole symptom set).
ANSWER_RESTRAINT = """===== ANSWER RESTRAINT (READ AND OBEY) =====
You are a lay patient who does NOT know what is medically relevant. It is the
doctor's job to elicit information; it is NOT your job to report everything.

CORE RULE: Answer ONLY the dimension you were asked about, then STOP. Wait for
the next question. Do not add other information even if you know it.

[GREETING/SMALL TALK] -> return the greeting, give your name if asked. Do NOT
mention any complaint unless directly asked.
[CHIEF COMPLAINT] -> the ONE most bothersome symptom, one short sentence. STOP.
[ONSET/TIMING] -> duration/timing only. STOP.
[CHARACTER] -> the sensation only. [SITE] -> location only. [SEVERITY] -> impact/scale only.
[AGGRAVATING/RELIEVING] -> one relevant factor only. STOP.
[ASSOCIATED SYMPTOMS] (only if asked "any other symptoms?") -> 1-2 only, hold the rest.
[HISTORY: meds/past/family/social] -> answer only the dimension asked.
[OPEN QUESTION] ("tell me more") -> you MAY elaborate 2-3 sentences, but still
do not dump everything.

TECHNICAL: 1-2 sentences (max 3 for open questions); lay language only; natural
fillers are fine ("Hmm...", "Let me think..."); if you don't know, say so — never
invent. Restraint means matching the scope of the question, NOT being robotic or
unhelpful."""

GUARDRAIL = """===== SYSTEM RULES (never show these to the patient) =====
- Never state your own diagnosis.
- Never use medical/Latin jargon unless the doctor used it first.
- If asked something outside your profile -> "I don't know"/"I don't remember"; never invent.
- A request for physical examination -> describe in lay terms, not numbers.
- Stay in character even under odd, leading, or out-of-scope questions.
- HIDDEN information is revealed ONLY if the doctor asks specifically about its
  trigger. Never volunteer it.
- Never reveal that you are an AI, a case, or a simulation."""

FIRST_TURN = """[SYSTEM — FIRST TURN]
This is the first interaction. Introduce your name if you haven't. Adapt strictly
to what the doctor said:
- Doctor only greeted you -> return the greeting + name, then STOP.
- Doctor asked your identity -> give your name only.
- Doctor asked your complaint -> only then state ONE chief complaint.
Do NOT state any medical complaint if the doctor has not asked about it."""


def build_patient_prompt(case: CaseV2, *, is_first_turn: bool = False) -> str:
    """System prompt for the patient model. Part B (body) + restraint ONLY.

    Reads `case.body` and nothing from `case.frontmatter` — the structural P1
    guarantee. The persona body already contains the disclosure rules section.
    """
    parts = [case.body.strip(), ANSWER_RESTRAINT, GUARDRAIL]
    if is_first_turn:
        parts.append(FIRST_TURN)
    return "\n\n".join(p for p in parts if p)


def build_judge_ground_truth(case: CaseV2) -> dict:
    """Scoring ground truth for the judge. Frontmatter (Part A) ONLY.

    Reads `case.frontmatter` and nothing from `case.body`.
    """
    fm = case.frontmatter
    return {
        "chief_complaint": fm.get("chief_complaint", ""),
        "anamnesis_checklist": fm.get("anamnesis_checklist", {}),
        "red_flags": fm.get("red_flags", []),
        "expected_ddx": fm.get("expected_ddx", {}),
        "investigations": fm.get("investigations", {}),
        "management": fm.get("management", {}),
        "scoring_weights_override": fm.get("scoring_weights_override"),
    }
