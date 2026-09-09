"""Phase PNPK-2 — clinical evidence contracts (brief §5).

Source/Claim/Pack/Mapping/Config/Citation models for PNPK-grounded judge
feedback. INTENTIONALLY distinct from `case_v3/evidence.py::EvidencePack`
(family authoring bundle) and from `versions.EVIDENCE_PACK_VERSION`
(scoring-output contract "1.0.0", never bumped per content here).

All models are plain dataclasses with explicit `validate()` returning error
strings (empty = valid). No I/O, no LLM, deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PACK_SCHEMA_VERSION = "1.0"
CLINICAL_EVIDENCE_KIND = "clinical_evidence"

# Closed vocabularies (brief §5).
CATEGORIES = (
    "history", "red_flag", "diagnosis", "examination", "investigation",
    "management",
)
SUPPORT_KINDS = ("direct_guideline", "educator_synthesis")
REVIEW_STATUSES = ("draft", "in_review", "approved")
SOURCE_STATUSES = ("active", "superseded", "archived")
SOURCE_REVIEW = ("unreviewed", "source_hold", "verified_final_copy")
TARGET_KINDS = ("per_item", "per_dimension", "debrief")
TRIGGER_STATUSES = ("hit", "partial", "miss")
RATIONALE_KINDS = ("direct_guideline", "educator_synthesis")


@dataclass
class EvidenceSpan:
    source_version_id: str = ""
    section_path: list[str] = field(default_factory=list)
    heading: str = ""
    pdf_page_start: int = 0
    pdf_page_end: int = 0
    printed_page_label: str | None = None
    locator: str = ""  # paragraph/table/figure locator
    excerpt_hash: str = ""

    def validate(self) -> list[str]:
        errs = []
        if not self.source_version_id:
            errs.append("span without source_version_id")
        if self.pdf_page_start < 1 or self.pdf_page_end < 1:
            errs.append("span needs 1-based pdf_page_start/end")
        if self.pdf_page_end < self.pdf_page_start:
            errs.append("span pdf_page_end before start")
        return errs


@dataclass
class ClinicalClaim:
    claim_id: str = ""
    claim_revision: int = 1
    statement: str = ""
    category: str = ""
    support_kind: str = ""
    applicability: dict = field(default_factory=dict)
    evidence_spans: list[EvidenceSpan] = field(default_factory=list)
    grade: str | None = None
    review_status: str = "draft"
    reviewer: str = ""
    reviewed_at: str = ""
    approval_record_id: str = ""

    def validate(self) -> list[str]:
        errs = []
        if not self.claim_id:
            errs.append("claim without claim_id")
        if not self.statement.strip():
            errs.append(f"claim {self.claim_id}: empty statement")
        if self.category not in CATEGORIES:
            errs.append(f"claim {self.claim_id}: bad category {self.category!r}")
        if self.support_kind not in SUPPORT_KINDS:
            errs.append(f"claim {self.claim_id}: bad support_kind")
        if not self.evidence_spans:
            errs.append(f"claim {self.claim_id}: no evidence_spans")
        for sp in self.evidence_spans:
            errs.extend(f"claim {self.claim_id}: {e}" for e in sp.validate())
        if self.review_status not in REVIEW_STATUSES:
            errs.append(f"claim {self.claim_id}: bad review_status")
        if self.review_status == "approved" and not self.approval_record_id:
            errs.append(f"claim {self.claim_id}: approved without approval_record_id")
        return errs


@dataclass
class EvidenceTemplate:
    template_id: str = ""
    template_revision: int = 1
    statuses: list[str] = field(default_factory=list)  # hit/partial/miss subset
    text: str = ""
    placeholders: list[str] = field(default_factory=list)
    review_status: str = "draft"
    approval_record_id: str = ""

    def validate(self) -> list[str]:
        errs = []
        if not self.template_id:
            errs.append("template without template_id")
        if not self.text.strip():
            errs.append(f"template {self.template_id}: empty text")
        for st in self.statuses:
            if st not in TRIGGER_STATUSES:
                errs.append(f"template {self.template_id}: bad status {st!r}")
        import re

        found = sorted(set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", self.text)))
        if found != sorted(self.placeholders):
            errs.append(
                f"template {self.template_id}: placeholders {self.placeholders} "
                f"!= used {found}")
        if self.review_status not in REVIEW_STATUSES:
            errs.append(f"template {self.template_id}: bad review_status")
        if self.review_status == "approved" and not self.approval_record_id:
            errs.append(f"template {self.template_id}: approved without approval_record_id")
        return errs


@dataclass
class RubricEvidenceMapping:
    mapping_id: str = ""
    canonical_target_id: str = ""
    target_kind: str = ""
    rubric_revision: str = ""
    rubric_hash: str = ""
    claim_ids: list[str] = field(default_factory=list)
    trigger_statuses: list[str] = field(default_factory=list)
    template_id: str = ""
    display_priority: int = 0
    applicable_variant_ids: list[str] = field(default_factory=list)
    review_status: str = "draft"
    approval_record_id: str = ""

    def validate(self) -> list[str]:
        errs = []
        if not self.mapping_id:
            errs.append("mapping without mapping_id")
        if not self.canonical_target_id:
            errs.append(f"mapping {self.mapping_id}: no canonical_target_id")
        if self.target_kind not in TARGET_KINDS:
            errs.append(f"mapping {self.mapping_id}: bad target_kind")
        if not self.claim_ids:
            errs.append(f"mapping {self.mapping_id}: no claim_ids")
        for st in self.trigger_statuses:
            if st not in TRIGGER_STATUSES:
                errs.append(f"mapping {self.mapping_id}: bad trigger {st!r}")
        if not self.applicable_variant_ids:
            errs.append(f"mapping {self.mapping_id}: no applicable_variant_ids "
                        "(family-wide auto-approve forbidden)")
        if self.review_status not in REVIEW_STATUSES:
            errs.append(f"mapping {self.mapping_id}: bad review_status")
        if self.review_status == "approved" and not self.approval_record_id:
            errs.append(f"mapping {self.mapping_id}: approved without approval_record_id")
        return errs


@dataclass
class CaseEvidenceConfig:
    """Explicit per-variant release binding (no latest-resolution at runtime)."""
    variant_id: str = ""
    canonical_hash: str = ""
    rubric_hash: str = ""
    content_release_id: str = ""
    allowed_source_version_ids: list[str] = field(default_factory=list)
    evidence_pack_id: str = ""
    evidence_pack_revision: int = 0
    evidence_pack_sha256: str = ""
    status: str = "draft"
    supported_modes: list[str] = field(default_factory=list)
    supported_stages: list[str] = field(default_factory=list)
    disabled_claims: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errs = []
        if not self.variant_id:
            errs.append("binding without variant_id")
        if not self.canonical_hash:
            errs.append(f"binding {self.variant_id}: no canonical_hash")
        if not self.evidence_pack_sha256:
            errs.append(f"binding {self.variant_id}: no pack sha256 (latest forbidden)")
        if self.status not in REVIEW_STATUSES:
            errs.append(f"binding {self.variant_id}: bad status")
        return errs


@dataclass
class ClinicalEvidencePack:
    """Immutable approved pack (content revision, not format version)."""
    pack_id: str = ""
    pack_schema_version: str = PACK_SCHEMA_VERSION
    pack_revision: int = 1
    pack_sha256: str = ""
    clinical_content_version: str = ""
    compatible_scoring_versions: list[str] = field(default_factory=list)
    scoring_rubric_digest: str = ""
    case_binding_digest: str = ""
    source_versions: list[dict] = field(default_factory=list)
    claims: list[ClinicalClaim] = field(default_factory=list)
    mappings: list[RubricEvidenceMapping] = field(default_factory=list)
    templates: list[EvidenceTemplate] = field(default_factory=list)
    review_record: dict = field(default_factory=dict)
    compiler_version: str = ""

    def payload_digest_fields(self) -> dict:
        """Exact fields covered by pack_sha256 (stable key order at build)."""
        from dataclasses import asdict

        return {
            "pack_id": self.pack_id,
            "pack_schema_version": self.pack_schema_version,
            "pack_revision": self.pack_revision,
            "clinical_content_version": self.clinical_content_version,
            "compatible_scoring_versions": list(self.compatible_scoring_versions),
            "scoring_rubric_digest": self.scoring_rubric_digest,
            "case_binding_digest": self.case_binding_digest,
            "source_versions": self.source_versions,
            "claims": [asdict(c) for c in self.claims],
            "mappings": [asdict(m) for m in self.mappings],
            "templates": [asdict(t) for t in self.templates],
        }
