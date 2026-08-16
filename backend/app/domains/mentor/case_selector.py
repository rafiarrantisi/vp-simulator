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

LEVEL_MAP = {"preklinik": 1, "koas": 2, "ppds": 3}
LEVEL_NAMES = {1: "preklinik", 2: "koas", 3: "ppds"}

MAX_JOURNEY_CASES = 21  # cap: 1 case/day, at most 3 weeks of grind

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


def _level_to_difficulty(context: dict) -> int:
    level = (context.get("level") or "koas").lower()
    return LEVEL_MAP.get(level, 2)


def _red_flag_count(case) -> int:
    try:
        return len(case.red_flag_items())
    except Exception:  # noqa: BLE001
        return 0


def _sort_key(case):
    """Foundational → advanced: fewer red flags first, then easier, then quicker."""
    return (_red_flag_count(case), case.frontmatter.get("difficulty", 2),
            case.frontmatter.get("estimated_minutes", 15))


def _case_dict(case, day: int) -> dict:
    fm = case.frontmatter
    return {
        "day": day,
        "case_id": case.id,
        "specialty": fm.get("specialty"),
        "presentation": fm.get("presentation"),
        "target_condition": fm.get("target_condition"),
        "mode": fm.get("mode_default", "anamnesis"),
        "difficulty": fm.get("difficulty", 2),
        "estimated_minutes": fm.get("estimated_minutes", 15),
        "focus_area": fm.get("presentation") or f"Anamnesis {fm.get('specialty', '')}".strip(),
        "learning_objective": (
            f"Menguasai tatalaksana pada presentasi '{fm.get('presentation')}'"
        ),
    }


def select_cases(context: dict, cases: list) -> list[dict]:
    """Core selection: filter → prioritize weaknesses → order → assign days."""
    target = _level_to_difficulty(context)
    timeline = max(1, min(90, int(context.get("timeline_days") or 7)))
    weaknesses = map_weaknesses(context.get("weaknesses"))

    # 1. Filter by level (difficulty). Exact pool first; when it can't fill the
    #    timeline, extend with adjacent difficulties (same specialty preferred)
    #    so short specialty pools still produce a full journey.
    exact = [c for c in cases if c.frontmatter.get("difficulty") == target]
    pool = list(exact)
    if len(pool) < timeline:
        for adj in (target - 1, target + 1):
            if adj in (1, 2, 3):
                pool += [c for c in cases
                         if c.frontmatter.get("difficulty") == adj and c not in pool]
            if len(pool) >= timeline:
                break

    # 2. Prioritize weaknesses: weakness-specialty cases first, each group
    #    ordered foundational → advanced (sorting must NOT destroy priority).
    weak = [c for c in pool if c.frontmatter.get("specialty") in weaknesses]
    rest = [c for c in pool if c.frontmatter.get("specialty") not in weaknesses]
    ordered = sorted(weak, key=_sort_key) + sorted(rest, key=_sort_key)
    if not ordered:
        return []

    # 3. Mode mix: timeline >= 3 days → guarantee >= 1 osce_full, preferring
    #    the weakness specialty, then same difficulty, then any.
    if timeline >= 3 and not any(c.frontmatter.get("mode_default") == "osce_full"
                                 for c in ordered):
        for bucket in (
            [c for c in cases if c.frontmatter.get("mode_default") == "osce_full"
             and c not in ordered and c.frontmatter.get("specialty") in weaknesses],
            [c for c in cases if c.frontmatter.get("mode_default") == "osce_full"
             and c not in ordered and c.frontmatter.get("difficulty") == target],
            [c for c in cases if c.frontmatter.get("mode_default") == "osce_full"
             and c not in ordered],
        ):
            if bucket:
                pick = sorted(bucket, key=_sort_key)[0]
                ordered.insert(len(ordered) // 2, pick)
                break

    # 4. Budget: ONE case per day (schema UNIQUE constraint), capped at 21.
    total = min(len(ordered), timeline, MAX_JOURNEY_CASES)
    chosen = ordered[:total]

    # 5. Mock exam on the final day: the hardest case (max difficulty, max RF).
    hardest = max(chosen, key=lambda c: (c.frontmatter.get("difficulty", 2), _red_flag_count(c)))
    chosen = [c for c in chosen if c is not hardest]

    assigned: list[dict] = []
    n = len(chosen)
    for i, case in enumerate(chosen):
        # Spread non-mock cases across days 1..timeline-1 (final day = mock exam).
        day = 1 + round(i * (timeline - 2) / max(1, n - 1)) if n > 1 else 1
        assigned.append(_case_dict(case, day))
    assigned.append(_case_dict(hardest, timeline))  # mock exam: final day

    assigned.sort(key=lambda d: d["day"])
    _log.info("select_cases: %d cases over %d days (level=%s, weaknesses=%s)",
              len(assigned), timeline, LEVEL_NAMES.get(target, target), weaknesses)
    return assigned


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
