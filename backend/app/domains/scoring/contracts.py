"""FASE 2 — normalized scoring output contract (one data language).

Every consumer — Result screen, Dashboard, Progress, Mentor, Readiness,
Analytics — must read the SAME versioned shape instead of each parsing a
different judge's raw dict. This module is PURE mapping (no I/O, no LLM,
no DB): adapters translate the existing stored reports into `NormalizedScore`
at read/export time. Stored `SessionRow.report` JSON is NEVER rewritten, so
old sessions keep their original scores when guidelines or judges update.

Contract versioning: `CONTRACT_VERSION` bumps only on breaking shape change;
adapters always emit the current version and record the source engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

CONTRACT_VERSION = "1.0"
SCHEMA = "normalized_score/1.0"

# Core OSCE domains every consumer understands. A domain is `None` when the
# session's mode never assessed it (missing) — never silently 0 (failed).
CORE_OSCE_DOMAINS = (
    "history",
    "physical_exam",
    "investigations",
    "diagnosis",
    "management",
    "communication",
    "safety",
)

# per_dimension key -> core domain (V2 + V3-compat keys; unmapped stays
# learning-only, still visible in `learning_dimensions`).
_DIM_TO_CORE = {
    "history_coverage": "history",
    "coverage": "history",
    "info_gathering": "history",
    "physical_exam": "physical_exam",
    "investigations": "investigations",
    "investigation_strategy": "investigations",
    "diagnostic_reasoning": "diagnosis",
    "diagnostic_quality": "diagnosis",
    "management": "management",
    "management_safety": "management",
    "communication": "communication",
    "clinical_safety": "safety",
    "red_flags": "safety",
}

GLOBAL_RATINGS = frozenset({"pass", "borderline", "fail"})


@dataclass
class NormalizedScore:
    schema: str = SCHEMA
    contract_version: str = CONTRACT_VERSION
    session_id: str = ""
    case_id: str = ""
    content_schema: str = "legacy"          # legacy | new
    mode: str = ""                          # anamnesis | osce_full | ...
    rubric_name: str = ""
    weights: dict = field(default_factory=dict)
    overall_0_100: Optional[float] = None
    core_osce_domains: dict = field(default_factory=dict)   # domain -> {score,max} | None
    learning_dimensions: dict = field(default_factory=dict)  # dim -> {score,max,feedback}
    rubric_items: list[dict] = field(default_factory=list)   # {dimension,item,status,evidence}
    safety_gates: list[dict] = field(default_factory=list)   # {type,detail}
    global_rating: Optional[str] = None     # pass | borderline | fail | None
    feedback: dict = field(default_factory=dict)  # {summary,strengths[],improvements[]}
    answer_key_present: bool = False
    sources: dict = field(default_factory=dict)  # {evidence_pack_version,clinical_content_version,guideline_refs[]}
    scoring: dict = field(default_factory=dict)  # {engine,model,contract_version}

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> list[str]:
        errs: list[str] = []
        if self.schema != SCHEMA:
            errs.append(f"schema must be '{SCHEMA}'")
        if self.contract_version != CONTRACT_VERSION:
            errs.append(f"contract_version must be '{CONTRACT_VERSION}'")
        if self.overall_0_100 is not None and not (0 <= self.overall_0_100 <= 100):
            errs.append("overall_0_100 must be within 0..100")
        for d in CORE_OSCE_DOMAINS:
            if d not in self.core_osce_domains:
                errs.append(f"core_osce_domains lacks '{d}' (use None when unassessed)")
        for it in self.rubric_items:
            if it.get("status") not in ("hit", "partial", "miss"):
                errs.append(f"rubric item status must be hit|partial|miss: {it.get('item', '?')[:60]}")
        if self.global_rating is not None and self.global_rating not in GLOBAL_RATINGS:
            errs.append("global_rating must be pass|borderline|fail")
        return errs


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _core_from_dimensions(per_dimension: dict) -> dict:
    core: dict[str, Optional[dict]] = {d: None for d in CORE_OSCE_DOMAINS}
    for dim, entry in (per_dimension or {}).items():
        target = _DIM_TO_CORE.get(str(dim))
        if not target or not isinstance(entry, dict):
            continue
        score, mx = _num(entry.get("score")), _num(entry.get("max"))
        cur = core[target]
        if cur is None or score / max(mx, 1e-9) >= cur["score"] / max(cur["max"], 1e-9):
            core[target] = {"score": score, "max": mx}
    return core


def _items(raw_items: Any) -> list[dict]:
    out: list[dict] = []
    for it in (raw_items or []):
        if not isinstance(it, dict):
            continue
        status = str(it.get("status", "miss")).lower()
        out.append({
            "dimension": str(it.get("dimension", "")).strip(),
            "item": str(it.get("item", "")).strip(),
            "status": status if status in ("hit", "partial", "miss") else "miss",
            "evidence": str(it.get("evidence", "")).strip(),
        })
    return out


def _gates(raw_gates: Any) -> list[dict]:
    out: list[dict] = []
    for g in (raw_gates or []):
        if isinstance(g, dict):
            out.append({"type": str(g.get("type", g.get("gate", ""))).strip(),
                        "detail": str(g.get("detail", g.get("note", ""))).strip()})
        elif isinstance(g, str):
            out.append({"type": g.strip(), "detail": ""})
    return out


def from_v2_report(report: dict, *, session_id: str = "", case_id: str = "",
                   content_schema: str = "legacy", mode: str = "",
                   rubric_name: str = "", engine: str = "llm_judge_v2",
                   model: str = "", clinical_content_version: str = "",
                   evidence_pack_version: str = "") -> NormalizedScore:
    """Adapt a stored V2-shaped report (judge_v2, or judge_v3 via the V3
    compat facade — same shape) into the normalized contract."""
    report = report or {}
    per_dim = report.get("per_dimension") or {}
    learning = {}
    for dim, entry in per_dim.items():
        if isinstance(entry, dict):
            learning[str(dim)] = {"score": _num(entry.get("score")),
                                  "max": _num(entry.get("max")),
                                  "feedback": str(entry.get("feedback", "")).strip()}
    ak = report.get("answer_key")
    return NormalizedScore(
        session_id=session_id, case_id=case_id, content_schema=content_schema,
        mode=mode or str(report.get("mode", "") or ""),
        rubric_name=rubric_name,
        weights=dict(report.get("weights") or {}),
        overall_0_100=_num(report.get("overall"), 0.0),
        core_osce_domains=_core_from_dimensions(per_dim),
        learning_dimensions=learning,
        rubric_items=_items(report.get("per_item")),
        safety_gates=_gates(report.get("safety_gates")),
        feedback={"summary": str(report.get("summary", "")).strip(),
                  "strengths": [], "improvements": []},
        answer_key_present=bool(ak),
        sources={"evidence_pack_version": evidence_pack_version,
                 "clinical_content_version": clinical_content_version,
                 "guideline_refs": []},
        scoring={"engine": engine, "model": model, "contract_version": CONTRACT_VERSION},
    )


def from_v3_native(score_result: dict, *, session_id: str = "", case_id: str = "",
                   engine: str = "score_encounter",
                   clinical_content_version: str = "") -> NormalizedScore:
    """Adapt a deterministic native V3 `ScoreResult.to_dict()` payload
    ({total, max, by_dimension, safety_flags}) into the contract. Dimension
    scores are 0..1 ratios; core domains carry ratio-preserving {score,max}
    pairs scaled to 100 so consumers share one scale."""
    score_result = score_result or {}
    by_dim = score_result.get("by_dimension") or {}
    learning, core_src = {}, {}
    for dim, entry in by_dim.items():
        if not isinstance(entry, dict):
            continue
        ratio = max(0.0, min(1.0, _num(entry.get("score"), 0.5)))
        learning[str(dim)] = {"score": round(ratio * 100, 1), "max": 100,
                              "feedback": str(entry.get("notes", "")).strip()}
        core_src[str(dim)] = {"score": round(ratio * 100, 1), "max": 100}
    total, mx = _num(score_result.get("total")), _num(score_result.get("max"), 1.0)
    overall = round(100.0 * total / mx, 1) if mx else 0.0
    return NormalizedScore(
        session_id=session_id, case_id=case_id, content_schema="new",
        mode="v3_native",
        overall_0_100=overall,
        core_osce_domains=_core_from_dimensions(core_src),
        learning_dimensions=learning,
        safety_gates=_gates(score_result.get("safety_flags")),
        feedback={"summary": "", "strengths": [], "improvements": []},
        answer_key_present=False,
        sources={"evidence_pack_version": "", "clinical_content_version": clinical_content_version,
                 "guideline_refs": []},
        scoring={"engine": engine, "model": "", "contract_version": CONTRACT_VERSION},
    )
