"""Phase 11 Tasks B–C — scheduled checks with metadata-first comparison
(plan §31, Phase 11-B/C).

Ordering guarantee: revision hash / version / dates are compared BEFORE any
expensive semantic analysis, so identical metadata never pays for (or risks)
an LLM judgement. The live judge NEVER browses: scoring stays deterministic
and day-to-day stable; only this offline watcher looks outward.

Change kinds (terminal first):
- superseded ......... observed superseded_date is new information.
- new_version ......... observed_version differs (a revision by another name).
- focused_update ...... same version, different revision hash (content moved).
- effective_date_change  same version+hash, new effective date.
- no_change ........... nothing comparable moved (or nothing observed).
"""
from __future__ import annotations

from dataclasses import dataclass, field

CHANGE_KINDS = (
    "no_change",
    "new_version",
    "focused_update",
    "superseded",
    "effective_date_change",
)


@dataclass
class ObservedSnapshot:
    """One scheduled observation of a watched source (injected, never fetched
    by this module — the watcher has no built-in fetcher by design)."""

    observed_version: str = ""
    revision_hash: str = ""
    publication_date: str = ""
    effective_date: str = ""
    superseded_date: str = ""
    checked_at: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "observed_version": self.observed_version,
            "revision_hash": self.revision_hash,
            "publication_date": self.publication_date,
            "effective_date": self.effective_date,
            "superseded_date": self.superseded_date,
            "checked_at": self.checked_at,
            "note": self.note,
        }


def _snapshot_of(observed) -> ObservedSnapshot:
    if isinstance(observed, ObservedSnapshot):
        return observed
    src = observed if isinstance(observed, dict) else {}
    return ObservedSnapshot(
        observed_version=str(src.get("observed_version") or ""),
        revision_hash=str(src.get("revision_hash") or ""),
        publication_date=str(src.get("publication_date") or ""),
        effective_date=str(src.get("effective_date") or ""),
        superseded_date=str(src.get("superseded_date") or ""),
        checked_at=str(src.get("checked_at") or ""),
        note=str(src.get("note") or ""),
    )


@dataclass
class SurveillanceFinding:
    """Outcome of one target check (metadata verdict + raw observation)."""

    target_id: str = ""
    change_kind: str = "no_change"
    observed: dict = field(default_factory=dict)
    checked_at: str = ""
    decided_by_metadata: bool = True

    @property
    def has_change(self) -> bool:
        return self.change_kind != "no_change"

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "change_kind": self.change_kind,
            "has_change": self.has_change,
            "observed": dict(self.observed or {}),
            "checked_at": self.checked_at,
            "decided_by_metadata": self.decided_by_metadata,
        }


def _metadata_decision(target, obs: ObservedSnapshot) -> tuple[str, bool]:
    """Return (change_kind, metadata_conclusive).

    `metadata_conclusive=False` only when the observation carries nothing
    comparable at all, or the version matches but content sameness cannot be
    established (hash missing on either side) with no other signal — the only
    situations where an (optional, offline) semantic pass may be consulted.
    """
    cur_ver = str(getattr(target, "current_version", "") or "")
    cur_hash = str(getattr(target, "revision_hash", "") or "")
    cur_eff = str(getattr(target, "effective_date", "") or "")
    cur_sup = str(getattr(target, "superseded_date", "") or "")

    new_sup = (obs.superseded_date or "").strip()
    if new_sup and new_sup != cur_sup:
        return "superseded", True

    new_ver = (obs.observed_version or "").strip()
    if new_ver and cur_ver and new_ver != cur_ver:
        return "new_version", True
    if new_ver and not cur_ver:
        return "new_version", True

    new_hash = (obs.revision_hash or "").strip()
    hash_comparable = bool(new_hash and cur_hash)
    if hash_comparable and new_hash != cur_hash:
        return "focused_update", True

    new_eff = (obs.effective_date or "").strip()
    if new_eff and cur_eff and new_eff != cur_eff:
        return "effective_date_change", True
    if new_eff and not cur_eff:
        return "effective_date_change", True

    new_pub = (obs.publication_date or "").strip()
    cur_pub = str(getattr(target, "publication_date", "") or "")
    if new_pub and cur_pub and new_pub != cur_pub:
        # Same version/hash/effective date, new publication stamp: a metadata
        # correction worth a look, never silent.
        return "focused_update", True

    any_signal = any([new_ver, new_hash, new_eff, new_pub, new_sup])
    if not any_signal:
        return "no_change", False
    if new_ver and not cur_ver:
        return "new_version", True  # unreachable (handled above), kept explicit
    if new_ver == cur_ver and not hash_comparable:
        return "no_change", False
    return "no_change", True


def detect_change(target, observed=None) -> SurveillanceFinding:
    """Pure metadata comparison (no fetch, no semantic, no side effects)."""
    obs = _snapshot_of(observed) if observed is not None else None
    if obs is None:
        return SurveillanceFinding(
            target_id=str(getattr(target, "target_id", "") or ""),
            change_kind="no_change", observed={}, checked_at="",
            decided_by_metadata=True)
    kind, conclusive = _metadata_decision(target, obs)
    return SurveillanceFinding(
        target_id=str(getattr(target, "target_id", "") or ""),
        change_kind=kind, observed=obs.to_dict(),
        checked_at=obs.checked_at, decided_by_metadata=conclusive)


def check_target(target, observed=None, *, semantic_fn=None, fetch_fn=None) -> SurveillanceFinding:
    """Scheduled per-target check: fetch → metadata → (optional) semantic.

    `fetch_fn(target)` supplies the observation when none is passed.
    `semantic_fn()` (zero-arg, offline) is consulted ONLY when metadata is
    inconclusive — and only a valid change-kind string it returns is adopted.
    Identical metadata short-circuits before any semantic work.
    """
    if observed is None and fetch_fn is not None:
        try:
            observed = fetch_fn(target)
        except Exception:
            observed = None
    finding = detect_change(target, observed)
    if finding.decided_by_metadata or semantic_fn is None:
        return finding
    try:
        proposal = semantic_fn()
    except Exception:
        return finding
    if isinstance(proposal, str) and proposal in CHANGE_KINDS:
        finding.change_kind = proposal
        finding.decided_by_metadata = False
    return finding
