"""FASE 2 — Approved Clinical Evidence Pack (source-of-truth per family/variant).

A family/variant is only as trustworthy as the sources behind it. The
EvidencePack is the single structured answer to "what evidence backs this
clinical truth, under which authority, since when, reviewed by whom":

  competency authority  SKD 2026 (scope + category Tuntas / Tatalaksana awal
                        dan rujuk). SKDI 2012 3A/3B/4A is a legacy crosswalk
                        ONLY when verified — never auto-inferred.
  primary management    PNPK / national guideline / Indonesian society
                        (Tier 0-2). This is the management truth.
  formulary context     Fornas / JKN (formulary kind). Context only — never a
                        management guideline and never a disease truth.
  international         WHO / NICE / ESC / GINA / GOLD / KDIGO / ADA / IDSA /
                        ... accepted as ADDITIONAL source or update trigger.
                        Never auto-overrides Indonesian guidance; a Tier-3-only
                        management basis requires an explicit interim flag +
                        human rationale.
  dates                 publication / effective / superseded per source, plus
                        family source_review_date and clinical_content_version.
  review                review_status + named human reviewers (AI self-promote
                        stays forbidden — see governance.assert_ai_can_promote).

Everything here is report/validation logic over content files. It never
promotes, never rewrites clinical truth, and never touches the live
V2/V3 runtime paths.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from pipeline.case_v3.lint import LintIssue
from pipeline.case_v3.models import CaseFamily, ClinicalVariant, Source
from pipeline.case_v3.vocab import (
    HUMAN_REVIEWED_STATES,
    SKD2026_CATEGORIES,
    ReviewState,
)

EVIDENCE_PACK_VERSION = "1.0"

# ── Authority recognition (advisory inference; human review decides) ─────────
# Matched case-insensitively against `authority` + `title`.
NATIONAL_COMPETENCY_ORGS = ("kki", "konsil kedokteran", "kemenkes")
NATIONAL_GUIDELINE_MARKERS = ("kemenkes", "pnpk", "pedoman nasional", "program nasional")
SPECIALTY_ORGS = (
    "papdi", "perki", "idai", "pogi", "perdosni", "pdpi", "pds", "perhi",
    "pdgi", "persi", "pabdi", "pernefri", "inasn",
)
INTERNATIONAL_ORGS = (
    "who", "nice", "esc", "acc", "aha", "gina", "gold", "kdigo",
    "ada", "idsa", "aap", "eau", "ssc", "unesco", "unicef",
)
FORMULARY_MARKERS = ("fornas", "formularium", "jkn", "e-fornas")

# tier codes mirror vocab.SourceTier values ("0".."4")
TIER_COMPETENCY = "0"
TIER_NATIONAL = "1"
TIER_SOCIETY = "2"
TIER_INTERNATIONAL = "3"
TIER_EDUCATIONAL = "4"


def _hay(s: Source) -> str:
    return f"{s.authority or ''} {s.title or ''}".lower()


def infer_tier(s: Source) -> str:
    """Advisory tier inference. An explicit `Source.tier` always wins."""
    if (s.tier or "").strip():
        return s.tier.strip()
    hay = _hay(s)
    kind = (s.kind or "").lower()
    if kind == "competency":
        return TIER_COMPETENCY
    if kind == "formulary" or any(m in hay for m in FORMULARY_MARKERS):
        return "formulary"
    # A Kemenkes/PNPK *guideline* is national management truth (Tier 1),
    # not the competency authority — check guideline markers before orgs.
    if any(m in hay for m in NATIONAL_GUIDELINE_MARKERS):
        return TIER_NATIONAL
    if any(m in hay for m in NATIONAL_COMPETENCY_ORGS):
        return TIER_COMPETENCY
    if any(m in hay for m in SPECIALTY_ORGS):
        return TIER_SOCIETY
    if any(m in hay for m in INTERNATIONAL_ORGS):
        return TIER_INTERNATIONAL
    if kind in ("guideline", "epidemiology", "diagnosis", "management"):
        return TIER_EDUCATIONAL
    return ""


def _is_current(s: Source) -> bool:
    rs = (s.review_status or "").strip().lower()
    if rs:
        return rs == "current"
    return not (s.superseded_by or "").strip()


# ── Evidence pack ────────────────────────────────────────────────────────────
@dataclass
class EvidencePack:
    """Structured source-of-truth for one family (+ its variants)."""
    pack_version: str = EVIDENCE_PACK_VERSION
    family_id: str = ""
    variant_ids: list[str] = field(default_factory=list)
    # competency authority (SKD 2026 primary; SKDI legacy crosswalk only).
    # A family may legitimately span categories (e.g. mild=tuntas while
    # severe=initial_management_and_referral) — hence a LIST, never one value.
    competency_standard: str = "SKD 2026"
    competency_reference: str = ""
    competency_categories: list[str] = field(default_factory=list)
    competency_system: str = ""
    legacy_standard: str = "SKDI 2012"
    legacy_level: str = ""
    legacy_mapping_confirmed: bool = False
    # management truth layers
    primary_guideline: dict = field(default_factory=dict)   # Tier 0-2 source dict
    society_guidelines: list[dict] = field(default_factory=list)
    international_refs: list[dict] = field(default_factory=list)
    formulary_context: list[dict] = field(default_factory=list)
    epidemiology_sources: list[dict] = field(default_factory=list)
    # interim flag: Tier-3 is the ONLY management basis (needs human rationale)
    intl_primary_interim: bool = False
    intl_primary_rationale: str = ""
    # dates / review / version
    source_review_date: str = ""
    clinical_content_version: str = ""
    review_status: str = ""
    reviewers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _src_dict(s: Source, tier: str) -> dict:
    d = s.to_dict()
    d["inferred_tier"] = tier
    return d


def build_evidence_pack(family: CaseFamily, variants: list[ClinicalVariant],
                        *, reviewers: Optional[list[str]] = None) -> EvidencePack:
    """Assemble the pack from family governance + variant sources.

    Hierarchy enforced here is representational: national (Tier 0-2)
    management sources become `primary_guideline`/`society_guidelines`,
    international (Tier 3) become `international_refs`, formulary becomes
    `formulary_context`. Nothing is discarded — every source keeps its tier.
    """
    pack = EvidencePack(family_id=family.id)
    pack.variant_ids = [v.id for v in variants]
    pack.review_status = family.status or ""
    if reviewers:
        pack.reviewers = list(reviewers)

    cats = sorted({v.competency.category for v in variants
                   if v.competency and v.competency.category})
    pack.competency_categories = cats
    refs = {v.competency.reference for v in variants if v.competency and v.competency.reference}
    if refs:
        pack.competency_reference = sorted(refs)[0]
    systems = {v.competency.system for v in variants if v.competency and v.competency.system}
    fam_sys = (family.skd2026_mapping or {}).get("system", "")
    pack.competency_system = fam_sys or (sorted(systems)[0] if systems else "")
    legacy = [(v.competency.legacy_level, v.competency.legacy_mapping_confirmed)
              for v in variants if v.competency and v.competency.legacy_level]
    if legacy:
        pack.legacy_level = sorted({lv for lv, _ in legacy})[0]
        pack.legacy_mapping_confirmed = all(cf for _, cf in legacy)

    seen: set[str] = set()
    national_mgmt: list[dict] = []
    for v in variants:
        for s in (v.sources or []):
            key = (s.title or "", s.authority or "", s.year or "")
            if key in seen:
                continue
            seen.add(key)
            tier = infer_tier(s)
            kind = (s.kind or "").lower()
            d = _src_dict(s, tier)
            if tier == "formulary" or kind == "formulary":
                pack.formulary_context.append(d)
            elif kind == "epidemiology":
                pack.epidemiology_sources.append(d)
            elif kind == "competency":
                continue  # authority recorded above, not a management truth
            elif tier in (TIER_COMPETENCY, TIER_NATIONAL):
                national_mgmt.append(d)
            elif tier == TIER_SOCIETY:
                pack.society_guidelines.append(d)
            elif tier == TIER_INTERNATIONAL:
                pack.international_refs.append(d)
            else:
                national_mgmt.append(d)  # unknown tier: surface, don't hide
    if national_mgmt:
        # Prefer an explicitly-tiered or PNPK/Kemenkes source as primary.
        def _rank(d: dict) -> int:
            hay = f"{d.get('authority', '')} {d.get('title', '')}".lower()
            if "pnpk" in hay or "kemenkes" in hay:
                return 0
            if d.get("tier") in (TIER_COMPETENCY, TIER_NATIONAL):
                return 1
            return 2
        ordered = sorted(national_mgmt, key=_rank)
        pack.primary_guideline = ordered[0]
        pack.society_guidelines = ordered[1:] + pack.society_guidelines

    dates = {v.source_review_date for v in variants if v.source_review_date}
    if dates:
        pack.source_review_date = sorted(dates)[0]
    versions = {v.clinical_content_version for v in variants if v.clinical_content_version}
    if len(versions) == 1:
        pack.clinical_content_version = next(iter(versions))
    return pack


def validate_evidence_pack(pack: EvidencePack, *, for_publishable: bool = True) -> list[LintIssue]:
    """Hierarchy + completeness rules. Errors block publishability; warnings
    are gaps a human reviewer must close. Pure function — no I/O."""
    path = f"family:{pack.family_id or '?'}"
    issues: list[LintIssue] = []
    if not for_publishable:
        return issues

    # 1) SKD 2026 competency authority must be explicit.
    if not pack.competency_categories:
        issues.append(LintIssue(path, "evidence pack lacks SKD 2026 `competency_category`", "error"))
    else:
        for c in pack.competency_categories:
            if c not in SKD2026_CATEGORIES:
                issues.append(LintIssue(path, f"competency_category '{c}' "
                                              "is not an official SKD 2026 term", "error"))
    if pack.competency_standard != "SKD 2026":
        issues.append(LintIssue(path, "competency authority must be 'SKD 2026'", "error"))

    # 2) Legacy crosswalk: a level without human confirmation is not usable.
    if pack.legacy_level and not pack.legacy_mapping_confirmed:
        issues.append(LintIssue(path, f"legacy SKDI level {pack.legacy_level} present but "
                                      "not human-confirmed (never auto-infer)", "error"))

    # 3) Primary management truth must be national (Tier 0-2), current.
    prim = pack.primary_guideline or {}
    if not prim:
        if pack.international_refs and not pack.intl_primary_interim:
            issues.append(LintIssue(path, "management basis is international-only with no "
                                          "national guideline and no `intl_primary_interim` human rationale", "error"))
        else:
            issues.append(LintIssue(path, "evidence pack lacks a primary national (Tier 0-2) "
                                          "management source", "error"))
    else:
        if not _current_dict(prim):
            issues.append(LintIssue(path, f"primary guideline '{prim.get('title', '?')}' is "
                                          "superseded — management truth expired", "error"))
    if pack.intl_primary_interim and not (pack.intl_primary_rationale or "").strip():
        issues.append(LintIssue(path, "`intl_primary_interim` requires a human rationale", "error"))

    # 4) Formulary is context, never management truth (structural by construction,
    #    but re-assert in case a pack was hand-assembled).
    for f in pack.formulary_context:
        if (f.get("kind") or "").lower() == "management":
            issues.append(LintIssue(path, f"formulary source '{f.get('title', '?')}' must not be "
                                          "typed as a management guideline", "error"))

    # 5) Dates / review hygiene (warnings — reviewer closes them).
    if not pack.source_review_date:
        issues.append(LintIssue(path, "pack lacks `source_review_date`", "warning"))
    if not pack.clinical_content_version:
        issues.append(LintIssue(path, "pack lacks uniform `clinical_content_version`", "warning"))
    for layer in ("primary_guideline",):
        d = pack.primary_guideline or {}
        if d and not (d.get("publication_date") or d.get("year")):
            issues.append(LintIssue(path, f"primary guideline '{d.get('title', '?')}' has no "
                                          "publication date", "warning"))
        if d and not (d.get("url") or ""):
            issues.append(LintIssue(path, f"primary guideline '{d.get('title', '?')}' has no URL "
                                          "(cannot verify availability)", "warning"))
    return issues


def _current_dict(d: dict) -> bool:
    rs = (d.get("review_status") or "").strip().lower()
    if rs:
        return rs == "current"
    return not (d.get("superseded_by") or "").strip()


def lint_evidence_family(family: CaseFamily, variants: list[ClinicalVariant],
                         *, reviewers: Optional[list[str]] = None,
                         for_publishable: bool = True) -> list[LintIssue]:
    """Build + validate + medication-contract check for one family.

    Returns LintIssues (severity error|warning). Never raises on content.
    """
    pack = build_evidence_pack(family, variants, reviewers=reviewers)
    issues = validate_evidence_pack(pack, for_publishable=for_publishable)
    for v in variants:
        for m in (v.medications or []):
            for e in m.validate():
                issues.append(LintIssue(f"{v.id}.medications.{m.generic_name or '?'}", e, "error"))
    # Variant↔family consistency: family-declared active ids must resolve.
    active = set(family.active_variant_ids or [])
    have = {v.id for v in variants}
    for missing in sorted(active - have):
        issues.append(LintIssue(f"family:{family.id}", f"active_variant_id '{missing}' "
                                                       "has no loaded variant", "error"))
    return issues
