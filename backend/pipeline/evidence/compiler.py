"""Phase PNPK-2 — evidence pack compiler (brief §12).

Authoring JSON (content/evidence/) + PNPK catalog/manifest + live registry
  -> validated, deterministic compiled pack (build/evidence/<sha>.json).

Refuses (§12): unknown IDs, non-PNPK sources, bad/missing locators,
unapproved content, source_hold, digest mismatches, inapplicable
age/pregnancy, unknown template substitutions, orphan citations,
canonical conflicts, patient-route payload keys, placeholders, bad versions.

No I/O beyond explicit dirs. No LLM. No network. Deterministic: same input
bytes -> same output bytes (sorted keys/lists, no timestamps in payload).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline.clinical_contracts.evidence_clinical import (
    PACK_SCHEMA_VERSION,
    CaseEvidenceConfig,
    ClinicalClaim,
    ClinicalEvidencePack,
    EvidenceSpan,
    EvidenceTemplate,
    RubricEvidenceMapping,
)

COMPILER_VERSION = "qora-evidence-compiler-1.0"

# Structural keys that must never ship toward patient/browser contexts.
BANNED_PAYLOAD_KEYS = (
    "patient_prompt", "full_transcript", "answer_key", "working_diagnosis",
    "local_path", "file://",
)


class CompileError(Exception):
    pass


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise CompileError(f"unreadable JSON {path}: {e}")


def _payload_canonical(payload: dict) -> dict:
    """Remove authoring-only review aids from the hashed payload."""
    import copy

    payload = copy.deepcopy(payload)
    for c in payload.get("claims") or []:
        for sp in c.get("evidence_spans") or []:
            sp.pop("excerpt", None)
    return payload


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def _as_span(d: dict, where: str) -> EvidenceSpan:
    try:
        return EvidenceSpan(
            source_version_id=str(d.get("source_version_id") or ""),
            section_path=list(d.get("section_path") or []),
            heading=str(d.get("heading") or ""),
            pdf_page_start=int(d.get("pdf_page_start") or 0),
            pdf_page_end=int(d.get("pdf_page_end") or d.get("pdf_page_start") or 0),
            printed_page_label=d.get("printed_page_label"),
            locator=str(d.get("locator") or ""),
            excerpt_hash=str(d.get("excerpt_hash") or ""),
        )
    except Exception as e:  # noqa: BLE001
        raise CompileError(f"{where}: bad span: {e}")


def _as_claim(d: dict) -> ClinicalClaim:
    return ClinicalClaim(
        claim_id=str(d.get("claim_id") or ""),
        claim_revision=int(d.get("claim_revision") or 1),
        statement=str(d.get("statement") or ""),
        category=str(d.get("category") or ""),
        support_kind=str(d.get("support_kind") or ""),
        applicability=dict(d.get("applicability") or {}),
        evidence_spans=[_as_span(x, d.get("claim_id", "?")) for x in d.get("evidence_spans") or []],
        grade=d.get("grade"),
        review_status=str(d.get("review_status") or "draft"),
        reviewer=str(d.get("reviewer") or ""),
        reviewed_at=str(d.get("reviewed_at") or ""),
        approval_record_id=str(d.get("approval_record_id") or ""),
    )


def _as_template(d: dict) -> EvidenceTemplate:
    return EvidenceTemplate(
        template_id=str(d.get("template_id") or ""),
        template_revision=int(d.get("template_revision") or 1),
        statuses=list(d.get("statuses") or []),
        text=str(d.get("text") or ""),
        placeholders=list(d.get("placeholders") or []),
        review_status=str(d.get("review_status") or "draft"),
        approval_record_id=str(d.get("approval_record_id") or ""),
    )


def _as_mapping(d: dict) -> RubricEvidenceMapping:
    return RubricEvidenceMapping(
        mapping_id=str(d.get("mapping_id") or ""),
        canonical_target_id=str(d.get("canonical_target_id") or ""),
        target_kind=str(d.get("target_kind") or ""),
        rubric_revision=str(d.get("rubric_revision") or ""),
        rubric_hash=str(d.get("rubric_hash") or ""),
        claim_ids=list(d.get("claim_ids") or []),
        trigger_statuses=list(d.get("trigger_statuses") or []),
        template_id=str(d.get("template_id") or ""),
        display_priority=int(d.get("display_priority") or 0),
        applicable_variant_ids=list(d.get("applicable_variant_ids") or []),
        review_status=str(d.get("review_status") or "draft"),
        approval_record_id=str(d.get("approval_record_id") or ""),
    )


def _pdf_pages(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def _variant_rubric(registry, variant_id: str) -> list[dict]:
    from pipeline.judge.evidence import build_rubric_from_variant

    v = registry.variants.get(variant_id)
    if v is None:
        raise CompileError(f"unknown variant {variant_id}")
    return build_rubric_from_variant(v)


def _rubric_hash(items: list[dict]) -> str:
    slim = [{"item_id": i.get("item_id"), "domain": i.get("domain"),
             "expected": i.get("expected"), "kind": i.get("kind"),
             "criticality": i.get("criticality")} for i in items]
    return _sha(sorted(slim, key=lambda x: str(x.get("item_id"))))


def _check_applicability(claim: ClinicalClaim, variant, errors: list[str]) -> None:
    app = claim.applicability or {}
    preg = app.get("pregnancy", "any")
    vpreg = str(getattr(getattr(variant, "identity", None), "pregnancy_status", "") or "").lower()
    if preg == "yes" and vpreg not in ("yes", "pregnant", "true", "1"):
        errors.append(f"claim {claim.claim_id}: pregnancy=yes on non-pregnant {variant.id}")
    if preg == "no" and vpreg in ("yes", "pregnant", "true", "1"):
        errors.append(f"claim {claim.claim_id}: pregnancy=no on pregnant {variant.id}")
    sex = str(app.get("sex") or "any").lower()
    vsex = str(getattr(getattr(variant, "identity", None), "biological_sex", "") or "").lower()
    if sex in ("male", "female") and vsex and vsex != sex:
        errors.append(f"claim {claim.claim_id}: sex={sex} on {vsex} {variant.id}")
    try:
        age = getattr(getattr(variant, "identity", None), "age_years", None)
        lo = app.get("min_age_years")
        hi = app.get("max_age_years")
        if age is not None and (lo is not None or hi is not None):
            if (lo is not None and age < float(lo)) or (hi is not None and age > float(hi)):
                errors.append(f"claim {claim.claim_id}: age {age} outside [{lo},{hi}] for {variant.id}")
    except (TypeError, ValueError):
        errors.append(f"claim {claim.claim_id}: bad age applicability")


def compile_pack(pack_def: dict, *, claims_dir: Path, mappings_dir: Path,
                 templates_dir: Path, catalog: dict, manifest: dict,
                 registry, pdf_root: Path | None,
                 allow_draft: bool = False):
    """Compile one pack definition. Raises CompileError listing ALL problems.

    allow_draft=True (authoring iteration only): approval gaps are REPORTED
    as the third return value instead of failing, every other rule still
    enforced, and the pack digest is still computed. Draft output must never
    be published or loaded at runtime.
    """
    errors: list[str] = []
    pack_id = str(pack_def.get("pack_id") or "")
    if not pack_id:
        raise CompileError("pack without pack_id")

    def _load_many(d: Path, conv, kind: str):
        out = []
        if d.is_dir():
            for f in sorted(d.glob("*.json")):
                data = _load_json(f)
                items = data if isinstance(data, list) else [data]
                for it in items:
                    try:
                        out.append(conv(it))
                    except CompileError as e:
                        errors.append(f"{kind} {f.name}: {e}")
        return out

    claims = _load_many(claims_dir, _as_claim, "claim")
    templates = _load_many(templates_dir, _as_template, "template")
    mappings = _load_many(mappings_dir, _as_mapping, "mapping")
    for c in claims:
        errors.extend(c.validate())
    for t in templates:
        errors.extend(t.validate())
    for m in mappings:
        errors.extend(m.validate())
    by_claim = {c.claim_id: c for c in claims}
    by_template = {t.template_id: t for t in templates}

    # catalog whitelist: edition_id -> entry (supports documents/editions/sources shapes)
    editions = {}
    for ed in (catalog.get("documents") or []) + (catalog.get("editions") or []) + (catalog.get("sources") or []):
        eid = ed.get("edition_id") or ed.get("source_id")
        if eid:
            editions[eid] = ed
    # manifest artifacts by source_version identity
    artifacts = {}
    for _doc, body in (manifest.get("documents") or {}).items():
        for a in body.get("artifacts") or []:
            artifacts[a.get("artifact_id")] = a

    # source versions referenced by spans
    for c in claims:
        for sp in c.evidence_spans:
            sv = sp.source_version_id
            ed_id = sv.split("@sha256:")[0] if "@sha256:" in sv else sv
            if ed_id not in editions:
                errors.append(f"claim {c.claim_id}: source {ed_id} outside PNPK whitelist")
                continue
            entry = editions[ed_id]
            if entry.get("clinical_review_status") == "source_hold":
                errors.append(f"claim {c.claim_id}: source_hold {ed_id} not publishable")
            if "@sha256:" in sv:
                want = sv.split("@sha256:", 1)[1]
                art = artifacts.get(sv)
                if art is None:
                    errors.append(f"claim {c.claim_id}: artifact {sv} missing from manifest")
                elif art.get("sha256") != want:
                    errors.append(f"claim {c.claim_id}: artifact digest mismatch {sv}")

    # page ranges vs local PDFs
    if pdf_root is not None:
        for c in claims:
            for sp in c.evidence_spans:
                art = artifacts.get(sp.source_version_id)
                if art is None:
                    continue
                rel = art.get("local_path", "")
                pdf = pdf_root / rel if rel else None
                if pdf is None or not pdf.is_file():
                    continue  # unverifiable here; publish gate decides
                pages = _pdf_pages(pdf)
                if pages is None:
                    continue
                if sp.pdf_page_end > pages:
                    errors.append(f"claim {c.claim_id}: pages {sp.pdf_page_start}-{sp.pdf_page_end} out of range (pdf has {pages})")

    # mappings: claims/templates/variants/rubric/applicability
    rubric_cache: dict[str, list[dict]] = {}
    for m in mappings:
        for cid in m.claim_ids:
            if cid not in by_claim:
                errors.append(f"mapping {m.mapping_id}: unknown claim {cid}")
                continue
            claim = by_claim[cid]
            if claim.review_status != "approved":
                errors.append(f"mapping {m.mapping_id}: claim {cid} not approved")
        if m.template_id not in by_template:
            errors.append(f"mapping {m.mapping_id}: unknown template {m.template_id}")
        else:
            tpl = by_template[m.template_id]
            if tpl.review_status != "approved":
                errors.append(f"mapping {m.mapping_id}: template {m.template_id} not approved")
            missing = [st for st in m.trigger_statuses if st not in tpl.statuses]
            if missing:
                errors.append(f"mapping {m.mapping_id}: triggers {missing} not in template statuses")
        if m.review_status != "approved":
            errors.append(f"mapping {m.mapping_id}: mapping not approved")
        for vid in m.applicable_variant_ids:
            if vid not in registry.variants:
                errors.append(f"mapping {m.mapping_id}: unknown variant {vid}")
                continue
            if vid not in rubric_cache:
                try:
                    rubric_cache[vid] = _variant_rubric(registry, vid)
                except CompileError as e:
                    errors.append(str(e))
                    continue
            items = rubric_cache[vid]
            ids = {i.get("item_id") for i in items}
            if m.canonical_target_id not in ids:
                errors.append(f"mapping {m.mapping_id}: target {m.canonical_target_id} not in rubric of {vid}")
            rh = _rubric_hash(items)
            if m.rubric_hash and m.rubric_hash != rh:
                errors.append(f"mapping {m.mapping_id}: rubric_hash mismatch for {vid}")
            elif not m.rubric_hash:
                m.rubric_hash = rh
            v = registry.variants[vid]
            for cid in m.claim_ids:
                if cid in by_claim:
                    _check_applicability(by_claim[cid], v, errors)

    # banned payload keys anywhere in authoring text
    def _scan(obj, where: str):
        if isinstance(obj, dict):
            for k, val in obj.items():
                if k in BANNED_PAYLOAD_KEYS:
                    errors.append(f"{where}: banned payload key {k!r}")
                _scan(val, where)
        elif isinstance(obj, list):
            for it in obj:
                _scan(it, where)
        elif isinstance(obj, str):
            for bad in ("file://",):
                if bad in obj:
                    errors.append(f"{where}: banned marker {bad!r}")

    _scan(pack_def, f"pack {pack_id}")

    # condition allowlist (canonical-conflict proxy)
    allowed_conditions = set(pack_def.get("allowed_conditions") or [])
    if allowed_conditions:
        for c in claims:
            conds = set((c.applicability or {}).get("condition_codes") or [])
            if conds and not (conds & allowed_conditions):
                errors.append(f"claim {c.claim_id}: conditions {sorted(conds)} outside pack allowlist")

    if errors:
        approval_gaps = [e for e in errors
                         if "not approved" in e or "without approval_record_id" in e]
        if not (allow_draft and len(approval_gaps) == len(errors)):
            raise CompileError("pack invalid:\n- " + "\n- ".join(sorted(set(errors))))
        draft_gaps: list[str] = sorted(set(approval_gaps))
    else:
        draft_gaps = []

    # family defaults -> explicit per-variant bindings
    bindings: list[CaseEvidenceConfig] = []
    fam_defaults = pack_def.get("family_defaults") or {}
    fams = pack_def.get("families") or []
    for fam_id in fams:
        fam = registry.families.get(fam_id)
        if fam is None:
            raise CompileError(f"pack {pack_id}: unknown family {fam_id}")
        for v in registry.variants_for_family(fam_id):
            bindings.append(CaseEvidenceConfig(
                variant_id=v.id, canonical_hash=v.canonical_hash(),
                rubric_hash=_rubric_hash(rubric_cache.get(
                    v.id) or _variant_rubric(registry, v.id)),
                content_release_id=str(pack_def.get("content_release_id") or ""),
                allowed_source_version_ids=sorted(
                    {sp.source_version_id for c in claims for sp in c.evidence_spans}),
                evidence_pack_id=pack_id,
                evidence_pack_revision=int(pack_def.get("pack_revision") or 1),
                evidence_pack_sha256="",
                status="approved",
                supported_modes=list(pack_def.get("supported_modes") or []),
                supported_stages=list(pack_def.get("supported_stages") or []),
                disabled_claims=list(pack_def.get("disabled_claims") or []),
            ))
    for b in bindings:
        errs = b.validate()
        # sha filled after pack digest; validate the rest
        errs = [e for e in errs if "pack sha256" not in e]
        if errs:
            raise CompileError("binding invalid:\n- " + "\n- ".join(errs))

    sources_detail: dict[str, dict] = {}
    for c in claims:
        for sp in c.evidence_spans:
            sv = sp.source_version_id
            if sv in sources_detail:
                continue
            ed_id = sv.split("@sha256:")[0] if "@sha256:" in sv else sv
            ed = editions.get(ed_id, {})
            art = artifacts.get(sv, {})
            sources_detail[sv] = {
                "source_id": ed.get("source_id"),
                "title": ed.get("title"),
                "publisher": ed.get("publisher"),
                "year": ed.get("year"),
                "decision_number": ed.get("decision_number"),
                "official_url": art.get("official_url") or ed.get("official_url"),
                "document_sha256": art.get("sha256"),
            }
    pack = ClinicalEvidencePack(
        pack_id=pack_id,
        pack_schema_version=PACK_SCHEMA_VERSION,
        pack_revision=int(pack_def.get("pack_revision") or 1),
        clinical_content_version=str(pack_def.get("clinical_content_version") or ""),
        compatible_scoring_versions=list(pack_def.get("compatible_scoring_versions") or []),
        scoring_rubric_digest=_sha(sorted({m.rubric_hash for m in mappings})),
        case_binding_digest=_sha(sorted(b.variant_id + b.canonical_hash for b in bindings)),
        source_versions=sorted(
            {sp.source_version_id for c in claims for sp in c.evidence_spans}),
        claims=sorted(claims, key=lambda c: c.claim_id),
        mappings=sorted(mappings, key=lambda m: m.mapping_id),
        templates=sorted(templates, key=lambda t: t.template_id),
        review_record=dict(pack_def.get("review_record") or {}),
        compiler_version=COMPILER_VERSION,
        sources=sources_detail,
    )
    digest = _sha(_payload_canonical(pack.payload_digest_fields()))
    pack.pack_sha256 = digest
    if draft_gaps:
        pack._draft_gaps = draft_gaps  # type: ignore[attr-defined]
    for b in bindings:
        b.evidence_pack_sha256 = digest
    return pack, bindings


def emit_pack(pack: ClinicalEvidencePack, bindings: list[CaseEvidenceConfig],
              out_dir: Path) -> tuple[Path, Path]:
    """Write deterministic pack JSON + release index. Returns (pack_path, index_path)."""
    from dataclasses import asdict

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = _payload_canonical(pack.payload_digest_fields())
    assert _sha(payload) == pack.pack_sha256, "digest mismatch (non-determinism?)"
    pack_path = out_dir / f"{pack.pack_sha256}.json"
    pack_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1,
                                    sort_keys=True) + "\n", encoding="utf-8")
    bindings_doc = [asdict(b) for b in sorted(bindings, key=lambda x: x.variant_id)]
    index = {
        "index_schema": 1,
        "packs": [{
            "pack_id": pack.pack_id,
            "pack_revision": pack.pack_revision,
            "sha256": pack.pack_sha256,
            "compiler": COMPILER_VERSION,
            "variants": [b["variant_id"] for b in bindings_doc],
        }],
        "bindings": bindings_doc,
    }
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1,
                                     sort_keys=True) + "\n", encoding="utf-8")
    return pack_path, index_path


def reverse_index(pack: ClinicalEvidencePack,
                  bindings: list[CaseEvidenceConfig]) -> dict:
    """source_version -> claims -> mappings -> packs -> variants (governance)."""
    idx: dict = {}
    for c in pack.claims:
        for sp in c.evidence_spans:
            idx.setdefault(sp.source_version_id, {}).setdefault("claims", [])
            if c.claim_id not in idx[sp.source_version_id]["claims"]:
                idx[sp.source_version_id]["claims"].append(c.claim_id)
    for m in pack.mappings:
        for cid in m.claim_ids:
            for c in pack.claims:
                if c.claim_id != cid:
                    continue
                for sp in c.evidence_spans:
                    node = idx.setdefault(sp.source_version_id, {})
                    node.setdefault("mappings", [])
                    if m.mapping_id not in node["mappings"]:
                        node["mappings"].append(m.mapping_id)
    idx["pack"] = pack.pack_id
    idx["variants"] = sorted(b.variant_id for b in bindings)
    return idx
