"""Phase 8 Task C/D/E — evidence-based readiness engine (plan §Phase 8-C/D/E,
§44, §6, §36).

Single engine shared by Dashboard progress and Mentor readiness so the same
performance can never produce contradictory claims (§36).

Conceptual components (§44), all explicit + versioned in READINESS_WEIGHTS:
- proficiency: weighted native-dimension averages (V2 weights preserved
  exactly; V3/native weights defined below; renormalized over dims present);
- coverage: distinct OSCE core domains observed / 8;
- safety: recent safety-gate triggers penalize AND cap (safety outranks
  checklist accumulation — a high scorer with a recent safety failure is
  capped, never "Great job!");
- consistency: distinct practice days / span (regular practice);
- trajectory: improving vs declining recent overalls;
- recency: stale performance lowers the estimate + confidence;
- integrated OSCE: zero OSCE sessions caps OSCE-readiness (many easy
  Practice cases != exam ready);
- evidence/confidence: sparse evidence can never yield high confidence;
  1 session is always "Building", never "Ready".

Every output explains its drivers (Task E): top positive/negative factors,
strengths, needs work, and the evidence summary behind the number.
"""
from __future__ import annotations

from datetime import datetime, timezone

READINESS_VERSION = "qora-readiness-1.0"

V2_DIM_WEIGHTS = {
    "history_coverage": 0.20,
    "red_flags": 0.15,
    "diagnostic_reasoning": 0.15,
    "management": 0.15,
    "physical_exam": 0.10,
    "communication": 0.10,
    "ice_fife": 0.10,
    "questioning_technique": 0.05,
}

V3_DIM_WEIGHTS = {
    "info_gathering": 0.20,
    "focus_efficiency": 0.10,
    "reasoning_coherence": 0.15,
    "diagnostic_quality": 0.15,
    "investigation_strategy": 0.10,
    "management_safety": 0.20,
    "communication": 0.10,
}

NATIVE_DIM_WEIGHTS: dict = dict(V2_DIM_WEIGHTS)
NATIVE_DIM_WEIGHTS.update(V3_DIM_WEIGHTS)

READINESS_WEIGHTS = {
    "native_dims": dict(NATIVE_DIM_WEIGHTS),
    "coverage_blend": 0.10,
    "safety_step": 0.15,
    "safety_floor_factor": 0.50,
    "safety_cap_recent": 59,
    "no_osce_cap": 74,
    "single_session_cap": 59,
    "two_session_cap": 69,
    "error_penalty_per_critical": 2,
    "error_penalty_cap": 10,
    "trajectory_window": 5,
    "safety_window": 5,
    "safety_cap_window": 3,
}

_N_CORE = 8


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def interpret_score(score: int) -> dict:
    """Interpretation tiers (same bands as the Phase-1 calculator)."""
    if score >= 90:
        return {"level": "distinction", "label": "Exam ready — predicted distinction",
                "color": "var(--teal)"}
    if score >= 75:
        return {"level": "pass", "label": "Ready — predicted clear pass",
                "color": "var(--green)"}
    if score >= 60:
        return {"level": "borderline",
                "label": "Borderline — needs targeted improvement", "color": "var(--amber)"}
    if score >= 40:
        return {"level": "not_ready", "label": "Not ready — significant gaps",
                "color": "var(--red)"}
    return {"level": "foundation", "label": "Foundation needed — repeat basics",
            "color": "var(--red-d)"}


def compute_readiness(sessions: list[dict], *, now: datetime | None = None,
                      critical_errors: int = 0) -> dict:
    """Evidence-based readiness over normalized sessions (oldest->newest).

    `sessions` are NormalizedSession dicts (see longitudinal). Pure function.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    sessions = [s for s in (sessions or []) if isinstance(s, dict)]
    n = len(sessions)
    if n == 0:
        return {
            "version": READINESS_VERSION,
            "score": 0,
            "confidence": "insufficient_data",
            "state": "No evidence",
            "session_count": 0,
            "base_score": 0,
            "trajectory_bonus": 1.0,
            "consistency_bonus": 1.0,
            "error_penalty": 0,
            "dimensions": {},
            "core_dimensions": {},
            "components": {},
            "drivers": [{"factor": "evidence", "direction": "info",
                         "detail": "No completed sessions yet — complete a case to start building readiness."}],
            "strengths": [],
            "needs_work": [],
            "evidence": {"sessions": 0, "osce_sessions": 0, "domains_covered": 0,
                         "days_span": 0, "days_since_last": None},
            "interpretation": None,
        }

    dim_accum: dict[str, list[float]] = {}
    for s in sessions:
        for dim, pct in (s.get("dim_pcts") or {}).items():
            try:
                dim_accum.setdefault(str(dim), []).append(float(pct))
            except (TypeError, ValueError):
                continue
    dims = {d: round(sum(v) / len(v), 1) for d, v in dim_accum.items()}
    active_w = {d: w for d, w in NATIVE_DIM_WEIGHTS.items() if d in dims}
    if active_w:
        wsum = sum(active_w.values())
        base = sum(dims[d] * (w / wsum) for d, w in active_w.items())
    else:
        overalls_all = [float(s.get("overall_0_100") or 0) for s in sessions]
        base = sum(overalls_all) / len(overalls_all) if overalls_all else 0

    covered: set = set()
    for s in sessions:
        for c in (s.get("core_pcts") or {}):
            covered.add(c)
    coverage = len(covered) / _N_CORE

    W = READINESS_WEIGHTS["trajectory_window"]
    scores = [int(s.get("overall_0_100") or 0) for s in sessions[-W:]]
    if len(scores) >= 3:
        trajectory = (scores[-1] - scores[0]) / len(scores)
        trajectory_bonus = min(1.1, max(0.9, 1.0 + trajectory / 100))
    else:
        trajectory_bonus = 1.0

    dates = sorted({_parse_dt(s.get("completed_at")).date() for s in sessions
                    if _parse_dt(s.get("completed_at"))})
    if dates:
        span = (dates[-1] - dates[0]).days + 1
        consistency = min(1.0, len(dates) / max(1, span))
        days_span = span
        last_date = dates[-1]
        days_since_last = (now.date() - last_date).days
    else:
        consistency, days_span, days_since_last = 1.0, 1, 0
    consistency_bonus = 0.9 + 0.1 * consistency

    if days_since_last <= 7:
        recency_factor, stale = 1.0, False
    elif days_since_last <= 30:
        recency_factor, stale = 0.95, False
    elif days_since_last <= 60:
        recency_factor, stale = 0.9, True
    else:
        recency_factor, stale = 0.85, True

    SW = READINESS_WEIGHTS["safety_window"]
    recent = sessions[-SW:]
    n_safe_recent = sum(1 for s in recent if s.get("safety_triggered"))
    safety_factor = max(READINESS_WEIGHTS["safety_floor_factor"],
                        1.0 - READINESS_WEIGHTS["safety_step"] * n_safe_recent)
    cap_window = sessions[-READINESS_WEIGHTS["safety_cap_window"]:]
    safety_capped = any(s.get("safety_triggered") for s in cap_window)
    n_osce = sum(1 for s in sessions if s.get("is_osce"))
    no_osce = (n_osce == 0)

    try:
        n_crit = max(0, int(critical_errors or 0))
    except (TypeError, ValueError):
        n_crit = 0
    error_penalty = min(READINESS_WEIGHTS["error_penalty_cap"],
                        n_crit * READINESS_WEIGHTS["error_penalty_per_critical"])

    raw = base * trajectory_bonus * consistency_bonus
    cov_adj = raw * ((1.0 - READINESS_WEIGHTS["coverage_blend"])
                     + READINESS_WEIGHTS["coverage_blend"] * coverage)
    rec_adj = cov_adj * recency_factor * safety_factor
    final = max(0, min(100, round(rec_adj - error_penalty)))

    caps_applied: list[str] = []
    if safety_capped:
        final = min(final, READINESS_WEIGHTS["safety_cap_recent"])
        caps_applied.append(f"safety:{READINESS_WEIGHTS['safety_cap_recent']}")
    if no_osce and n > 0:
        final = min(final, READINESS_WEIGHTS["no_osce_cap"])
        caps_applied.append(f"no_osce:{READINESS_WEIGHTS['no_osce_cap']}")
    if n == 1:
        final = min(final, READINESS_WEIGHTS["single_session_cap"])
        caps_applied.append(f"evidence_n1:{READINESS_WEIGHTS['single_session_cap']}")
    elif n == 2:
        final = min(final, READINESS_WEIGHTS["two_session_cap"])
        caps_applied.append(f"evidence_n2:{READINESS_WEIGHTS['two_session_cap']}")

    if n >= 10:
        confidence = "medium" if stale else "high"
    elif n >= 5:
        confidence = "medium"
    elif n >= 3:
        confidence = "low"
    else:
        confidence = "low"
    if stale and confidence == "high":
        confidence = "medium"

    if n < 3:
        state = "Building"
    else:
        state = interpret_score(final)["level"]

    drivers: list[dict] = []
    drivers.append({"factor": "proficiency", "direction": "info",
                    "detail": f"Weighted skill average {round(base, 1)} across {len(dims)} dimensions."})
    drivers.append({"factor": "coverage", "direction": "+/-",
                    "detail": f"{len(covered)}/{_N_CORE} OSCE core domains observed."})
    if trajectory_bonus > 1.0:
        drivers.append({"factor": "trajectory", "direction": "+",
                        "detail": "Recent scores are improving."})
    elif trajectory_bonus < 1.0:
        drivers.append({"factor": "trajectory", "direction": "-",
                        "detail": "Recent scores are declining — practise consistently."})
    if consistency < 1.0:
        drivers.append({"factor": "consistency", "direction": "-",
                        "detail": "Practice days are irregular — daily practice builds readiness."})
    if n_safe_recent:
        drivers.append({"factor": "safety", "direction": "-",
                        "detail": f"{n_safe_recent} safety gate(s) triggered in the last {len(recent)} sessions — review red flags and urgent steps."})
    if safety_capped:
        drivers.append({"factor": "safety_cap", "direction": "cap",
                        "detail": f"A recent safety failure caps readiness at {READINESS_WEIGHTS['safety_cap_recent']} until remediated."})
    if no_osce:
        drivers.append({"factor": "osce", "direction": "cap",
                        "detail": f"No integrated OSCE session yet — Practice-only history caps readiness at {READINESS_WEIGHTS['no_osce_cap']}."})
    if n < 3:
        drivers.append({"factor": "evidence", "direction": "cap",
                        "detail": f"Only {n} session(s) — not enough evidence for a reliable estimate. Keep practising."})
    if stale:
        drivers.append({"factor": "recency", "direction": "-",
                        "detail": f"Last session was {days_since_last} days ago — performance may be stale."})
    if error_penalty:
        drivers.append({"factor": "critical_errors", "direction": "-",
                        "detail": f"{n_crit} unresolved critical reasoning error(s) (-{error_penalty})."})
    if caps_applied:
        drivers.append({"factor": "caps", "direction": "info",
                        "detail": f"Caps applied: {', '.join(caps_applied)}."})

    claimable = {d: v for d, v in dims.items() if len(dim_accum.get(d, [])) >= 2}
    strengths = sorted(claimable, key=claimable.get, reverse=True)[:2]
    needs_work = sorted(claimable, key=claimable.get)[:2]

    core_dimensions = {
        c: round(sum(s.get("core_pcts", {}).get(c, 0) for s in sessions if c in (s.get("core_pcts") or {}))
                 / max(1, sum(1 for s in sessions if c in (s.get("core_pcts") or {}))), 1)
        for c in covered
    }

    return {
        "version": READINESS_VERSION,
        "score": final,
        "confidence": confidence,
        "state": state,
        "session_count": n,
        "base_score": round(base),
        "trajectory_bonus": round(trajectory_bonus, 2),
        "consistency_bonus": round(consistency_bonus, 2),
        "error_penalty": error_penalty,
        "dimensions": dims,
        "core_dimensions": core_dimensions,
        "components": {
            "proficiency": round(base, 1),
            "coverage": round(coverage, 2),
            "domains_covered": len(covered),
            "safety_factor": round(safety_factor, 2),
            "safety_triggers_recent": n_safe_recent,
            "safety_capped": safety_capped,
            "consistency": round(consistency, 2),
            "recency_factor": recency_factor,
            "stale": stale,
            "osce_sessions": n_osce,
            "caps_applied": caps_applied,
            "weights": "native_dims_renormalized",
        },
        "drivers": drivers,
        "strengths": strengths,
        "needs_work": needs_work,
        "evidence": {"sessions": n, "osce_sessions": n_osce,
                     "domains_covered": len(covered),
                     "days_span": days_span, "days_since_last": days_since_last},
        "interpretation": interpret_score(final),
    }
