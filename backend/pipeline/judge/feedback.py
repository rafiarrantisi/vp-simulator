"""Phase 7F — feedback composer (plan §26).

Detailed feedback is generated AFTER scoring is finalized, from the
evidence ledger + item results + domain scores + safety flags + diagnosis /
management quality + approved sources + learner level + mode. It must NEVER
claim the learner performed an action absent from the evidence ledger —
"what you did well" contains ONLY hit items with quotes; everything else
is framed as missed/partial with the transparent expected standard.
"""

from __future__ import annotations


def compose_feedback(
    ledger: list,
    *,
    per_domain: dict,
    overall: int,
    gates: list[dict] | None,
    global_rating: str,
    sources: list[dict] | None = None,
    learner_stage: str = "koas",
    mode: str = "practice",
    next_actions: list[str] | None = None,
) -> dict:
    """Build the 8-section examiner feedback dict (deterministic, no LLM)."""
    gates = list(gates or [])
    sources = list(sources or [])
    did_well = [e for e in ledger if getattr(e, "adjudication", "") == "hit"]
    missed = [e for e in ledger if getattr(e, "adjudication", "") != "hit"]
    well_lines: list = []
    for e in did_well[:6]:
        ev = getattr(e, "evidence", None) or []
        quote = ev[0].get("quote", "") if ev else ""
        well_lines.append(
            {
                "item_id": getattr(e, "item_id", ""),
                "expected": getattr(e, "expected", ""),
                "evidence": quote,
            }
        )
    miss_lines = [
        {
            "item_id": getattr(e, "item_id", ""),
            "expected": getattr(e, "expected", ""),
            "reason": getattr(e, "reason", ""),
            "criticality": getattr(e, "criticality", "routine"),
        }
        for e in missed[:10]
    ]
    weakest = sorted((per_domain or {}).items(), key=lambda kv: (kv[1] or {}).get("pct", 0))[:2]
    strongest = sorted(
        (per_domain or {}).items(), key=lambda kv: (kv[1] or {}).get("pct", 0), reverse=True
    )[:2]
    tone = "examiner-like and concise" if mode == "osce" else "explanatory with actionable teaching"
    overall_assessment = (
        f"Overall {overall}/100 — {global_rating} ({mode}, {learner_stage}; {tone}). "
        f"{len(did_well)} item(s) evidenced, {len(missed)} missed/partial. "
        + (f"{len(gates)} safety issue(s) require attention. " if gates else "No safety gates triggered.")
    )
    src_titles = [s.get("title", "") for s in sources if s.get("title")]
    feedback = {
        "overall_assessment": overall_assessment,
        "what_you_did_well": well_lines,
        "what_you_missed": miss_lines,
        "clinical_reasoning": _reasoning_line(ledger),
        "examination_investigations": _exam_inv_line(ledger),
        "management": _management_line(ledger, gates),
        "what_examiner_expected": _expected_line(ledger, weakest),
        "what_to_practise_next": list(next_actions or _default_next(weakest)),
        "strongest": [d for d, _ in strongest],
        "needs_work": [d for d, _ in weakest],
        "safety_flags": [{"type": g.get("type"), "detail": g.get("detail")} for g in gates],
        "sources": src_titles[:8],
        "mode": mode,
        "tone": tone,
    }
    return feedback


def _reasoning_line(ledger) -> str:
    dx = [e for e in ledger if getattr(e, "kind", "") == "diagnosis"]
    if not dx:
        return "No diagnosis items in this rubric."
    ok = [e for e in dx if getattr(e, "adjudication", "") == "hit"]
    return f"Diagnosis: {len(ok)}/{len(dx)} evidenced. " + (
        "Working diagnosis supported by elicited evidence. "
        if ok
        else "Working diagnosis not supported by evidence yet. "
    )


def _exam_inv_line(ledger) -> str:
    items = [e for e in ledger if getattr(e, "kind", "") in ("examination", "investigation")]
    if not items:
        return "No examination/investigation items in this rubric."
    ok = [e for e in items if getattr(e, "adjudication", "") == "hit"]
    return f"Examination & investigations: {len(ok)}/{len(items)} evidenced. " + (
        "Targeted selection observed. "
        if ok
        else "Key areas/tests missing — review the expected list. "
    )


def _management_line(ledger, gates) -> str:
    items = [e for e in ledger if getattr(e, "kind", "") in ("management", "medication", "safety")]
    if not items:
        return "No management items in this rubric."
    ok = [e for e in items if getattr(e, "adjudication", "") == "hit"]
    base = f"Management: {len(ok)}/{len(items)} evidenced. "
    if gates:
        base += "Safety-critical priority missed — stabilize/refer first. "
    elif ok:
        base += "Priorities, medication, and referral recorded. "
    else:
        base += "Priorities/stabilization/medication need work. "
    return base


def _expected_line(ledger, weakest) -> str:
    names = ", ".join(d for d, _ in weakest) or "—"
    return (
        f"An examiner expected evidence for each rubric item (weakest domains: {names}). "
        "Full credit requires an observed action/statement in the encounter — inference alone earns nothing."
    )


def _default_next(weakest) -> list[str]:
    return [f"Practise {d} (weakest domain)" for d, _ in weakest[:2]] or [
        "Repeat a variant of the same family with a different presentation"
    ]
