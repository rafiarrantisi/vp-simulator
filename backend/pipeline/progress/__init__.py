"""Phase 8 — unified progress / dashboard / readiness data layer (plan §Phase 8).

Pure data-layer package: NO app/DB imports, NO network, NO LLM. It adapts
V2 + V3 (compat + native deterministic) session reports into ONE normalized
longitudinal learning model so Result, Dashboard, Progress, and Mentor speak
the same language (plan §36), then derives:

- progress  — completed sessions, score history, XP/streak deltas,
  achievements inputs, specialty coverage, skill history (§43);
- readiness — evidence-based, confidence-aware, explainable (§44, §6).

Raw session reports are NEVER rewritten here — adapters only read them and
keep the original in `raw_preserved` (plan §27). No fake metrics (§3.7):
every number documents its source sessions, window, and normalization.
"""
from pipeline.progress.longitudinal import NormalizedSession, adapt_report, adapt_session
from pipeline.progress.progress import PROGRESS_VERSION, apply_progress_for_session, compute_progress
from pipeline.progress.readiness import READINESS_VERSION, READINESS_WEIGHTS, compute_readiness

__all__ = [
    "NormalizedSession", "adapt_report", "adapt_session",
    "PROGRESS_VERSION", "apply_progress_for_session", "compute_progress",
    "READINESS_VERSION", "READINESS_WEIGHTS", "compute_readiness",
]
