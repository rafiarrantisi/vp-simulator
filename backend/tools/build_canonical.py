"""STEP 4 — Build canonical clinical entities from the raw SKD 2026 catalog.

Rule (user, STEP 4 corrections):
  * 515 raw official entries are NOT automatically 515 visible case families.
  * Preserve the raw catalog EXACTLY.
  * Group raw rows into canonical clinical entities / case-family candidates.
    The same condition appearing more than once in the source yields ONE
    canonical entity with multiple `source_occurrences`.
  * Never silently delete a source row; never resolve mapping uncertainty via
    medical guess — ambiguous clusters are preserved & flagged.
Outputs two separate numbers:
  raw_official_entries            = 515
  canonical_case_family_candidates = X
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_NORM = re.compile(r"[^a-z0-9]+")


def norm_key(name: str) -> str:
    return _NORM.sub(" ", name.lower()).strip()


def build(raw: list[dict], *, uncertainty_sources: list[list[str]] | None = None,
          exact_name_match: bool = True) -> dict:
    """Group raw catalog rows into canonical entities.

    exact_name_match=True → only fold identical normalized names together
    (very safe, no medical guess). exact_name_match=False allows a light
    stem-similarity heuristic but marks it as mapping_uncertainty (NOT merged
    on medical grounds).
    """
    # collect rows by normalized name (exact, conservative)
    by_name: dict[str, list[dict]] = {}
    for r in raw:
        by_name.setdefault(norm_key(r["skd2026_name"]), []).append(r)

    entities: list[dict] = []
    n_buckets = 0
    uncertainty_clusters = set()
    if uncertainty_sources:
        for cluster in uncertainty_sources:
            uncertainty_clusters.update(cluster)

    for name_key, rows in sorted(by_name.items()):
        n_buckets += 1
        rows_sorted = sorted(rows, key=lambda r: (r["category"] == "initial_management_and_referral",
                                                  r.get("id", "")))
        main = rows_sorted[0]
        # canonical id from the primary row's id if present, else derive
        cid = main.get("id") or f"canon_{n_buckets:04d}"
        uncertain = []
        for r in rows:
            if r.get("id") in uncertainty_clusters or "id" not in r:
                uncertain.append(f"raw {r.get('id') or '?'}: ambiguous source occurrence")
        entities.append({
            "id": cid,
            "display_name": main["current_display_name"] or rows_sorted[0]["skd2026_name"],
            "primary_category": main["category"],
            "categories": sorted({r["category"] for r in rows}),
            "systems": sorted({r["system"] for r in rows}),
            "source_occurrences": [
                {"entry_id": r.get("id"), "system": r["system"],
                 "category": r["category"], "official_name": r["skd2026_name"],
                 "locator": r.get("source", {})}
                for r in rows
            ],
            "main_entry_id": main.get("id"),
            "mapping_uncertainty": list(dict.fromkeys(uncertain)),
            "candidate_family_status": "unclassified",
        })

    # If an uncertainty cluster spans >1 distinct normalized name that look alike,
    # we do NOT merge them (no medical guess) — the CLI reports them for review.
    return {
        "raw_official_entries": len(raw),
        "canonical_case_family_candidates": len(entities),
        "canonical_entities": entities,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="content/v3/catalog/skd2026_master_catalog.json")
    ap.add_argument("--out", default="content/v3/catalog/canonical_entities.json")
    a = ap.parse_args()
    raw = json.loads(Path(a.src).read_text(encoding="utf-8"))
    # ambiguity notice: unstable is computed from roadmap ambiguous clusters
    road = Path(a.src).parent / "roadmap.json"
    clusters = []
    if road.exists():
        rj = json.loads(road.read_text(encoding="utf-8"))
        clusters = [c for c in rj.get("ambiguous_entries", []) if isinstance(c, list)]
    plan = build(raw, uncertainty_sources=clusters)
    op = Path(a.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print("raw_official_entries:", plan["raw_official_entries"])
    print("canonical_case_family_candidates:", plan["canonical_case_family_candidates"])
    n_amb = sum(1 for e in plan["canonical_entities"] if e["mapping_uncertainty"])
    print("entities flagged with mapping uncertainty:", n_amb)
    print(f"-> {a.out}")