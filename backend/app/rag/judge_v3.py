"""V3 LLM judge — mirrors `judge_v2.evaluate_v2` so V3-backed sessions get the
SAME quality of scoring the V2 frontend already trusts.

`score_encounter` (runtime) is deterministic and does NOT read the transcript,
which is why a session with only 3 questions still scored "diagnostic 100%" and
finished in ~3s. V2 instead runs an LLM judge over the full transcript + ground
truth, producing per-item hit/miss WITH transcript evidence, honest dimension
scores, safety gates, and a narrative examiner summary. This module ports that
exact approach onto the V3 `ClinicalVariant` ground truth, and returns the
V2-shaped report the frontend consumes.
"""
from __future__ import annotations

import json

from app.config import get_settings
from app.rag.llm import get_llm_client, is_stub
from pipeline.case_v3.derive import (
    derive_history_checklist, derive_red_flags,
)
from pipeline.case_v3.runtime import learner_profile

_JUDGE_TEMPERATURE = 0.1
_JUDGE_TIMEOUT_S = 110.0
_JUDGE_MAX_RETRIES = 1

# V3 dimension set (from learner_profile). We scale the fractional weights to
# integer max scores that sum to ~100 so `overall` reads like a percentage.
_V3_DIMENSIONS = ["info_gathering", "focus_efficiency", "reasoning_coherence",
                  "diagnostic_quality", "investigation_strategy",
                  "management_safety", "communication"]


def _v3_weights(learner_stage: str = "koas") -> dict[str, int]:
    prof = learner_profile(learner_stage or "koas")
    w = prof.get("weights", {})
    out = {}
    for d in _V3_DIMENSIONS:
        out[d] = int(round((w.get(d, 0) or 0) * 100))
    return out


# ── ground truth block ─────────────────────────────────────────────────────
def _fmt(val) -> str:
    if isinstance(val, list):
        return " · ".join(str(x) for x in val)
    return str(val)


def _ground_truth_block(v, with_pf: bool) -> str:
    """Render the V3 ClinicalVariant ground truth (never shown to the patient)."""
    parts = []

    # history checklist grouped by history group
    cl = derive_history_checklist(v)
    groups = {}
    for it in cl:
        groups.setdefault(it.get("group") or "history", []).append(it)
    if groups:
        blk = ["[HISTORY — what a complete history should cover]"]
        for gname, items in groups.items():
            blk.append(f"[{str(gname).replace('_', ' ')}]")
            for it in items:
                imp = " (important)" if it.get("importance") in ("critical", "key") else ""
                blk.append(f"  - {it.get('item')}{imp}")
        parts.append("\n".join(blk))

    # red flags
    rf = [r for r in derive_red_flags(v) if r.get("status") == "present"]
    if rf:
        blk = ["[RED FLAGS — must be screened & acted on]"]
        for r in rf:
            blk.append(f"  - {r.get('fact')} (criticality: {r.get('criticality')})")
        parts.append("\n".join(blk))

    # diagnosis
    dd = v.diagnostic or type("D", (), {"working_diagnosis": "", "differentials": []})()
    parts.append("[TARGET DIAGNOSIS]\n" + (dd.working_diagnosis or ""))
    if getattr(dd, "differentials", None):
        diffs = [d.name if isinstance(d, dict) else getattr(d, "name", str(d))
                 for d in dd.differentials]
        parts.append("[REASONABLE DIFFERENTIALS]\n" + "\n".join(f"  - {x}" for x in diffs))

    # investigations
    inv = getattr(v, "investigations", None) or []
    appr = [i for i in inv if (getattr(i, "appropriateness", None) or "appropriate") in ("appropriate",)]
    if appr:
        blk = ["[APPROPRIATE INVESTIGATIONS]"]
        for i in appr:
            name = getattr(i, "name", None) or ""
            exp = getattr(i, "expected_result", None) or ""
            blk.append(f"  - {name} → {exp}")
        parts.append("\n".join(blk))

    # management buckets
    mgmt = getattr(v, "management", None) or type("M", (), {})()
    def _flat(*names):
        out = []
        for n in names:
            out.extend(getattr(mgmt, n, None) or [])
        return out
    mg = _flat("stabilization", "pharmacologic", "non_pharmacologic",
               "referral", "follow_up", "education_safety_netting")
    if mg:
        parts.append("[EXPECTED MANAGEMENT]\n" + "\n".join(f"  - {x}" for x in mg))

    # physical exam findings
    if with_pf:
        pe = getattr(v, "physical_exam", None)
        if pe and getattr(pe, "system_findings", None):
            blk = ["[PHYSICAL EXAM FINDINGS — the patient's REAL findings]"]
            for k, val in pe.system_findings.items():
                blk.append(f"  - {str(k).replace('_', ' ')}: {val}")
            parts.append("\n".join(blk))

    return "\n\n".join(parts)


# ── transcript & student decisions (mirror judge_v2) ───────────────────────
def _transcript_text(transcript: list[dict]) -> str:
    rows = []
    for m in transcript:
        if m.get("role") not in ("user", "patient"):
            continue
        text = str(m.get("content", m.get("text", ""))).strip()
        if len(text) > 500:
            text = text[:500] + "…"
        rows.append(f"{'Doctor' if m.get('role') == 'user' else 'Patient'}: {text}")
    return "\n".join(rows[-40:])


def _student_decisions(ddx: dict | None, plan: dict | None,
                       pf_notes: str | None, pf_areas: list | None) -> str:
    out = []
    if ddx and isinstance(ddx, dict):
        vals = [str(x) for x in ddx.values() if x and not str(x).lower() in ("none", "null", "skip")]
        if vals:
            out.append("STUDENT DIFFERENTIALS / DIAGNOSIS: " + ", ".join(vals))
    if plan and isinstance(plan, dict):
        for k, label in (("penunjang", "STUDENT INVESTIGATIONS"),
                         ("terapi", "STUDENT MANAGEMENT"),
                         ("edukasi", "STUDENT EDUCATION")):
            v = plan.get(k)
            if v:
                out.append(f"{label}: {v}")
        if plan.get("complete"):
            out.append("STUDENT REPORTED MANAGEMENT COMPLETE")
    if pf_areas or pf_notes:
        if pf_areas:
            out.append("PHYSICAL EXAM AREAS EXAMINED: " + ", ".join(pf_areas))
        if pf_notes:
            out.append("PHYSICAL EXAM NOTES: " + str(pf_notes))
    return "\n".join(out)


def build_judge_prompt(v, transcript: list[dict], learner_stage: str,
                       weights: dict[str, int], *,
                       ddx: dict | None = None, management: dict | None = None,
                       pf_notes: str | None = None, pf_areas: list | None = None,
                       with_pf: bool = False) -> tuple[str, list[dict]]:
    """Build the judge system+user prompt for a V3 variant + transcript."""
    weight_lines = "\n".join(
        f"  - {d.replace('_', ' ')}: max {w}" for d, w in weights.items()
        if w > 0)
    system = (
        "You are a strict but fair OSCE examiner evaluating a medical student's "
        "patient consultation. Score ONLY from the transcript (what the candidate "
        "actually asked / said) and the candidate's submitted decisions — never "
        "invent evidence. Be honest: if the candidate only asked a few questions "
        "or skipped key areas, that must be reflected in the scores.\n"
        f"\nDimensions & max scores:\n{weight_lines}\n"
        f"\nScoring principles:\n"
        "  - info_gathering: did they cover the relevant history groups and key "
        "facts (compare against [HISTORY])? Unasked items reduce this. "
        "Scattergun/blanket questioning does NOT equal good coverage.\n"
        "  - focus_efficiency: were questions focused; did they avoid redundancy "
        "and aimless rambling? A few well-targeted questions vs. many but few "
        "useful ones.\n"
        "  - reasoning_coherence: did their reasoning and differentials follow "
        "logically from the findings?\n"
        "  - diagnostic_quality: is the working diagnosis / differential "
        "appropriate given what they found? Only award high marks if the "
        "diagnosis is actually supported by evidence they elicited.\n"
        "  - investigation_strategy: appropriate, prioritised tests for the "
        "suspected diagnosis (compare [APPROPRIATE INVESTIGATIONS]); reward "
        "selective reasoned choices, penalise blanket ordering.\n"
        "  - management_safety: appropriate + safe management, red-flag urgency, "
        "referral & stabilisation. Missing a critical red flag heavily reduces this.\n"
        "  - communication: empathy, lay language, consent, rapport.\n"
        "\n=== SAFETY GATES ===\n"
        "Independently of dimension scores, output 'safety_gates' ONLY for events "
        "actually present in the transcript, as {type, detail} where type is one of: "
        "missed_critical_red_flag | unsafe_management | failed_urgent_referral. "
        "If none occurred, output [] — never invent. Also output 'summary', a "
        "2-4 sentence examiner-style paragraph that SPECIFIES what the candidate "
        "actually covered and what they missed (name concrete topics), plus an "
        "overall impression.\n"
        "\n=== OUTPUT FORMAT ===\n"
        "Output ONLY valid JSON (no prose outside it). Schema:\n"
        '{"per_item":[{"dimension":"<dim>","item":"<ground-truth item text>",'
        '"status":"hit|partial|miss","evidence":"<verbatim transcript quote or empty>"}],'
        '"per_dimension":{"<dim>":{"score":<int 0..max>,"feedback":"<short>"}},'
        '"safety_gates":[{"type":"missed_critical_red_flag","detail":"<...>"}],'
        '"summary":"<examiner paragraph>"}'
    )
    gt = _ground_truth_block(v, with_pf)
    extra = _student_decisions(ddx, management, pf_notes, pf_areas)
    content = f"GROUND TRUTH (never shown to the patient):\n{gt}\n\n" \
              f"TRANSCRIPT:\n{_transcript_text(transcript)}"
    if extra:
        content += f"\n\nSTUDENT CLINICAL DECISIONS:\n{extra}"
    return system, [{"role": "user", "content": content}]


def _extract_json(text: str):
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


def _empty_report(weights: dict[str, int], note: str) -> dict:
    return {
        "per_item": [],
        "per_dimension": {d: {"score": 0, "max": w, "feedback": ""}
                          for d, w in weights.items()},
        "overall": 0,
        "summary": "",
        "safety_gates": [],
        "_note": note,
    }


def _normalize(raw: dict, weights: dict[str, int]) -> dict:
    per_dim = {}
    raw_dim = raw.get("per_dimension") or {}
    for d, w in weights.items():
        entry = raw_dim.get(d) or {}
        try:
            score = int(round(float(entry.get("score", 0))))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(score, w))
        per_dim[d] = {"score": score, "max": w,
                      "feedback": str(entry.get("feedback", "")).strip()}
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
    # honest overall percentage out of 100
    pct = int(round((overall / sum(weights.values())) * 100)) if sum(weights.values()) else 0
    return {
        "per_item": per_item,
        "per_dimension": per_dim,
        "overall": pct,
        "overall_raw": overall,
        "max_score": sum(weights.values()),
        "summary": str(raw.get("summary", "")).strip(),
        "safety_gates": _normalize_gates(raw.get("safety_gates")),
    }


def _normalize_gates(gates):
    if not gates:
        return []
    out = []
    allowed = ("missed_critical_red_flag", "unsafe_management",
               "failed_urgent_referral")
    for g in gates if isinstance(gates, list) else [gates]:
        if not isinstance(g, dict):
            continue
        typ = str(g.get("type", g.get("gate", ""))).strip().lower()
        if typ not in allowed:
            continue
        detail = str(g.get("detail", "")).strip()
        if detail:
            out.append({"type": typ, "detail": detail})
    return out


def evaluate_v3(v, transcript: list[dict], *,
                learner_stage: str = "koas", ddx: dict | None = None,
                management: dict | None = None,
                pf_notes: str | None = None, pf_areas: list | None = None,
                with_pf: bool = False) -> dict:
    """Score a V3 session with an LLM judge over the transcript. Returns the
    V2-shaped report (per_item / per_dimension / overall / summary / safety_gates)
    that the V2 frontend already renders. Falls back deterministically on stub
    or judge failure so scoring never hard-fails the session."""
    weights = _v3_weights(learner_stage)
    if is_stub():
        return _empty_report(
            weights, "Stub LLM: set LLM_API_KEY for real scoring. Valid V2 shape; scores 0.")
    try:
        system, user = build_judge_prompt(
            v, transcript, learner_stage, weights, ddx=ddx, management=management,
            pf_notes=pf_notes, pf_areas=pf_areas, with_pf=with_pf)
        raw_text = get_llm_client().generate(
            system, user,
            model=get_settings().llm_judge_model,
            max_tokens=get_settings().llm_judge_max_tokens,
            temperature=_JUDGE_TEMPERATURE,
            timeout=_JUDGE_TIMEOUT_S,
            max_retries=_JUDGE_MAX_RETRIES,
        )
        obj = _extract_json(raw_text)
        return _normalize(obj, weights) if obj is not None else \
            _empty_report(weights, "judge returned no parseable JSON")
    except Exception as e:  # scoring must never fail the session
        return _empty_report(weights, f"judge failed, valid fallback: {e}")