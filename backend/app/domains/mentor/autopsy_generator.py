"""Qora Mentor — reasoning autopsy generator (PRD_QORA_MENTOR §4.2).

Post-session analysis: dissect the student's reasoning pathway vs the expert
pathway, detect cognitive-bias errors, and produce a "clinical pearl".

Design:
- A DETERMINISTIC core derives errors from ground truth + per-item report
  (missed red flags are computed from actual checklist misses — more reliable
  than an LLM guessing), and builds user/expert pathway summaries from the
  transcript.
- The LLM (when a key is present) ENRICHES the output: pearl, refined error
  descriptions with transcript quotes, expert pathway narrative.
- No LLM → deterministic output only. Tests run $0.
"""
from __future__ import annotations

import json
import logging

from app.config import get_settings
from app.rag.llm import get_llm_client, is_stub

_log = logging.getLogger("mentor.autopsy")

_AUTOPSY_SYSTEM = """You are a senior clinical examiner performing a "reasoning autopsy" —
analyzing not just WHAT the student asked, but HOW they thought.

Your analysis must be:
1. Evidence-based — quote the transcript verbatim
2. Specific — identify exact moments of divergence
3. Constructive — focus on learning, not criticism
4. Actionable — provide a "clinical pearl" the student can apply

Error taxonomy:
- anchoring: fixating on initial hypothesis
- premature_closure: stopping data gathering too early
- confirmation_bias: only asking confirming questions
- scattergun: ordering too many tests without hypothesis
- missed_red_flag: failing to screen critical red flag
- poor_signposting: disorganized interview flow
- leading_questions: suggesting answers
- ignoring_ice: not exploring ideas/concerns/expectations

Return ONLY valid JSON, no prose, no markdown fences:
{
  "user_pathway": ["step1", "step2", ...],
  "expert_pathway": ["step1", "step2", ...],
  "divergence_points": [{"step": 1, "user": "...", "expert": "...", "error_type": "..."}],
  "errors_detected": [{"type": "...", "severity": "critical|moderate|minor",
                       "description": "...", "evidence": "transcript quote"}],
  "pearl": "One actionable insight for improvement",
  "readiness_impact": -5
}"""

_SEVERITY = {"critical": "critical", "moderate": "moderate", "minor": "minor"}


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


def _transcript_text(transcript: list[dict]) -> str:
    return "\n".join(f"{t.get('role','?')}: {t.get('content','')}" for t in transcript)


# ---------------------------------------------------------------------------
# Deterministic core
# ---------------------------------------------------------------------------

def _missed_red_flags(case, report: dict) -> list[dict]:
    """Critical red flags the student failed to elicit (ground-truth based)."""
    out: list[dict] = []
    per_item = {str(p.get("item", "")).strip().lower(): p for p in (report.get("per_item") or [])}
    for rf in case.red_flag_items():
        item = str(rf.get("item", "")).strip()
        key = item.lower()
        st = per_item.get(key, {}).get("status")
        if st == "miss":
            out.append({
                "type": "missed_red_flag",
                "severity": "critical",
                "value": str(rf.get("id", rf.get("item", ""))),
                "description": f"Red flag tidak ditanyakan: '{item}'.",
                "evidence": "",
            })
    return out


def _user_pathway(transcript: list[dict]) -> list[str]:
    """Compact summary of the student's actual question sequence."""
    steps: list[str] = []
    for t in transcript:
        if t.get("role") != "user":
            continue
        text = str(t.get("content", "")).strip()
        if not text:
            continue
        snippet = text if len(text) <= 90 else text[:87] + "..."
        steps.append(f'"{snippet}"')
    return steps or ["(tidak ada pertanyaan tercatat)"]


def _expert_pathway(case) -> list[str]:
    """Gold-standard pathway from the case's checklist structure."""
    steps: list[str] = []
    cl = case.frontmatter.get("anamnesis_checklist") or {}
    for group in ("hpi_socrates", "past_medical", "medications", "family_history",
                  "social_history", "red_flags", "ice_fife"):
        items = cl.get(group) or []
        if items:
            labels = {"hpi_socrates": "Anamnesis keluhan utama (SOCRATES)",
                      "past_medical": "Riwayat penyakit dahulu",
                      "medications": "Riwayat obat",
                      "family_history": "Riwayat keluarga",
                      "social_history": "Riwayat sosial",
                      "red_flags": "Skrining red flag",
                      "ice_fife": "ICE/FIFE (ide, kekhawatiran, harapan)"}
            steps.append(f"{labels.get(group, group)}: tanyakan {len(items)} item")
    return steps or ["(kasus tidak punya checklist anamnesis)"]


def _deterministic_autopsy(case, transcript: list[dict], report: dict) -> dict:
    """Deterministic output — always available, no LLM."""
    errors = _missed_red_flags(case, report)

    # Readiness impact: -2 per critical missed red flag (bounded -10).
    impact = -min(10, 2 * len([e for e in errors if e["severity"] == "critical"]))

    pearl = None
    if errors:
        rf = errors[0]
        pearl = (
            f"Kasus ini punya red flag kritis '{rf['value']}' yang tidak kamu tanyakan. "
            "Selalu skrining red flag SEBELUM menutup diagnosis — satu pertanyaan "
            "screening bisa mengubah tatalaksana sepenuhnya."
        )

    return {
        "user_pathway": _user_pathway(transcript),
        "expert_pathway": _expert_pathway(case),
        "divergence_points": [],
        "errors_detected": errors,
        "pearl": pearl,
        "readiness_impact": impact,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_autopsy(case, transcript: list[dict], report: dict) -> dict:
    """Deterministic core, LLM-enriched when a key is configured."""
    base = _deterministic_autopsy(case, transcript, report)
    try:
        if is_stub():
            return base
        gt = case.part_a() if hasattr(case, "part_a") else case.frontmatter
        raw = get_llm_client().generate(
            _AUTOPSY_SYSTEM,
            [{"role": "user", "content": json.dumps({
                "case_ground_truth": gt,
                "student_transcript": _transcript_text(transcript),
                "report": {k: report.get(k) for k in ("overall", "per_dimension", "per_item")},
            }, ensure_ascii=False)}],
            model=get_settings().llm_model,
            max_tokens=1400,
            temperature=0.3,
        )
        data = _extract_json(raw)
        if not data:
            return base
        return _merge(base, data)
    except Exception:  # noqa: BLE001
        _log.warning("autopsy LLM failed; returning deterministic output")
        return base


def _merge(base: dict, data: dict) -> dict:
    """LLM enrichment merged over the deterministic base (server keeps control
    of the error list so hallucinated errors can't leak in)."""
    out = dict(base)
    if isinstance(data.get("user_pathway"), list) and data["user_pathway"]:
        out["user_pathway"] = [str(s) for s in data["user_pathway"]][:12]
    if isinstance(data.get("expert_pathway"), list) and data["expert_pathway"]:
        out["expert_pathway"] = [str(s) for s in data["expert_pathway"]][:12]
    if isinstance(data.get("divergence_points"), list):
        out["divergence_points"] = [d for d in data["divergence_points"]
                                    if isinstance(d, dict)][:8]
    pearl = str(data.get("pearl") or "").strip()
    if len(pearl) > 20:
        out["pearl"] = pearl
    # Errors: deterministic list wins; LLM may only ADD non-critical refinements.
    existing = {(e.get("type"), e.get("severity")) for e in out["errors_detected"]}
    for e in data.get("errors_detected") or []:
        if not isinstance(e, dict):
            continue
        sev = str(e.get("severity") or "moderate").lower()
        sev = sev if sev in _SEVERITY else "moderate"
        key = (str(e.get("type") or "").lower(), sev)
        if key in existing:
            continue
        desc = str(e.get("description") or "").strip()
        if desc and len(out["errors_detected"]) < 5:
            out["errors_detected"].append({
                "type": str(e.get("type") or "unknown").lower(),
                "severity": sev,
                "description": desc,
                "evidence": str(e.get("evidence") or "").strip()[:200],
            })
    imp = data.get("readiness_impact")
    if isinstance(imp, (int, float)):
        out["readiness_impact"] = max(-15, min(10, int(imp)))
    return out
