"""Phase 2 scoring-output constants (minimal restore for FASE 8).

Restores the exact domain vocabulary the oracle `pipeline.progress`
modules were built against (verified against oracle bytecode):

- OSCE_CORE_DOMAINS: 8 core OSCE domains (§15).
- V2_DIM_TO_CORE / V3_DIM_TO_CORE: native judge dim -> core domain.
- QORA_LEARNING_DIMS: Layer-B learning dims.
"""
from __future__ import annotations

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
