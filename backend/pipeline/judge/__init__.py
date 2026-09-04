"""Phase 7 — Evidence-Locked Hybrid Clinical Judge (plan §10-27, §40-41).

Advisory-only library: evidence extraction → semantic adjudication →
deterministic scoring → safety gating → global rating → feedback composer.
Pure `pipeline.*` logic (no app/DB/network/LLM) so tests stay isolated.

STOP-GATE RULE (plan Phase 7): this package NEVER wires itself into the live
`/score` endpoints. Live V2/V3 judges are untouched; the hybrid runs
side-by-side in tests/calibration until human calibration review approves a
promotion. `HYBRID_JUDGE_MODE = "advisory"` is the only supported mode.
"""
from __future__ import annotations

from pipeline.judge.domains import (
    CRITICALITY_LEVELS,
    LEARNER_WEIGHT_PROFILES,
    MODE_PARAMS,
    OSCE_VERIFICATION_NOTE,
)
from pipeline.judge.engine import aggregate_scores, apply_safety_caps
from pipeline.judge.evidence import LedgerEntry, UserPerformanceRecord, build_evidence_ledger
from pipeline.judge.feedback import compose_feedback
from pipeline.judge.pipeline import HYBRID_JUDGE_MODE, run_hybrid_judge
from pipeline.judge.rating import assign_global_rating
from pipeline.judge.semantic import Adjudication, adjudicate

__all__ = [
    "HYBRID_JUDGE_MODE",
    "CRITICALITY_LEVELS",
    "LEARNER_WEIGHT_PROFILES",
    "MODE_PARAMS",
    "OSCE_VERIFICATION_NOTE",
    "Adjudication",
    "adjudicate",
    "LedgerEntry",
    "UserPerformanceRecord",
    "build_evidence_ledger",
    "aggregate_scores",
    "apply_safety_caps",
    "assign_global_rating",
    "compose_feedback",
    "run_hybrid_judge",
]
