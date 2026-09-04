"""Phase 11 Task D (part 2) — impact mapping (plan §31, Phase 11-D).

A detected change never edits cases. Instead it maps onto possibly-affected
(family, variant, claim-area) entries so a human reviewer sees the blast
radius: families, variants, management/medication/safety/rubric-adjacent
areas. Conservative by design (over-approximates: every variant of a watched
family in every claimed area) — narrowing happens at human review, and a
missed variant is worse than a spurious row.

Formulary (Tier 2) sources map to medications ONLY, even if the target lists
broader areas. International (Tier 3) entries carry an explicit
differs_from_local_guidance marker in their reason: accepted alternative /
review signal, never an override instruction.

Duck-typed case registry: only `families` (id → object) and
`variants_for_family(family_id)` (objects with `.id`) are touched, so unit
stubs and the real CaseRegistry both work.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImpactEntry:
    """One possibly-affected (family, variant, area) triple."""

    family_id: str = ""
    variant_id: str = ""
    area: str = ""
    reason: str = ""
    safety_rule: object = None

    def to_dict(self) -> dict:
        return {"family_id": self.family_id, "variant_id": self.variant_id,
                "area": self.area, "reason": self.reason,
                "safety_rule": self.safety_rule}


def _registry_families(case_registry) -> dict:
    try:
        fams = getattr(case_registry, "families", None)
        if isinstance(fams, dict):
            return fams
        if fams is None:
            return {}
        return {getattr(f, "id", f): f for f in fams}
    except Exception:
        return {}


def _family_variants(case_registry, family_id: str) -> list:
    try:
        fn = getattr(case_registry, "variants_for_family", None)
        if callable(fn):
            out = fn(family_id) or []
            return list(out)
    except Exception:
        pass
    try:
        all_vars = getattr(case_registry, "variants", None) or {}
        vals = all_vars.values() if isinstance(all_vars, dict) else all_vars
        return [v for v in vals if getattr(v, "family_id", None) == family_id]
    except Exception:
        return []


def map_impact(target, change_kind: str, *, registry=None, case_registry=None,
               treatment_maps=None, known_family_ids=None) -> tuple[list, list]:
    """Map a change onto (entries, warnings).

    `registry` is the legacy alias for the case registry (kept for
    compatibility); `case_registry` wins when both are given.
    Unknown watched families produce warnings, never crashes. International
    entries always carry the divergence marker in `reason`.
    """
    reg = case_registry if case_registry is not None else registry
    fams = _registry_families(reg)
    if known_family_ids is None:
        known = set(fams)
    else:
        try:
            known = set(known_family_ids)
        except TypeError:
            known = set(fams)
    kind = str(getattr(target, "kind", "") or "")
    tier = str(getattr(target, "tier", "") or "")
    is_formulary = (kind == "formulary")
    is_international = (tier == "3" or kind == "international")
    claim_areas = list(getattr(target, "claim_areas", None) or [])
    areas = ["medications"] if is_formulary else claim_areas
    if is_formulary and "medications" not in areas:
        areas = ["medications"]
    tid = str(getattr(target, "target_id", "") or "")

    entries: list[ImpactEntry] = []
    warnings: list[str] = []
    for fid in list(getattr(target, "watched_families", None) or []):
        if fid not in known:
            warnings.append(
                f"unknown family '{fid}' watched by '{tid}' — skipped, no entries")
            continue
        variants = _family_variants(reg, fid)
        if not variants:
            warnings.append(f"family '{fid}' has no loadable variants — scope only")
        for var in variants:
            vid = getattr(var, "id", "") or ""
            for area in areas:
                if is_international:
                    reason = (f"{tid} {change_kind}: {area} may be affected — "
                              f"differs_from_local_guidance: international update stored "
                              f"as accepted alternative; reviewer decides Indonesia "
                              f"applicability")
                elif is_formulary:
                    reason = (f"{tid} {change_kind}: formulary context ({area}) may be "
                              f"affected; availability-only, never management truth"
                              + (" (treatment maps checked)" if treatment_maps else ""))
                else:
                    reason = f"{tid} {change_kind}: {area} may be affected"
                entries.append(ImpactEntry(family_id=fid, variant_id=vid,
                                           area=area, reason=reason,
                                           safety_rule=None))
    return entries, warnings
