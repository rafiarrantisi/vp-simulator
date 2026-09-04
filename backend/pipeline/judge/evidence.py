"""Phase 7B — User Performance Record + Evidence Ledger (plan §12-13).

The judge considers the COMPLETE normalized user performance — never the
transcript alone when the learner entered clinical information in another
UI step (exam actions, investigations, diagnosis/DDx, treatment). Every
scored rubric item carries: expected behavior, observed evidence, evidence
source, adjudication, score, reason. No supporting evidence → no full
credit (plan §3.4); clinically equivalent wording gets fair credit (§13).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.judge.semantic import Adjudication, adjudicate

EVIDENCE_SOURCES = (
    "conversation",
    "examination",
    "investigation",
    "diagnosis",
    "management",
    "medication",
    "other",
)

KIND_CHANNELS = {
    "history": ("conversation",),
    "examination": ("examination", "conversation"),
    "investigation": ("investigation", "conversation", "management"),
    "diagnosis": ("diagnosis",),
    "management": ("management", "conversation", "medication"),
    "medication": ("medication", "management", "conversation"),
    "communication": ("conversation",),
    "safety": ("conversation", "examination", "investigation", "diagnosis", "management", "medication"),
    "general": ("conversation", "examination", "investigation", "diagnosis", "management", "medication"),
}


@dataclass
class UserPerformanceRecord:
    """Complete normalized learner performance for one session (§12)."""

    conversation_turns: list[dict] = field(default_factory=list)
    exam_actions: list[dict] = field(default_factory=list)
    investigations: list[str] = field(default_factory=list)
    diagnosis_primary: str = ""
    diagnosis_ddx: list[str] = field(default_factory=list)
    management_lines: list[str] = field(default_factory=list)
    medication_text: str = ""
    referral_text: str = ""
    education_text: str = ""
    overtime: bool = False
    interaction_mode: str = "practice"
    learner_level: str = "koas"

    def channel_texts(self, channel: str) -> list[str]:
        if channel == "conversation":
            return [
                str(t.get("content", t.get("text", "")))
                for t in self.conversation_turns
                if t.get("role") == "user"
            ]
        if channel == "examination":
            return [
                f"{a.get('area', '')}: {a.get('finding', a.get('notes', ''))}"
                for a in self.exam_actions
            ]
        if channel == "investigation":
            return list(self.investigations or [])
        if channel == "diagnosis":
            return ([self.diagnosis_primary] if self.diagnosis_primary else []) + list(
                self.diagnosis_ddx or []
            )
        if channel == "management":
            return (
                list(self.management_lines or [])
                + ([self.referral_text] if self.referral_text else [])
                + ([self.education_text] if self.education_text else [])
            )
        if channel == "medication":
            return [self.medication_text] if self.medication_text else []
        return []


@dataclass
class LedgerEntry:
    """One scored rubric item with its evidence trail (§13)."""

    item_id: str = ""
    domain: str = ""
    expected: str = ""
    kind: str = "general"
    criticality: str = "routine"
    synonyms: list = field(default_factory=list)
    acceptable_alternatives: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    adjudication: str = ""
    score_0_3: int = 0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "domain": self.domain,
            "expected": self.expected,
            "kind": self.kind,
            "criticality": self.criticality,
            "evidence": self.evidence,
            "adjudication": self.adjudication,
            "score_0_3": self.score_0_3,
            "reason": self.reason,
        }


def _collect_channel_quotes(
    record: UserPerformanceRecord, channels: tuple[str, ...]
) -> tuple[list[str], list[dict]]:
    texts: list[str] = []
    refs: list[dict] = []
    for ch in channels:
        for i, t in enumerate(record.channel_texts(ch)):
            if not (t or "").strip():
                continue
            texts.append(t)
            refs.append({"source": ch, "ref": f"{ch}:{i}", "quote": t.strip()[:500]})
    return texts, refs


def build_evidence_ledger(
    rubric_items: list[dict], record: UserPerformanceRecord
) -> list[LedgerEntry]:
    """Extract evidence for every rubric item and adjudicate deterministically.

    `rubric_items`: [{item_id, domain, expected, kind?, criticality?,
    synonyms?, acceptable_alternatives?}]. Items whose channels contain no
    matching evidence get miss/0 — full credit without evidence is
    structurally impossible here (the adjudicator only returns hit/3 when
    it found a supporting quote).
    """
    ledger: list[LedgerEntry] = []
    for i, raw in enumerate(rubric_items or []):
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("kind", "general") or "general").lower()
        channels = KIND_CHANNELS.get(kind, KIND_CHANNELS["general"])
        texts, refs = _collect_channel_quotes(record, channels)
        adj = adjudicate(
            str(raw.get("expected", "") or ""),
            texts,
            synonyms=[str(s) for s in (raw.get("synonyms") or [])],
            acceptable_alternatives=[str(s) for s in (raw.get("acceptable_alternatives") or [])],
            kind=(
                "diagnosis"
                if kind == "diagnosis"
                else (
                    "medication"
                    if kind == "medication"
                    else ("management" if kind in ("management", "investigation") else "general")
                )
            ),
        )
        evidence: list[dict] = []
        if adj.matched_quote:
            src = next(
                (r["source"] for r in refs if r["quote"] == adj.matched_quote[:500]),
                channels[0],
            )
            evidence = [{"source": src, "ref": f"{src}:matched", "quote": adj.matched_quote}]
        score = adj.score_0_3
        status = adj.status
        if score == 3 and not evidence:
            score, status = 0, "miss"
        ledger.append(
            LedgerEntry(
                item_id=str(raw.get("item_id", f"item_{i + 1}")),
                domain=str(raw.get("domain", "history") or "history"),
                expected=str(raw.get("expected", "") or ""),
                kind=kind,
                criticality=str(raw.get("criticality", "routine") or "routine"),
                synonyms=[str(s) for s in (raw.get("synonyms") or [])],
                acceptable_alternatives=[str(s) for s in (raw.get("acceptable_alternatives") or [])],
                evidence=evidence,
                adjudication=status,
                score_0_3=score,
                reason=adj.reason,
            )
        )
    return ledger


def build_rubric_from_variant(v) -> list[dict]:
    """Derive rubric items from ONE canonical variant truth (§3.3, §7D).

    The same variant object feeds patient engine, exam, and rubric — score
    truth cannot differ from patient truth. Accepts a ClinicalVariant
    (duck-typed so tests can pass lightweight fakes).
    """
    from pipeline.case_v3.derive import (
        derive_history_checklist,
        derive_investigations,
        derive_red_flags,
    )

    items: list[dict] = []

    try:
        checklist = derive_history_checklist(v)
    except Exception:
        checklist = []
    for n, it in enumerate(checklist):
        imp = (it.get("importance") or "helpful").lower()
        crit = {"critical": "safety-critical"}.get(
            imp, ("important" if imp == "key" else "routine")
        )
        items.append(
            {
                "item_id": f"hx_{n + 1}",
                "domain": "history",
                "expected": str(it.get("item", "")),
                "kind": "history",
                "criticality": crit,
            }
        )

    try:
        red_flags = [r for r in derive_red_flags(v) if r.get("status") == "present"]
    except Exception:
        red_flags = []
    for n, r in enumerate(red_flags):
        crit = (
            "safety-critical"
            if (r.get("criticality", "") or "").lower() == "critical"
            else "critical"
        )
        items.append(
            {
                "item_id": f"rf_{n + 1}",
                "domain": "history",
                "expected": f"Screen red flag: {r.get('fact', '')}",
                "kind": "safety",
                "criticality": crit,
            }
        )

    diag = getattr(v, "diagnostic", None)
    if diag is not None and getattr(diag, "working_diagnosis", ""):
        items.append(
            {
                "item_id": "dx_1",
                "domain": "diagnosis_ddx",
                "expected": str(diag.working_diagnosis),
                "kind": "diagnosis",
                "criticality": "critical",
                "synonyms": list(getattr(diag, "synonyms", None) or []),
            }
        )
        for n, d in enumerate(list(getattr(diag, "differentials", None) or [])):
            if isinstance(d, dict):
                name = d.get("name")
            else:
                name = getattr(d, "name", str(d))
            if not name:
                continue
            items.append(
                {
                    "item_id": f"ddx_{n + 1}",
                    "domain": "diagnosis_ddx",
                    "expected": f"Consider differential: {name}",
                    "kind": "diagnosis",
                    "criticality": "important",
                }
            )

    try:
        invs = [
            i
            for i in derive_investigations(v)
            if i.get("appropriateness") in ("essential", "appropriate")
        ]
    except Exception:
        invs = []
    for n, inv in enumerate(invs[:6]):
        items.append(
            {
                "item_id": f"inv_{n + 1}",
                "domain": "investigations",
                "expected": f"Order {inv.get('name', '')}",
                "kind": "investigation",
                "criticality": "important",
            }
        )

    mgmt = getattr(v, "management", None)
    if mgmt is not None:
        for bucket, dom, crit in (
            ("stabilization", "management_non_pharma", "safety-critical"),
            ("pharmacologic", "management_pharma", "critical"),
            ("non_pharmacologic", "management_non_pharma", "important"),
            ("referral", "management_non_pharma", "critical"),
            ("education_safety_netting", "communication_education", "important"),
        ):
            for n, line in enumerate(list(getattr(mgmt, bucket, None) or [])):
                kind = "medication" if bucket == "pharmacologic" else "management"
                items.append(
                    {
                        "item_id": f"mg_{bucket}_{n + 1}",
                        "domain": dom,
                        "expected": str(line),
                        "kind": kind,
                        "criticality": crit,
                    }
                )

    for err in list(getattr(v, "safety_critical_errors", None) or [])[:4]:
        items.append(
            {
                "item_id": f"sf_avoid_{len(items)}",
                "domain": "management_non_pharma",
                "expected": f"Avoid unsafe action: {err}",
                "kind": "safety",
                "criticality": "safety-critical",
            }
        )
    return items
