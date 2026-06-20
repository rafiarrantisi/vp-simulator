"""Calibrated, data-driven LLM judge for schema-v2 cases (BUILD_PLAN §6.2).

Corrects the documented LLM-judge upward bias by:
  * grading against the EXPLICIT anamnesis_checklist / red_flags (not exam findings);
  * crediting an item ONLY if the transcript shows it was actually elicited;
  * emitting structured per-item hit/partial/miss + evidence;
  * running at low temperature;
  * recomputing the overall score server-side from per-dimension scores
    (never trusting the model's own arithmetic).

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
    if "red_flags" in dims:
        rf = "\n".join(
            f"  - {i['item']}{'  [CRITICAL]' if i['critical'] else ''}"
            for i in _as_items(gt.get("red_flags"))
        )
        parts.append("[red_flags — MUST be screened]\n" + rf)
    if "diagnostic_reasoning" in dims:
        ddx = gt.get("expected_ddx") or {}
        parts.append(
            "[expected_ddx]\n  working: " + str(ddx.get("working_diagnosis", ""))
            + "\n  differentials: " + ", ".join(ddx.get("differentials") or [])
        )
    if "investigations" in dims:
        inv = (gt.get("investigations") or {}).get("appropriate") or []
        parts.append("[appropriate_investigations]\n" + "\n".join(
            f"  - {e.get('name')} -> {e.get('expected')}" for e in inv if isinstance(e, dict)
        ))
    if "management" in dims:
        mg = gt.get("management") or {}
        flat = (mg.get("pharmacological") or []) + (mg.get("non_pharmacological") or []) \
            + (mg.get("education_safety_netting") or [])
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
    system = (
        "You are a STRICT OSCE examiner scoring a medical student's patient "
        "interview. Examiners are documented to over-score — be conservative.\n"
        "RULES:\n"
        "1. Credit a checklist or red-flag item ONLY if the TRANSCRIPT shows the "
        "student actually ELICITED it by asking. Do NOT credit information that is "
        "merely present in the ground truth but was never asked about. When in "
        "doubt, mark 'miss'.\n"
        "2. For each ground-truth item output status 'hit' (clearly elicited), "
        "'partial' (vaguely/indirectly touched), or 'miss', with a short verbatim "
        "evidence quote from the transcript ('' if miss). CRITICAL items matter most.\n"
        "3. Score each dimension out of its max. 'communication' is judged from the "
        "transcript: introduction, consent, empathy, signposting, logical structure, "
        "lay language.\n"
        "4. Output ONLY valid JSON: {\"per_item\":[{\"dimension\":..,\"item\":..,"
        "\"status\":\"hit|partial|miss\",\"evidence\":..}], \"per_dimension\":"
        "{\"<dim>\":{\"score\":int,\"feedback\":str}}, \"summary\":str}.\n"
        f"DIMENSIONS & MAX SCORES:\n{weight_lines}"
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
