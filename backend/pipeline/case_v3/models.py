"""STEP 2 — canonical clinical schema model (case_v3).

Hierarchy:
  Specialty/Domain → CaseFamily → ClinicalVariant → PersonaConstraints
  → Runtime Persona Instance → Dynamic Conversation

`ClinicalVariant` IS the canonical medical truth. Every downstream artefact
(checklist, vitals, exam, investigations, diagnosis, management, scoring
profile, answer key, debrief) is DERIVED from it — there is no independent
copy, so contradictions of the paediatric-fever-proto class are structurally
difficult.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from pipeline.case_v3.vocab import (
    Appropriateness,
    ClinicalVitalUnits,
    DisclosureMode,
    FactStatus,
    FamilyType,
    ItemImportance,
    LearnerStage,
    RedFlagCriticality,
    VariationLevel,
)

KNOWN_FIELD_ALIASES = {
    "age": ["age_years", "age_months", "age_range", "umur"],
    "sex": ["biological_sex", "gender_bio", "jenis_kelamin"],
    "pregnancy": ["gravida", "parity", "gestation", "hamil"],
}


def _coerce_enum(value: Any, enum_cls, default=None):
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            return default
    return default


# ── Identity constraints (clinically meaningful only) ──────────────────────
@dataclass
class IdentityConstraints:
    age_years: Optional[float] = None
    age_range: Optional[str] = None          # e.g. "2-5y" when interchangeable
    biological_sex: Optional[str] = None
    pregnancy_status: Optional[str] = None
    informant_type: Optional[str] = None     # e.g. "mother", "patient", "carer"
    setting: Optional[str] = None            # e.g. "primary care", "ED"
    population_tags: list[str] = field(default_factory=list)

    @property
    def clinically_meaningful(self) -> bool:
        """At least one clinically meaningful attribute present."""
        return any(
            v not in (None, "", [], {}) for v in (
                self.age_years, self.age_range, self.biological_sex,
                self.pregnancy_status, self.informant_type, self.setting,
                self.population_tags,
            )
        )


# ── History fact with disclosure semantics (no freeform prose) ─────────────
@dataclass
class HistoryFact:
    key: str                       # e.g. "travel_to_endemic_area"
    value: Any                      # canonical value
    disclosure: DisclosureMode = DisclosureMode.DIRECT_QUESTION
    acceptable_intents: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "disclosure": self.disclosure.value,
            "acceptable_intents": self.acceptable_intents,
            "note": self.note,
        }


@dataclass
class HistoryGroup:
    """Complaint-appropriate history — NOT forced generic SOCRATES."""
    name: str                       # e.g. "onset", "chronology", "exposure"
    facts: list[HistoryFact] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "facts": [f.to_dict() for f in self.facts]}


# ── Red flags ──────────────────────────────────────────────────────────────
@dataclass
class RedFlag:
    fact: str
    status: FactStatus = FactStatus.PRESENT
    criticality: RedFlagCriticality = RedFlagCriticality.CRITICAL
    why_matters: str = ""
    disclosure: DisclosureMode = DisclosureMode.DIRECT_QUESTION
    acceptable_intents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "fact": self.fact,
            "status": self.status.value,
            "criticality": self.criticality.value,
            "why_matters": self.why_matters,
            "disclosure": self.disclosure.value,
            "acceptable_intents": self.acceptable_intents,
        }


# ── Physical examination (canonical) ───────────────────────────────────────
@dataclass
class VitalSign:
    name: str
    value: Optional[float]
    unit: ClinicalVitalUnits = ClinicalVitalUnits.NONE
    normal_range: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "unit": self.unit.value,
                "normal_range": self.normal_range, "note": self.note}


@dataclass
class PhysicalExam:
    general_appearance: str = ""
    consciousness: Optional[str] = None
    vitals: list[VitalSign] = field(default_factory=list)
    system_findings: dict[str, str] = field(default_factory=dict)  # system -> findings

    def to_dict(self) -> dict:
        return {
            "general_appearance": self.general_appearance,
            "consciousness": self.consciousness,
            "vitals": [v.to_dict() for v in self.vitals],
            "system_findings": self.system_findings,
        }


# ── Investigation ──────────────────────────────────────────────────────────
@dataclass
class Investigation:
    name: str
    expected_result: str
    appropriateness: Appropriateness = Appropriateness.APPROPRIATE
    rationale: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name, "expected_result": self.expected_result,
            "appropriateness": self.appropriateness.value,
            "rationale": self.rationale, "source": self.source,
        }


# ── Diagnostic truth ───────────────────────────────────────────────────────
@dataclass
class Differential:
    name: str
    discriminating_features: str = ""
    reverting: bool = False  # must be ruled out for safety

    def to_dict(self) -> dict:
        return {"name": self.name,
                "discriminating_features": self.discriminating_features,
                "reverting": self.reverting}


@dataclass
class DiagnosticTruth:
    working_diagnosis: str
    synonyms: list[str] = field(default_factory=list)
    differentials: list[Differential] = field(default_factory=list)
    reasoning_anchors: list[str] = field(default_factory=list)  # decision anchors
    icd10: str = ""

    def to_dict(self) -> dict:
        return {
            "working_diagnosis": self.working_diagnosis,
            "synonyms": self.synonyms,
            "differentials": [d.to_dict() for d in self.differentials],
            "reasoning_anchors": self.reasoning_anchors,
            "icd10": self.icd10,
        }


# ── Management ─────────────────────────────────────────────────────────────
@dataclass
class Management:
    stabilization: list[str] = field(default_factory=list)
    pharmacologic: list[str] = field(default_factory=list)
    non_pharmacologic: list[str] = field(default_factory=list)
    referral: list[str] = field(default_factory=list)
    follow_up: list[str] = field(default_factory=list)
    education_safety_netting: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Assessment item ────────────────────────────────────────────────────────
@dataclass
class AssessmentItem:
    text: str
    importance: ItemImportance = ItemImportance.HELPFUL
    group: str = ""
    learner_stage: Optional[LearnerStage] = None  # None = both

    def to_dict(self) -> dict:
        return {"text": self.text, "importance": self.importance.value,
                "group": self.group,
                "learner_stage": self.learner_stage.value if self.learner_stage else None}


# ── Source-governance ──────────────────────────────────────────────────────
@dataclass
class Source:
    title: str
    authority: str = ""       # e.g. "Kemenkes PNPK", "KKI SKDI"
    version: str = ""
    year: str = ""
    url: str = ""
    kind: str = ""            # competency | guideline | epidemiology | formulary

    def to_dict(self) -> dict:
        return asdict(self)


# ── CLINICAL VARIANT — canonical medical truth ─────────────────────────────
@dataclass
class Competency:
    """SKD 2026 competency classification (primary) + legacy SKDI 2012 crosswalk.

    `standard` names the authority; `category` uses the OFFICIAL SKD 2026 terms
    ('tuntas' | 'initial_management_and_referral'). `legacy_level` (3A/3B/4A)
    is OPTIONAL and ONLY set when verified against SKDI 2012 — never inferred
    from the 2026 category. `mapping_confirmed` records that a human reviewed it.
    """
    standard: str = "SKD 2026"
    category: Optional[str] = None                     # SKD2026_CATEGORIES
    reference: str = ""                                # HK.01.02/KKI/2183/2026
    system: str = ""                                   # SKD2026_SYSTEMS bucket
    legacy_standard: str = "SKDI 2012"
    legacy_level: Optional[str] = None                 # 3A/3B/4A or None
    legacy_mapping_confirmed: bool = False
    legacy_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClinicalVariant:
    id: str
    family_id: str
    variation_level: VariationLevel = VariationLevel.PRESENTATION
    title: str = ""
    supported_stages: list[LearnerStage] = field(default_factory=lambda: [LearnerStage.KOAS])
    # competency (SKD 2026 primary + SKDI 2012 legacy crosswalk) — see Competency dataclass
    @property
    def skdi_level(self) -> Optional[str]:
        # backward-compat read: legacy level lives on competency.legacy_level
        return self.competency.legacy_level if self.competency else None

    identity: IdentityConstraints = field(default_factory=IdentityConstraints)
    chief_complaint: str = ""
    opening_context: str = ""
    duration: str = ""
    severity: str = ""
    key_chronology: str = ""
    history: list[HistoryGroup] = field(default_factory=list)

    competency: Competency = field(default_factory=Competency)
    red_flags: list[RedFlag] = field(default_factory=list)
    physical_exam: PhysicalExam = field(default_factory=PhysicalExam)
    investigations: list[Investigation] = field(default_factory=list)
    diagnostic: DiagnosticTruth = field(default_factory=lambda: DiagnosticTruth(""))
    management: Management = field(default_factory=Management)

    assessment_items: list[AssessmentItem] = field(default_factory=list)
    safety_critical_errors: list[str] = field(default_factory=list)

    sources: list[Source] = field(default_factory=list)
    source_governance: dict = field(default_factory=dict)

    status: str = "draft"
    clinical_content_version: str = ""
    source_review_date: str = ""
    variant_previous_version: Optional[str] = None

    # Derived single-source convenience ------------------------------------
    def history_lookup(self, key: str) -> Optional[HistoryFact]:
        for g in self.history:
            for f in g.facts:
                if f.key == key:
                    return f
        return None

    def all_history_facts(self) -> list[HistoryFact]:
        return [f for g in self.history for f in g.facts]

    def protected_fields_canonical(self) -> dict:
        """The clinical fields persona generation must NEVER override."""
        return {
            "working_diagnosis": self.diagnostic.working_diagnosis,
            "red_flags": [r.fact for r in self.red_flags],
            "vitals": [v.to_dict() for v in self.physical_exam.vitals],
            "chief_complaint": self.chief_complaint,
        }

    # Publishability guard
    @property
    def publishable(self) -> bool:
        if self.status in ("published",):
            return True
        return self.status in ("clinically_reviewed", "pilot_verified")

    def to_dict(self) -> dict:
        return {
            "id": self.id, "family_id": self.family_id,
            "variation_level": self.variation_level.value, "title": self.title,
            "supported_stages": [s.value for s in self.supported_stages],
            "competency": self.competency.to_dict() if self.competency else {"standard": "SKD 2026"},
            "identity": asdict(self.identity),
            "chief_complaint": self.chief_complaint,
            "opening_context": self.opening_context, "duration": self.duration,
            "severity": self.severity, "key_chronology": self.key_chronology,
            "history": [g.to_dict() for g in self.history],
            "red_flags": [r.to_dict() for r in self.red_flags],
            "physical_exam": self.physical_exam.to_dict(),
            "investigations": [i.to_dict() for i in self.investigations],
            "diagnostic": self.diagnostic.to_dict(),
            "management": self.management.to_dict(),
            "assessment_items": [i.to_dict() for i in self.assessment_items],
            "safety_critical_errors": self.safety_critical_errors,
            "sources": [s.to_dict() for s in self.sources],
            "source_governance": self.source_governance,
            "status": self.status, "clinical_content_version": self.clinical_content_version,
            "source_review_date": self.source_review_date,
            "variant_previous_version": self.variant_previous_version,
        }

    # Reproducibility: a canonical content hash of the CLINICAL truth only
    # (persona fields excluded), so two variants differing only in "name" hash equal.
    def canonical_hash(self) -> str:
        d = dict(self.to_dict())
        d.pop("id", None)  # id is identity, not clinical truth
        d.pop("title", None)
        payload = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ── CASE FAMILY ────────────────────────────────────────────────────────────
@dataclass
class CaseFamily:
    id: str
    family_type: FamilyType = FamilyType.DISEASE
    title_id: str = ""
    title_en: str = ""
    primary_specialty: str = ""
    cross_specialty_tags: list[str] = field(default_factory=list)
    presenting_complaints: list[str] = field(default_factory=list)
    population_tags: list[str] = field(default_factory=list)
    target_stages: list[LearnerStage] = field(default_factory=lambda: [LearnerStage.KOAS])
    skdi_mappings: dict = field(default_factory=dict)   # {level: [competency_codes]}
    learning_objectives: list[str] = field(default_factory=list)
    common_differentials: list[str] = field(default_factory=list)
    active_variant_ids: list[str] = field(default_factory=list)  # refs (not copies)
    source_governance: dict = field(default_factory=dict)
    status: str = "draft"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "family_type": self.family_type.value,
            "title_id": self.title_id, "title_en": self.title_en,
            "primary_specialty": self.primary_specialty,
            "cross_specialty_tags": self.cross_specialty_tags,
            "presenting_complaints": self.presenting_complaints,
            "population_tags": self.population_tags,
            "target_stages": [s.value for s in self.target_stages],
            "skdi_mappings": self.skdi_mappings,
            "learning_objectives": self.learning_objectives,
            "common_differentials": self.common_differentials,
            "active_variant_ids": self.active_variant_ids,
            "source_governance": self.source_governance, "status": self.status,
        }


# ── PERSONA CONSTRAINTS (never a source of clinical truth) ────────────────
@dataclass
class PersonaConstraints:
    relationship: str = ""                    # caregiver/patient relationship
    allow_name_generation: bool = False
    age_range_interchangeable: str = ""       # only if clinically neutral
    occupation_set: list[str] = field(default_factory=list)  # only clinically non-critical
    education_health_literacy: str = ""
    language_style: str = ""
    anxiety_level: str = "neutral"            # range allowed, not affecting medicine
    verbosity: str = "medium"
    cultural_social_context: str = ""
    # The persona may randomize these; must NEVER randomize protected clinical fields.
    randomizable_fields: list[str] = field(default_factory=lambda: [
        "name", "non_critical_occupation", "hobbies", "phrasing", "emotional_tone",
    ])

    def to_dict(self) -> dict:
        return asdict(self)


# ── RUNTIME INSTANCE ───────────────────────────────────────────────────────
@dataclass
class SessionInstance:
    family_id: str
    variant_id: str
    persona_seed: int
    session_facts: dict = field(default_factory=dict)     # deterministic per-session facts
    language: str = "id"
    learner_stage: LearnerStage = LearnerStage.KOAS
    mode: str = "blind"                                   # blind | targeted | random
    timer_enabled: bool = True
    hidden_labels: dict = field(default_factory=dict)     # what learner does/doesn't see
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    entry_point: Optional[str] = None                     # "disease:dengue" | "presentation:fever"

    def to_dict(self) -> dict:
        return {
            "family_id": self.family_id, "variant_id": self.variant_id,
            "persona_seed": self.persona_seed, "session_facts": self.session_facts,
            "language": self.language, "learner_stage": self.learner_stage.value,
            "mode": self.mode, "timer_enabled": self.timer_enabled,
            "hidden_labels": self.hidden_labels, "session_id": self.session_id,
            "entry_point": self.entry_point,
        }

    def reproducibility_key(self) -> str:
        """Stable key: same inputs → same instance (for audit/debug)."""
        d = dict(self.to_dict())
        d.pop("session_id", None)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:24]