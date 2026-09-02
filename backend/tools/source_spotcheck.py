"""STEP 9 §7/§11 — per-batch source spot-check workflow (HUMAN, not fake).

Turns a batch's cited sources into a spot-check manifest a doctor/educator must
verify in person:
  * URL exists / resolves (best-effort HEAD/GET flagged, but final = human)
  * source is current or explicitly justified
  * the guideline/PNPK audibly SUPPORTS the management claim the variant makes

This is a checklist generator + tracker — it NEVER auto-blesses a source. Each
batch's manifest must be signed by a named human reviewer before promotion.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry


def spotcheck(variant_ids: list[str], *, out: str | None = None) -> dict:
    reg = CaseRegistry.from_dir()
    items = []
    for vid in variant_ids:
        v = reg.variants.get(vid)
        if v is None:
            items.append({"variant": vid, "status": "error", "note": "not found"})
            continue
        for s in v.sources:
            items.append({
                "variant": vid,
                "source_title": getattr(s, "title", ""),
                "authority": getattr(s, "authority", ""),
                "kind": getattr(s, "kind", ""),
                "year": getattr(s, "year", ""),
                "url": getattr(s, "url", ""),
                # human must set these (never auto-filled)
                "url_resolves": None,
                "current_or_justified": None,
                "supports_management_claim": None,
                "reviewer": "",
                "review_date": "",
                "signed": False,
            })
    manifest = {
        "batch": variant_ids,
        "instruction": "Each row MUST be verified by a named doctor/clinical "
                       "educator. Left None/False = not verified. Nothing is "
                       "promoted to clinically_reviewed until this manifest is "
                       "fully signed.",
        "items": items,
    }
    if out:
        Path(out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = spotcheck(a.ids, out=a.out)
    unsigned = sum(1 for i in m["items"] if not i["signed"])
    print(json.dumps({"sources_to_verify": len(m["items"]), "unsigned": unsigned,
                      "manifest": a.out}, indent=2))