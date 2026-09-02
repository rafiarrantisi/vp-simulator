"""STEP 2 — derive canonical outputs from a ClinicalVariant (one source of truth).

Everything the runtime/scoring/debrief needs is DERIVED from the variant's
canonical truth. There are no independent copies, so the paediatric-fever
contradiction class (one section states one HR, persona prose another) is
structurally prevented: every screen reads from the same canonical objects.
"""
from __future__ import annotations

from pipeline.case_v3.models import ClinicalVariant, ItemImportance, LearnerStage
from pipeline.case_v3.vocab import Appropriateness


def derive_history_checklist(v: ClinicalVariant, *, learner_stage: LearnerStage | None = None,
                             group_filter: str | None = None) -> list[dict]:
    """Assessment checklist items from canonical history facts + explicit items.

    Every history fact yields a "ask about X" checklist item; explicit
    assessment items merge on top. Optionally filtered by learner stage.
    """
    out: list[dict] = []
    for g in v.history:
        for f in g.facts:
            item = {
                "item": f"Ask about {f.key.replace('_', ' ')}",
                "canonical_key": f.key,
                "value": f.value,
                "disclosure": f.disclosure.value,
                "importance": ItemImportance.HELPFUL.value,
                "group": g.name,
            }
            out.append(item)
    for a in v.assessment_items:
        if learner_stage and a.learner_stage and a.learner_stage != learner_stage:
            continue
        out.append({
            "item": a.text, "canonical_key": "", "value": None,
            "disclosure": "", "importance": a.importance.value, "group": a.group,
        })
    return out


def derive_red_flags(v: ClinicalVariant) -> list[dict]:
    return [
        {"fact": r.fact, "status": r.status.value, "criticality": r.criticality.value,
         "why_matters": r.why_matters, "disclosure": r.disclosure.value}
        for r in v.red_flags
    ]


def derive_vitals(v: ClinicalVariant) -> list[dict]:
    """Vitals screen reads the SAME canonical PhysicalExam.vitals as the persona."""
    return [x.to_dict() for x in v.physical_exam.vitals]


def derive_physical_exam(v: ClinicalVariant) -> dict:
    return v.physical_exam.to_dict()


def derive_investigations(v: ClinicalVariant, *, appropriateness: str | None = None) -> list[dict]:
    inv = [i.to_dict() for i in v.investigations]
    if appropriateness:
        inv = [i for i in inv if i["appropriateness"] == appropriateness]
    return inv


def derive_answer_key(v: ClinicalVariant) -> dict:
    """Answer key — fully determined by canonical truth (no separate copy)."""
    return {
        "working_diagnosis": v.diagnostic.working_diagnosis,
        "synonyms": v.diagnostic.synonyms,
        "differentials": [d.to_dict() for d in v.diagnostic.differentials],
        "reasoning_anchors": v.diagnostic.reasoning_anchors,
        "investigations": derive_investigations(v),
        "management": v.management.to_dict(),
        "red_flags": derive_red_flags(v),
        "sources": [s.to_dict() for s in v.sources],
    }


def derive_scoring_profile(v: ClinicalVariant, *, learner_stage: LearnerStage = LearnerStage.KOAS) -> dict:
    """Scoring profile per learner stage, from the same canonical truth."""
    items = derive_history_checklist(v, learner_stage=learner_stage)
    critical = [i for i in items if i["importance"] == ItemImportance.CRITICAL.value]
    helpful = [i for i in items if i["importance"] == ItemImportance.HELPFUL.value]
    rf_critical = [r for r in derive_red_flags(v)
                   if r["criticality"] in ("critical", "high", "moderate")]
    return {
        "learner_stage": learner_stage.value,
        "checklist_critical_count": len(critical),
        "checklist_total_count": len(items),
        "red_flag_critical_count": len(rf_critical),
        "safety_critical_errors": list(v.safety_critical_errors),
        "require_investigations": learner_stage == LearnerStage.KOAS,
    }


def derive_debrief(v: ClinicalVariant) -> dict:
    """Debrief content — derived, so 'feedback is source-backed' is structural."""
    return {
        "working_diagnosis": v.diagnostic.working_diagnosis,
        "missed_red_flags": [r for r in derive_red_flags(v) if r["status"] == "present"],
        "management_expectations": v.management.to_dict(),
        "sources": [s.to_dict() for s in v.sources],
        "investigations": derive_investigations(v),
    }


def essential_investigations(v: ClinicalVariant) -> list[dict]:
    return [i for i in derive_investigations(v)
            if i["appropriateness"] in (Appropriateness.ESSENTIAL.value, Appropriateness.APPROPRIATE.value)]


def derive_mode_views(v: ClinicalVariant, family_title: str = "") -> dict:
    """Course presentation per mode (STEP 5 §7).

    Targeted mode → diagnosis/family visible.
    Blind/OSCE mode → diagnosis hidden; only a candidate brief is shown, and
    the user reasons from the presenting complaint.
    """
    diag = v.diagnostic.working_diagnosis
    return {
        "targeted": {
            "family_title": family_title,
            "diagnosis_visible": True,
            "title": v.targeted_title or family_title or diag,
            "diagnosis": diag,
        },
        "blind": {
            "family_title": family_title,
            "diagnosis_visible": False,
            "candidate_brief": v.blind_candidate_brief or v.chief_complaint,
            "diagnosis": None,   # hidden
        },
    }


def derive_generation_bundle(v: ClinicalVariant, family_title: str = "") -> dict:
    """End-to-end scoring fixture for one variant (STEP 5 §12 'scoring fixture').

    One call that produces everything the pipeline needs from the single
    canonical truth — persona is generated separately and must stay skinned.
    """
    return {
        "variant_id": v.id,
        "family_id": v.family_id,
        "competency": v.competency.to_dict() if v.competency else {},
        "management_expectations": v.management_expectations.to_dict(),
        "history_checklist": derive_history_checklist(v),
        "red_flags": derive_red_flags(v),
        "vitals": derive_vitals(v),
        "physical_exam": derive_physical_exam(v),
        "investigations": derive_investigations(v),
        "answer_key": derive_answer_key(v),
        "scoring_profile": derive_scoring_profile(v),
        "debrief": derive_debrief(v),
        "modes": derive_mode_views(v, family_title),
        "sources": [s.to_dict() for s in v.sources],
    }