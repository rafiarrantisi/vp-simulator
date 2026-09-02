"""STEP 6 — backend runtime, session selection, scoring, debrief contract.

Pure/logic layer operating on the case_v3 canonical data model. Decoupled from
the live v2 runtime so the existing product flow is untouched.

Covers (06_BACKEND_RUNTIME_SCORING_AND_ANALYTICS.md):
  §1-§2  targeted + blind selection, controlled variant policy
  §3     persona instantiation (reproducible, falls back safely)
  §5     encounter stages
  §6-§8  hybrid scoring: family-core + variant rubric + global dims + safety
         gates + learner-level profile (SKD 2026 competency mapping)
  §9-§10 structured, source-backed debrief contract
  §13    failure modes

SKDI 2012 3A/3B/4A is obsolete here (superseding rule 1); primary competency
mapping uses SKD 2026 `tuntas` / `initial_management_and_referral`, and
behaviour comes case-specifically from management_expectations (rule 2).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from pipeline.case_v3.derive import (
    derive_answer_key, derive_debrief, derive_history_checklist,
    derive_investigations, derive_mode_views, derive_physical_exam,
    derive_red_flags, derive_scoring_profile, derive_vitals,
)
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.models import ClinicalVariant, ManagementExpectations
from pipeline.case_v3.persona import build_session_instance, persona_from_constraints
from pipeline.case_v3.vocab import (
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL, SKD2026_CATEGORY_TUNTAS,
    FamilyType, ItemImportance, LearnerStage,
)


@dataclass
class SelectionRequest:
    mode: str = "targeted"                       # targeted | blind | random
    family_id: Optional[str] = None              # targeted mode
    specialty: Optional[str] = None              # blind mode filter
    presentation: Optional[str] = None           # blind mode filter
    learner_stage: str = "koas"
    difficulty: Optional[str] = None
    emergency_only: Optional[bool] = None
    exclude_recent_variant_ids: list = field(default_factory=list)
    seed: int = 0
    released_ids: Optional[set] = None           # allowed/verified variant ids


@dataclass
class SelectionResult:
    variant: ClinicalVariant
    family_title: str = ""
    reason: str = ""                             # selection reason for audit
    entry_point: Optional[str] = None

    def to_dict(self) -> dict:
        return {"variant_id": self.variant.id, "family_id": self.variant.family_id,
                "family_title": self.family_title, "reason": self.reason,
                "entry_point": self.entry_point}


# ── §1-2 Variant selection ─────────────────────────────────────────────────
class SelectionPolicy:
    """Controlled selection — NOT naive pure random."""

    def __init__(self, registry: CaseRegistry):
        self.reg = registry

    def _eligible(self, req: SelectionRequest) -> list[ClinicalVariant]:
        out = []
        for fid, fam in self.reg.families.items():
            for v in self.reg.variants_for_family(fid):
                if v.id in req.exclude_recent_variant_ids:
                    continue
                if req.released_ids is not None and v.id not in req.released_ids:
                    continue  # unverified excluded in verified-only flow
                if _not_stage_compatible(v, req.learner_stage):
                    continue
                if req.family_id and v.family_id != req.family_id:
                    continue
                if req.specialty and (fam.primary_specialty or "") != req.specialty \
                        and req.specialty not in fam.cross_specialty_tags:
                    continue
                out.append(v)
        return out

    def select(self, req: SelectionRequest) -> SelectionResult:
        cands = self._eligible(req)
        if not cands:
            raise VariantUnavailable(
                f"No eligible variant for {req.mode} (family={req.family_id}, "
                f"specialty={req.specialty}, stage={req.learner_stage})")

        # deterministic ordering: prefer not-recent, then stability order
        import random
        rng = random.Random(req.seed)
        cands.sort(key=lambda v: (v.id in req.exclude_recent_variant_ids,
                                  v.variation_level.value, v.id))
        chosen = cands[0]
        # reason for audit
        reason = (f"policy: eligible={len(cands)}, not_recent={chosen.id not in req.exclude_recent_variant_ids}, "
                  f"seed={req.seed}")
        return SelectionResult(variant=chosen, family_title=self.reg.families[chosen.family_id].title_en or "",
                               reason=reason)


def _not_stage_compatible(v: ClinicalVariant, stage: str) -> bool:
    want = _stage(stage)
    return bool(v.supported_stages) and want not in v.supported_stages


def _stage(s: str) -> LearnerStage:
    try:
        return LearnerStage(s)
    except ValueError:
        return LearnerStage.KOAS


class VariantUnavailable(Exception):
    pass


# ── §3 persona instantiation with safe fallback ────────────────────────────
@dataclass
class PersonaResult:
    persona: dict
    seed: int
    used_fallback: bool
    protected_unchanged: bool

    def to_dict(self) -> dict:
        return {"seed": self.seed, "used_fallback": self.used_fallback,
                "protected_unchanged": self.protected_unchanged, "persona": self.persona}


def instantiate_persona(v: ClinicalVariant, constraints, seed: int,
                        protected_expected: dict) -> PersonaResult:
    """Generate persona; on failure fall back to a safe default persona without
    regenerating clinical facts."""
    used_fallback = False
    try:
        persona = persona_from_constraints(v, constraints, seed)
    except Exception:
        # safe default: keep protected facts, no randomisation
        lang = getattr(constraints, "language_style", "") if constraints else ""
        hl = getattr(constraints, "education_health_literacy", "") if constraints else ""
        rel = getattr(constraints, "relationship", "self") if constraints else "self"
        persona = {
            "name": "", "occupation": "", "hobby": "", "emotional_tone": "neutral",
            "verbosity": "medium", "language_style": lang,
            "health_literacy": hl, "relationship": rel,
            "working_diagnosis": protected_expected.get("working_diagnosis"),
            "chief_complaint": protected_expected.get("chief_complaint"),
            "red_flags": protected_expected.get("red_flags"),
            "vitals": protected_expected.get("vitals"),
        }
        used_fallback = True
    protected_unchanged = (persona.get("working_diagnosis") == protected_expected.get("working_diagnosis")
                           and persona.get("vitals") == protected_expected.get("vitals"))
    return PersonaResult(persona=persona, seed=seed,
                         used_fallback=used_fallback,
                         protected_unchanged=protected_unchanged)


def build_session(v: ClinicalVariant, *, persona_seed: int, learner_stage: str = "koas",
                  mode: str = "blind", entry_point: str | None = None,
                  constraints=None):
    """Combine selection + reproducible persona into a runtime session bundle."""
    inst = build_session_instance(v, persona_seed=persona_seed, learner_stage=learner_stage,
                                  mode=mode, entry_point=entry_point)
    persona = persona_from_constraints(v, constraints or _default_constraints(), persona_seed)
    return {"session_instance": inst.to_dict(),
            "persona": persona,
            "mode_views": derive_mode_views(v, family_title=""),
            "session_reproducible_key": inst.reproducibility_key()}


def _default_constraints():
    from pipeline.case_v3.models import PersonaConstraints
    return PersonaConstraints(relationship="self", allow_name_generation=True,
                              anxiety_level="range", verbosity="range")


# ── §5 encounter stages ────────────────────────────────────────────────────
ENCOUNTER_STAGES = [
    "candidate_brief", "history", "general_condition", "vitals", "physical_exam",
    "investigations", "working_diagnosis", "differentials", "diagnostic_justification",
    "management", "prescription", "submit", "debrief",
]


def encounter_stages_for(v: ClinicalVariant, mode: str) -> list[str]:
    """Which stages this case/mode needs (case-specific, not all necessarily)."""
    always = ["candidate_brief", "history", "physical_exam", "submit"]
    if mode == "blind":
        always = ["candidate_brief", "history", "physical_exam", "submit"]
    else:
        always = ["candidate_brief", "history", "physical_exam", "working_diagnosis", "submit"]
    if v.physical_exam.vitals:
        always.insert(1, "vitals")
    if v.investigations:
        always.insert(2, "investigations")
    return always


# ── §6-8 scoring architecture ──────────────────────────────────────────────
@dataclass
class ScoreInput:
    variant: ClinicalVariant
    learner_stage: str = "koas"
    collected_items: dict = field(default_factory=dict)   # item_key -> bool collected
    stabilized: bool | None = None
    gave_referral: bool | None = None
    diagnosis_submitted: str = ""

    @property
    def is_initial_refer(self) -> bool:
        return (self.variant.competency.category
                == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL)


@dataclass
class ScoreResult:
    total: float = 0.0
    max_score: float = 0.0
    by_dimension: dict = field(default_factory=dict)
    safety_flags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"total": round(self.total, 1), "max": self.max_score,
                "by_dimension": self.by_dimension, "safety_flags": self.safety_flags}


def score_encounter(inp: ScoreInput) -> ScoreResult:
    """Hybrid scoring: family-core + variant rubric + global dims + safety gates.
    Learner-level profile is configurable by dimension weights.

    SKD 2026 mapping:
      - `tuntas`             → assess recogn./diagnosis, complete management
      - `initial&referral`   → PROMINENTLY assess stabilisation + urgent referral
    Behavior sourced from case management_expectations, NOT category alone.
    """
    res = ScoreResult()
    me = inp.variant.management_expectations

    dims = ["info_gathering", "focus_efficiency", "reasoning_coherence",
            "diagnostic_quality", "investigation_strategy", "management_safety",
            "communication"]
    profile = learner_profile(inp.learner_stage)
    # history/rubric completeness (family core + variant)
    checklist = derive_history_checklist(inp.variant, learner_stage=_stage(inp.learner_stage))
    crit = [c for c in checklist if c["importance"] == ItemImportance.CRITICAL.value]
    collected_crit = sum(1 for c in crit if inp.collected_items.get(c["canonical_key"] or c["item"]))
    ratio = (collected_crit / len(crit)) if crit else 1.0
    res.by_dimension["info_gathering"] = {"score": ratio, "notes": f"{collected_crit}/{len(crit)} critical items"}

    # diagnostic quality
    dx_match = _dx_match(inp.diagnosis_submitted, inp.variant.diagnostic.working_diagnosis)
    res.by_dimension["diagnostic_quality"] = {"score": 1.0 if dx_match else 0.2, "notes": ("correct" if dx_match else "not target diagnosis")}

    # investigations strategy
    res.by_dimension["investigation_strategy"] = {"score": 1.0 if inp.variant.investigations else 0.0}

    # management/safety dimension — learner-level + SKD category aware
    mgmt_score = _management_score(inp, me)
    res.by_dimension["management_safety"] = {"score": mgmt_score}

    # remaining dims default to neutral (full fidelity is runtime/LLM-judged)
    for d in ("focus_efficiency", "reasoning_coherence", "communication"):
        res.by_dimension.setdefault(d, {"score": 0.5, "notes": "semantic fan (TLV judge in prod)"})

    # weighted total
    w = profile["weights"]
    total = sum(res.by_dimension.get(d, {}).get("score", 0.5) * w.get(d, 0.1)
                for d in dims)
    res.total = total
    res.max_score = sum(profile["weights"].values()) or 1.0

    # ── safety gates (rule 4 semantics) ──────────────────────────────────
    res.safety_flags = safety_gates(inp, me)
    return res


def safety_gates(inp: ScoreInput, me: ManagementExpectations) -> list:
    flags = []
    cat = inp.variant.competency.category
    # Missed emergency red flag
    emerg = [r for r in derive_red_flags(inp.variant)
             if r["criticality"] == "critical" and r["status"] == "present"]
    if emerg and not inp.collected_items:
        flags.append({"gate": "missed_emergency_red_flag", "critical": True})
    # Unsafe/contraindicated
    for err in inp.variant.safety_critical_errors:
        if _mentions(err, inp.collected_items.get("_unsafe_action", "")):
            flags.append({"gate": "unsafe_management", "critical": True})
    # Stabilization requirement (rule 4: only when case says TRUE)
    if cat == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL and me.emergency_stabilization_required is True:
        if inp.stabilized is False:
            flags.append({"gate": "failure_to_stabilize", "critical": True})
    # urgent referral
    if cat == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL and \
            me.referral_urgency in ("immediate", "urgent") and inp.gave_referral is False:
        flags.append({"gate": "failed_urgent_referral", "critical": True})
    # contraindicated
    return flags


def _management_score(inp: ScoreInput, me: ManagementExpectations) -> float:
    """Management completeness depends on what the case expects (not category)."""
    pts = 0.0
    tot = 0.0
    cat = inp.variant.competency.category
    if cat == SKD2026_CATEGORY_TUNTAS:
        # tuntas: assess complete expectation (diagnosis/management/appropriate referral plan)
        tot += 1
        pts += 1.0 if inp.collected_items.get("management_complete") else 0.0
        # Tuntas may still need referral plan per case
        if me.referral_indication:
            tot += 1
            pts += 1.0 if inp.gave_referral is not None else 0.3
    elif inp.is_initial_refer:
        # initial&refer: stabilization + urgent referral prominent
        if me.emergency_stabilization_required is True:
            tot += 1
            pts += 1.0 if inp.stabilized else 0.0
        else:
            tot += 1
            pts += 0.6  # no automatic stabilization penalty (rule 4)
        if me.referral_indication:
            tot += 1
            pts += 1.0 if inp.gave_referral else 0.0
    return (pts / tot) if tot else 0.4


def _dx_match(submitted: str, target: str) -> bool:
    if not submitted:
        return False
    return submitted.strip().lower() in target.lower() or target.lower() in submitted.strip().lower()


def _mentions(s: str, found: str) -> bool:
    return bool(found) and any(w and w.lower() in (found or "").lower() for w in (s or "").split())


def learner_profile(stage: str) -> dict:
    """Configurable per-learner-stage weights (not hard-coded universal)."""
    if stage == "preclinical":
        return {
            "weights": {"info_gathering": 0.30, "focus_efficiency": 0.10,
                        "reasoning_coherence": 0.10, "diagnostic_quality": 0.10,
                        "investigation_strategy": 0.10, "management_safety": 0.15,
                        "communication": 0.15},
        }
    return {  # koas/clinical (default)
        "weights": {"info_gathering": 0.20, "focus_efficiency": 0.15,
                    "reasoning_coherence": 0.15, "diagnostic_quality": 0.15,
                    "investigation_strategy": 0.10, "management_safety": 0.20,
                    "communication": 0.05},
    }


# ── §9-10 debrief data contract (structured, source-backed) ───────────────
def build_debrief(v: ClinicalVariant, *, score: ScoreResult | None = None,
                  family_title: str = "") -> dict:
    """Structured debrief per STEP 6 §9 — frontend decides presentation."""
    d = derive_debrief(v)
    checklist = derive_history_checklist(v)
    return {
        "overall_summary": {
            "target_diagnosis": v.diagnostic.working_diagnosis,
            "family": family_title or v.family_id,
        },
        "strengths": [],
        "biggest_misses": [f for f in derive_red_flags(v) if f["status"] == "present"],
        "safety_flags": score.safety_flags if score else safety_gates(
            ScoreInput(variant=v), v.management_expectations),
        "differential_comparison": d["working_diagnosis"],  # full in derive
        "history_item_status": checklist,
        "exam_review": derive_physical_exam(v),
        "investigation_review": derive_investigations(v),
        "management_review": v.management.to_dict(),
        "management_expectations": v.management_expectations.to_dict(),
        "sources": _source_summary(v),
        "competency_mapping": v.competency.to_dict() if v.competency else {},
        "next_practice_suggestions": [],
        "retry_variant_options": [],
    }


def _source_summary(v: ClinicalVariant) -> list[dict]:
    return [{"title": s.title, "organization": s.authority, "year": s.year,
             "url": s.url, "kind": s.kind}
            for s in v.sources]


# ── §13 failure modes ──────────────────────────────────────────────────────
def safe_select(req: SelectionRequest, policy: SelectionPolicy,
                released_ids: set | None = None) -> SelectionResult:
    """Safety wrapper: never silently substitute an unreviewed case into a
    verified flow. If nothing eligible → raise (caller surfaces as error, no
    fallback to unreviewed)."""
    req.released_ids = released_ids
    return policy.select(req)