"""Qora Mentor — case selection algorithm (PRD_QORA_MENTOR §4.1.2).

Input: extracted context + available cases (CaseV2 objects from v2_catalog).
Output: ordered list of {day, case_id, ...} assignments.

Design notes (adapted from PRD sketch to the real 92-case catalog + schema):
- Level map: preklinik=1, koas=2, ppds=3 (default koas).
- Weakness specialties are prioritized (come first; the journey still mixes in
  some variety — "prioritize", not "only").
- Foundational → advanced: red-flag count asc, then difficulty asc, then time.
- Schema constraint `UNIQUE(journey_id, day_number)` → exactly ONE case/day.
  Cap 21 cases/journey; when total < timeline, cases are spread across the
  whole span with the mock exam on the final day.
- Timeline >= 3 days guarantees at least one osce_full case in the mix.
"""
from __future__ import annotations

import logging

_log = logging.getLogger("mentor.case_selector")


# Indonesian + English aliases → catalog specialty ids (content/cases/*.md).
SPECIALTY_ALIASES: dict[str, str] = {
    # paediatrics
    "paediatrics": "paediatrics", "pediatrics": "paediatrics",
    "pediatrik": "paediatrics", "anak": "paediatrics",
    "ilmu_kesehatan_anak": "paediatrics", "paediatric": "paediatrics",
    # surgery
    "surgery": "surgery", "bedah": "surgery", "operasi": "surgery",
    "ilmu_bedah": "surgery",
    # internal medicine
    "internal_medicine": "internal_medicine", "penyakit_dalam": "internal_medicine",
    "internis": "internal_medicine", "internal": "internal_medicine",
    # dermatology
    "dermatology": "dermatology", "dermatologi": "dermatology", "kulit": "dermatology",
    "dermato": "dermatology",
    # emergency
    "emergency": "emergency", "gawat_darurat": "emergency", "igd": "emergency",
    "emergensi": "emergency",
    # ENT
    "ent": "ent", "tht": "ent", "telinga_hidung_tenggorok": "ent",
    # neurology
    "neurology": "neurology", "neurologi": "neurology", "saraf": "neurology",
    "neuro": "neurology",
    # obstetrics & gynaecology
    "obstetrics_gynaecology": "obstetrics_gynaecology",
    "obgyn": "obstetrics_gynaecology", "obstetri": "obstetrics_gynaecology",
    "kandungan": "obstetrics_gynaecology",
    "obstetrics": "obstetrics_gynaecology", "ginekologi": "obstetrics_gynaecology",
    # ophthalmology
    "ophthalmology": "ophthalmology", "oftalmologi": "ophthalmology", "mata": "ophthalmology",
    "ophthal": "ophthalmology",
    # psychiatry
    "psychiatry": "psychiatry", "psikiatri": "psychiatry", "jiwa": "psychiatry",
    "kejiwaan": "psychiatry",
}


def map_weaknesses(weaknesses: list | None) -> list[str]:
    """Normalize user-reported weaknesses to catalog specialty ids."""
    out: list[str] = []
    for w in weaknesses or []:
        key = str(w).strip().lower().replace(" ", "_").replace("-", "_")
        sid = SPECIALTY_ALIASES.get(key) or SPECIALTY_ALIASES.get(str(w).strip().lower())
        if sid and sid not in out:
            out.append(sid)
    return out


def build_fallback_proposal(context: dict, selected: list[dict]) -> dict:
    """Deterministic template proposal — used when the LLM returns garbage
    (risk mitigation per PRD §12: 'template fallback')."""
    days = max(1, min(90, int(context.get("timeline_days") or 7)))
    start = max(0, min(90, int(context.get("confidence_score") or 0)))
    target = max(start + 20, 80)
    weaknesses = context.get("weaknesses") or []
    label = (weaknesses[0].replace("_", " ").title()
             if weaknesses else "Clinical")
    return {
        "package_name": f"{label} {days}-Day Journey",
        "duration_days": days,
        "cases": selected,
        "reasoning": (
            "Disusun dari presentasi umum ke kompleks, ditutup mock exam di hari "
            f"terakhir. Fokus pada {' & '.join(weaknesses) if weaknesses else 'area klinis utama'}."
        ),
        "readiness_start": start,
        "readiness_target": min(target, 95),
        "milestones": [
            {"day": max(1, days // 2), "checkpoint": "Foundational skills mastered"},
            {"day": days, "checkpoint": "Ready for exam"},
        ],
    }


# ---------------------------------------------------------------------------
# FASE 10 — multi-day planner over V3 families (V2 retired from planning).
# ---------------------------------------------------------------------------

def _library_pool(ctx: dict, level: str) -> list[dict]:
    """Family candidates mirroring the live library: every non-draft family
    with servable variants for the stage (reviewed families rank higher via
    review_rank in rank_candidates — same content the library already serves)."""
    try:
        from app.domains.mentor import planning_policy as pp
        from app.domains.sessions.progress_adapter import cached_registry
    except Exception:  # noqa: BLE001
        return []
    try:
        reg = cached_registry()
        fams = [f for f in (getattr(reg, "families", {}) or {}).values()
                if str(getattr(f, "status", "") or "") != "draft"]
    except Exception:  # noqa: BLE001
        return []
    target = ctx.get("target_specialty")
    weaknesses = list(ctx.get("weaknesses") or [])
    keep = [f for f in fams
            if getattr(f, "primary_specialty", None) in ([target] if target else []) + weaknesses]
    if not keep:
        keep = list(fams)
    out = []
    for fam in keep:
        try:
            cand = pp.build_candidate_from_family(reg, fam, level)
        except Exception:  # noqa: BLE001
            cand = None
        if cand:
            out.append(cand)
    return out


def select_journey_cases(ctx: dict, cases: list | None = None, *, budget_default: int = 45) -> list[dict]:
    """Deterministic multi-day plan over V3 families.

    `cases` is accepted and ignored (legacy signature); the pool is always
    the live library families. Workload comes from minutes/day (one
    encounter/day, estimated at the daily budget — never a fixed cases/day
    count). Days 1..N-1 progress Foundation → Reasoning (difficulty
    ascending); the final day is always an integrated OSCE mock. Every row
    carries the planner's reason so the mission screen can answer "why this
    case?" without LLM invention.
    """
    ctx = ctx or {}
    try:
        days = max(1, min(21, int(ctx.get("timeline_days") or 7)))
    except (TypeError, ValueError):
        days = 7
    try:
        budget = int(ctx.get("available_minutes_per_day") or budget_default)
    except (TypeError, ValueError):
        budget = budget_default
    level = str(ctx.get("level") or "koas").lower()
    goal = str(ctx.get("goal") or "general").lower()
    target = ctx.get("target_specialty")
    weaknesses = list(ctx.get("weaknesses") or [])

    from app.domains.mentor import planning_policy as pp
    pool = _library_pool(ctx, level)
    if not pool:
        return []

    ranked = pp.rank_candidates(pool, ctx, day=days, duration_days=days)
    chosen = ranked[:days]
    if not chosen:
        return []

    # Integrated mock on the final day: hardest osce_full in the pool.
    osce_pool = [c for c in pool if str(c.get("mode")) == "osce_full"]
    mock = None
    if osce_pool:
        mock = sorted(osce_pool, key=lambda c: (-int(c.get("difficulty", 2) or 2), str(c.get("ref"))))[0]
        if all(c["ref"] != mock["ref"] for c in chosen):
            chosen = chosen[:-1] + [dict(mock)] if len(chosen) >= 1 else [dict(mock)]
    rest = [c for c in chosen if mock is None or c["ref"] != mock["ref"]]
    # Educational progression on days 1..N-1: history-taking before full
    # OSCE arcs, easier before harder (relevance already decided membership).
    rest.sort(key=lambda c: (1 if str(c.get("mode")) == "osce_full" else 0,
                             int(c.get("difficulty", 2) or 2), str(c.get("ref"))))
    ordered = rest + ([dict(mock)] if mock is not None else [])

    out = []
    for i, cand in enumerate(ordered[:days]):
        day_no = i + 1
        spec = cand.get("specialty") or "unknown"
        is_mock = mock is not None and cand.get("ref") == mock.get("ref") and day_no == len(ordered[:days])
        reasons = []
        if target and spec == target:
            reasons.append(f"matches your {str(target).replace('_', ' ')} focus")
        elif spec in weaknesses:
            reasons.append(f"targets your weak area ({str(spec).replace('_', ' ')})")
        else:
            reasons.append("breadth coverage for the exam")
        if cand.get("kind") == "v3_family":
            reasons.append("reviewed canonical content")
        if is_mock:
            reasons.append("integrated OSCE mock")
        elif day_no <= max(1, days // 3):
            reasons.append("foundation first")
        title = cand.get("title") or cand.get("ref")
        focus = cand.get("presentation") or title
        out.append({
            "day": day_no,
            "case_id": cand.get("ref"),
            "kind": cand.get("kind") or "v2",
            "specialty": spec,
            "mode": cand.get("mode") or ("osce_full" if is_mock else "anamnesis"),
            "difficulty": cand.get("difficulty", 2),
            "estimated_minutes": budget,
            "slot_type": "core",
            "selection_reason": f"Day {day_no}: {title} — " + "; ".join(reasons) + ".",
            "focus_area": focus,
            "learning_objective": f"Train {str(focus).lower()} toward {goal} readiness",
            "title": title,
            "presentation": cand.get("presentation") or "",
        })
    return out
