"""Phase 11 Task F — scheduled surveillance cycle (plan §31, Phase 11-F).

One cycle: for every watched target, compare the injected observation
against registry metadata (hash/version/dates FIRST), map impact, grade the
claim change, and file a reviewer task. The cycle NEVER writes case content,
NEVER publishes, and NEVER scores — `live_truth_changed` is structurally
always False. Humans promote approved changes through the normal
lint → QA → regression → promotion path; active sessions stay pinned.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.surveillance.check import check_target
from pipeline.surveillance.diff import diff_claims
from pipeline.surveillance.impact import map_impact
from pipeline.surveillance.queue import ReviewerQueue, build_task


@dataclass
class CycleResult:
    """Cycle outcome (counts only — content is never touched)."""

    tasks_created: int = 0
    live_truth_changed: bool = False
    targets_checked: int = 0


def _default_claim_provider(target, finding):
    area = ""
    try:
        areas = list(getattr(target, "claim_areas", None) or [])
        area = areas[0] if areas else "management"
    except Exception:
        area = "management"
    return "", "", area


def run_surveillance_cycle(targets=None, observations=None, *, claim_provider=None,
                           checked_at: str = "", case_registry=None,
                           treatment_maps=None) -> tuple:
    """Run one offline surveillance cycle → (CycleResult, ReviewerQueue).

    - targets: iterable of SurveillanceTarget.
    - observations: {target_id: observed-dict} (injected fixtures/snapshots).
    - claim_provider(target, finding) → (old_claim, new_claim, claim_area).
    - case_registry: duck-typed {families, variants_for_family} (may be None
      → impact entries are skipped, tasks still filed).
    - treatment_maps: formulary context (informational only).
    """
    targets = list(targets or [])
    observations = observations if isinstance(observations, dict) else {}
    provider = claim_provider or _default_claim_provider
    queue = ReviewerQueue()
    created = 0
    for target in targets:
        tid = str(getattr(target, "target_id", "") or "")
        observed = (observations or {}).get(tid)
        finding = check_target(target, observed)
        if not finding.has_change:
            continue
        try:
            produced = provider(target, finding)
            old_claim, new_claim, area = produced
        except (TypeError, ValueError):
            old_claim, new_claim, area = "", "", "management"
        kind = str(getattr(target, "kind", "") or "")
        tier = str(getattr(target, "tier", "") or "")
        diff = diff_claims(
            old_claim, new_claim, claim_area=area or "management",
            is_formulary_source=(kind == "formulary"),
            is_international_source=(tier == "3" or kind == "international"),
            change_kind=finding.change_kind)
        entries, _warnings = map_impact(
            target, finding.change_kind, case_registry=case_registry,
            treatment_maps=treatment_maps)
        task = build_task(
            tid, finding, diff, entries,
            source_metadata={"title": str(getattr(target, "title", "") or ""),
                             "organization": str(getattr(target, "organization", "") or ""),
                             "tier": tier, "kind": kind},
            created_at=str(checked_at or ""))
        queue.add(task)
        created += 1
    return CycleResult(tasks_created=created, live_truth_changed=False,
                       targets_checked=len(targets)), queue
