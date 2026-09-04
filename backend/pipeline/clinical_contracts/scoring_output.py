"""Phase 2 scoring-output constants (minimal restore for FASE 8).

Restores the exact domain vocabulary the oracle `pipeline.progress`
modules were built against (verified against oracle bytecode):

- OSCE_CORE_DOMAINS: 8 core OSCE domains (§15).
- V2_DIM_TO_CORE / V3_DIM_TO_CORE: native judge dim -> core domain.
- QORA_LEARNING_DIMS: Layer-B learning dims.
"""
from __future__ import annotations

from dataclasses import dataclass, field

OSCE_CORE_DOMAINS = (
    "history",
    "physical_examination",
    "investigations",
    "diagnosis_ddx",
    "management_non_pharma",
    "management_pharma",
    "communication_education",
    "professional_behavior",
)

QORA_LEARNING_DIMS = (
    "red_flag_recognition",
    "questioning",
    "focus_efficiency",
    "reasoning",
    "safety",
    "management_prioritization",
    "communication",
    "completeness",
)

V2_DIM_TO_CORE = {
    "history_coverage": "history",
    "ice_fife": "communication_education",
    "red_flags": "history",
    "clinical_safety": "history",
    "diagnostic_reasoning": "diagnosis_ddx",
    "investigations": "investigations",
    "management": "management_non_pharma",
    "physical_exam": "physical_examination",
    "communication": "communication_education",
    "questioning_technique": "history",
}

V3_DIM_TO_CORE = {
    "info_gathering": "history",
    "focus_efficiency": "history",
    "reasoning_coherence": "diagnosis_ddx",
    "diagnostic_quality": "diagnosis_ddx",
    "investigation_strategy": "investigations",
    "management_safety": "management_non_pharma",
    "communication": "communication_education",
}


@dataclass
class EvidenceRef:
    """One supporting quote behind a scored rubric item (§13)."""

    source: str = "other"
    ref: str = ""
    quote: str = ""


@dataclass
class RubricItemResult:
    """One scored rubric item with its evidence trail (§13)."""

    item_id: str = ""
    domain: str = ""
    expected: str = ""
    evidence: list = field(default_factory=list)
    adjudication: str = ""
    score_0_3: int = 0
    criticality: str = ""
    reason: str = ""


@dataclass
class SafetyGate:
    """One evaluated safety gate (§11: never overridden by score)."""

    gate: str = ""
    triggered: bool = False
    detail: str = ""
    score_cap: int | None = None


@dataclass
class NormalizedScoringOutput:
    """Phase 2 scoring contract (§27): overall + core domains + items with
    evidence refs + safety gates + global rating + feedback + source
    metadata + pinned versions. Raw inputs are preserved, never rewritten."""

    session_id: str = ""
    scoring_version: str = ""
    evidence_pack_version: str = ""
    clinical_content_version: str = ""
    overall_0_100: int = 0
    core_domains: dict = field(default_factory=dict)
    learning_dims: dict = field(default_factory=dict)
    items: list = field(default_factory=list)
    safety_gates: list = field(default_factory=list)
    global_rating: str = ""
    feedback: dict = field(default_factory=dict)
    source_metadata: dict = field(default_factory=dict)
    raw_preserved: dict = field(default_factory=dict)
