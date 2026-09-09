"""Phase PNPK-4 — enrichment wiring (brief §7).

Single entry `maybe_enrich_report`: flag-gated, fail-closed, metadata-only
metrics. Never raises, never mutates score-critical fields, never calls
network/LLM/PDF. Default OFF (QORA_EVIDENCE_ENRICH=1 to enable for pilot).
"""
from __future__ import annotations

import os

ENRICH_FLAG = "QORA_EVIDENCE_ENRICH"
EVIDENCE_DIR_ENV = "QORA_EVIDENCE_DIR"


def _evidence_dir():
    from pathlib import Path

    custom = os.environ.get(EVIDENCE_DIR_ENV)
    return Path(custom) if custom else None


def maybe_enrich_report(report: dict, *, variant_id: str = "",
                        canonical_hash: str = "", rubric_items=None,
                        mode: str = "practice", learner_stage: str = "koas",
                        clock=None) -> str:
    """Attach `clinical_evidence` when an approved binding exists.

    Returns the outcome label (attached/unavailable_*/enrichment_error).
    Report dict is mutated ONLY by adding the optional namespace key.
    """
    def _count(name: str, n: int = 1) -> None:
        try:
            if clock is not None:
                clock.count(name, n)
        except Exception:
            pass

    try:
        if os.environ.get(ENRICH_FLAG) != "1":
            return "disabled_flag_off"
        if not isinstance(report, dict):
            return "unavailable_bad_input"
        from app.domains.scoring import evidence_loader
        from app.domains.scoring.feedback_composer import compose_clinical_evidence

        binding = evidence_loader.resolve_binding(
            variant_id, canonical_hash, evidence_dir=_evidence_dir())
        if binding is None:
            _count("enrichment_unavailable")
            return "unavailable_no_binding"
        try:
            pack = evidence_loader.load_pack(
                binding.get("evidence_pack_sha256") or "",
                evidence_dir=_evidence_dir())
        except Exception:
            _count("enrichment_unavailable")
            return "unavailable_pack_invalid"
        ns, outcome = compose_clinical_evidence(
            report=report, rubric_items=rubric_items or [], pack=pack,
            binding=binding, mode=mode, learner_stage=learner_stage,
            variant_id=variant_id)
        if ns is None:
            _count("enrichment_unavailable")
            return outcome
        report["clinical_evidence"] = ns
        _count("enrichment_attached")
        _count("enrichment_citations", len(ns.get("references") or []))
        return "attached"
    except Exception:
        try:
            _count("enrichment_error")
        except Exception:
            pass
        return "enrichment_error"
