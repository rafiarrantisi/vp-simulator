"""Phase 8 Task A — historical adapter (plan §Phase 8-A, §27, §36).

Maps V2 and V3 reports into ONE normalized longitudinal learning model.
Read-only: the original raw report is never mutated, only referenced.

Supported raw shapes (all observed in production):
- V2 judge report:      {overall, per_dimension:{dim:{score,max}}, per_item,
                         safety_gates, summary}                    (engine v2)
- V3-compat report:     same V2 shape but V3 dim names + {schema:'new',
                         variantId, familyId}                      (engine v3_compat)
- V3 native report:     deterministic score_encounter {total, by_dimension,
                         safety_flags}                            (engine v3_native)

OSCE detection (documented heuristic, plan §48):
- SessionRow.mode in {"osce", "osce_full"} -> OSCE (V2 case mode_default).
- Everything else (anamnesis, targeted, blind, random) -> practice.
- The UI practice/osce toggle at score time is NOT persisted today, so a V2
  session started from an osce_full case counts as OSCE exposure. This is
  stated here (not hidden) and listed as a known gap for a future
  `interaction_mode` persistence fix.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from pipeline.clinical_contracts.scoring_output import (
    OSCE_CORE_DOMAINS,
    V2_DIM_TO_CORE,
    V3_DIM_TO_CORE,
)

_COMBINED_TO_CORE: dict = dict(V2_DIM_TO_CORE)
_COMBINED_TO_CORE.update(V3_DIM_TO_CORE)

_OSCE_MODES = frozenset({"osce", "osce_full"})


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


def _dim_pct(entry) -> float | None:
    """Normalize one per_dimension/by_dimension entry to 0..100 (None = skip)."""
    if not isinstance(entry, dict):
        return None
    try:
        sc = float(entry.get("score", 0) or 0)
    except (TypeError, ValueError):
        return None
    mx = entry.get("max", entry.get("max_score"))
    try:
        mx = float(mx) if mx is not None else None
    except (TypeError, ValueError):
        mx = None
    if mx is not None and mx > 0:
        pct = 100.0 * sc / mx
    elif mx is None and 0 <= sc <= 1.0 and isinstance(entry.get("score"), float):
        # Fractional native dim without max (score_encounter 0..1 ratio).
        pct = 100.0 * sc
    else:
        pct = float(sc)
    return max(0.0, min(100.0, pct))


def _fold_to_core(dim_pcts: dict[str, float]) -> dict[str, float]:
    """Average native dim pcts into the 8 OSCE core domains (§15)."""
    buckets: dict[str, list[float]] = {}
    for dim, pct in dim_pcts.items():
        core = _COMBINED_TO_CORE.get(dim, "history")
        buckets.setdefault(core, []).append(pct)
    return {c: round(sum(v) / len(v), 1) for c, v in buckets.items()}


def _safety_from_report(report: dict) -> tuple[bool, list[str]]:
    gates = (report or {}).get("safety_gates") or (report or {}).get("safety_flags") or []
    labels: list[str] = []
    if isinstance(gates, dict):
        gates = [gates]
    for g in gates or []:
        if isinstance(g, dict):
            label = str(g.get("type") or g.get("gate") or "") or "safety_gate"
            # Explicit triggered=False means "checked, not triggered" -> skip.
            if g.get("triggered") is False:
                continue
            labels.append(label)
        elif isinstance(g, str):
            if g.strip():
                labels.append(g.strip())
    return (len(labels) > 0, labels)


@dataclass
class NormalizedSession:
    """One completed session in the longitudinal model (derived, never stored
    over the raw report)."""

    session_id: str = ""
    case_id: str = ""
    family_id: str | None = None
    variant_id: str | None = None
    specialty: str = "unknown"
    engine: str = "v2"
    overall_0_100: int = 0
    dim_pcts: dict = field(default_factory=dict)
    core_pcts: dict = field(default_factory=dict)
    safety_triggered: bool = False
    safety_labels: list = field(default_factory=list)
    is_osce: bool = False
    completed_at: str = ""
    scoring_version: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def adapt_report(report: dict, *, content_schema: str = "legacy", session_id: str = "") -> NormalizedSession:
    """Adapt ONE raw report dict into a NormalizedSession (meta filled by
    adapt_session; specialty/is_osce default here and may be overridden)."""
    if not isinstance(report, dict):
        report = {}
    ns = NormalizedSession(session_id=session_id)
    if isinstance(report.get("by_dimension"), dict):
        engine = "v3_native" if content_schema == "new" else "v3_native"
        dims = report.get("by_dimension") or {}
        try:
            overall = int(round(float(report.get("total", 0) or 0) * 100))
        except (TypeError, ValueError):
            overall = 0
        ns.engine = engine
    else:
        ns.engine = "v3_compat" if content_schema == "new" else "v2"
        dims = report.get("per_dimension") or {}
        try:
            overall = int(report.get("overall", 0) or 0)
        except (TypeError, ValueError):
            overall = 0
    ns.overall_0_100 = max(0, min(100, overall))
    for dim, entry in (dims or {}).items():
        pct = _dim_pct(entry)
        if pct is None:
            continue
        ns.dim_pcts[str(dim)] = round(pct, 1)
    ns.core_pcts = _fold_to_core(ns.dim_pcts)
    triggered, labels = _safety_from_report(report)
    ns.safety_triggered = triggered
    ns.safety_labels = labels
    sv = report.get("scoring_version") or report.get("score_version") or ""
    ns.scoring_version = str(sv) if sv else ""
    return ns


def adapt_session(row: dict, *, specialty: str | None = None) -> NormalizedSession:
    """Adapt one session row (plain dict — NO SQLAlchemy import so pipeline
    stays app-free) into the longitudinal model.

    Expected keys: id/session_id, case_id, mode, content_schema, family_id,
    variant_id, total_score, report, ended_at/started_at (ISO or datetime).
    Sessions without a usable report return overall from total_score with
    empty dims (marked engine + scoring_version "" so downstream can tell
    "score without breakdown" apart from a real zero).
    """
    if not row:
        row = {}
    sid = str(row.get("id") or row.get("session_id") or "")
    report = row.get("report")
    ns = adapt_report(
        report if isinstance(report, dict) else {},
        content_schema=str(row.get("content_schema") or "legacy"),
        session_id=sid,
    )
    ns.case_id = str(row.get("case_id") or "")
    ns.family_id = row.get("family_id")
    ns.variant_id = row.get("variant_id")
    if not isinstance(report, dict) or not report:
        try:
            ns.overall_0_100 = max(0, min(100, int(row.get("total_score") or 0)))
        except (TypeError, ValueError):
            ns.overall_0_100 = 0
    if specialty:
        ns.specialty = str(specialty)
    elif row.get("specialty"):
        ns.specialty = str(row.get("specialty"))
    mode = str(row.get("mode") or "").lower()
    ns.is_osce = mode in _OSCE_MODES
    if not ns.variant_id and isinstance(report, dict):
        ns.variant_id = report.get("variantId")
    if not ns.family_id and isinstance(report, dict):
        ns.family_id = report.get("familyId")
    dt = _parse_dt(row.get("ended_at")) or _parse_dt(row.get("started_at"))
    ns.completed_at = dt.isoformat() if dt else ""
    return ns


def core_domain_list() -> list[str]:
    return list(OSCE_CORE_DOMAINS)
