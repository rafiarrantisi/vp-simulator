"""Phase 7A — rubric / core domains / criticality / learner profiles.

Plan §15-17, §24-25. The 8-domain matrix starts from the well-established
historical Indonesian UKMPPD structure (also reused by the Phase 2
`NormalizedScoringOutput` contract). Verification note below is honest:
we do NOT claim an older document is the current official standard —
labels only, defensible against current Indonesian clinical-education
practice (plan §15).
"""
from __future__ import annotations

OSCE_VERIFICATION_NOTE = "Structural basis: historical Indonesian UKMPPD 8-competency layout (anamnesis; physical examination; supporting-test interpretation; diagnosis/DDx; non-pharmacological management; pharmacological management; communication/education; professional behavior). Used as labels/organization only — NOT claimed as the current official standard (plan §15). Re-verification against the latest authoritative Indonesian OSCE material is tracked as a human-review task in the Phase 7 calibration sheet; domain renames require no code change because weights/aggregation are data-driven here."

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

CRITICALITY_LEVELS = ("routine", "important", "critical", "safety-critical")

CRITICALITY_WEIGHTS = {"routine": 1, "important": 2, "critical": 3, "safety-critical": 4}

SCORE_LABELS = {
    0: "not done / incorrect",
    1: "attempted but substantially inadequate",
    2: "partially adequate / clinically incomplete",
    3: "adequate / correct",
}

ADJUDICATION_TO_SCORE = {"hit": 3, "partial": 2, "miss": 0}

LEARNER_WEIGHT_PROFILES = {
    "preclinical": {
        "history": 25,
        "physical_examination": 15,
        "investigations": 5,
        "diagnosis_ddx": 10,
        "management_non_pharma": 10,
        "management_pharma": 5,
        "communication_education": 20,
        "professional_behavior": 10,
    },
    "koas": {
        "history": 15,
        "physical_examination": 10,
        "investigations": 15,
        "diagnosis_ddx": 20,
        "management_non_pharma": 10,
        "management_pharma": 15,
        "communication_education": 5,
        "professional_behavior": 10,
    },
}

LEARNER_WEIGHT_PROFILES["general_doctor"] = dict(LEARNER_WEIGHT_PROFILES["koas"])

MODE_PARAMS = {
    "practice": {
        "pass_threshold": 55,
        "superior_threshold": 80,
        "borderline_threshold": 40,
        "safety_cap": 50,
        "catastrophic_cap": 35,
        "tone": "explanatory",
    },
    "osce": {
        "pass_threshold": 60,
        "superior_threshold": 85,
        "borderline_threshold": 45,
        "safety_cap": 45,
        "catastrophic_cap": 30,
        "tone": "examiner",
    },
}


def resolve_learner_stage(stage: str) -> str:
    s = (stage or "").strip().lower().replace("-", "_").replace(" ", "_")
    if s in ("preclinical", "preklinik", "pre_clinical"):
        return "preclinical"
    if s in ("general_doctor", "gp", "dokter", "dokter_umum"):
        return "general_doctor"
    return "koas"


def domain_weights(learner_stage: str) -> dict[str, int]:
    return dict(LEARNER_WEIGHT_PROFILES[resolve_learner_stage(learner_stage)])


def mode_params(mode: str) -> dict:
    return dict(MODE_PARAMS.get((mode or "practice").lower(), MODE_PARAMS["practice"]))


def validate_weights(weights: dict[str, int]) -> list[str]:
    errs = []
    if set(weights) != set(OSCE_CORE_DOMAINS):
        errs.append("weights must cover exactly the 8 core domains")
    if any(not isinstance(v, int) or v < 0 for v in weights.values()):
        errs.append("weights must be non-negative ints")
    if sum(v for v in weights.values() if isinstance(v, int)) != 100:
        errs.append(f"weights must sum to 100 (got {sum(weights.values())})")
    return errs
