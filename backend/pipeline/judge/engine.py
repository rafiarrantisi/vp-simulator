"""Phase 7D — deterministic score engine (plan §17-18, §20-21).

Server owns arithmetic, weights, aggregation, safety, caps, overtime.
The LLM (future semantic adjudicator / feedback composer) NEVER does
arithmetic here: overall/domain scores are recomputed from the ledger.
Safety outranks checklist accumulation (§18): a catastrophic safety error
caps the overall and forces feedback, no "82 — Great job!".
"""

from __future__ import annotations

from pipeline.judge.domains import CRITICALITY_WEIGHTS, mode_params, resolve_learner_stage

OVERTIME_PENALTY = 10
GATE_TYPES = (
    "missed_critical_red_flag",
    "unsafe_management",
    "failed_urgent_referral",
    "failure_to_stabilize",
    "unsafe_discharge",
    "dangerous_contraindication",
)
_SAFETY_CRITICALITIES = ("safety-critical",)


def aggregate_scores(
    ledger: list,
    *,
    learner_stage: str = "koas",
    mode: str = "practice",
    overtime: bool = False,
) -> dict:
    """Aggregate ledger → domain scores + overall 0..100 (deterministic).

    Per domain: weighted mean of item scores (criticality-weighted) scaled
    to the learner-profile domain weight. Overall: sum of domain
    contributions (0..100). Overtime subtracts a fixed penalty.
    """
    from pipeline.judge.domains import domain_weights

    weights = domain_weights(learner_stage)
    by_domain: dict = {}
    for entry in ledger:
        d = getattr(entry, "domain", "history")
        slot = by_domain.setdefault(
            d, {"earned": 0.0, "possible": 0.0, "items": 0, "hits": 0}
        )
        w = CRITICALITY_WEIGHTS.get(getattr(entry, "criticality", "routine"), 1)
        slot["earned"] += float(getattr(entry, "score_0_3", 0)) * w
        slot["possible"] += 3.0 * w
        slot["items"] += 1
        if getattr(entry, "adjudication", "") == "hit":
            slot["hits"] += 1
    per_domain: dict = {}
    overall = 0.0
    for domain, w in weights.items():
        slot = by_domain.get(domain, {"earned": 0.0, "possible": 0.0, "items": 0, "hits": 0})
        frac = slot["earned"] / slot["possible"] if slot["possible"] else 0.0
        score = round(frac * w, 1)
        per_domain[domain] = {
            "score": score,
            "max": w,
            "pct": round(frac * 100, 1),
            "items": slot["items"],
            "hits": slot["hits"],
        }
        overall += score
    overall = int(round(max(0.0, min(100.0, overall))))
    penalty = 0
    if overtime:
        penalty = OVERTIME_PENALTY
        overall = max(0, overall - penalty)
    return {
        "per_domain": per_domain,
        "overall": overall,
        "overtime_penalty": penalty if penalty else None,
    }


def evaluate_safety_gates(
    ledger: list,
    record=None,
    *,
    treatment_grade: dict | None = None,
    diagnosis_status: str = "",
) -> list[dict]:
    """Deterministic safety evaluation from evidence + grades.

    Rules (§18): missed safety-critical items with no evidence, unsafe
    treatment outcomes, dangerous diagnosis misses, and explicit
    unsafe-discharge / failed-referral signals in management text.
    """
    gates: list = []

    def _texts(ch: str) -> list[str]:
        if record is None:
            return []
        try:
            return [t for t in record.channel_texts(ch) if (t or "").strip()]
        except Exception:
            return []

    mgmt_blob = " ".join(_texts("management") + _texts("medication")).lower()
    dx_blob = " ".join(_texts("diagnosis")).lower()
    missed_safety = [
        e
        for e in ledger
        if getattr(e, "criticality", "") in _SAFETY_CRITICALITIES
        and getattr(e, "score_0_3", 0) == 0
    ]
    if missed_safety:
        first = missed_safety[0]
        gates.append(
            {
                "type": "missed_critical_red_flag",
                "detail": f"Missed {len(missed_safety)} safety-critical item(s); e.g. '{getattr(first, 'expected', '')[:120]}'",
                "catastrophic": True,
            }
        )
    if (treatment_grade or {}).get("outcome") == "unsafe":
        gates.append(
            {
                "type": "unsafe_management",
                "detail": f"Unsafe medication: {(treatment_grade or {}).get('detail', '')[:160]}",
                "catastrophic": True,
            }
        )
    if diagnosis_status == "dangerous_miss":
        gates.append(
            {
                "type": "unsafe_management",
                "detail": "Dangerous diagnosis miss: life-threatening condition not recognized",
                "catastrophic": True,
            }
        )
    discharge_markers = (
        "pulang",
        "discharge",
        "rawat jalan",
        "outpatient",
        "observe at home",
        "home observation",
    )
    urgent_markers = (
        "rujuk",
        "refer",
        "igd",
        "emergency",
        "gawat",
        "resusitasi",
        "stabil",
        "stabilis",
    )
    if (
        any(m in mgmt_blob for m in discharge_markers)
        and not any(m in mgmt_blob for m in urgent_markers)
        and any(getattr(e, "criticality", "") in _SAFETY_CRITICALITIES for e in ledger)
    ):
        gates.append(
            {
                "type": "unsafe_discharge",
                "detail": "Discharge/outpatient plan without stabilization or urgent referral despite safety-critical expectations",
                "catastrophic": True,
            }
        )
    if ("rujuk" in dx_blob or "refer" in dx_blob) and not any(
        m in mgmt_blob for m in urgent_markers
    ):
        gates.append(
            {
                "type": "failed_urgent_referral",
                "detail": "Referral need recognized but no urgent referral/stabilization action recorded",
                "catastrophic": False,
            }
        )
    seen: dict = {}
    for g in gates:
        if g["type"] not in seen:
            seen[g["type"]] = g
    allowed = set(GATE_TYPES)
    return [g for t, g in seen.items() if t in allowed]


def apply_safety_caps(
    overall: int,
    gates: list[dict],
    *,
    mode: str = "practice",
) -> dict:
    """Safety outranks checklist accumulation (§18). Returns capped overall."""
    params = mode_params(mode)
    if not gates:
        return {"overall": overall, "capped": False, "cap": None}
    catastrophic = any(g.get("catastrophic") for g in gates)
    cap = params["catastrophic_cap"] if catastrophic else params["safety_cap"]
    if overall > cap:
        return {"overall": cap, "capped": True, "cap": cap}
    return {"overall": overall, "capped": False, "cap": cap}


def grade_diagnosis_hierarchy(
    submitted_primary: str,
    *,
    canonical: str,
    synonyms: list[str] | None = None,
    family_terms: list[str] | None = None,
    dangerous_miss_terms: list[str] | None = None,
) -> dict:
    """Diagnosis grading hierarchy (plan §19), deterministic.

    exact(+severity) > family-correct-but-incomplete > broad/partial >
    incorrect > dangerous miss. Uses the same adjudicator so wording
    differences never decide alone.
    """
    from pipeline.judge.semantic import adjudicate

    sub = (submitted_primary or "").strip()
    if not sub:
        return {"grade": "incorrect", "status": "miss", "detail": "no diagnosis submitted → no credit"}
    adj = adjudicate(canonical, [sub], synonyms=(synonyms or []), kind="diagnosis")
    if adj.status == "hit" and adj.score_0_3 == 3:
        return {"grade": "exact", "status": "hit", "detail": adj.reason}
    for term in dangerous_miss_terms or []:
        t = adjudicate(term, [sub], kind="diagnosis")
        if t.status == "hit":
            return {
                "grade": "dangerous_miss",
                "status": "dangerous_miss",
                "detail": f"dangerous miss pattern: '{term}'",
            }
    if adj.status == "partial":
        return {"grade": "family_incomplete", "status": "partial", "detail": adj.reason}
    for fam in family_terms or []:
        f = adjudicate(fam, [sub], kind="diagnosis")
        if f.status in ("hit", "partial"):
            return {
                "grade": "broad",
                "status": "partial",
                "detail": f"broad but partially relevant ('{fam}')",
            }
    return {"grade": "incorrect", "status": "miss", "detail": "incorrect diagnosis"}


def resolve_stage(stage: str) -> str:
    return resolve_learner_stage(stage)
