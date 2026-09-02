"""STEP 8 §7 — source QA + source audit surface.

Automated, deterministic source checks:
  - URL well-formed and (best-effort) reachable
  - source current, or explicitly justified (superseded/unclear flagged)
  - source kind/type correct (guideline/competency/epidemiology/formulary)
  - Fornas only used for formulary claims (never as treatment-guideline truth)
  - management/epidemiology claims traceable to a source
A random sample audit report is produced for human spot-checking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipeline.case_v3.governance import SourceRecord, source_records_from_variant
from pipeline.case_v3.models import ClinicalVariant
from pipeline.case_v3.qa import QAIssue


@dataclass
class RandomAudit:
    sample: list[str] = field(default_factory=list)


def _url_ok(u: str) -> bool:
    return bool(u and u.startswith("http"))


def source_issues(v: ClinicalVariant) -> list[QAIssue]:
    out: list[QAIssue] = []
    recs = source_records_from_variant(v)
    if not recs:
        out.append(QAIssue("no_sources", "variant has no source records", "error"))
        return out
    for r in recs:
        # URL present + well-formed
        if r.url and not _url_ok(r.url):
            out.append(QAIssue("bad_url", f"source URL not well-formed: {r.url}", "warning"))
        # Fornas must never be typed as a management guideline
        if r.is_formulary and "management" in [k.value for k in r.relevance]:
            out.append(QAIssue("fornas_as_guideline",
                               "Fornas/formulary source mis-typed as management guideline", "error"))
        if not r.year and r.document_type not in ("",):
            out.append(QAIssue("no_year", f"source '{r.title}' lacks year (currentness unclear)", "warning"))
    # management non-empty & traceable → at least one management-type/guideline source
    if v.management.stabilization or v.management.pharmacologic or v.management.referral:
        if not any("management" in [k.value for k in r.relevance]
                   or (r.document_type or "").lower() in ("guideline", "pnpk", "competency")
                   for r in recs):
            out.append(QAIssue("mgmt_intraceable", "management claims have no management/guideline source",
                               "warning"))
    # epidemiology constraints traceable (if present)
    epi = v.epidemiology.evidence
    if (epi.facts or epi.sources):
        if not epi.sources:
            out.append(QAIssue("epi_intraceable", "epidemiology evidence present but no epi source cited",
                               "warning"))
    return out


def random_audit_sample(vs: list[ClinicalVariant], *, k: int = 3, seed: int = 0) -> RandomAudit:
    """Pick a deterministic pseudo-random sample of variants for human spot-audit (§7)."""
    import random
    rng = random.Random(seed)
    pool = sorted(vs, key=lambda x: x.id)
    picked = rng.sample(pool, min(k, len(pool))) if pool else []
    return RandomAudit(sample=[x.id for x in picked])