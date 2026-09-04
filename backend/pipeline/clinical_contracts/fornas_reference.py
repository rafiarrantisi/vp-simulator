"""Phase 5 Task A — Fornas reference layer (plan §4 Tier 2, §9, Phase 5A).

Tracks the current national formulary context (KMK HK.01.07/MENKES/1199/2025,
established 31 Dec 2025, effective 1 Apr 2026) as FORMULARY CONTEXT ONLY.

Hard rule (mirrors governance + sourceqa + evidence_pack):

> Fornas is not a substitute for disease-management guidance.

A formulary entry may state availability/restriction level; it MUST NOT be
typed as a management guideline and MUST NOT decide clinical correctness.
Clinical correctness comes from the guideline-to-medication mapping
(`treatment_maps.py`); Fornas only annotates local preference/context.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

FORNAS_REFERENCE = 'KMK HK.01.07/MENKES/1199/2025'
FORNAS_ESTABLISHED_DATE = '2025-12-31'
FORNAS_EFFECTIVE_DATE = '2026-04-01'
FORNAS_PORTAL_URL = 'https://e-fornas.farmalkes.kemkes.go.id/guest/landing'
FORNAS_KMK_URL = 'https://farmalkes.kemkes.go.id/en/unduh/keputusan-menteri-kesehatan-republik-indonesia-nomor-hk-01-07-menkes-1199-2025-tentang-formularium-nasional/'

FORNAS_LEVELS = ('unrestricted', 'restricted', 'program_only', 'hospital_only', 'unknown')


@dataclass
class FornasEntry:
    """Formulary context for one generic agent (NOT a treatment recommendation)."""

    generic_name: str
    in_fornas: bool | None = None
    restriction: str = 'unknown'
    fornas_note: str = ''
    reference: str = FORNAS_REFERENCE
    last_checked: str = ''

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'FornasEntry':
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (d or {}).items() if k in known})

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not (self.generic_name or '').strip():
            errors.append('generic_name empty')
        if self.restriction not in FORNAS_LEVELS:
            errors.append(f"restriction '{self.restriction}' not in {list(FORNAS_LEVELS)}")
        if self.in_fornas is None and not self.fornas_note:
            errors.append(f"'{self.generic_name}': unverified formulary status needs a fornas_note explaining the uncertainty")
        return errors


@dataclass
class FornasReference:
    """Versioned pointer to the active national formulary edition."""

    reference: str = FORNAS_REFERENCE
    established_date: str = FORNAS_ESTABLISHED_DATE
    effective_date: str = FORNAS_EFFECTIVE_DATE
    portal_url: str = FORNAS_PORTAL_URL
    entries: list[FornasEntry] = field(default_factory=list)
    review_state: str = 'draft'
    reviewed_by: str = ''

    def to_dict(self) -> dict:
        return {
            'reference': self.reference,
            'established_date': self.established_date,
            'effective_date': self.effective_date,
            'portal_url': self.portal_url,
            'entries': [e.to_dict() for e in self.entries],
            'review_state': self.review_state,
            'reviewed_by': self.reviewed_by,
        }

    def lookup(self, generic_name: str) -> FornasEntry | None:
        from pipeline.clinical_contracts.medication import normalize_medication_text

        want = normalize_medication_text(generic_name)
        for e in self.entries:
            if normalize_medication_text(e.generic_name) == want:
                return e
        return None

    def validate(self) -> tuple[list[str], list[str]]:
        """Return (errors, warnings). Fornas-as-guideline misuse is an error."""
        errors: list[str] = []
        warnings: list[str] = []
        if self.reference != FORNAS_REFERENCE:
            warnings.append(f"reference '{self.reference}' differs from current {FORNAS_REFERENCE}")
        seen: set = set()
        for e in self.entries:
            errors.extend(f'fornas entry: {m}' for m in e.validate())
            key = (e.generic_name or '').strip().lower()
            if key in seen:
                errors.append(f"duplicate fornas entry for '{e.generic_name}'")
            seen.add(key)
        if self.review_state in ('clinically_reviewed', 'pilot_verified', 'published') and not (
            self.reviewed_by or ''
        ).strip():
            errors.append(
                f"review_state '{self.review_state}' requires a named human reviewer (AI self-attestation is forbidden)"
            )
        return errors, warnings


def fornas_claim_is_formulary_only(claim_area: str) -> bool:
    """Guard helper: only 'formulary' claims may cite Fornas.

    Anything claiming diagnosis/management/safety/referral from a Fornas
    source is misuse — mirror of evidence_pack.validate_source.
    """
    return (claim_area or '').strip().lower() == 'formulary'
