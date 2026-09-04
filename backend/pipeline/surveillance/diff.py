"""Phase 11 Task D (part 1) — human-readable claim diffs + severity
(plan §31, Phase 11-D).

Severity ladder (low → high):
informational < minor < clinically_meaningful < safety_critical.

Rules (all deterministic, ID/EN, no LLM):
- Safety signals in the NEW claim (or warnings dropped from the old claim)
  force safety_critical — no semantic proposal, formulary cap, or wording
  similarity can clear them.
- Formulary (Tier 2) sources are availability-only: capped at minor, and can
  never establish disease-management truth.
- Wording-only edits (near-identical tokens) are informational.
- Anything else substantive defaults to clinically_meaningful.
- A superseded change_kind escalates one rung (floor: minor).
- International sources diverging from local guidance are flagged via
  differs_from_local_guidance + a Tier-1 reason (stored as review signal,
  never auto-applied).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

SEVERITIES = ("informational", "minor", "clinically_meaningful", "safety_critical")

_SEVERITY_RANK = {name: i for i, name in enumerate(SEVERITIES)}

# Substring signals (lowercased) that make a claim safety-relevant. Bare
# "bahaya" is deliberately ABSENT — routine "tanda bahaya" education must
# not trip the safety gate.
SAFETY_PATTERNS = (
    "kontraindikasi",
    "contraindicat",
    "jangan berikan",
    "jangan diberikan",
    "dilarang memberikan",
    "do not give",
    "do not administer",
    "syok",
    "shock",
    "gagal napas",
    "respiratory failure",
    "gagal jantung",
    "heart failure",
    "rujuk segera",
    "urgent referral",
    "segera ke icu",
    "kematian",
    "fatal",
    "overdosis",
    "overdose",
    "perdarahan berat",
    "severe bleeding",
    "henti napas",
    "henti jantung",
)

_WORDING_OVERLAP_CUT = 0.8


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> list[str]:
    return _norm(text).split()


def token_overlap(old: str, new: str) -> float:
    """Jaccard-style overlap of normalized tokens (new vs old)."""
    a, b = set(_tokens(old)), set(_tokens(new))
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(len(a), len(b))


def find_safety_signals(old_claim: str, new_claim: str) -> list[str]:
    """Safety patterns in the new claim, plus warnings dropped from old."""
    new_l = (new_claim or "").lower()
    old_l = (old_claim or "").lower()
    out: list[str] = []
    for pat in SAFETY_PATTERNS:
        if pat in new_l and pat not in out:
            out.append(pat)
        elif pat in old_l and pat not in new_l and pat not in out:
            out.append(pat + " (removed)")
    return out


@dataclass
class ClaimDiff:
    """Old vs new recommendation for one claim area (human-readable)."""

    old_claim: str = ""
    new_claim: str = ""
    claim_area: str = "management"
    severity: str = "informational"
    reasons: list = field(default_factory=list)
    safety_signals: list = field(default_factory=list)
    differs_from_local_guidance: bool = False

    def to_dict(self) -> dict:
        return {
            "old_claim": self.old_claim,
            "new_claim": self.new_claim,
            "claim_area": self.claim_area,
            "severity": self.severity,
            "reasons": list(self.reasons or []),
            "safety_signals": list(self.safety_signals or []),
            "differs_from_local_guidance": self.differs_from_local_guidance,
        }


def diff_claims(old_claim: str, new_claim: str, *, claim_area: str = "management",
                is_formulary_source: bool = False,
                is_international_source: bool = False,
                change_kind: str | None = None,
                semantic_fn=None) -> ClaimDiff:
    """Grade one claim change. Safety first, then source caps, then content."""
    old_claim, new_claim = old_claim or "", new_claim or ""
    signals = find_safety_signals(old_claim, new_claim)
    differs = bool(is_international_source) and token_overlap(old_claim, new_claim) < _WORDING_OVERLAP_CUT
    reasons: list[str] = []

    if signals:
        severity = "safety_critical"
        reasons.append(f"safety signal(s): {', '.join(signals)}")
        if semantic_fn is not None:
            reasons.append("semantic proposal set aside — safety signals decide")
    else:
        overlap = token_overlap(old_claim, new_claim)
        if overlap >= _WORDING_OVERLAP_CUT:
            severity = "informational"
            reasons.append("wording-only change (meaning preserved)")
        else:
            severity = "clinically_meaningful"
            reasons.append(f"substantive {claim_area} change")
        if is_formulary_source and _SEVERITY_RANK[severity] > _SEVERITY_RANK["minor"]:
            severity = "minor"
            reasons.append(
                "formulary source (Tier 2): availability-only, capped at minor; "
                "cannot establish disease-management truth")
        if semantic_fn is not None and not signals:
            try:
                proposal = semantic_fn(old_claim, new_claim) or {}
            except Exception:
                proposal = {}
            if isinstance(proposal, dict):
                proposed = proposal.get("proposed_severity")
                if proposed in _SEVERITY_RANK:
                    severity = proposed
                    note = str(proposal.get("note") or "").strip()
                    reasons.append(f"semantic pass: {note}" if note else "semantic pass adopted")

    if differs:
        reasons.append(
            "differs from Tier 1 local guidance — stored as review signal; "
            "a clinical reviewer decides Indonesia applicability, resources, "
            "GP scope and exam relevance (never auto-override)")
    if change_kind == "superseded" and _SEVERITY_RANK[severity] < _SEVERITY_RANK["minor"]:
        severity = "minor"
        reasons.append("superseded document: escalated one level")

    return ClaimDiff(old_claim=old_claim, new_claim=new_claim, claim_area=claim_area,
                     severity=severity, reasons=reasons, safety_signals=signals,
                     differs_from_local_guidance=differs)


def classify_severity(old_claim: str, new_claim: str, *, claim_area: str = "management",
                      is_formulary_source: bool = False,
                      is_international_source: bool = False,
                      change_kind: str | None = None) -> ClaimDiff:
    """Severity-only entry point (same engine as diff_claims, no semantic)."""
    return diff_claims(old_claim, new_claim, claim_area=claim_area,
                       is_formulary_source=is_formulary_source,
                       is_international_source=is_international_source,
                       change_kind=change_kind, semantic_fn=None)
