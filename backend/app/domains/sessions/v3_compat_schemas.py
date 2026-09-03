"""V3-compat shims for the V2 external contract (Phase B).

Frontend V2 is frozen and keeps calling `/api/v2/*`. This module maps V3
internal objects (families, variants, scoring) onto the EXACT shapes the V2
frontend already consumes (CaseCard, session DTO, turns/reply, PF, report).

No frontend change is required: dispatch happens server-side based on whether
the requested `case_id` resolves to a V3 family public ref, and on the
session's persisted `content_schema`.
"""
from __future__ import annotations

from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.models import CaseFamily, ClinicalVariant
from pipeline.case_v3.vocab import FamilyType


def default_registry() -> CaseRegistry:
    return CaseRegistry.from_dir()


def is_v3_family_ref(ref: str) -> bool:
    """True if `ref` is a V3 family public id (e.g. 'fam_dengue')."""
    if not ref or not ref.startswith("fam_"):
        return False
    reg = default_registry()
    return ref in reg.families


def resolve_ref(ref: str) -> str:
    """Return 'v3' when `ref` is a V3 family public ref, else 'v2'."""
    return "v3" if is_v3_family_ref(ref) else "v2"


def family_type(family: CaseFamily) -> str:
    """targeted (disease, dx known) vs blind (presentation, dx hidden)."""
    return "blind" if family.family_type == FamilyType.PRESENTATION else "targeted"


# ── V2 CaseCard adapter ───────────────────────────────────────────────────
def family_to_card(reg: CaseRegistry, fam: CaseFamily, variant_count: int) -> dict:
    """Map a V3 family onto the exact V2 CaseCard shape consumed by QV2Catalogue
    + QV2SessionSetup. Acts as the source_type='v3_family' adapter item."""
    title = fam.title_en or fam.title_id or fam.id
    first_imp = (fam.presenting_complaints[0] if fam.presenting_complaints
                 else title)
    # mode_default mirrors the V2 card pill ("OSCE" vs "Anamnesis"). Disease
    # families default to the full OSCE arc; presentation families default to
    # practice history (blind). The V2 setup still lets the user pick either.
    mode_default = "osce_full" if fam.family_type == FamilyType.DISEASE else "anamnesis"
    difficulty = 2
    return {
        "id": fam.id,                      # == the family public ref (case_id on start)
        "source_type": "v3_family",
        "family_type": fam.family_type.value,          # disease | presentation
        "public_id": fam.id,
        "specialty": fam.primary_specialty or "medicine",
        "system": fam.skd2026_mapping.get("system"),
        "presentation_id": fam.presenting_complaints[0] if fam.presenting_complaints else "",
        "presentation": fam.title_id,
        "first_impression": first_imp,
        "first_impression_id": fam.title_id,
        "title": title,
        "difficulty": difficulty,
        "mode": mode_default,
        "estimated_minutes": 15,
        "status": fam.status,
        "eligible_variant_count": variant_count,
        # V3-internal metadata (V2 ignores it; compat dispatcher uses it)
        "_v3": {
            "family_id": fam.id,
            "family_type": fam.family_type.value,
            "targeted": family_type(fam) == "targeted",
            "variant_count": variant_count,
        },
    }


def resolve_start_variants(reg: CaseRegistry, fam: CaseFamily,
                             learner_stage: str = "koas") -> list[ClinicalVariant]:
    """Variants a `start` may instantiate for this family, in deterministic
    pick order. Disease families use the family-scoped policy (same rule as
    the card count). Presentation (blind) families curate CROSS-family
    variant refs in `active_variant_ids` (e.g. fever → dengue / UTI
    differentials) — those resolve by id and are stage-filtered here, so the
    card count and `start` can never disagree (FASE 3 canary fix: the blind
    card used to advertise while `start` 404'd). No silent fallback: empty
    stays empty and the caller returns a clear 404."""
    from pipeline.case_v3.runtime import _not_stage_compatible
    if fam.family_type != FamilyType.PRESENTATION:
        return []
    out = []
    for vid in (fam.active_variant_ids or []):
        v = reg.variants.get(vid)
        if v is None:
            continue
        if _not_stage_compatible(v, learner_stage):
            continue
        out.append(v)
    out.sort(key=lambda v: (v.variation_level.value, v.id))
    return out


def family_variant_count(reg: CaseRegistry, fam: CaseFamily,
                         learner_stage: str = "koas") -> int:
    from pipeline.case_v3.runtime import SelectionPolicy, SelectionRequest
    if fam.family_type == FamilyType.PRESENTATION:
        return len(resolve_start_variants(reg, fam, learner_stage))
    policy = SelectionPolicy(reg)
    return policy.eligible_count(
        SelectionRequest(mode="targeted", family_id=fam.id,
                         learner_stage=learner_stage))


def variant_opening_line(v: ClinicalVariant) -> str:
    """V2 uses `case.find_section('opening line')`. Mirror it from V3 truth
    without leaking the diagnosis."""
    return v.opening_context or v.chief_complaint or ""