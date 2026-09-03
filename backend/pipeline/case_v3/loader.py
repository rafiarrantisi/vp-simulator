"""STEP 2 — case_v3 loader / registry (canonical clinical schema).

Loads families + variants from `content/v3/` (YAML), maintains ID uniqueness,
validates references, and indexes variants by family + by entry point so one
variant is reachable from multiple families (disease AND presentation).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import yaml

from pipeline.case_v3.models import (
    Appropriateness,
    AssessmentItem,
    CaseFamily,
    ClinicalVariant,
    Competency,
    DiagnosticTruth,
    Differential,
    DisclosureMode,
    FactStatus,
    HistoryFact,
    HistoryGroup,
    IdentityConstraints,
    Investigation,
    ItemImportance,
    LearnerStage,
    Management,
    ManagementExpectations,
    PersonaConstraints,
    PhysicalExam,
    RedFlag,
    RedFlagCriticality,
    Source,
    VitalSign,
    ClinicalVitalUnits,
)
from pipeline.case_v3.vocab import FamilyType, VariationLevel

REPO = Path(__file__).resolve().parents[2]  # backend/
_DEFAULT_ROOT = REPO.parent / "content" / "v3"


def _enum(enum_cls, raw, default):
    if not raw:
        return default
    try:
        return enum_cls(raw) if isinstance(raw, str) else raw
    except ValueError:
        return default


def _stage(raw) -> Optional[LearnerStage]:
    return _enum(LearnerStage, raw, None)


def _stages(raw) -> list[LearnerStage]:
    out = [_stage(s) for s in (raw or ["koas"])]
    return [s for s in out if s is not None]


def load_variant(raw: dict) -> ClinicalVariant:
    v = ClinicalVariant(
        id=str(raw.get("id", "")), family_id=str(raw.get("family_id", "")),
        variation_level=_enum(VariationLevel, raw.get("variation_level"), VariationLevel.PRESENTATION),
        title=str(raw.get("title", "")),
        supported_stages=_stages(raw.get("supported_stages")),
    )
    # legacy flat `skdi_level` promoted into the competency crosswalk (SKDI 2012)
    comp = raw.get("competency") or {}
    if "legacy_level" not in comp and raw.get("skdi_level"):
        comp = dict(comp, legacy_level=raw.get("skdi_level"))
    v.competency = Competency(
        standard=str(comp.get("standard") or "SKD 2026"),
        category=(comp.get("category") or None),
        reference=str(comp.get("reference") or ""),
        system=str(comp.get("system") or ""),
        legacy_standard=str(comp.get("legacy_standard") or "SKDI 2012"),
        legacy_level=comp.get("legacy_level") or None,
        legacy_mapping_confirmed=bool(comp.get("legacy_mapping_confirmed", False)),
        legacy_note=str(comp.get("legacy_note") or ""),
    )
    ident = raw.get("identity") or {}
    v.identity = IdentityConstraints(
        age_years=ident.get("age_years"), age_range=ident.get("age_range"),
        biological_sex=ident.get("biological_sex"), pregnancy_status=ident.get("pregnancy_status"),
        informant_type=ident.get("informant_type"), setting=ident.get("setting"),
        population_tags=list(ident.get("population_tags") or []),
    )
    v.chief_complaint = str(raw.get("chief_complaint") or "")
    v.opening_context = str(raw.get("opening_context") or "")
    v.duration = str(raw.get("duration") or "")
    v.severity = str(raw.get("severity") or "")
    v.key_chronology = str(raw.get("key_chronology") or "")
    for gh in raw.get("history") or []:
        facts = []
        for fr in gh.get("facts") or []:
            facts.append(HistoryFact(
                key=str(fr.get("key", "")), value=fr.get("value"),
                disclosure=_enum(DisclosureMode, fr.get("disclosure"), DisclosureMode.DIRECT_QUESTION),
                acceptable_intents=list(fr.get("acceptable_intents") or []),
                note=str(fr.get("note") or ""),
            ))
        v.history.append(HistoryGroup(name=str(gh.get("name", "")), facts=facts))
    for rr in raw.get("red_flags") or []:
        v.red_flags.append(RedFlag(
            fact=str(rr.get("fact", "")),
            status=_enum(FactStatus, rr.get("status"), FactStatus.PRESENT),
            criticality=_enum(RedFlagCriticality, rr.get("criticality"), RedFlagCriticality.CRITICAL),
            why_matters=str(rr.get("why_matters") or ""),
            disclosure=_enum(DisclosureMode, rr.get("disclosure"), DisclosureMode.DIRECT_QUESTION),
            acceptable_intents=list(rr.get("acceptable_intents") or []),
        ))
    # management_expectations (rule: per-disease, not inferred from category)
    me = raw.get("management_expectations") or {}
    v.management_expectations = ManagementExpectations(
        recognize_diagnose=str(me.get("recognize_diagnose") or ""),
        initial_management=str(me.get("initial_management") or ""),
        emergency_stabilization_required=me.get("emergency_stabilization_required"),
        referral_urgency=str(me.get("referral_urgency") or ""),
        referral_indication=str(me.get("referral_indication") or ""),
        do_not_miss_actions=list(me.get("do_not_miss_actions") or []),
        source_refs=list(me.get("source_refs") or []),
    )
    # epidemiology 3-layer (evidence / variant constraints / persona vars)
    epi = raw.get("epidemiology") or {}
    ev = epi.get("evidence") or {}
    v.epidemiology.evidence.facts = dict(ev.get("facts") or {})
    for sr in ev.get("sources") or []:
        v.epidemiology.evidence.sources.append(Source(
            title=str(sr.get("title") or ""), authority=str(sr.get("authority") or ""),
            version=str(sr.get("version") or ""), year=str(sr.get("year") or ""),
            url=str(sr.get("url") or ""), kind=str(sr.get("kind") or "")))
    vc = epi.get("variant_constraints") or {}
    from pipeline.case_v3.models import VariantDemographicConstraints
    v.epidemiology.variant_constraints = VariantDemographicConstraints(
        age_range=vc.get("age_range"), biological_sex=vc.get("biological_sex"),
        pregnancy_status=vc.get("pregnancy_status"),
        geographic_endemicity=vc.get("geographic_endemicity"),
        occupation_risk=vc.get("occupation_risk"))
    pv = epi.get("persona_variables") or {}
    from pipeline.case_v3.models import RuntimePersonaVariables
    v.epidemiology.persona_variables = RuntimePersonaVariables(
        name=bool(pv.get("name", True)),
        occupation_set=list(pv.get("occupation_set") or []),
        harmless_hobbies=list(pv.get("harmless_hobbies") or []),
        verbosity=str(pv.get("verbosity") or "range"),
        emotional_tone=str(pv.get("emotional_tone") or "range"),
        cultural_context=str(pv.get("cultural_context") or "range"))
    v.canonical_entity_id = str(raw.get("canonical_entity_id") or "")
    v.blind_candidate_brief = str(raw.get("blind_candidate_brief") or "")
    v.targeted_title = str(raw.get("targeted_title") or "")
    pe = raw.get("physical_exam") or {}
    v.physical_exam = PhysicalExam(
        general_appearance=str(pe.get("general_appearance") or ""),
        consciousness=pe.get("consciousness"),
        vitals=[VitalSign(name=str(x.get("name", "")), value=x.get("value"),
                          unit=ClinicalVitalUnits(x.get("unit") or "") if (x.get("unit") or "") in {u.value for u in ClinicalVitalUnits} else ClinicalVitalUnits.NONE,
                          normal_range=str(x.get("normal_range") or ""),
                          note=str(x.get("note") or ""))
                for x in (pe.get("vitals") or [])],
        system_findings={str(k): str(vv) for k, vv in (pe.get("system_findings") or {}).items()},
    )
    for ir in raw.get("investigations") or []:
        v.investigations.append(Investigation(
            name=str(ir.get("name", "")), expected_result=str(ir.get("expected_result") or ""),
            appropriateness=_enum(Appropriateness, ir.get("appropriateness"), Appropriateness.APPROPRIATE),
            rationale=str(ir.get("rationale") or ""), source=str(ir.get("source") or ""),
        ))
    dg = raw.get("diagnostic") or {}
    v.diagnostic = DiagnosticTruth(
        working_diagnosis=str(dg.get("working_diagnosis") or ""),
        synonyms=list(dg.get("synonyms") or []),
        differentials=[Differential(name=str(d.get("name", "")),
                                    discriminating_features=str(d.get("discriminating_features") or ""),
                                    reverting=bool(d.get("reverting", False)))
                       for d in (dg.get("differentials") or [])],
        reasoning_anchors=list(dg.get("reasoning_anchors") or []),
        icd10=str(dg.get("icd10") or ""),
    )
    mg = raw.get("management") or {}
    v.management = Management(
        stabilization=list(mg.get("stabilization") or []),
        pharmacologic=list(mg.get("pharmacologic") or []),
        non_pharmacologic=list(mg.get("non_pharmacologic") or []),
        referral=list(mg.get("referral") or []),
        follow_up=list(mg.get("follow_up") or []),
        education_safety_netting=list(mg.get("education_safety_netting") or []),
    )
    v.assessment_items = [AssessmentItem(text=str(a.get("text", "")),
                                         importance=_enum(ItemImportance, a.get("importance"), ItemImportance.HELPFUL),
                                         group=str(a.get("group") or ""),
                                         learner_stage=_stage(a.get("learner_stage")))
                          for a in (raw.get("assessment_items") or [])]
    v.safety_critical_errors = list(raw.get("safety_critical_errors") or [])
    v.sources = [Source(title=str(s.get("title", "")), authority=str(s.get("authority") or ""),
                        version=str(s.get("version") or ""), year=str(s.get("year") or ""),
                        url=str(s.get("url") or ""), kind=str(s.get("kind") or ""),
                        tier=str(s.get("tier") or ""),
                        publication_date=str(s.get("publication_date") or ""),
                        effective_date=str(s.get("effective_date") or ""),
                        superseded_by=str(s.get("superseded_by") or ""),
                        review_status=str(s.get("review_status") or ""),
                        locator=str(s.get("locator") or ""))
                 for s in (raw.get("sources") or [])]
    from pipeline.case_v3.models import MedicationConcept
    v.medications = [MedicationConcept(
                        generic_name=str(m.get("generic_name", "")),
                        drug_class=str(m.get("drug_class") or ""),
                        preferred_local_agent=str(m.get("preferred_local_agent") or ""),
                        acceptable_alternatives=list(m.get("acceptable_alternatives") or []),
                        dose_range=str(m.get("dose_range") or ""),
                        route=str(m.get("route") or ""),
                        frequency=str(m.get("frequency") or ""),
                        duration=str(m.get("duration") or ""),
                        contraindications=list(m.get("contraindications") or []),
                        monitoring=list(m.get("monitoring") or []),
                        referral_restriction=str(m.get("referral_restriction") or ""),
                        source_refs=list(m.get("source_refs") or []),
                        formulary_status=str(m.get("formulary_status") or "unknown"))
                     for m in (raw.get("medications") or [])]
    v.source_governance = raw.get("source_governance") or {}
    v.status = str(raw.get("status") or "draft")
    v.clinical_content_version = str(raw.get("clinical_content_version") or "")
    v.source_review_date = str(raw.get("source_review_date") or "")
    v.variant_previous_version = raw.get("variant_previous_version")
    return v


def load_family(raw: dict) -> CaseFamily:
    return CaseFamily(
        id=str(raw.get("id", "")),
        family_type=_enum(FamilyType, raw.get("family_type"), FamilyType.DISEASE),
        title_id=str(raw.get("title_id") or ""), title_en=str(raw.get("title_en") or ""),
        primary_specialty=str(raw.get("primary_specialty") or ""),
        cross_specialty_tags=list(raw.get("cross_specialty_tags") or []),
        presenting_complaints=list(raw.get("presenting_complaints") or []),
        population_tags=list(raw.get("population_tags") or []),
        target_stages=_stages(raw.get("target_stages")),
        skdi_mappings=raw.get("skdi_mappings") or {},
        learning_objectives=list(raw.get("learning_objectives") or []),
        common_differentials=list(raw.get("common_differentials") or []),
        active_variant_ids=list(raw.get("active_variant_ids") or []),
        source_governance=raw.get("source_governance") or {},
        status=str(raw.get("status") or "draft"),
    )


class CaseRegistry:
    """In-memory registry of families + variants, with ID-uniqueness + ref checks."""

    def __init__(self, families: list[CaseFamily] = None, variants: list[ClinicalVariant] = None):
        self.families: dict[str, CaseFamily] = {}
        self.variants: dict[str, ClinicalVariant] = {}
        self._variant_by_entry: dict[str, list[ClinicalVariant]] = {}
        for f in (families or []):
            self._add_family(f)
        for v in (variants or []):
            self._add_variant(v)

    def _add_family(self, f: CaseFamily) -> None:
        if f.id in self.families:
            raise ValueError(f"Duplicate family id: {f.id}")
        self.families[f.id] = f

    def _index_entry(self, key: str, v: ClinicalVariant) -> None:
        bucket = self._variant_by_entry.setdefault(key, [])
        if not any(x.id == v.id for x in bucket):
            bucket.append(v)

    def _add_variant(self, v: ClinicalVariant) -> None:
        if v.id in self.variants:
            raise ValueError(f"Duplicate variant id: {v.id}")
        if v.family_id not in self.families:
            raise ValueError(f"Variant {v.id} references missing family {v.family_id}")
        self.variants[v.id] = v
        # index by disease entry + presentation entry (cross-entry-point linking)
        fam = self.families[v.family_id]
        self._index_entry(f"disease:{fam.id}", v)
        self._index_entry(f"disease:{v.diagnostic.working_diagnosis.lower()}", v)
        if fam.title_id:
            self._index_entry(f"disease:{fam.title_id.strip().lower()}", v)
        if fam.title_en:
            self._index_entry(f"disease:{fam.title_en.strip().lower()}", v)
        for comp in fam.presenting_complaints:
            self._index_entry(f"presentation:{comp.strip().lower()}", v)

    def family(self, fid: str) -> Optional[CaseFamily]:
        return self.families.get(fid)

    def variant(self, vid: str) -> Optional[ClinicalVariant]:
        return self.variants.get(vid)

    def variants_for_family(self, fid: str) -> list[ClinicalVariant]:
        return [v for v in self.variants.values() if v.family_id == fid]

    def by_entry_point(self, entry: str) -> list[ClinicalVariant]:
        return list(self._variant_by_entry.get(entry, []))

    @classmethod
    def from_dir(cls, root: Path | str = None) -> "CaseRegistry":
        root = Path(root) if root else _DEFAULT_ROOT
        families = [load_family(yaml.safe_load(f.read_text())) for f in sorted((root / "families").glob("*.yaml"))]
        variants = [load_variant(yaml.safe_load(f.read_text())) for f in sorted((root / "variants").glob("*.yaml"))]
        return cls(families, variants)


def default_registry() -> CaseRegistry:
    return CaseRegistry.from_dir()


# persona constraints loader lives with persona generator (persona.py).