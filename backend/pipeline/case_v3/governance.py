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
    SKDI_LEVELS_KNOWN,
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


# ── SKDI registry (STEP 3 §2 / §3) ─────────────────────────────────────────
@dataclass(frozen=True)
class SKDIEntry:
    level: str
    standard: str = "SKDI"
    authority: str = "Konsil Kedokteran Indonesia (KKI)"
    version: str = "2012"
    definition: str = ""
    verification_date: str = ""


# Operational definitions per STEP 3 §3 (verify wording against official source).
_SKDI_DEFINITIONS = {
    "3A": ("Diagnosis + initial management in non-emergency context + referral as appropriate."),
    "3B": ("Diagnosis + emergency initial management / stabilization + referral."),
    "4A": ("Diagnosis + independent management at graduation level."),
}
_VERIFICATION_DATE = "2026-09-01"  # date the baseline was recorded / re-checked


def skdi_registry() -> dict[str, SKDIEntry]:
    """Curated SKDI level registry limited to the primary bank scope."""
    return {
        lvl: SKDIEntry(level=lvl, definition=_SKDI_DEFINITIONS.get(lvl, ""),
                       verification_date=_VERIFICATION_DATE)
        for lvl in sorted(SKDI_LEVELS_KNOWN)
    }


def skdi_allowed_levels() -> frozenset[str]:
    from pipeline.case_v3.vocab import SKDI_LEVELS_ALLOWED_PRIMARY
    return SKDI_LEVELS_ALLOWED_PRIMARY


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


def validate_governance(v: ClinicalVariant, *, primary_bank_skdi_only: bool = True,
                        require_clinical_source_for_publishable: bool = True) -> "ValidationResult":
    """STEP 3 governance validation: SKDI scope, clinical-source presence,
    Fornas isolation, AI self-promote guard, conflict representability.
    Implemented here + mirrored into case-v3 validate via a thin wrapper."""
    from pipeline.case_v3.validate import ValidationResult, ValidationIssue
    res = ValidationResult()
    # 1) SKDI level only allows verified values for the primary bank.
    if v.skdi_level:
        if v.skdi_level not in SKDI_LEVELS_KNOWN:
            res.issues.append(ValidationIssue(v.id + ".skdi_level",
                                              f"SKDI level {v.skdi_level} not in verified values"))
        if primary_bank_skdi_only and v.skdi_level not in skdi_allowed_levels():
            res.issues.append(ValidationIssue(v.id + ".skdi_level",
                                              f"SKDI {v.skdi_level} outside primary bank scope (3A/3B/4A)"))

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