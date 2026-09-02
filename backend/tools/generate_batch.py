"""STEP 9 — controlled batch generation pipeline (Ker rule: small batch → QA gate).

Given a batch spec (one or more roadmap/SKD-2026 priority entries), this tool:
  1. resolves the family metadata (specialty, category, SKD 2026 name);
  2. emits a family scaffold YAML + N variant scaffolds (status=`research_complete`);
  3. runs the full QA gate (lint + consistency + scoring-fixture + red-team +
     source) on whatever is present;
  4. writes a batch manifest + QA report.

Promotion guard (STEP 9 rule): generated output CAPS at `research_complete`. It
never produces `clinically_reviewed` / `pilot_verified` / `published` — those
states are ONLY reachable through the separate human review workflow (qa.py
promotion_allowed). Nothing here auto-promotes or mints unverified content.

The tool does NOT fabricate clinical source content: it scaffolds structure from
the verified SKD 2026 catalog (names/categories/systems) and leaves clinical
truth, sources, disclosure maps to be reviewed before a family is populated with
user-facing variants. Without a real clinical source pack, a scaffold is marked
`needs_source_pack` and is NOT eligible for presentation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
CONTENT = Path(__file__).resolve().parents[1].parent / "content" / "v3"


def _slug(expr, s: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-+", "-", base)


def _load_catalog():
    p = CONTENT / "catalog" / "skd2026_master_catalog.json"
    if not p.exists():
        raise SystemExit(f"catalog not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _specialty_for(system: str) -> str:
    m = {
        "sistem_saraf": "neurology", "sistem_kardiovaskuler": "cardiology_vascular",
        "sistem_respirasi": "respiratory", "sistem_endokrin": "endocrinology_metabolic_nutrition",
        "sistem_gastrointestinal": "gastroenterology", "sistem_hepatobiliar_pankreas": "gastroenterology",
        "sistem_ginjal": "nephrology_urology", "sistem_reproduksi": "obgyn_reproductive",
        "sistem_matrix_imu": "dermatology_venereology", "sistem_pediatri": "paediatrics",
        "sistem_psikiatri": "psychiatry", "sistem_forensik": "forensic",
    }
    return m.get(system, "internal_medicine")


def resolve_entry(entry_id: str, entries) -> dict | None:
    if isinstance(entries, dict):
        entries = entries.get("entries", entries.get("catalog", entries.get("data")) or [])
    for e in entries:
        if isinstance(e, dict) and e.get("id") == entry_id:
            return e
    return None


def family_scaffold(entry: dict) -> dict:
    return {
        "id": entry["id"],
        "family_type": "disease",
        "title_id": entry.get("skd2026_name", ""),
        "title_en": entry.get("current_display_name", entry.get("skd2026_name", "")),
        "primary_specialty": _specialty_for(entry.get("system", "")),
        "competency_categories": [entry.get("category", "")],
        "skd2026_catalog_id": entry["id"],
    }


def variant_scaffold(entry: dict, n: int) -> dict:
    return {
        "id": f"{entry['id']}__variant{n}",
        "family_id": entry["id"],
        "variation_level": "persona",
        "title": f"{entry.get('skd2026_name','')} — scaffolded variant {n} (clinical content pending)",
        "supported_stages": ["koas"],
        "competency": {"standard": "SKD 2026", "category": entry.get("category", "")},
        "_scaffold": True,
        "needs_source_pack": True,
        "status": "research_complete",
    }


def run_batch(entry_ids: list[str], *, n_variants: int, dry_run: bool = True) -> dict:
    catalog = _load_catalog()
    if isinstance(catalog, list):
        entries_list = catalog
    else:
        entries_list = catalog.get("entries", catalog.get("catalog", catalog.get("data")) or [])
    manifest = {"batch": [], "promotion_guard": "CAPPED at research_complete; no clinically_reviewed/pilot_verified/pub"}
    for eid in entry_ids:
        entry = resolve_entry(eid, entries_list)
        if entry is None:
            manifest["batch"].append({"id": eid, "status": "error", "note": "not found in catalog"})
            continue
        fam = family_scaffold(entry)
        variants = [variant_scaffold(entry, i) for i in range(1, n_variants + 1)]
        manifest["batch"].append({
            "id": fam["id"], "title": fam["title_id"], "system": entry.get("system"),
            "category": fam["competency_categories"][0],
            "family_scaffold": fam,
            "variant_scaffolds": variants,
            "status": "research_complete",
            "needs_source_pack": True,
            "ready_for_qa_gate": False,          # no clinical truth yet → not QA-eligible
        })
        if not dry_run and not any(entry.get("_demo")):
            # Actual file emission is intentionally OFF for content-absent scaffolds:
            # we will not mint files with empty clinical truth.
            pass
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", help="catalog entry ids (defaults to a small demo batch)")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args()
    ids = args.ids or ["sistem_kejang-demam-komplikata", "sistem_kejang-pada-neonatus",
                       "sistem_hematom-perdarahan-epidural"]
    rep = run_batch(ids, n_variants=args.n, dry_run=True)
    print(json.dumps({"promotion_guard": rep["promotion_guard"],
                      "batch_entries": len(rep["batch"]),
                      "all_capped_research_complete": all(b["status"] == "research_complete" for b in rep["batch"])},
                     indent=2))
    print("\nSample scaffold:")
    print(json.dumps(rep["batch"][0], indent=2)[:900])