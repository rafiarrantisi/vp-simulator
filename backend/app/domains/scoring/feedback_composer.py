"""Phase PNPK-4 — deterministic clinical-evidence composer (brief §7.7, §8).

Pure function: final score view + approved compiled pack + case context
  -> `clinical_evidence` namespace (rationale items + citation references).

Hard rules:
- Score-critical inputs are READ-ONLY: the composer never mutates per_item,
  safety_gates, overall, or answer_key (proven by deep-snapshot tests).
- Item identity comes from the CANONICAL rubric (stable IDs), status from
  the report via the SAME text-equality the existing answer-key merge uses.
  No fuzzy matching, no nearest-neighbor, no invented exclusions.
- Templates render allowlisted placeholders only ({label, status_word,
  reason, ref}); anything else fails the item closed (skipped, counted).
- No transcript passed to the renderer; no HTML/URL/SQL/eval templating.
- Unavailable pack/binding/mapping -> None (caller omits the namespace),
  with a machine-readable reason for metrics. Never fabricate.
"""
from __future__ import annotations

STATUS_WORD = {"hit": "met", "partial": "partially met", "miss": "missed"}
ALLOWED_PLACEHOLDERS = ("label", "status_word", "reason", "ref")


class ComposeError(Exception):
    pass


def _norm_text(value) -> str:
    return " ".join(str(value or "").split()).lower()


def _safety_first(mapping: dict, claims_by_id: dict) -> tuple[int, int]:
    cats = {(claims_by_id.get(cid) or {}).get("category") for cid in mapping.get("claim_ids") or []}
    safety = 0 if ("red_flag" in cats or (mapping.get("target_kind") == "per_item"
                                          and "sf_" in str(mapping.get("canonical_target_id") or ""))) else 1
    return (safety, int(mapping.get("display_priority") or 0))


def compose_clinical_evidence(*, report: dict, rubric_items: list[dict],
                              pack: dict, binding: dict,
                              mode: str = "practice",
                              learner_stage: str = "koas",
                              variant_id: str = "") -> dict | None:
    """Compose the additive namespace, or None with `reason` when unavailable.

    Returns (namespace_dict, outcome) where outcome is one of
    available/unavailable_* for metrics. The namespace carries its own
    status; callers omit the key entirely when None.
    """
    if not isinstance(report, dict) or not isinstance(pack, dict):
        return None, "unavailable_bad_input"
    if not isinstance(binding, dict):
        return None, "unavailable_no_binding"
    if mode not in (binding.get("supported_modes") or [mode]):
        return None, "unavailable_mode"
    if learner_stage not in (binding.get("supported_stages") or [learner_stage]):
        return None, "unavailable_stage"

    claims = {c.get("claim_id"): c for c in pack.get("claims") or []}
    templates = {t.get("template_id"): t for t in pack.get("templates") or []}
    rubric = {i.get("item_id"): i for i in rubric_items or []}
    # report status by canonical rubric ID (attached at merge time), with
    # direct expected-text equality as fallback for rubric-shaped rows.
    status_by_target: dict[str, str] = {}
    status_by_expected: dict[str, str] = {}
    for it in report.get("per_item") or []:
        if not isinstance(it, dict):
            continue
        status = str(it.get("status") or "miss").lower()
        for rid in it.get("rubric_ids") or []:
            status_by_target.setdefault(str(rid), status)
        status_by_expected[_norm_text(it.get("item"))] = status

    disabled = set(binding.get("disabled_claims") or [])
    items_out: list[dict] = []
    skipped = 0
    emitted_targets: set[str] = set()
    for m in sorted(pack.get("mappings") or [],
                    key=lambda mm: _safety_first(mm, claims)):
        if not isinstance(m, dict):
            skipped += 1
            continue
        if variant_id and variant_id not in (m.get("applicable_variant_ids") or []):
            continue
        target = m.get("canonical_target_id")
        if target in emitted_targets:
            continue  # one rationale per target (highest priority wins)
        ritem = rubric.get(target)
        if ritem is None:
            skipped += 1
            continue
        status = status_by_target.get(
            target, status_by_expected.get(_norm_text(ritem.get("expected")), ""))
        if status not in (m.get("trigger_statuses") or []):
            continue
        cids = [c for c in (m.get("claim_ids") or []) if c not in disabled]
        cids = [c for c in cids if c in claims]
        if not cids:
            skipped += 1
            continue
        tpl = templates.get(m.get("template_id"))
        if tpl is None:
            skipped += 1
            continue
        if status not in (tpl.get("statuses") or []):
            skipped += 1
            continue
        primary = claims[cids[0]]
        subs = {
            "label": str(ritem.get("expected") or target),
            "status_word": STATUS_WORD.get(status, status),
            "reason": str(primary.get("statement") or ""),
        }
        tpl_text = str(tpl.get("text") or "").replace("[{ref}]", "\x00REF\x00")
        try:
            rationale = tpl_text.format(**{
                k: subs[k] for k in tpl.get("placeholders") or [] if k != "ref"})
        except (KeyError, IndexError, ValueError):
            skipped += 1
            continue
        items_out.append({
            "target_kind": m.get("target_kind"),
            "target_id": target,
            "dimension_id": ritem.get("domain"),
            "rationale": rationale,
            "_claim_ids": cids,
            "_template": tpl,
            "rationale_kind": primary.get("support_kind"),
        })
        emitted_targets.add(target)
    if not items_out:
        return None, "unavailable_no_mappings"

    # citations: dedup by (artifact sha + pages), numbers in first-use order
    references: list[dict] = []
    seen: dict[tuple, str] = {}

    def _cite_id(span: dict, source: dict) -> str:
        key = (span.get("source_version_id"), span.get("pdf_page_start"),
               span.get("pdf_page_end"))
        if key not in seen:
            n = len(references) + 1
            cid = f"ref-{n}"
            seen[key] = cid
            references.append({
                "citation_id": cid,
                "source_version_id": span.get("source_version_id"),
                "source_id": source.get("source_id"),
                "title": source.get("title"),
                "publisher": source.get("publisher"),
                "year": source.get("year"),
                "decision_number": source.get("decision_number"),
                "official_url": source.get("official_url"),
                "document_sha256": source.get("document_sha256"),
                "section_path": span.get("section_path"),
                "pdf_page_start": span.get("pdf_page_start"),
                "pdf_page_end": span.get("pdf_page_end"),
                "printed_page_label": span.get("printed_page_label"),
            })
        return seen[key]

    sources = pack.get("sources") or {}
    for it in items_out:
        tpl = it.pop("_template")
        cids = it.pop("_claim_ids")
        cite_ids: list[str] = []
        for cid in cids:
            for sp in (claims[cid].get("evidence_spans") or []):
                src = sources.get(sp.get("source_version_id"), {})
                cite_ids.append(_cite_id(sp, src))
        # dedup preserving order
        cite_ids = list(dict.fromkeys(cite_ids))
        it["claim_ids"] = cids
        it["citation_ids"] = cite_ids
        nums = sorted({c.split("-")[1] for c in cite_ids if c.startswith("ref-")},
                      key=int)
        it["rationale"] = it["rationale"].replace(
            "\x00REF\x00", "[" + ",".join(nums) + "]")

    return ({
        "schema_version": "1.0",
        "status": "available",
        "pack": {
            "id": pack.get("pack_id"),
            "revision": pack.get("pack_revision"),
            "sha256": binding.get("evidence_pack_sha256") or pack.get("pack_sha256"),
        },
        "items": items_out,
        "references": references,
    }, "available")
