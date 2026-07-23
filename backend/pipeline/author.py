"""AI case-authoring pipeline (BUILD_PLAN_pivot_v4 §5.3) — the P3 breadth engine.

Drafts a COMPLETE, schema-valid case (frontmatter + persona body) from a
(specialty, presentation, target_condition, difficulty) tuple, then self-corrects
against the linter. The author model is configurable (AUTHOR_MODEL); a real key is
required (StubLLM cannot author clinical content).

Pure prompt-building lives here (testable without a key); `tools/author_case.py`
is the CLI that calls the model, writes files, and runs the lint loop.
"""
from __future__ import annotations

import re

from app.config import get_settings
from app.rag.llm import get_llm_client, is_stub
from pipeline.case_v2 import MODES, SPECIALTIES, lint, parse_string

# Static schema spec (literal braces — NOT a format template, to avoid colliding
# with the YAML inline-dict braces below).
_SCHEMA_SPEC = """Output a COMPLETE case file: a YAML frontmatter block between `---` lines,
then a markdown persona body. NOTHING else (no commentary, no code fences).

FRONTMATTER (Part A — hidden scoring ground truth, NEVER shown to the patient):
  id: <id from TARGET>
  schema_version: 2
  status: in_review
  specialty: <specialty from TARGET>
  system: <body system, lowercase>
  presentation: "<presentation from TARGET>"
  target_condition: "<target_condition from TARGET>"
  difficulty: <integer 1..5 from TARGET>
  estimated_minutes: <int>
  mode_default: <mode from TARGET>
  languages: [en]
  source_refs: [ "<authoritative guideline used>" ]
  authoring: { drafted_by: ai_v1, model: "<author model>", reviewed_by: null, reviewed_at: null, review_notes: null }
  chief_complaint: "<one lay sentence>"
  anamnesis_checklist:        # items the student should ELICIT; each { item, critical }
    hpi_socrates: [ ... ]     # >=1 item critical: true somewhere in the whole checklist
    associated_symptoms: [ ... ]
    pmh: [ ... ]
    medications: [ ... ]
    family_social: [ ... ]
    ice_fife:                 # REQUIRED, non-empty
      - { item: "Ideas - what they think is wrong", critical: true }
      - { item: "Concerns - what worries them", critical: true }
      - { item: "Expectations - what they hope for", critical: false }
  red_flags:                  # non-empty, >=1 critical: true; clinical screening labels
    - { item: "<must-screen red flag>", critical: true }
  expected_ddx:
    working_diagnosis: "<target_condition>"
    differentials: [ "<dx>", "<dx>" ]   # >=2
  investigations:             # REQUIRED if mode_default is osce_full
    appropriate: [ { name: "<test>", expected: "<expected result>" } ]
    inappropriate: [ "<low-value test>" ]
  physical_exam_findings: { general: "...", vitals: {} }
  management:
    pharmacological: [ ... ]
    non_pharmacological: [ ... ]
    education_safety_netting: [ ... ]
  scoring_weights_override: null

PERSONA BODY (Part B — markdown, this is ALL the patient model sees). Required H2 sections:
  ## Identity                 (THOROUGH: full name, age, occupation, family, personality traits, fears, quirks — make them feel like a real person, not a template)
  ## Opening line             (one verbatim first line, lay words)
  ## How I present            (physical demeanour: posture, voice, eye contact, emotional state visible on their face)
  ## What I know              (the facts to disclose ONLY when asked, structured as bullet points)
  ## Communication profile    (education level, vocabulary, tendency to ramble/be terse, emotional tone)
  ## Disclosure rules         (answer restraint: answer only what is asked, then stop)

HARD RULES:
- Lay language only in the body. The patient does NOT know medical terms or their diagnosis.
- The body must NOT contain: the working diagnosis text, the word "differential",
  ICD codes, or any frontmatter/scoring/checklist structure (leakage = fail).
- Internal consistency: every checklist item that expects a patient answer must have
  a matching fact in "## What I know".
- English. Clinically accurate per standard references."""


def build_author_prompt(case_id: str, specialty: str, presentation: str,
                        target_condition: str, difficulty: int, mode: str,
                        reference_text: str = "") -> tuple[str, list[dict]]:
    system = (
        "You are a medical educator authoring a virtual-patient anamnesis case "
        "for a study-aid trainer. You write clinically accurate cases with a "
        "realistic lay-patient persona that practises strict answer restraint. "
        "Follow the schema EXACTLY so an automated linter passes."
    )
    target = (
        "TARGET:\n"
        f"  id: {case_id}\n"
        f"  specialty: {specialty}\n"
        f"  presentation: {presentation}\n"
        f"  target_condition: {target_condition}\n"
        f"  difficulty: {difficulty}\n"
        f"  mode_default: {mode}\n"
        f"  author model: {get_settings().llm_author_model or get_settings().llm_model}\n"
        "Use EXACTLY these values in the frontmatter.\n\n"
    )
    user = target + _SCHEMA_SPEC
    if reference_text.strip():
        user += f"\n\nREFERENCE MATERIAL (ground your clinical facts in this):\n{reference_text.strip()}"
    return system, [{"role": "user", "content": user}]


def extract_case_markdown(raw: str) -> str:
    """Strip accidental code fences / commentary around the case."""
    text = raw.strip()
    fence = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    idx = text.find("---")
    return text[idx:].strip() if idx > 0 else text


def validate_inputs(specialty: str, mode: str) -> list[str]:
    errs = []
    if specialty not in SPECIALTIES:
        errs.append(f"specialty '{specialty}' not in controlled vocab")
    if mode not in MODES:
        errs.append(f"mode '{mode}' not in {sorted(MODES)}")
    return errs


def draft_case(case_id: str, specialty: str, presentation: str,
               target_condition: str, difficulty: int, mode: str,
               reference_text: str = "", fix_errors: list[str] | None = None) -> str:
    """Call the author model once; return the case markdown. Raises if StubLLM
    (cannot author clinical content without a real key)."""
    if is_stub():
        raise RuntimeError(
            "AUTHOR_MODEL key required: set LLM_API_KEY (+ AUTHOR_MODEL) in .env. "
            "StubLLM cannot author clinical content."
        )
    system, messages = build_author_prompt(
        case_id, specialty, presentation, target_condition, difficulty, mode, reference_text
    )
    if fix_errors:
        messages[0]["content"] += (
            "\n\nThe previous draft FAILED the linter with these errors — fix them all "
            "and re-output the full corrected case:\n- " + "\n- ".join(fix_errors)
        )
    raw = get_llm_client().generate(
        system, messages,
        model=get_settings().llm_author_model or get_settings().llm_model,
        max_tokens=4000,
        temperature=0.4,
    )
    return extract_case_markdown(raw)


def lint_markdown(markdown: str):
    """Parse + lint an in-memory case markdown string. Returns (CaseV2, LintResult)."""
    case = parse_string(markdown, fallback_id="draft")
    return case, lint(case)
