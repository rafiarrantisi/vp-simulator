"""Answer-key (model-answer) builder for the debrief reveal (BUILD_PLAN §6.3).

Produces the full "what a complete workup should have included" structure from a
schema-v2 case's Part A frontmatter ONLY. The frontend overlays the student's
per-item hits/misses (from the judge) on top of this. Pure: no LLM, no DB.
"""
from __future__ import annotations

from pipeline.case_v2 import CaseV2


def build_answer_key(case: CaseV2) -> dict:
    """The complete model answer for one case (Part A only)."""
    fm = case.frontmatter
    ddx = fm.get("expected_ddx") or {}
    inv = fm.get("investigations") or {}
    mgmt = fm.get("management") or {}
    return {
        "case_id": case.id,
        "presentation": fm.get("presentation", ""),
        "chief_complaint": fm.get("chief_complaint", ""),
        "anamnesis_checklist": _grouped_checklist(case),
        "red_flags": case.red_flag_items(),
        "expected_ddx": {
            "working_diagnosis": ddx.get("working_diagnosis", ""),
            "differentials": list(ddx.get("differentials") or []),
        },
        "investigations": {
            "appropriate": list(inv.get("appropriate") or []),
            "inappropriate": list(inv.get("inappropriate") or []),
        },
        "management": {
            "pharmacological": list(mgmt.get("pharmacological") or []),
            "non_pharmacological": list(mgmt.get("non_pharmacological") or []),
            "education_safety_netting": list(mgmt.get("education_safety_netting") or []),
        },
    }


def _grouped_checklist(case: CaseV2) -> list[dict]:
    """Checklist grouped by dimension, preserving order, for tabbed display."""
    cl = case.frontmatter.get("anamnesis_checklist") or {}
    out: list[dict] = []
    if isinstance(cl, dict):
        for group, items in cl.items():
            out.append({
                "group": group,
                "items": [
                    {"item": str((it or {}).get("item", it) if isinstance(it, dict) else it).strip(),
                     "critical": bool(it.get("critical", False)) if isinstance(it, dict) else False}
                    for it in (items or [])
                ],
            })
    return out
