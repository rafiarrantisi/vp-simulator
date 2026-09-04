"""Qora Mentor — planning policy (FASE 10, Adaptive Mentor V1).

Deterministic curriculum decisions over eligible content. Principle:
**LLM understands and explains, the Qora planning engine decides.**
This module takes NO LLM input, so model suggestions structurally cannot
override hard exclusions (pinned by test).

Two content kinds flow through one candidate schema so V3 families and V2
cases are ranked by the same engine::

    {"kind": "v3_family" | "v2", "ref": <family id | case id>,
     "specialty": <id>, "difficulty": 1..5, "mode": "osce_full" | "anamnesis",
     "review_rank": int, "title": str, "presentation": str,
     "estimated_minutes": int}

Hard exclusions (any one drops the candidate):
- unknown/empty ref, unknown kind;
- V3 family not in the registry, or status outside human-reviewed states
  (draft / ai_generated / research_complete / in_review / needs_update /
  superseded / retired are NOT auto-plannable — human-gated by design);
- learner stage not in the family's target stages (or none of the active
  variants supports the stage);
- difficulty outside 1..5; review_rank < 0 (unreviewed / LLM-invented).

Scoring (all deterministic, stable-sorted by (-score, ref)):
- target-specialty match +3, weakness match +2 (each);
- review_rank +0.5/rank (reviewed truth preferred, never decisive alone);
- difficulty fit to learner level (koas→2, preklinik→1, ppds→3): exact +1.5,
  adjacent +0.5;
- day-phase fit: early days (first third) prefer anamnesis/foundation (+0.5),
  final day prefers osce_full mock (+1.0);
- time fit: estimated_minutes within daily budget +0.5;
- novelty: ref in ctx seen_case_ids → −2 (spaced repetition, not a ban —
  remediation intentionally repeats the same family with a different
  variant; exact-variant dedupe happens at session start).
"""
from __future__ import annotations

import logging

_log = logging.getLogger("mentor.planning_policy")

# Statuses a human reviewer has actually signed (pipeline vocab
# HUMAN_REVIEWED_STATES). Everything else is human-gated, never auto-planned.
HUMAN_REVIEWED_STATES = frozenset({"clinically_reviewed", "pilot_verified", "published"})

_LEVEL_DIFFICULTY = {"preklinik": 1, "koas": 2, "ppds": 3, "general": 2}


def _stage_values(stages) -> set[str]:
    """LearnerStage enums stringify as 'LearnerStage.koas' — use .value."""
    out = set()
    for s in stages or []:
        v = getattr(s, "value", s)
        out.add(str(v).lower())
    return out


def eligible_v3_families(registry, learner_stage: str = "koas") -> list:
    """V3 families the planner may use: reviewed + stage-fit + has variants."""
    stage = (learner_stage or "koas").lower()
    out = []
    fams = getattr(registry, "families", {}) or {}
    for fid in sorted(fams):
        fam = fams[fid]
        if (getattr(fam, "status", "") or "") not in HUMAN_REVIEWED_STATES:
            continue
        if _stage_values(getattr(fam, "target_stages", None)) - {""}:
            if stage not in _stage_values(getattr(fam, "target_stages", None)):
                continue
        if not _family_variants_for_stage(registry, fam, stage):
            continue
        out.append(fam)
    return out


def _family_variants_for_stage(registry, fam, stage: str) -> list:
    """Active variants of a family supporting the learner stage (stable order)."""
    try:
        from pipeline.case_v3.runtime import _not_stage_compatible
    except Exception:  # noqa: BLE001 — conservative: keep registry-declared ids
        _not_stage_compatible = None
    out = []
    for vid in sorted(getattr(fam, "active_variant_ids", None) or []):
        v = (getattr(registry, "variants", {}) or {}).get(vid)
        if v is None:
            continue
        if _not_stage_compatible is not None:
            try:
                if _not_stage_compatible(v, stage):
                    continue
            except Exception:  # noqa: BLE001
                continue
        else:
            if _stage_values(getattr(v, "supported_stages", None)) - {""}:
                if stage not in _stage_values(getattr(v, "supported_stages", None)):
                    continue
        out.append(v)
    return out


def build_candidate_from_family(registry, fam, learner_stage: str = "koas") -> dict | None:
    """Map an eligible V3 family onto the planner candidate schema."""
    variants = _family_variants_for_stage(registry, fam, (learner_stage or "koas").lower())
    if not variants:
        return None
    status_rank = {"published": 3, "pilot_verified": 2, "clinically_reviewed": 1}.get(
        getattr(fam, "status", ""), 0)
    try:
        from app.domains.sessions.v3_compat_schemas import family_to_card, family_variant_count
        card = family_to_card(registry, fam, family_variant_count(registry, fam, learner_stage))
        mode = card.get("mode") or "anamnesis"
        title = card.get("title") or fam.id
        presentation = card.get("presentation") or ""
    except Exception:  # noqa: BLE001
        mode, title, presentation = "anamnesis", getattr(fam, "id", ""), ""
    return {
        "kind": "v3_family",
        "ref": getattr(fam, "id", ""),
        "specialty": getattr(fam, "primary_specialty", None) or "unknown",
        "difficulty": 2,
        "mode": mode,
        "review_rank": status_rank,
        "title": title,
        "presentation": presentation,
        "estimated_minutes": 15,
    }


def build_candidate_from_v2(case) -> dict | None:
    """Map a V2 catalog case onto the planner candidate schema."""
    try:
        fm = case.frontmatter or {}
    except Exception:  # noqa: BLE001
        return None
    if not getattr(case, "id", None):
        return None
    try:
        diff = int(fm.get("difficulty", 2))
    except (TypeError, ValueError):
        diff = 2
    return {
        "kind": "v2",
        "ref": case.id,
        "specialty": fm.get("specialty") or "unknown",
        "difficulty": diff,
        "mode": fm.get("mode_default", "anamnesis"),
        "review_rank": 0,
        "title": fm.get("presentation") or case.id,
        "presentation": fm.get("presentation") or "",
        "estimated_minutes": fm.get("estimated_minutes") or 15,
    }


def _is_excluded(cand: dict, registry=None) -> str | None:
    """Return an exclusion reason, or None when the candidate is eligible."""
    if not isinstance(cand, dict):
        return "not-a-candidate"
    ref = str(cand.get("ref") or "").strip()
    if not ref:
        return "empty-ref"
    kind = cand.get("kind") or ("v3_family" if ref.startswith("fam_") else "v2")
    try:
        diff = int(cand.get("difficulty", 2))
    except (TypeError, ValueError):
        return "bad-difficulty"
    if diff < 1 or diff > 5:
        return "difficulty-out-of-range"
    try:
        rank = int(cand.get("review_rank", 0))
    except (TypeError, ValueError):
        return "bad-review-rank"
    if rank < 0:
        return "unreviewed"
    if kind == "v3_family" and registry is not None:
        fams = getattr(registry, "families", {}) or {}
        fam = fams.get(ref)
        if fam is None:
            return "unknown-family"
        if (getattr(fam, "status", "") or "") not in HUMAN_REVIEWED_STATES:
            return "unreviewed-status"
    return None


def build_candidates(prior=(), *, registry=None, learner_stage: str = "koas") -> list[dict]:
    """Build planner candidates from registry families (deterministic, pure).

    Primary source is `eligible_v3_families` (human-reviewed + stage-fit);
    when nothing is eligible, fall back to reviewed families regardless of
    stage fit — still human-gated, never draft/AI content. Every candidate
    carries `review_state` (never "draft") so downstream can audit gating.
    `prior` (past session refs) is accepted for future novelty use and
    currently only normalizes input.
    """
    _ = list(prior or [])
    stage = (learner_stage or "koas").lower()
    fams = eligible_v3_families(registry, stage) if registry is not None else []
    if not fams and registry is not None:
        all_fams = getattr(registry, "families", {}) or {}
        fams = [
            all_fams[fid] for fid in sorted(all_fams)
            if (getattr(all_fams[fid], "status", "") or "") in HUMAN_REVIEWED_STATES
        ]
    out = []
    for fam in fams:
        cand = build_candidate_from_family(
            registry, fam, stage) if registry is not None else None
        if not cand:
            continue
        status = getattr(fam, "status", "") or ""
        cand["review_state"] = "reviewed" if status in HUMAN_REVIEWED_STATES else "unreviewed"
        out.append(cand)
    return out


def rank_candidates(candidates: list[dict], ctx: dict, *, day: int = 1,
                    duration_days: int = 7, registry=None) -> list[dict]:
    """Deterministically rank candidates for one plan day (stable, pure).

    Hard exclusions first (see module docstring); survivors score on
    specialty/weakness relevance, review rank, difficulty fit, day-phase,
    time budget and novelty. Ties break on ref so reruns are identical.
    """
    ctx = ctx or {}
    level = str(ctx.get("level") or "koas").lower()
    target = ctx.get("target_specialty")
    weaknesses = list(ctx.get("weaknesses") or [])
    try:
        budget = int(ctx.get("available_minutes_per_day") or 45)
    except (TypeError, ValueError):
        budget = 45
    want = _LEVEL_DIFFICULTY.get(level, 2)
    try:
        span = max(1, int(duration_days or 7))
        pos = min(1.0, max(0.0, int(day or 1) / span))
    except (TypeError, ValueError):
        pos = 0.0
    seen = set(ctx.get("seen_case_ids") or []) | set(ctx.get("recent_refs") or [])
    goal = str(ctx.get("goal") or "general").lower()

    scored: list[tuple[float, str, dict]] = []
    for cand in candidates or []:
        if _is_excluded(cand, registry) is not None:
            continue
        ref = str(cand.get("ref"))
        spec = cand.get("specialty")
        s = 0.0
        reasons: list[str] = []
        if target and spec == target:
            s += 3.0
            reasons.append("target-specialty")
        if spec in weaknesses:
            s += 2.0
            reasons.append("weakness")
        try:
            rank = int(cand.get("review_rank", 0) or 0)
            s += 0.5 * rank
            if rank > 0:
                reasons.append(f"reviewed-rank-{rank}")
        except (TypeError, ValueError):
            pass
        try:
            diff = int(cand.get("difficulty", 2))
        except (TypeError, ValueError):
            diff = 2
        if diff == want:
            s += 1.5
            reasons.append("difficulty-fit")
        elif abs(diff - want) == 1:
            s += 0.5
            reasons.append("difficulty-adjacent")
        mode = str(cand.get("mode") or "")
        if pos >= 0.85 and mode == "osce_full":
            s += 1.0  # final stretch: integrated mock
            reasons.append("final-mock")
        elif pos <= 0.34 and mode in ("anamnesis", "targeted", "blind"):
            s += 0.5  # foundation first
            reasons.append("foundation-first")
        if goal == "osce" and mode == "osce_full":
            s += 0.5
            reasons.append("osce-goal")
        try:
            if int(cand.get("estimated_minutes") or 0) <= budget:
                s += 0.5
                reasons.append("time-fit")
        except (TypeError, ValueError):
            pass
        if ref in seen:
            s -= 2.0  # spaced repetition: deprioritize, never ban here
            reasons.append("seen-novelty-penalty")
        enriched = dict(cand)
        enriched["_score"] = round(s, 2)
        enriched["_reasons"] = reasons
        scored.append((s, ref, enriched))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [dict(c) for _, _, c in scored]
