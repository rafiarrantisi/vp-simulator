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
        skdi_level=str(raw.get("skdi_level") or "") or None,
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
                        url=str(s.get("url") or ""), kind=str(s.get("kind") or ""))
                 for s in (raw.get("sources") or [])]
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