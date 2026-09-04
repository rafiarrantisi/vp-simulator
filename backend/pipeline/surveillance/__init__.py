"""Phase 11 — Guideline Watcher / Clinical Surveillance (plan §30–31).

Offline, deterministic, human-gated: metadata/hash/version comparison first,
impact mapping second, reviewer queue third. Nothing here fetches the web,
scores sessions, edits cases, or publishes — see `service` for the
structural no-write guarantee.
"""
from pipeline.surveillance.check import (
    CHANGE_KINDS,
    ObservedSnapshot,
    SurveillanceFinding,
    check_target,
    detect_change,
)
from pipeline.surveillance.diff import (
    SEVERITIES,
    ClaimDiff,
    classify_severity,
    diff_claims,
)
from pipeline.surveillance.impact import ImpactEntry, map_impact
from pipeline.surveillance.queue import (
    ReviewerQueue,
    ReviewTask,
    approve_task,
    build_task,
    reject_task,
)
from pipeline.surveillance.registry import (
    CLAIM_AREAS,
    SOURCE_KINDS,
    TIERS,
    SurveillanceTarget,
    default_surveillance_registry,
    get_target,
    validate_registry,
)
from pipeline.surveillance.service import CycleResult, run_surveillance_cycle

__all__ = [
    "CHANGE_KINDS",
    "SEVERITIES",
    "TIERS",
    "SOURCE_KINDS",
    "CLAIM_AREAS",
    "SurveillanceTarget",
    "ObservedSnapshot",
    "SurveillanceFinding",
    "ClaimDiff",
    "ImpactEntry",
    "ReviewTask",
    "ReviewerQueue",
    "CycleResult",
    "default_surveillance_registry",
    "validate_registry",
    "get_target",
    "detect_change",
    "check_target",
    "diff_claims",
    "classify_severity",
    "map_impact",
    "build_task",
    "approve_task",
    "reject_task",
    "run_surveillance_cycle",
]
