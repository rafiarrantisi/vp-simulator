"""Data-driven, mode-aware scoring rubric (BUILD_PLAN_pivot_v4 §6.1).

Weights are DATA, not code: read from a mode config, overridable per case via
the frontmatter `scoring_weights_override`. The legacy 40/20/20/20 rubric is
preserved as the named `classic_anamnesis` preset. No single rubric is hardcoded
into the judge.

Each dimension maps to a source of ground truth in schema v2 (Part A):
  history_coverage     -> anamnesis_checklist (hpi/associated/pmh/meds/family_social)
  red_flags            -> red_flags
  ice_fife             -> anamnesis_checklist.ice_fife
  questioning_technique-> judged from transcript pattern (open/closed/leading/signposting)
  communication        -> judged from transcript (intro/consent/empathy/structure)
  diagnostic_reasoning -> expected_ddx (vs student DDx)
  investigations       -> investigations (osce_full only)
  management           -> management (osce_full only)
  clinical_safety      -> critical red-flag recognition + safety-netting
"""
from __future__ import annotations

# Canonical mode rubrics. Each must sum to 100.
RUBRICS: dict[str, dict[str, int]] = {
    # Pure history-taking — anamnesis mode.
    "anamnesis": {
        "history_coverage": 25,
        "red_flags": 15,
        "ice_fife": 8,
        "questioning_technique": 15,
        "communication": 10,
        "diagnostic_reasoning": 15,
        "clinical_safety": 12,
    },
    # Full OSCE arc.
    "osce_full": {
        "history_coverage": 20,
        "red_flags": 10,
        "ice_fife": 5,
        "questioning_technique": 10,
        "communication": 10,
        "investigations": 15,
        "diagnostic_reasoning": 15,
        "management": 10,
        "clinical_safety": 5,
    },
    # Legacy OphthaSim rubric, preserved as a named preset for eye-style cases.
    "classic_anamnesis": {
        "coverage": 40,
        "fife": 20,
        "red_flags": 20,
        "communication": 20,
    },
}

DEFAULT_MODE = "anamnesis"

# Human-readable labels for the UI / answer-key.
DIMENSION_LABELS: dict[str, str] = {
    "history_coverage": "History coverage",
    "red_flags": "Red-flag screening",
    "ice_fife": "ICE / FIFE",
    "questioning_technique": "Questioning technique",
    "communication": "Communication & professionalism",
    "diagnostic_reasoning": "Diagnostic reasoning (DDx)",
    "investigations": "Investigation selection",
    "management": "Management",
    "clinical_safety": "Clinical safety & red-flag action",
    "coverage": "Coverage (anamnesis)",
    "fife": "FIFE",
}


def validate_weights(weights: dict[str, int]) -> list[str]:
    """Return error strings; empty = valid. Weights must be a non-empty dict of
    non-negative ints summing to 100."""
    errs: list[str] = []
    if not weights or not isinstance(weights, dict):
        return ["weights must be a non-empty mapping"]
    for k, v in weights.items():
        if not isinstance(v, int) or v < 0:
            errs.append(f"weight for '{k}' must be a non-negative integer (got {v!r})")
    total = sum(v for v in weights.values() if isinstance(v, int))
    if total != 100:
        errs.append(f"weights must sum to 100 (got {total})")
    return errs


def resolve_weights(mode: str | None, override: dict[str, int] | None = None) -> dict[str, int]:
    """Resolve the active weights: a valid per-case override wins; else the mode
    rubric; else the default mode. Falls back safely for unknown modes."""
    if override:
        if not validate_weights(override):
            return dict(override)
        # Invalid override -> ignore it and fall through to the mode rubric.
    m = (mode or DEFAULT_MODE).lower()
    return dict(RUBRICS.get(m, RUBRICS[DEFAULT_MODE]))


def dimensions_for(mode: str | None) -> list[str]:
    return list(resolve_weights(mode).keys())
