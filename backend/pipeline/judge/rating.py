"""Phase 7E — global clinical rating (plan §22-23).

Examiner-like holistic rating AFTER evidence/item scoring, constrained by
evidence and safety: it may consider coherence/prioritization/maturity but
may NOT override hard safety rules, and sparse evidence caps confidence.
NOT BRM (§23): single-session evidence score + global rating + locally
calibrated thresholds only — never labeled BRM.
"""
from __future__ import annotations

from pipeline.judge.domains import mode_params

GLOBAL_RATINGS = ("Fail", "Borderline", "Pass", "Superior")


def assign_global_rating(
    overall: int,
    gates: list[dict] | None,
    *,
    mode: str = "practice",
    evidence_count: int = 0,
    rubric_size: int = 0,
) -> dict:
    """Return {rating, confidence, reasons}. Deterministic.

    - Base rating from mode thresholds (provisional until calibrated).
    - Any triggered gate caps at Borderline; catastrophic gates → Fail.
    - Sparse evidence (<3 supporting refs, or empty ledger) caps at
      Borderline with low confidence — never high-confidence readiness
      from thin evidence (plan §44 inputs).
    """
    params = mode_params(mode)
    gates = list(gates or [])
    reasons = []
    if overall >= params["superior_threshold"]:
        rating = "Superior"
    elif overall >= params["pass_threshold"]:
        rating = "Pass"
    elif overall >= params["borderline_threshold"]:
        rating = "Borderline"
    else:
        rating = "Fail"
    reasons.append(
        f"overall {overall} vs {mode} thresholds (pass {params['pass_threshold']}, superior {params['superior_threshold']})"
    )
    catastrophic = any(g.get("catastrophic") for g in gates)
    if catastrophic:
        rating = "Fail"
        reasons.append("catastrophic safety gate triggered → Fail (global rating cannot override safety)")
    elif gates:
        if rating in ("Pass", "Superior"):
            rating = "Borderline"
        reasons.append(f"{len(gates)} safety gate(s) triggered → capped at Borderline maximum")
    confidence = "High" if evidence_count >= 8 else "Moderate" if evidence_count >= 3 else "Low"
    if evidence_count < 3 and rating in ("Pass", "Superior"):
        rating = "Borderline"
        reasons.append(
            "sparse evidence (<3 supporting refs) → capped at Borderline; not enough evidence for reliable rating"
        )
    if rubric_size and evidence_count == 0:
        rating = "Fail"
        reasons.append("no evidenced items at all → Fail")
    return {"rating": rating, "confidence": confidence, "reasons": reasons}
