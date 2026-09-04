"""Phase 11 Task E–F — human reviewer queue + approval gate
(plan §31, Phase 11-E/F).

A detected change NEVER edits cases and NEVER auto-publishes. It becomes a
review task (old claim, new claim, source, affected content, severity) that
waits in ReviewerQueue (JSONL-serializable, exportable anywhere EXCEPT
inside the live content tree). Only a NAMED human reviewer can approve or
reject; safety-critical approvals additionally require a clinical role.
Approval proposes a new clinical-content version (minor bump) and flags
safety-critical content needs_update; rejection clears proposals so old
truth stands untouched.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

APPROVABLE = ("pending",)
DECIDED = ("approved", "rejected")

_CLINICAL_ROLE_HINTS = ("clinic", "dokter", "doctor", "spesialis", "specialist",
                        "physician", "surgeon", "pediatrician", "bedah", "anak")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_clinical_role(role) -> bool:
    low = str(role or "").lower()
    return any(h in low for h in _CLINICAL_ROLE_HINTS)


def _entry_to_dict(entry) -> dict:
    to_dict = getattr(entry, "to_dict", None)
    if callable(to_dict):
        try:
            out = to_dict()
            if isinstance(out, dict):
                return out
        except Exception:
            pass
    if isinstance(entry, dict):
        return dict(entry)
    return {"family_id": getattr(entry, "family_id", ""),
            "variant_id": getattr(entry, "variant_id", ""),
            "area": getattr(entry, "area", ""),
            "reason": getattr(entry, "reason", "")}


@dataclass
class ReviewTask:
    """One flagged change awaiting a named human decision."""

    task_id: str = ""
    target_id: str = ""
    change_kind: str = ""
    severity: str = "informational"
    old_claim: str = ""
    new_claim: str = ""
    claim_area: str = "management"
    safety_signals: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    diff_reasons: list = field(default_factory=list)
    differs_from_local_guidance: bool = False
    affected_content: list = field(default_factory=list)
    proposed_content_flag: str = ""
    proposed_clinical_content_version: str = ""
    status: str = "pending"
    reviewed_by: str = ""
    reviewer_role: str = ""
    decision_note: str = ""
    source_metadata: dict = field(default_factory=dict)
    observed: dict = field(default_factory=dict)
    checked_at: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "target_id": self.target_id,
            "change_kind": self.change_kind, "severity": self.severity,
            "old_claim": self.old_claim, "new_claim": self.new_claim,
            "claim_area": self.claim_area,
            "safety_signals": list(self.safety_signals or []),
            "reasons": list(self.reasons or []),
            "diff_reasons": list(self.diff_reasons or self.reasons or []),
            "differs_from_local_guidance": self.differs_from_local_guidance,
            "affected_content": [_entry_to_dict(e) for e in (self.affected_content or [])],
            "proposed_content_flag": self.proposed_content_flag,
            "proposed_clinical_content_version": self.proposed_clinical_content_version,
            "status": self.status, "reviewed_by": self.reviewed_by,
            "reviewer_role": self.reviewer_role, "decision_note": self.decision_note,
            "source_metadata": dict(self.source_metadata or {}),
            "observed": dict(self.observed or {}),
            "checked_at": self.checked_at, "created_at": self.created_at,
        }


def _bump_minor_clinical_version(current: str) -> str:
    """v3.0 → v3.1 (minor bump for an approved content revision)."""
    text = str(current or "").strip()
    prefix = ""
    while text and not text[0].isdigit():
        prefix += text[0]
        text = text[1:]
    parts = text.split(".") if text else []
    nums: list[int] = []
    for part in parts:
        if part.isdigit():
            nums.append(int(part))
        else:
            break
    if not nums:
        return (prefix or "v") + "0.1"
    nums[-1] += 1
    return f"{prefix}{'.'.join(str(n) for n in nums)}"


def build_task(target_id: str, finding, diff, impacts, *, source_metadata=None,
               created_at: str | None = None) -> ReviewTask:
    """Assemble a pending review task (pure — no I/O, no publishing)."""
    severity = str(getattr(diff, "severity", "informational") or "informational")
    reasons = list(getattr(diff, "reasons", None) or [])
    return ReviewTask(
        task_id=str(uuid.uuid4()),
        target_id=str(target_id or ""),
        change_kind=str(getattr(finding, "change_kind", "") or ""),
        severity=severity,
        old_claim=str(getattr(diff, "old_claim", "") or ""),
        new_claim=str(getattr(diff, "new_claim", "") or ""),
        claim_area=str(getattr(diff, "claim_area", "") or "management"),
        safety_signals=list(getattr(diff, "safety_signals", None) or []),
        reasons=reasons,
        diff_reasons=list(reasons),
        differs_from_local_guidance=bool(getattr(diff, "differs_from_local_guidance", False)),
        affected_content=list(impacts or []),
        proposed_content_flag="needs_update" if severity == "safety_critical" else "",
        proposed_clinical_content_version="",
        status="pending",
        source_metadata=dict(source_metadata or {}),
        observed=dict(getattr(finding, "observed", None) or {}),
        checked_at=str(getattr(finding, "checked_at", "") or ""),
        created_at=created_at or _now_iso(),
    )


def _require_named(reviewer_name: str) -> str:
    name = str(reviewer_name or "").strip()
    if not name:
        raise ValueError("named human reviewer required — approvals cannot be anonymous")
    return name


def approve_task(task: ReviewTask, reviewer_name: str, role: str | None = None,
                 note: str | None = None) -> ReviewTask:
    """Human approval gate. Safety-critical needs a clinical role."""
    if getattr(task, "status", None) != "pending":
        raise ValueError(f"already {getattr(task, 'status', 'decided')} — task decided")
    name = _require_named(reviewer_name)
    if str(getattr(task, "severity", "")) == "safety_critical" and not _is_clinical_role(role):
        raise ValueError("safety-critical approval requires clinical role")
    try:
        from pipeline.clinical_contracts.versions import CLINICAL_CONTENT_VERSION
    except Exception:  # noqa: BLE001 — fall back to the shipped baseline
        CLINICAL_CONTENT_VERSION = "v3.0"
    task.status = "approved"
    task.reviewed_by = name
    task.reviewer_role = str(role or "")
    task.decision_note = str(note or "")
    task.proposed_clinical_content_version = _bump_minor_clinical_version(CLINICAL_CONTENT_VERSION)
    return task


def reject_task(task: ReviewTask, reviewer_name: str, role: str | None = None,
                note: str | None = None) -> ReviewTask:
    """Human rejection gate — proposals cleared, old truth stands."""
    if getattr(task, "status", None) != "pending":
        raise ValueError(f"already {getattr(task, 'status', 'decided')} — task decided")
    task.status = "rejected"
    task.reviewed_by = _require_named(reviewer_name)
    task.reviewer_role = str(role or "")
    task.decision_note = str(note or "")
    task.proposed_clinical_content_version = ""
    task.proposed_content_flag = ""
    return task


class ReviewerQueue:
    """In-memory reviewer queue; JSONL export for human tooling."""

    def __init__(self, tasks=None):
        self._tasks: list = list(tasks or [])

    def add(self, task: ReviewTask) -> ReviewTask:
        if not getattr(task, "task_id", None):
            task.task_id = str(uuid.uuid4())
        self._tasks.append(task)
        return task

    def all(self) -> list:
        return list(self._tasks)

    def pending(self) -> list:
        return [t for t in self._tasks if getattr(t, "status", None) == "pending"]

    def __len__(self) -> int:
        return len(self._tasks)

    def export_jsonl(self, path) -> int:
        """Write pending+decided tasks as JSONL. Refuses the live content
        tree outright — reviewer exports must never land inside content/."""
        dest = Path(path)
        if "content" in dest.parts:
            raise ValueError(
                f"refusing to write reviewer export inside content/ tree: {path}")
        if dest.parent and str(dest.parent) not in ("", "."):
            dest.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with open(dest, "w", encoding="utf-8") as fh:
            for task in self._tasks:
                to_dict = getattr(task, "to_dict", None)
                payload = to_dict() if callable(to_dict) else dict(task)
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
                n += 1
        return n
