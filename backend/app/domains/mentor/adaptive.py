"""Qora Mentor — adaptation decisions (FASE 13, final integration).

Deterministic remediation/advance decisions over ONE normalized journey
report. Principle: **LLM understands and explains, the Qora planning
engine decides.** Pure function — no DB, no network, no LLM.

Contract (pinned by Phase 13 integration):
- score < 60 (or a real safety-gate list on the report) → remediate:
  action "remediate", slot_kind "remediation", mandatory True.
- score >= 60 → advance: slot_kind "none" (strong) or "spaced_revisit".
"""
from __future__ import annotations

REMEDIATE_BELOW = 60.0
STRONG_AT = 70.0


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def decide_adaptation(
    score=0,
    report=None,
    family_ref: str = "",
    recent_scores=None,
) -> dict:
    """Decide the next learning slot from a session score + journey report."""
    s = _num(score)
    gates: list = []
    if isinstance(report, dict):
        raw = report.get("safety_gates")
        # A bare True is a compat flag, not an itemized gate list — only a
        # real (non-empty list) of gates forces remediation on its own.
        if isinstance(raw, list):
            gates = [g for g in raw if g]
    recent = [_num(x) for x in (recent_scores or []) if isinstance(x, (int, float))]
    trend = (recent[-1] - recent[0]) / max(1, len(recent) - 1) if len(recent) >= 2 else 0.0

    if s < REMEDIATE_BELOW or gates:
        return {
            "action": "remediate",
            "slot_kind": "remediation",
            "mandatory": True,
            "family_ref": str(family_ref or ""),
            "score": s,
            "recent_scores": list(recent_scores or []),
            "trend_per_session": round(trend, 2),
            "safety_gates": gates,
            "reason": (
                "safety gates triggered — remediate before advancing"
                if gates
                else f"score {s:g} below mastery threshold {REMEDIATE_BELOW:g}"
            ),
        }
    slot = "none" if s >= STRONG_AT else "spaced_revisit"
    return {
        "action": "advance",
        "slot_kind": slot,
        "mandatory": False,
        "family_ref": str(family_ref or ""),
        "score": s,
        "recent_scores": list(recent_scores or []),
        "trend_per_session": round(trend, 2),
        "safety_gates": gates,
        "reason": f"score {s:g} meets mastery threshold {REMEDIATE_BELOW:g}",
    }
