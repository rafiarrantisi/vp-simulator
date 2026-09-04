"""Phase 8 Task B — unified progress computation (plan §Phase 8-B, §43, §36).

Single source of truth for Result/Dashboard/Progress/Mentor derived metrics.
Every metric documents source sessions, window, and normalization (§36) in
the returned `definitions` block. No invented numbers (§3.7): sparse data
returns honest low-evidence flags instead of fabricated percentages.

Metric definitions (§43):
- total_sessions: COMPLETED sessions with a stored report only (Practice +
  OSCE, all-time unless `window_days` is given). Started-but-abandoned and
  failed-scoring sessions never inflate this.
- avg_score: arithmetic mean of session overall_0_100 over in-scope
  sessions. Cross-version note: V2 and V3-compat overalls are both 0..100
  examiner-style overall scores, so a plain mean is the documented,
  least-surprising normalization. Sessions with no numeric overall are
  excluded (and counted in `excluded_no_score`).
- skill score: recency-weighted mean per native dim over the last 20
  in-scope sessions (linear rank weights: most recent session weighs most).
  Dims observed <2 times are flagged low_evidence and excluded from
  strongest/weakest claims.
- specialty coverage: explicit counts — sessions per specialty, distinct
  families, distinct variants. A count is NEVER labelled mastery.
"""
from __future__ import annotations

from datetime import datetime, timezone

PROGRESS_VERSION = "qora-progress-1.0"
_SKILL_WINDOW = 20


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime | None:
    if value is None:
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


def _rank_weights(n: int) -> list[float]:
    """Linear rank weights oldest->newest: 1..n normalized (recent matters)."""
    if n <= 0:
        return []
    if n == 1:
        return [1.0]
    total = n * (n + 1) / 2.0
    return [(i + 1) / total for i in range(n)]


def compute_progress(sessions: list[dict], *, window_days: int | None = None, now: datetime | None = None) -> dict:
    """Derive unified progress from normalized sessions (oldest->newest input
    preferred; output history is most-recent-first like the V2 contract)."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    sessions = [s for s in (sessions or []) if isinstance(s, dict)]
    if window_days is not None:
        cutoff = now.timestamp() - window_days * 86400
        sessions = [
            s for s in sessions
            if (_parse_dt(s.get("completed_at")) is not None
                and _parse_dt(s.get("completed_at")).timestamp() >= cutoff)
        ]
    scored: list[dict] = []
    for s in sessions:
        try:
            float(s.get("overall_0_100"))
            scored.append(s)
        except (TypeError, ValueError):
            continue
    excluded = len(sessions) - len(scored)
    overalls = [int(float(s.get("overall_0_100"))) for s in scored]
    avg = round(sum(overalls) / len(overalls), 1) if overalls else 0

    window = scored[-_SKILL_WINDOW:]
    weights = _rank_weights(len(window))
    dim_vals: dict[str, list[tuple[float, float]]] = {}
    for s, w in zip(window, weights):
        for dim, pct in (s.get("dim_pcts") or {}).items():
            try:
                dim_vals.setdefault(str(dim), []).append((float(pct), w))
            except (TypeError, ValueError):
                continue
    dim_avg: dict[str, float] = {}
    dim_detail: dict[str, dict] = {}
    for dim, pairs in dim_vals.items():
        wsum = sum(w for _, w in pairs)
        avg_d = sum(v * w for v, w in pairs) / wsum if wsum else 0
        n_obs = len(pairs)
        vals = [v for v, _ in pairs]
        # Trend: mean(last 3) - mean(first 3), rounded to 1 decimal.
        try:
            last_mean = sum(vals[-3:]) / len(vals[-3:])
            first_mean = sum(vals[:3]) / len(vals[:3])
            trend = round(last_mean - first_mean, 1)
        except (TypeError, ValueError, ZeroDivisionError):
            trend = 0.0
        dim_avg[dim] = round(avg_d, 1)
        dim_detail[dim] = {"avg": round(avg_d, 1), "n": n_obs, "trend": trend,
                           "low_evidence": n_obs < 2}
    claimable = {k: v for k, v in dim_avg.items() if not dim_detail[k].get("low_evidence")}
    strongest = max(claimable, key=claimable.get) if claimable else None
    weakest = min(claimable, key=claimable.get) if claimable else None

    spec_counts: dict[str, int] = {}
    for s in scored:
        sp = str(s.get("specialty") or "unknown")
        spec_counts[sp] = spec_counts.get(sp, 0) + 1
    families = {s.get("family_id") for s in scored if s.get("family_id")}
    variants = {s.get("variant_id") for s in scored if s.get("variant_id")}
    distinct_cases = {str(s.get("case_id")) for s in scored if s.get("case_id")}

    history = [
        {"ts": s.get("completed_at") or _iso_now(),
         "caseId": s.get("case_id") or "",
         "specialty": str(s.get("specialty") or "unknown"),
         "overall": int(s.get("overall_0_100") or 0),
         "dims": {str(k): int(v) for k, v in (s.get("dim_pcts") or {}).items()}}
        for s in reversed(scored)
    ]

    recent_improvement = None
    if len(overalls) >= 4:
        prev = overalls[-6:-3] or overalls[:-3]
        last = overalls[-3:]
        if prev:
            recent_improvement = round(sum(last) / len(last) - sum(prev) / len(prev), 1)

    n_osce = sum(1 for s in scored if s.get("is_osce"))
    return {
        "version": PROGRESS_VERSION,
        "totalSessions": len(scored),
        "excludedNoScore": excluded,
        "avgScore": avg,
        "hasEvidence": len(scored) > 0,
        "dimensionAverages": dim_avg,
        "dimensionDetail": dim_detail,
        "strongestSkill": strongest,
        "weakestSkill": weakest,
        "recentImprovement": recent_improvement,
        "specialtyCounts": spec_counts,
        "coverage": {
            "specialties": len(spec_counts),
            "familiesCompleted": len(families),
            "variantsCompleted": len(variants),
            "distinctCases": len(distinct_cases),
            "osceSessions": n_osce,
            "practiceSessions": len(scored) - n_osce,
        },
        "sessions": history,
        "badgeMetrics": {
            "cases": len(distinct_cases),
            "specialties": len(spec_counts),
            "avg_score": avg,
            "sessions": len(scored),
        },
        "definitions": {
            "total_sessions": "completed sessions with a stored report (Practice+OSCE, all-time)",
            "avg_score": "mean of session overall_0_100 across scored sessions; unscored excluded",
            "skill": f"recency-weighted mean per dim over last {_SKILL_WINDOW} sessions (linear rank weights)",
            "coverage": "explicit counts of specialties/families/variants; not mastery",
            "window": "all-time" if window_days is None else f"last {window_days} days",
        },
    }


def apply_progress_for_session(
    extra: dict, state: dict, *, case_id: str, specialty: str, overall: int,
    dim_pcts: dict, today: str | None = None,
) -> tuple[dict, dict]:
    """Pure gamification updater shared by the V2 AND V3 score paths so both
    engines contribute identically (fixes the Phase-8-B under-count where V3
    sessions earned 0 XP/streak/badges).

    Mirrors the legacy v2_router._record_progress rules exactly (same keys,
    same streak rule, same caps) — extracted pure so it is unit-testable and
    engine-agnostic. `state` = {"xp": int, "streak": int, "total_sessions": int}.
    Returns (new_extra, new_state); inputs are never mutated.
    """
    overall = max(0, min(100, int(overall or 0)))
    if today is None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_extra = dict(extra or {})
    new_state = dict(state or {})
    history = list(new_extra.get("scoreHistory") or [])
    history.insert(0, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "caseId": case_id,
        "specialty": specialty or "",
        "overall": overall,
        "dims": {str(k): int(round(float(v))) for k, v in (dim_pcts or {}).items()
                 if isinstance(v, (int, float))},
    })
    new_extra["scoreHistory"] = history[:200]
    dates = dict(new_extra.get("sessionDates") or {})
    dates[today] = int(dates.get(today, 0) or 0) + 1
    new_extra["sessionDates"] = dates
    done = set(new_extra.get("completedCaseIds") or [])
    done.add(case_id)
    new_extra["completedCaseIds"] = sorted(done)
    last = new_extra.get("lastActiveDate")
    streak = int(new_state.get("streak") or 0)
    if last != today:
        try:
            prev = datetime.strptime(last, "%Y-%m-%d").date() if last else None
        except (ValueError, TypeError):
            prev = None
        try:
            today_d = datetime.strptime(today, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            today_d = datetime.now(timezone.utc).date()
        if prev is not None and (today_d - prev).days == 1:
            streak = streak + 1
        else:
            streak = 1
    new_extra["lastActiveDate"] = today
    new_extra["bestStreak"] = max(int(new_extra.get("bestStreak") or 0), streak)
    new_extra["bestScore"] = max(int(new_extra.get("bestScore") or 0), overall)
    new_state["xp"] = int(new_state.get("xp") or 0) + overall
    new_state["streak"] = streak
    new_state["total_sessions"] = int(new_state.get("total_sessions") or 0) + 1
    return new_extra, new_state
