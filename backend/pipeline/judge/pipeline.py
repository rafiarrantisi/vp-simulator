"""Phase 7 orchestration — evidence → adjudication → deterministic score →
safety → global rating → feedback (plan §11).

Single entry point `run_hybrid_judge` emits a `NormalizedScoringOutput`
(Phase 2 contract, §27): overall + 8 core domains + rubric items with
evidence refs + safety gates + global rating + feedback + source metadata
+ pinned scoring version. Raw inputs are preserved, never rewritten.
"""
from __future__ import annotations

from pipeline.clinical_contracts.scoring_output import (
    EvidenceRef,
    NormalizedScoringOutput,
    RubricItemResult,
    SafetyGate,
)
from pipeline.clinical_contracts.versions import (
    CLINICAL_CONTENT_VERSION,
    EVIDENCE_PACK_VERSION,
    SCORING_VERSION,
)
from pipeline.judge import evidence as _ev
from pipeline.judge.domains import OSCE_CORE_DOMAINS
from pipeline.judge.engine import (
    aggregate_scores,
    apply_safety_caps,
    evaluate_safety_gates,
    grade_diagnosis_hierarchy,
)
from pipeline.judge.evidence import build_evidence_ledger
from pipeline.judge.feedback import compose_feedback
from pipeline.judge.rating import assign_global_rating

HYBRID_JUDGE_MODE = "advisory"


def run_hybrid_judge(
    record: _ev.UserPerformanceRecord,
    rubric_items: list[dict],
    *,
    learner_stage: str = "koas",
    mode: str = "practice",
    canonical_diagnosis: str = "",
    diagnosis_synonyms: list[str] | None = None,
    treatment_concepts=None,
    sources: list[dict] | None = None,
    session_id: str = "",
    clinical_content_version: str = CLINICAL_CONTENT_VERSION,
    evidence_pack_version: str = EVIDENCE_PACK_VERSION,
) -> NormalizedScoringOutput:
    """Run the full evidence-locked hybrid pipeline (deterministic, no LLM)."""
    mode = (mode or "practice").lower()
    if mode not in ("practice", "osce"):
        mode = "practice"

    ledger = build_evidence_ledger(rubric_items, record)

    treatment_grade = {"outcome": "incomplete", "detail": "no treatment submitted"}
    if record.medication_text and record.medication_text.strip() and treatment_concepts:
        from pipeline.clinical_contracts.medication import grade_regimen

        g = grade_regimen(record.medication_text, list(treatment_concepts))
        treatment_grade = {"outcome": g.outcome, "detail": g.detail}

    if canonical_diagnosis or record.diagnosis_primary:
        dx = grade_diagnosis_hierarchy(
            record.diagnosis_primary,
            canonical=(canonical_diagnosis or record.diagnosis_primary),
            synonyms=(diagnosis_synonyms or []),
        )
    else:
        dx = {"grade": "incorrect", "status": "miss", "detail": "no diagnosis scope"}

    gates = evaluate_safety_gates(
        ledger,
        record,
        treatment_grade=treatment_grade,
        diagnosis_status=(
            "dangerous_miss" if dx.get("grade") == "dangerous_miss" else ""
        ),
    )

    agg = aggregate_scores(
        ledger, learner_stage=learner_stage, mode=mode, overtime=record.overtime
    )
    capped = apply_safety_caps(agg["overall"], gates, mode=mode)

    evidence_count = sum(1 for e in ledger if e.evidence)
    rating = assign_global_rating(
        capped["overall"],
        gates,
        mode=mode,
        evidence_count=evidence_count,
        rubric_size=len(ledger),
    )

    feedback = compose_feedback(
        ledger,
        per_domain=agg["per_domain"],
        overall=capped["overall"],
        gates=gates,
        global_rating=rating["rating"],
        sources=(sources or []),
        learner_stage=learner_stage,
        mode=mode,
    )

    items = [
        RubricItemResult(
            item_id=e.item_id,
            domain=e.domain,
            expected=e.expected,
            evidence=[
                EvidenceRef(
                    source=r.get("source", "other"),
                    ref=r.get("ref", ""),
                    quote=r.get("quote", ""),
                )
                for r in e.evidence
            ],
            adjudication=e.adjudication,
            score_0_3=e.score_0_3,
            criticality=e.criticality,
            reason=e.reason,
        )
        for e in ledger
    ]
    core_domains = {
        d: {
            "score": (agg["per_domain"].get(d) or {}).get("score", 0),
            "max": (agg["per_domain"].get(d) or {}).get("max", 0),
            "pct": (agg["per_domain"].get(d) or {}).get("pct", 0.0),
            "feedback": "",
        }
        for d in OSCE_CORE_DOMAINS
    }

    out = NormalizedScoringOutput(
        session_id=session_id,
        scoring_version=SCORING_VERSION,
        evidence_pack_version=evidence_pack_version,
        clinical_content_version=clinical_content_version,
        overall_0_100=capped["overall"],
        core_domains=core_domains,
        learning_dims={},
        items=items,
        safety_gates=[
            SafetyGate(
                gate=g.get("type", ""),
                triggered=True,
                detail=g.get("detail", ""),
                score_cap=capped.get("cap"),
            )
            for g in gates
        ],
        global_rating=rating["rating"],
        feedback={
            **{},
            **feedback,
            "rating_confidence": rating["confidence"],
            "rating_reasons": rating["reasons"],
            "diagnosis_grade": dx,
            "treatment_grade": treatment_grade,
            "overtime_penalty": agg.get("overtime_penalty"),
            "judge_mode": HYBRID_JUDGE_MODE,
        },
        source_metadata={
            "producer": "hybrid-judge-advisory/1",
            "engine": "evidence_locked_hybrid",
            "mode": mode,
            "learner_stage": learner_stage,
        },
        raw_preserved={
            "rubric_size": len(rubric_items or []),
            "evidence_count": evidence_count,
            "mode": mode,
            "learner_stage": learner_stage,
        },
    )
    return out


__all__ = [
    "HYBRID_JUDGE_MODE",
    "UserPerformanceRecord",
    "build_evidence_ledger",
    "build_rubric_from_variant",
    "run_hybrid_judge",
]
