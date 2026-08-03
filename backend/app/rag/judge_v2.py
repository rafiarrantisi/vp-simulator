"""Calibrated, data-driven LLM judge for schema-v2 cases (BUILD_PLAN §6.2).

Corrects the documented LLM-judge upward bias by:
  * grading against the EXPLICIT anamnesis_checklist / red_flags (not exam findings);
  * crediting an item ONLY if the transcript shows it was actually elicited;
  * emitting structured per-item hit/partial/miss + evidence;
  * running at low temperature;
  * recomputing the overall score server-side from per-dimension scores
    (never trusting the model's own arithmetic).

Scoring principles are aligned with real OSCE examination practice:
  - Evidence-based marking
  - Borderline regression calibration
  - Safety threshold for critical missed items
  - Questioning technique assessment (open/closed/leading/signposting)
  - Per-item granularity across ALL dimensions

Judge context = Part A frontmatter (via build_judge_ground_truth) + transcript ONLY.
Stub fallback returns a valid-shaped zero report so scoring never fails a session.
"""
from __future__ import annotations

import json
import re

from app.config import get_settings
from app.domains.scoring.rubric_v2 import (
    DIMENSION_LABELS,
    resolve_weights,
)
from app.rag.answer_key import build_answer_key
from app.rag.llm import get_llm_client, is_stub
from app.rag.prompt_v2 import build_judge_ground_truth
from pipeline.case_v2 import CaseV2

_JUDGE_TEMPERATURE = 0.1  # low temp for stable, repeatable scoring


def _ground_truth_block(gt: dict, dims: list[str]) -> str:
    """Render only the ground truth relevant to the active rubric dimensions."""
    parts: list[str] = []

    if "history_coverage" in dims or "ice_fife" in dims:
        cl = gt.get("anamnesis_checklist") or {}
        for group, items in cl.items():
            if group == "ice_fife" and "ice_fife" not in dims:
                continue
            if group != "ice_fife" and "history_coverage" not in dims:
                continue
            lines = [
                f"  - {(it or {}).get('item', it)}"
                f"{'  [CRITICAL]' if isinstance(it, dict) and it.get('critical') else ''}"
                for it in (items or [])
            ]
            parts.append(f"[{group}]\n" + "\n".join(lines))

    if "red_flags" in dims or "clinical_safety" in dims:
        rf = "\n".join(
            f"  - {i['item']}{'  [CRITICAL]' if i['critical'] else ''}"
            for i in _as_items(gt.get("red_flags"))
        )
        if rf:
            parts.append("[red_flags — MUST be screened]\n" + rf)

    if "diagnostic_reasoning" in dims:
        ddx = gt.get("expected_ddx") or {}
        parts.append(
            "[expected_ddx]\n  working: " + str(ddx.get("working_diagnosis", ""))
            + "\n  differentials: " + ", ".join(ddx.get("differentials") or [])
        )

    if "investigations" in dims:
        inv = (gt.get("investigations") or {}).get("appropriate") or []
        inv_lines = []
        for e in inv:
            if isinstance(e, dict):
                inv_lines.append(f"  - {e.get('name')} -> {e.get('expected', '')}")
            else:
                inv_lines.append(f"  - {e}")
        if inv_lines:
            parts.append("[appropriate_investigations]\n" + "\n".join(inv_lines))

    if "management" in dims:
        mg = gt.get("management") or {}
        flat = (mg.get("pharmacological") or []) + (mg.get("non_pharmacological") or []) \
            + (mg.get("education_safety_netting") or [])
        if flat:
            parts.append("[management]\n" + "\n".join(f"  - {m}" for m in flat))

    return "\n\n".join(p for p in parts if p)


def _as_items(seq) -> list[dict]:
    out = []
    for it in seq or []:
        if isinstance(it, dict):
            out.append({"item": str(it.get("item", "")).strip(), "critical": bool(it.get("critical"))})
        else:
            out.append({"item": str(it).strip(), "critical": False})
    return out


def _transcript_text(transcript: list[dict]) -> str:
    return "\n".join(
        f"{'Doctor' if m.get('role') == 'user' else 'Patient'}: "
        f"{m.get('content', m.get('text', ''))}"
        for m in transcript if m.get("role") in ("user", "patient")
    )


def _student_decisions(ddx: dict | None, plan: dict | None) -> str:
    out = []
    if ddx and not ddx.get("skipped"):
        dxs = ", ".join(x for x in (ddx.get("dx1"), ddx.get("dx2"), ddx.get("dx3")) if x)
        if dxs:
            out.append(f"STUDENT DIFFERENTIALS: {dxs}")
        if ddx.get("reasoning"):
            out.append(f"STUDENT REASONING: {ddx['reasoning']}")
    if plan and not plan.get("skipped"):
        for k, label in (("penunjang", "STUDENT INVESTIGATIONS"),
                         ("terapi", "STUDENT MANAGEMENT"),
                         ("edukasi", "STUDENT EDUCATION")):
            if plan.get(k):
                out.append(f"{label}: {plan[k]}")
    return "\n".join(out)


def build_judge_prompt(case: CaseV2, transcript: list[dict], mode: str,
                       weights: dict[str, int],
                       ddx: dict | None = None, plan: dict | None = None):
    gt = build_judge_ground_truth(case)
    dims = list(weights.keys())
    weight_lines = "\n".join(f"  - {d} (max {w}): {DIMENSION_LABELS.get(d, d)}"
                             for d, w in weights.items())

    # Determine if questioning_technique is in-scope
    assess_questioning = "questioning_technique" in dims
    assess_safety = "clinical_safety" in dims

    system = (
        "You are a SENIOR CLINICAL EXAMINER — a consultant physician who has served "
        "as an OSCE examiner for 15+ years at a teaching hospital. You have sat on "
        "examination boards, calibrated hundreds of medical students and IMG candidates "
        "across multiple specialties, in MULTIPLE LANGUAGES, and know exactly what a safe, "
        "competent, independent practitioner looks like. You are rigorous, fair, and "
        "evidence-based.\n\n"
        "LANGUAGE NOTE: The candidate conducted this interview in a language that may not "
        "be English. The GROUND TRUTH checklists are in English. You evaluate the CLINICAL "
        "CONTENT regardless of language — a correctly elicited item is a 'hit' whether "
        "asked in English, Indonesian, Malay, Tagalog, Vietnamese, Thai, or any other "
        "language. Do NOT penalise for language; penalise ONLY for missing clinical content. "
        "Communication & rapport can be demonstrated in any language.\n\n"
        "=== SCORING PRINCIPLES ===\n"
        "1. EVIDENCE-BASED. Credit a checklist item ONLY if the TRANSCRIPT shows the "
        "candidate actually ELICITED it. Information that exists in the ground truth "
        "but was never asked is a MISS — never reward what they did not do. When in "
        "genuine doubt, mark 'miss'. 'Partial' is for items that were touched vaguely, "
        "indirectly, or incompletely — not for items they obviously knew but didn't express.\n\n"
        "2. PER-ITEM STATUS. For EVERY ground-truth item across all dimensions, output:\n"
        "   - 'hit'  (clearly and correctly elicited / stated)\n"
        "   - 'partial' (touched vaguely or incompletely)\n"
        "   - 'miss' (not asked or stated, or incorrect)\n"
        "   Include a SHORT VERBATIM evidence quote from the transcript (empty string if miss).\n"
        "   Do NOT invent quotes.\n\n"
        "3. NO HALLUCINATION. Every judgement must be grounded in a specific line of "
        "the transcript. Never add information that is not present.\n\n"
        "4. CRITICAL items carry MORE WEIGHT. Missing a critical red flag or a "
        "safety-critical history point must meaningfully lower the relevant dimension.\n\n"
        "5. BE CONSERVATIVE. LLM graders are documented to be too lenient. Deliberately "
        "correct for this: hold a realistic professional standard. The borderline pass "
        "threshold is 60/100. Below 50 is a clear fail. Above 75 is a clear pass. "
        "Scores of 85+ represent excellent, independent-practitioner level performance. "
        "Most competent students should score between 60-75. Adjust your scoring to "
        "match this calibration — do not cluster everyone in the 80-90 range.\n\n"
        "6. CONSISTENCY. Identical performance must earn the same score regardless of "
        "which case or which examiner session. Use the explicit criteria, not global "
        "impression.\n\n"
        "7. SPECIFIC FEEDBACK. For each dimension give 1-2 sentences identifying the "
        "single most useful strength and the single most useful area for improvement — "
        "the way a real supervisor debriefs a student. Be honest; never vague or flattering.\n"
    )

    if assess_questioning:
        system += (
            "\n=== QUESTIONING TECHNIQUE ===\n"
            "When scoring 'questioning_technique', evaluate the PATTERN and STRUCTURE "
            "of the candidate's questions, not the content:\n"
            "  - Did they START with open questions (\"Tell me about your problem\", "
            "\"How has this been affecting you?\") before moving to closed?\n"
            "  - Did they use APPROPRIATE closed questions to clarify details AFTER "
            "establishing the broad picture?\n"
            "  - Did they AVOID leading questions (\"It's painful when you cough, right?\") "
            "that suggest the answer?\n"
            "  - Did they SIGNPOST transitions (\"Now I'd like to ask about your past medical "
            "history…\") and SUMMARISE periodically?\n"
            "  - Did they use appropriate silence and allow the patient to finish?\n"
            "  - Did they follow a LOGICAL PROGRESSION (HPC → past → systems → social) "
            "rather than jumping randomly?\n"
            "A score of 10-15/15 represents a polished, structured interview. 5-9/15 is "
            "adequate but with notable weaknesses. 0-4/15 is disorganised or uses mostly "
            "leading/closed questions.\n"
        )

    if assess_safety:
        system += (
            "\n=== CLINICAL SAFETY ===\n"
            "When scoring 'clinical_safety', focus on:\n"
            "  - Did the candidate identify and explicitly RESPOND to critical red flags "
            "(e.g., arranged urgent referral, recommended immediate investigations)?\n"
            "  - Did they demonstrate appropriate URGENCY when the presentation warranted it?\n"
            "  - Did they provide appropriate SAFETY-NETTING advice (what to watch for, "
            "when to return)?\n"
            "  - Did they AVOID unsafe management decisions?\n"
            "MISSING a critical red flag must heavily reduce this score. Even if history "
            "coverage was good, failing to act on red flags is a safety concern.\n"
            "A score of 8-12/12 means they identified and acted on all safety issues. "
            "4-7/12 means partial awareness but gaps. 0-3/12 means significant safety concern.\n"
        )

    system += (
        "\n=== COMMUNICATION ===\n"
        "When scoring 'communication', evaluate:\n"
        "  - Did they introduce themselves and gain permission/consent?\n"
        "  - Did they demonstrate empathy, active listening, and rapport?\n"
        "  - Did they use lay language appropriate for the patient?\n"
        "  - Did they respond to the patient's ideas, concerns, and expectations?\n"
        "  - Was their manner professional and respectful?\n"
    )

    system += (
        "\n=== DIAGNOSTIC REASONING ===\n"
        "When scoring 'diagnostic_reasoning', evaluate:\n"
        "  - Is the working diagnosis appropriate given the history?\n"
        "  - Are the differentials relevant and well-prioritised?\n"
        "  - Does their reasoning demonstrate logical clinical thinking?\n"
        "  - Did they justify their choices with specific evidence from the history?\n"
        "  - Avoid rewarding scattergun lists — prioritised, focused differentials score higher.\n"
    )

    system += (
        "\n=== INVESTIGATIONS (when in scope) ===\n"
        "  - Are the chosen investigations APPROPRIATE for the suspected diagnosis?\n"
        "  - Are they appropriately PRIORITISED (first-line before second-line)?\n"
        "  - Did the candidate avoid unnecessary/invasive tests when simpler ones suffice?\n"
        "  - Do NOT reward blanket ordering — selective, reasoned choices score higher.\n"
    )

    system += (
        "\n=== MANAGEMENT (when in scope) ===\n"
        "  - Is the proposed management APPROPRIATE for the diagnosis?\n"
        "  - Does it include pharmacological, non-pharmacological, and education/safety-netting?\n"
        "  - Is it REALISTIC and SAFE in the clinical context?\n"
        "  - Does it include appropriate follow-up and escalation plans?\n"
    )

    system += (
        "\n=== OUTPUT FORMAT ===\n"
        "Output ONLY valid JSON (no prose outside it). Schema:\n"
        "{\n"
        '  "per_item": [{\n'
        '    "dimension": "<dim_name>",\n'
        '    "item": "<ground-truth item text>",\n'
        '    "status": "hit|partial|miss",\n'
        '    "evidence": "<verbatim transcript quote or empty string if miss>"\n'
        "  }],\n"
        '  "per_dimension": {\n'
        '    "<dim>": {"score": <int 0..max>, "feedback": "<2-sentence feedback>"}\n'
        "  },\n"
        '  "summary": "<2-3 sentence overall examiner verdict>"\n'
        "}\n"
        "The summary is what a real examiner would say at the end of a debrief: "
        "what the candidate did well, the key area for development, and an overall "
        "impression. Be honest but constructive.\n"
        f"\nDIMENSIONS & MAX SCORES (score each dimension out of its max):\n{weight_lines}"
    )

    content = (
        f"GROUND TRUTH (Part A — never shown to the patient):\n"
        f"{_ground_truth_block(gt, dims)}\n\n"
        f"TRANSCRIPT:\n{_transcript_text(transcript)}"
    )
    extra = _student_decisions(ddx, plan)
    if extra:
        content += f"\n\nSTUDENT CLINICAL DECISIONS:\n{extra}"
    return system, [{"role": "user", "content": content}]


def _empty_report(mode: str, weights: dict[str, int], note: str) -> dict:
    return {
        "mode": mode,
        "weights": weights,
        "per_item": [],
        "per_dimension": {d: {"score": 0, "max": w, "feedback": ""} for d, w in weights.items()},
        "overall": 0,
        "summary": "",
        "_note": note,
    }


def _normalize(raw: dict, mode: str, weights: dict[str, int]) -> dict:
    per_dim: dict[str, dict] = {}
    raw_dim = raw.get("per_dimension") or {}
    for d, w in weights.items():
        entry = raw_dim.get(d) or {}
        score = entry.get("score", 0)
        try:
            score = int(round(float(score)))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(score, w))  # clamp to [0, max]
        per_dim[d] = {"score": score, "max": w, "feedback": str(entry.get("feedback", "")).strip()}
    # Overall recomputed server-side — never trust the model's own total.
    overall = sum(d["score"] for d in per_dim.values())
    per_item = []
    for it in raw.get("per_item") or []:
        if not isinstance(it, dict):
            continue
        status = str(it.get("status", "miss")).lower()
        if status not in ("hit", "partial", "miss"):
            status = "miss"
        per_item.append({
            "dimension": str(it.get("dimension", "")).strip(),
            "item": str(it.get("item", "")).strip(),
            "status": status,
            "evidence": str(it.get("evidence", "")).strip(),
        })
    return {
        "mode": mode,
        "weights": weights,
        "per_item": per_item,
        "per_dimension": per_dim,
        "overall": overall,
        "summary": str(raw.get("summary", "")).strip(),
    }


def evaluate_v2(case: CaseV2, transcript: list[dict], *,
                mode: str | None = None,
                student_ddx: dict | None = None,
                student_management: dict | None = None) -> dict:
    """Score a session against schema-v2 ground truth. Returns a structured
    report + the answer key for the debrief reveal."""
    resolved_mode = (mode or case.frontmatter.get("mode_default") or "anamnesis").lower()
    weights = resolve_weights(resolved_mode, case.frontmatter.get("scoring_weights_override"))

    if is_stub():
        report = _empty_report(resolved_mode, weights,
                               "Stub LLM: set LLM_API_KEY for real scoring. Shape is valid; scores 0.")
    else:
        try:
            system, user = build_judge_prompt(case, transcript, resolved_mode, weights,
                                              student_ddx, student_management)
            raw_text = get_llm_client().generate(
                system, user,
                model=get_settings().llm_judge_model,
                max_tokens=get_settings().llm_judge_max_tokens,
                temperature=_JUDGE_TEMPERATURE,
            )
            m = re.search(r"\{.*\}", raw_text, re.DOTALL)
            report = _normalize(json.loads(m.group(0) if m else raw_text), resolved_mode, weights)
        except Exception as e:  # scoring must never fail the session
            report = _empty_report(resolved_mode, weights, f"judge parse failed, valid fallback: {e}")

    report["answer_key"] = build_answer_key(case)
    return report
