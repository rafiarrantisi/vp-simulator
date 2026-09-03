"""FASE 4 — deterministic prioritized expansion roadmap (no LLM, no fabrication).

Reads ONLY verified artifacts (SKD 2026 master catalog, canonical entities,
roadmap priority queue) + the existing families dir, and produces
`content/v3/roadmap_expansion.json`: tiered, batched, family-first execution
plan. Rules are transparent and printed with the output so a human reviewer
can audit every assignment. Nothing here authors clinical truth, promotes
content, or touches runtime.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
CONTENT = ROOT / "content" / "v3"

# Canonical entities already behind the live bank (conservative keyword map;
# the emitted `covered` list names every match for human audit).
COVERED_RULES = [
    ("fam_dengue", [r"dengue", r"demam berdarah", r"\bdhf\b", r"syok dengue"]),
    ("fam_uti", [r"saluran kemih", r"\buti\b", r"sistitis", r"uretritis"]),
    ("fam_hypertension", [r"hipertensi", r"tekanan darah tinggi", r"krisis hipertensi"]),
    ("fam_pyelonephritis", [r"pielonefritis"]),
    ("fam_fever_child", []),  # presentation family — covers no disease entity
]

# Planned depth axes for the existing bank (Batch B briefs — axes only,
# never clinical truth; a variant is minted only for a meaningful clinical
# difference, never for name/job/style).
BATCH_B_AXES = {
    "fam_dengue": ["severity (mild/warning/severe) — have 3, add convalescent + comorbid"],
    "fam_uti": ["population (child/adult/male/pregnant) + complicated vs uncomplicated"],
    "fam_hypertension": ["chronology (new/chronic) + urgency + comorbidity (diabetes/CKD)"],
    "fam_pyelonephritis": ["pregnancy + obstruction + sepsis axes"],
    "fam_fever_child": ["age band (neonate/infant/child) + referral-threshold variants"],
}


def _load(name):
    return json.loads((CONTENT / "catalog" / name).read_text(encoding="utf-8"))


def covered_entity_ids(entities):
    covered, audit = set(), {}
    for fid, patterns in COVERED_RULES:
        hits = []
        for e in entities:
            name = (e.get("display_name") or "").lower()
            if any(re.search(p, name) for p in patterns):
                covered.add(e["id"])
                hits.append(e["id"])
        audit[fid] = sorted(hits)
    return covered, audit


def tier_of(entity, score_by_entry):
    scores = [score_by_entry.get(o.get("entry_id"), 0) for o in entity.get("source_occurrences", [])]
    top = max(scores) if scores else 0
    cats = set(entity.get("categories") or [entity.get("primary_category", "")])
    if "initial_management_and_referral" in cats and top >= 1.2:
        return "high_risk"
    if ("tuntas" in cats and top >= 1.0) or top >= 1.2:
        return "core"
    if top >= 0.8:
        return "standard"
    return "long_tail"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-a-size", type=int, default=12)
    ap.add_argument("--min-systems", type=int, default=8)
    ap.add_argument("--out", default=str(CONTENT / "roadmap_expansion.json"))
    args = ap.parse_args()

    catalog = _load("skd2026_master_catalog.json")
    entries = catalog if isinstance(catalog, list) else catalog.get("entries", [])
    canon = _load("canonical_entities.json")["canonical_entities"]
    roadmap = _load("roadmap.json")
    score_by_entry = {q["id"]: q.get("priority_score", 0) for q in roadmap.get("priority_queue", [])}
    in_presentation = set()
    for pf in roadmap.get("presentation_families", []):
        in_presentation.update(pf.get("entry_ids", []))

    covered, cover_audit = covered_entity_ids(canon)
    tiers: dict[str, list[str]] = {"high_risk": [], "core": [], "standard": [], "long_tail": []}
    ent_by_id = {}
    for e in canon:
        if e["id"] in covered:
            continue
        ent_by_id[e["id"]] = e
        tiers[tier_of(e, score_by_entry)].append(e["id"])

    # Batch A: breadth — round-robin across systems over high_risk+core.
    # Forensic/medikolegal rows are catalog artifacts for a bedside trainer
    # (some are cross-reference notes, not diseases) — excluded by rule.
    pool = [ent_by_id[i] for i in tiers["high_risk"] + tiers["core"]
            if "forensik" not in ((ent_by_id[i].get("systems") or [""])[0])]
    by_system: dict[str, list[dict]] = {}
    for e in pool:
        sys0 = (e.get("systems") or ["unknown"])[0]
        by_system.setdefault(sys0, []).append(e)
    for lst in by_system.values():
        lst.sort(key=lambda e: (-max([score_by_entry.get(o.get("entry_id"), 0)
                                      for o in e.get("source_occurrences", [])] or [0]), e["id"]))
    batch_a: list[str] = []
    systems_used: set[str] = set()
    while len(batch_a) < args.batch_a_size and any(by_system.values()):
        for sys0 in sorted(by_system):
            if len(batch_a) >= args.batch_a_size or not by_system[sys0]:
                continue
            batch_a.append(by_system[sys0].pop(0)["main_entry_id"])
            systems_used.add(sys0)
    batch_c = sorted(set(ent_by_id) - set(
        e for t in ("high_risk", "core") for e in tiers[t]))

    out = {
        "version": "1.0",
        "generated_from": {"catalog_entries": len(entries),
                           "canonical_entities": len(canon),
                           "existing_families": 5},
        "rules": {
            "tiers": "high_risk = initial_management_and_referral + score 1.2; "
                     "core = tuntas + score>=1.0 (or score 1.2); "
                     "standard = score>=0.8; else long_tail",
            "batch_a": f"round-robin across systems over high_risk+core, n={args.batch_a_size}",
            "batch_b": "depth axes for the 5 existing families (briefs only)",
            "batch_c": "all remaining uncovered entities (long-tail execution, human-gated)",
            "variant_discipline": "variant only for meaningful clinical difference "
                                  "(severity/chronology/comorbidity/exposure/red-flag/setting/"
                                  "complication/pathway/management); never name/job/style",
            "promotion": "scaffolds cap at research_complete + needs_source_pack; "
                         "human clinical gate required beyond (governance.assert_ai_can_promote)",
        },
        "covered_by_existing_bank": cover_audit,
        "tiers": {k: sorted(v) for k, v in tiers.items()},
        "tier_counts": {k: len(v) for k, v in tiers.items()},
        "batches": {
            "A_breadth": batch_a,
            "A_systems": sorted(systems_used),
            "B_depth_briefs": BATCH_B_AXES,
            "C_long_tail_count": len([i for i in batch_c if i in tiers["long_tail"]]),
            "C_standard_count": len([i for i in batch_c if i in tiers["standard"]]),
        },
        "caveats": [
            "Existing variants carry empty competency.system — system coverage here "
            "comes from the catalog, not the live bank.",
            "Covered matching is keyword-conservative; review `covered_by_existing_bank`.",
            "System->specialty display mapping is intentionally NOT baked in "
            "(catalog system names predate the UI vocab).",
        ],
    }
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"tiers: {out['tier_counts']} | Batch A: {len(batch_a)} over {len(systems_used)} systems")
    print(f"Batch A systems: {sorted(systems_used)}")
    if len(systems_used) < args.min_systems:
        print(f"WARNING: systems {len(systems_used)} < min {args.min_systems}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
