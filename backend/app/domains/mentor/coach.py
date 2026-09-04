"""Qora Mentor — coach insight composer (FASE 13, final integration).

Turns ONE normalized journey report + adaptation decision into a short,
honest coach card. Principle: **LLM understands and explains, the Qora
planning engine decides** — this composer only *states* what the report
already contains (weak dims, safety gates); it never invents evidence.

Contract (pinned by Phase 13 integration):
- insight["headline"] is always a non-empty string;
- insight["safety_flag"] is True exactly when the report carries itemized
  safety gates (unsafe journey) — the headline then names safety;
- insight["evidence"]["weak_dims"] lists report dims scoring below mastery,
  so it is always a subset of the report's own dims.
"""
from __future__ import annotations

WEAK_BELOW = 60.0


def _num(value, default: float = 100.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_coach_insight(
    report=None,
    score=0,
    journey_ctx=None,
    adaptation=None,
    next_pick=None,
) -> dict:
    """Compose the coach card for one journey report."""
    rep = report if isinstance(report, dict) else {}
    ctx = journey_ctx if isinstance(journey_ctx, dict) else {}
    adapt = adaptation if isinstance(adaptation, dict) else {}

    gates = rep.get("safety_gates")
    gate_list = [g for g in gates] if isinstance(gates, list) else []
    per_dim = rep.get("per_dimension") or {}
    weak_dims = sorted(
        str(d)
        for d, v in per_dim.items()
        if isinstance(v, dict) and _num(v.get("score"), 100.0) < WEAK_BELOW
    )

    s = _num(score, 0.0)
    safety = bool(gate_list)
    goal = str(ctx.get("goal") or "practice")
    if safety:
        headline = (
            "Safety first: a safety-critical step was missed — "
            "remediate before advancing."
        )
    elif weak_dims:
        headline = f"Focus next on {', '.join(weak_dims)} ({goal} track, score {s:g})."
    else:
        headline = f"Solid {goal} session (score {s:g}) — keep the streak going."

    body = (
        f"Report overall {rep.get('overall', s):g}. "
        + (
            f"{len(gate_list)} safety gate(s) need review."
            if gate_list
            else ("Weak dimensions: " + ", ".join(weak_dims) + "." if weak_dims else "No weak dimensions.")
        )
    )
    evidence: dict = {
        "weak_dims": weak_dims,
        "safety_gates": [
            g if isinstance(g, dict) else {"type": str(g)} for g in gate_list
        ],
        "score": s,
    }
    if isinstance(next_pick, dict) and next_pick:
        evidence["next_pick"] = dict(next_pick)
    return {
        "headline": headline,
        "body": body,
        "safety_flag": safety,
        "weak_dims": weak_dims,
        "evidence": evidence,
        "adaptation": dict(adapt),
        "journey_ctx": dict(ctx),
    }
