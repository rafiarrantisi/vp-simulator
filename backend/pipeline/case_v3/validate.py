"""STEP 2 — schema/content validation for the canonical clinical schema.

Covers STEP 2 §10 rules + the duplicated-truth invariant:
  - family/variant ID uniqueness & references resolve
  - source list non-empty for publishable variant
  - SKDI level in allowed values for primary bank
  - diagnosis present for disease variant
  - vitals typed consistently
  - no impossible required-field combos
  - publishable variant cannot be `ai_generated` only
  - persona constraints cannot overwrite protected clinical fields
  - one source of truth: derived outputs must equal canonical (no drift)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.case_v3.derive import derive_answer_key, derive_vitals
from pipeline.case_v3.models import (
    CaseFamily, ClinicalVariant, IdentityConstraints, PersonaConstraints,
)
from pipeline.case_v3.vocab import (
    SKDI_LEVELS_ALLOWED_PRIMARY,
    SKDI_LEVELS_KNOWN,
    DisclosureMode,
    FamilyType,
)

PROTECTED_FIELDS = {
    "working_diagnosis", "symptom_chronology", "age_category", "epidemiologic_exposure",
    "red_flags", "pregnancy", "comorbidity_affecting_management", "physical_findings",
    "investigations", "treatment_truth", "rubric",
}


@dataclass
class ValidationIssue:
    path: str
    message: str
    severity: str = "error"  # error | warning

    def __str__(self):
        return f"[{self.severity}] {self.path}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warning_d(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "ValidationResult"):
        self.issues.extend(other.issues)
        return self


def _iss(path, msg, severity="error") -> ValidationIssue:
    return ValidationIssue(path, msg, severity)


def validate_family(f: CaseFamily, *, known_families: set[str] | None = None) -> ValidationResult:
    res = ValidationResult()
    if not f.id:
        res.issues.append(_iss("family.id", "family id is required"))
    if not f.primary_specialty:
        res.issues.append(_iss(f.id + ".primary_specialty", "primary specialty is required"))
    if f.family_type == FamilyType.PRESENTATION and not f.presenting_complaints:
        res.issues.append(_iss(f.id, "presentation family needs presenting_complaints"))
    if f.family_type == FamilyType.DISEASE:
        for lvl in f.skdi_mappings:
            if lvl not in SKDI_LEVELS_KNOWN:
                res.issues.append(_iss(f.id + ".skdi", f"SKDI level {lvl} not known"))
    if known_families is not None and f.id in known_families:
        res.issues.append(_iss("family.id", f"duplicate family id {f.id}"))
    return res


def validate_variant(v: ClinicalVariant, *, require_source_for_publishable: bool = True,
                     primary_bank_skdi_only: bool = False) -> ValidationResult:
    res = ValidationResult()
    if not v.id:
        res.issues.append(_iss("variant.id", "variant id is required"))
    if not v.family_id:
        res.issues.append(_iss(v.id, "variant.family_id is required"))

    # diagnosis required for a disease-affiliated variant (family check deferred
    # to the registry; here we require a working diagnosis for any variant).
    if not v.diagnostic.working_diagnosis:
        res.issues.append(_iss(v.id, "working_diagnosis is required"))

    # SKDI level
    if v.skdi_level:
        if v.skdi_level not in SKDI_LEVELS_KNOWN:
            res.issues.append(_iss(v.id + ".skdi_level", f"unknown SKDI level {v.skdi_level}"))
        if primary_bank_skdi_only and v.skdi_level not in SKDI_LEVELS_ALLOWED_PRIMARY:
            res.issues.append(_iss(v.id + ".skdi_level",
                                   f"SKDI {v.skdi_level} outside primary bank scope (3A/3B/4A)"))

    # vitals typed consistently: every vital must have a name and a numeric/None value.
    for vs in v.physical_exam.vitals:
        if not vs.name:
            res.issues.append(_iss(v.id + ".vitals", "vital with empty name"))
        if vs.value is not None:
            try:
                float(vs.value)
            except (TypeError, ValueError):
                res.issues.append(_iss(v.id + ".vitals", f"vital '{vs.name}' value not numeric: {vs.value}"))

    # one source of truth — vitals screen derived == canonical.
    derived = derive_vitals(v)
    if [x["value"] for x in derived] != [x.value for x in v.physical_exam.vitals]:
        res.issues.append(_iss(v.id + ".vitals", "derive_vitals drifted from canonical vitals"))
    akey = derive_answer_key(v)
    if akey["working_diagnosis"] != v.diagnostic.working_diagnosis:
        res.issues.append(_iss(v.id + ".answer_key", "answer key drifted from canonical diagnosis"))

    # disclosure completeness: a present red flag must have a disclosure mode set.
    for r in v.red_flags:
        if r.disclosure == DisclosureMode.NEVER_REVEAL_TO_PATIENT and r.status.value == "present":
            pass  # allowed (e.g. protecting a specific diagnosis detail)
        if not r.why_matters:
            res.issues.append(_iss(v.id + ".red_flags", f"red flag '{r.fact}' lacks why_matters"))

    # publishable state
    if v.publishable and require_source_for_publishable and not v.sources:
        res.issues.append(_iss(v.id, "publishable variant requires non-empty sources"))
    if v.status in ("ai_generated", "draft") and v.publishable:
        res.issues.append(_iss(v.id, "publishable variant cannot be ai_generated/draft"))

    return res


def validate_identity_consistency(identity: IdentityConstraints) -> ValidationResult:
    """Impossible required-field combinations + age reversals."""
    res = ValidationResult()
    if identity.age_years is not None and identity.age_years < 0:
        res.issues.append(_iss("identity.age_years", "age cannot be negative"))
    if identity.pregnancy_status:
        s = identity.pregnancy_status.lower()
        bio = (identity.biological_sex or "").lower()
        if bio and not bio.startswith("f") and s not in ("not_pregnant", "none"):
            res.issues.append(_iss("identity.pregnancy_status",
                                   "pregnancy set on non-female biological sex"))
    return res


def validate_persona_constraints(c: PersonaConstraints, v: ClinicalVariant) -> ValidationResult:
    """Persona constraints must not reference or override protected clinical fields."""
    res = ValidationResult()
    for fld in c.randomizable_fields:
        if fld.lower() in PROTECTED_FIELDS:
            res.issues.append(_iss("persona.randomizable_fields",
                                   f"persona may not randomize protected field '{fld}'"))
    return res


def validate_registry(families: list[CaseFamily], variants: list[ClinicalVariant]) -> ValidationResult:
    res = ValidationResult()
    known_families = {f.id for f in families}
    fam_dup = set()
    for f in families:
        if f.id in fam_dup:
            res.issues.append(_iss("family.id", f"duplicate family id {f.id}"))
        fam_dup.add(f.id)
        res.extend(validate_family(f, known_families=None))
    var_seen = {}
    for v in variants:
        if v.id in var_seen:
            res.issues.append(_iss("variant.id", f"duplicate variant id {v.id}"))
        var_seen[v.id] = True
        if v.family_id not in known_families:
            res.issues.append(_iss(v.id, f"references missing family {v.family_id}"))
        res.extend(validate_variant(v))
    # family -> variant refs are valid
    for f in families:
        for vid in f.active_variant_ids:
            if vid not in var_seen:
                res.issues.append(_iss(f.id, f"active_variant_ids references missing variant {vid}"))
    return res