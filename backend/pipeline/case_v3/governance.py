"""STEP 3 — SKDI, clinical source, epidemiology & formulary governance.

Core principle (STEP 3 §1):
  SKDI → what competency is expected.
  Current clinical guidance → what is clinically correct.
  Epidemiology → plausible patients.
  Fornas → JKN formulary context.
  OSCE design → how to test.

These are SEPARATE sources and must never be collapsed into one truth.
This module provides the source-record model, the SKDI registry, Tier
hierarchy, conflict policy, expiry/re-review detection, Fornas isolation,
and human-review enforcement that keeps AI from self-attesting.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional

from pipeline.case_v3.models import ClinicalVariant
from pipeline.case_v3.vocab import (
    HUMAN_REVIEWED_STATES,
    SKDI_LEVELS_ALLOWED_PRIMARY,
    SKDI_LEVELS_KNOWN,
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL,
    SKD2026_CATEGORY_TUNTAS,
    ReviewState,
    SourceKind,
    SourceStatusKind,
    SourceTier,
)


# ── Baseline URLs / identifiers (STEP 3 §2 / §4 / §5 / §6) ─────────────────
# These are the official baseline references; always re-verify live during
# research (STEP 4). Treat as starting points, not frozen truth.
SKDI_OFFICIAL_URL = "https://kki.go.id/uploads/media/1683689635_fa3dea59333025ae148a.pdf"
KONSI_REG_2012_URL = "https://peraturan.go.id/id/peraturan-kki-no-11-tahun-2012"
PNPK_REPO_URL = (
    "https://www.kemkes.go.id/id/media/subfolder/pedoman/pedoman-nasional-" 
    "pelayanan-kedokteran-pnpk"
)
FORNAS_URL = "https://e-fornas.farmalkes.kemkes.go.id/guest/landing"
FORNAS_KMK_2025_URL = (
    "https://farmalkes.kemkes.go.id/en/unduh/keputusan-menteri-kesehatan-republik-"
    "indonesia-nomor-hk-01-07-menkes-1199-2025-tentang-formularium-nasional/"
)
PERMENKES_2026_CAUTION_URL = "https://jdih.kemkes.go.id/documents/peraturan-menteri-kesehatan-nomor-4-tahun-2026"


# ── Source record (STEP 3 §8) ──────────────────────────────────────────────
@dataclass
class SourceRecord:
    source_id: str
    title: str
    organization: str = ""
    document_type: str = ""            # e.g. "guideline", "regulation", "PNPK", "competency"
    year: str = ""
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    url: str = ""
    accessed_reviewed_date: Optional[str] = None
    version: str = ""
    status: SourceStatusKind = SourceStatusKind.CURRENT
    tier: SourceTier = SourceTier.TIER1
    relevance: list[SourceKind] = field(default_factory=list)
    locator: str = ""                  # page/section/table
    reviewer_notes: str = ""
    supersedes_source_ids: list[str] = field(default_factory=list)
    reviewed_by_human: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_formulary(self) -> bool:
        title = (self.title or "").lower()
        return (SourceKind.FORMULARY in self.relevance
                or "formulary" in (self.document_type or "").lower()
                or "fornas" in title or "formularium" in title)


# ── SKD 2026 registry (PRIMARY competency authority, STEP 4) ───────────────
# SKD 2026 (HK.01.02/KKI/2183/2026) — Tab. 4 Spektrum Penyakit, 16 systems.
# IMPORTANT (rule STEP-4): the two official classifications are nominal SKD 2026
# labels — 'Tuntas' vs 'Tatalaksana awal dan rujuk'. They are NOT a universal
# clinical protocol. For non-emergency conditions, "tatalaksana awal" is not
# necessarily stabilisation/resuscitation. Exact expected actions, urgency,
# stabilisation need, and referral behaviour are defined PER DISEASE from the
# current clinical guideline (PNPK etc.) at authoring time — never inferred
# purely from the category. These definitions only record what the 2026 labels
# mean at authority level; they are not an executable treatment pathway.
SKD2026_CATEGORY_DEFINITIONS = {
    SKD2026_CATEGORY_TUNTAS: (
        "SKD 2026 'Tuntas' — the physician may manage the condition to "
        "resolution at primary level, per the current clinical guideline."
    ),
    SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL: (
        "SKD 2026 'Tatalaksana awal dan rujuk' — the physician provides "
        "initial management and refers onward as appropriate. The exact "
        "initial actions, urgency, stabilisation need and referral behaviour "
        "are PER-DISEASE, defined from the current clinical guideline at "
        "authoring time — not universally 'stabilise + refer'."
    ),
}
_VERIFICATION_DATE = "2026-09-01"  # date the baseline was recorded / re-checked


def skd2026_category_registry() -> dict[str, str]:
    """Official SKD 2026 classifications (primary authority for the new bank)."""
    return dict(SKD2026_CATEGORY_DEFINITIONS)


def skd2026_categories() -> frozenset[str]:
    from pipeline.case_v3.vocab import SKD2026_CATEGORIES
    return SKD2026_CATEGORIES


# ── SKDI 2012 registry — LEGACY crosswalk ONLY (not primary authority) ────
@dataclass(frozen=True)
class SKDILegacyEntry:
    level: str
    standard: str = "SKDI 2012"
    authority: str = "Konsil Kedokteran Indonesia (KKI)"
    version: str = "2012"
    definition: str = ""
    verification_date: str = ""


_SKDI_2012_DEFINITIONS = {
    "3A": ("Diagnosis + initial management in non-emergency context + referral as appropriate."),
    "3B": ("Diagnosis + emergency initial management / stabilization + referral."),
    "4A": ("Diagnosis + independent management at graduation level."),
}


def skdi_legacy_registry() -> dict[str, SKDILegacyEntry]:
    """Legacy SKDI 2012 levels for crosswalk/metadata only (never primary)."""
    return {
        lvl: SKDILegacyEntry(level=lvl, definition=_SKDI_2012_DEFINITIONS.get(lvl, ""),
                             verification_date=_VERIFICATION_DATE)
        for lvl in sorted(SKDI_LEVELS_KNOWN)
    }


def skdi_legacy_allowed_levels() -> frozenset[str]:
    return SKDI_LEVELS_ALLOWED_PRIMARY


# Backward-compat aliases (old STEP-3 names → legacy crosswalk roles).
skdi_registry = skdi_legacy_registry
skdi_allowed_levels = skdi_legacy_allowed_levels


# ── Source hierarchy (STEP 3 §4) ───────────────────────────────────────────
HIERARCHY_DOC = [
    ("Tier 0", "Regulatory / competency — KKI / current Konsil standards, Kemenkes regulations", SourceTier.TIER0),
    ("Tier 1", "Current Indonesian national clinical guidance — PNPK, national program guidelines", SourceTier.TIER1),
    ("Tier 2", "Indonesian specialty/professional organizations — PAPDI, PERKI, IDAI, POGI, PERDOSNI ...", SourceTier.TIER2),
    ("Tier 3", "High-authority international guideline when Indonesian source absent/outdated — WHO, NICE, ESC, ACC/AHA, GINA, KDIGO ...", SourceTier.TIER3),
    ("Tier 4", "Standard educational references for stable background concepts only", SourceTier.TIER4),
]


def is_valid_tier(tier) -> bool:
    try:
        SourceTier(tier) if isinstance(tier, str) else tier
        return True
    except ValueError:
        return False


def has_clinical_guidance_source(sources: list[SourceRecord]) -> bool:
    """At least one Tier 0-3 source relevant to management/diagnosis of CURRENT status."""
    for s in sources:
        if s.status != SourceStatusKind.SUPERSEDED:
            if any(k in (SourceKind.MANAGEMENT, SourceKind.DIAGNOSIS) for k in s.relevance) \
                    and s.tier in (SourceTier.TIER0, SourceTier.TIER1, SourceTier.TIER2, SourceTier.TIER3):
                return True
    return False


# ── Conflict policy (STEP 3 §9) ────────────────────────────────────────────
@dataclass
class SourceConflict:
    topic: str
    sources: list[str]          # source_ids in disagreement
    baseline_source_id: str = ""     # pilot baseline chosen with rationale
    baseline_rationale: str = ""
    alternatives: list[str] = field(default_factory=list)  # credible alternatives
    requires_human_review: bool = True


def detect_conflicts(sources: list[SourceRecord]) -> list[SourceConflict]:
    """Represent source conflicts that already exist in a record set.
    (Full discovery of cross-source disagreement is research/LLM work; this
    makes conflicts structurally representable in the schema.)"""
    conflicts: list[SourceConflict] = []
    sup = [s for s in sources if s.status == SourceStatusKind.SUPERSEDED]
    for s in sup:
        for prev in s.supersedes_source_ids:
            if any(x.source_id == prev for x in sources):
                conflicts.append(SourceConflict(
                    topic=f"{s.title} supersedes {prev}",
                    sources=[s.source_id, prev], baseline_source_id=s.source_id,
                    baseline_rationale="Newer current source supersedes prior version",
                    alternatives=[prev], requires_human_review=False,
                ))
    return conflicts


# ── Expiry / re-review (STEP 3 §11) ────────────────────────────────────────
@dataclass
class ReReviewSignals:
    source_id: str
    signals: list[str] = field(default_factory=list)


def re_review_needed(sources: list[SourceRecord], *, preferred_interval_years: int = 3,
                     today: date | None = None) -> list[ReReviewSignals]:
    today = today or date.today()
    out: list[ReReviewSignals] = []
    for s in sources:
        sig = []
        if s.status == SourceStatusKind.SUPERSEDED:
            sig.append("superseded")
        if s.publication_date:
            try:
                pub = date.fromisoformat(s.publication_date)
                age = (today - pub).days / 365.25
                if age > preferred_interval_years:
                    sig.append(f"older than {preferred_interval_years}y preferred interval ({age:.1f}y)")
            except ValueError:
                sig.append("unparseable publication_date")
        if not s.url:
            sig.append("no URL (cannot verify availability)")
        if sig:
            out.append(ReReviewSignals(s.source_id, sig))
    return out


# ── Human review enforcement (STEP 3 §10) ──────────────────────────────────
class HumanReviewError(ValueError):
    pass


def assert_ai_can_promote(state, *, proposed_reviewed_by: str = "") -> None:
    """An AI agent must NEVER mark its own case pilot_verified/clinical/published
    merely because tests pass — a named human clinical reviewer is required."""
    s = state if isinstance(state, ReviewState) else ReviewState(state)
    if s in HUMAN_REVIEWED_STATES and not (proposed_reviewed_by or "").strip():
        raise HumanReviewError(
            f"Cannot reach {s.value} without a named human clinical reviewer "
            "(AI self-attestation is forbidden)."
        )


def human_review_required_for(state) -> bool:
    return state in HUMAN_REVIEWED_STATES


def validate_governance(v: ClinicalVariant, *, require_skd2026_category: bool = True,
                        require_clinical_source_for_publishable: bool = True) -> "ValidationResult":
    """STEP 3/4 governance validation: SKD 2026 competency scope (PRIMARY),
    clinical-source presence, Fornas isolation, AI self-promote guard, and the
    SKDI 2012 legacy crosswalk rule (level only from verified values, never
    inferred from the 2026 category)."""
    from pipeline.case_v3.validate import ValidationResult, ValidationIssue
    from pipeline.case_v3.vocab import SKD2026_CATEGORIES
    res = ValidationResult()

    comp = v.competency
    # 1) PRIMARY: SKD 2026 category is the single authority for the new bank.
    if require_skd2026_category:
        if comp is None or not comp.category:
            res.issues.append(ValidationIssue(
                v.id, "variant requires `competency.category` from SKD 2026 (tuntas | initial_management_and_referral)"))
        elif comp.category not in SKD2026_CATEGORIES:
            res.issues.append(ValidationIssue(
                v.id + ".competency.category",
                f"SKD 2026 category '{comp.category}' not in verified values {sorted(SKD2026_CATEGORIES)}"))
        elif comp.standard != "SKD 2026":
            res.issues.append(ValidationIssue(v.id + ".competency.standard",
                                              "primary competency standard must be 'SKD 2026'"))

    # 1b) LEGACY SKDI 2012 crosswalk — level may ONLY come from verified values;
    #     never inferred from the 2026 category (kept optional for metadata).
    if comp and comp.legacy_level:
        if comp.legacy_level not in SKDI_LEVELS_KNOWN:
            res.issues.append(ValidationIssue(v.id + ".competency.legacy_level",
                                              f"SKDI legacy level {comp.legacy_level} not in verified values"))
        if comp.legacy_level not in SKDI_LEVELS_ALLOWED_PRIMARY:
            res.issues.append(ValidationIssue(
                v.id + ".competency.legacy_level",
                f"SKDI legacy level {comp.legacy_level} outside crosswalk scope (3A/3B/4A)"))
        # a legacy level must be explicitly confirmed by a human reviewer
        if not comp.legacy_mapping_confirmed:
            res.issues.append(ValidationIssue(
                v.id + ".competency.legacy_level",
                "legacy SKDI 2012 level present but `legacy_mapping_confirmed` is False (human review required)"))

    # 2) publishable requires at least one clinical source.
    if v.publishable and require_clinical_source_for_publishable:
        recs = source_records_from_variant(v)
        if not has_clinical_guidance_source(recs):
            res.issues.append(ValidationIssue(
                v.id, "publishable variant requires >=1 current clinical guidance source (Tier0-3, diagnosis/management)"))

    # 3) AI cannot self-promote to a human-reviewed state.
    if v.status in HUMAN_REVIEWED_STATES and not _has_named_human_review(v):
        res.issues.append(ValidationIssue(
            v.id, f"AI self-attestation forbidden: {v.status} requires a named human clinical reviewer"))

    # 4) Fornas is NOT a treatment-guideline source.
    for r in source_records_from_variant(v):
        if r.is_formulary and SourceKind.MANAGEMENT in r.relevance:
            res.issues.append(ValidationIssue(
                v.id, "formulary (Fornas) source must not be typed as a management guideline"))

    # 5) Management expectations for 'initial_management_and_referral' families
    #    must be EXPLICIT and source-backed (rule: never inferred from category).
    #    A publishable variant with that category must spell out recognize/
    #    diagnose, initial management, stabilisation need, referral urgency/
    #    indication and do-not-miss — determined from the current guideline.
    from pipeline.case_v3.vocab import SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL
    if (v.publishable and comp and comp.category == SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL):
        me = v.management_expectations
        missing = []
        if not (me.recognize_diagnose or "").strip():
            missing.append("recognize_diagnose")
        if not (me.initial_management or "").strip():
            missing.append("initial_management")
        if me.emergency_stabilization_required is None:
            missing.append("emergency_stabilization_required")
        if not (me.referral_urgency or "").strip():
            missing.append("referral_urgency")
        if not (me.referral_indication or "").strip():
            missing.append("referral_indication")
        if not me.do_not_miss_actions:
            missing.append("do_not_miss_actions")
        if missing:
            res.issues.append(ValidationIssue(
                v.id,
                "management_expectations must be explicitly sourced for a publishable "
                f"'initial_management_and_referral' variant; missing: {', '.join(missing)}"))

    return res


def _has_named_human_review(v: ClinicalVariant) -> bool:
    au = v.source_governance or {}
    reviewer = (au.get("clinical_reviewer") or au.get("reviewed_by") or "").strip()
    return bool(reviewer)


def source_records_from_variant(v: ClinicalVariant) -> list[SourceRecord]:
    """Map a variant's Source structures into governed SourceRecords."""
    out: list[SourceRecord] = []
    for i, s in enumerate(v.sources):
        relevance = []
        if s.kind == "competency":
            relevance.append(SourceKind.COMPETENCY)
        elif s.kind == "formulary":
            relevance.append(SourceKind.FORMULARY)
        elif s.kind == "epidemiology":
            relevance.append(SourceKind.EPIDEMIOLOGY)
        elif s.kind == "osce_rubric":
            relevance.append(SourceKind.OSCE_RUBRIC)
        elif s.kind == "guideline":
            relevance.append(SourceKind.MANAGEMENT)
        out.append(SourceRecord(
            source_id=f"{v.id}:src{i+1}", title=s.title, organization=s.authority,
            document_type=s.kind or "guideline", year=s.year, url=s.url,
            version=s.version, tier=SourceTier.TIER1, relevance=relevance,
            status=SourceStatusKind.CURRENT,
        ))
    return out