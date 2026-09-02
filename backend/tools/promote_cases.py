"""STEP-9 final — human-gated promotion of cases (Ker/Arran authorized).

Runner for the §13 promotion rule through a NAMED human reviewer. It:
  * validates the requested target via qa.promotion_allowed (human gate —
    reaching clinically_reviewed/pilot_verified/published REQUIRES a named
    human reviewer record; the tool refuses a blank/self-serving review);
  * writes a human review record (reviewer name/role/date/notes) to
    content/v3/human_review_records.json;
  * updates the variant YAML `status:` to the promoted state.

Honesty guard: `clinically_reviewed` semantically means "a clinical
doctor/educator reviewed the medicine". If the reviewer role does not claim
clinical credentials, the record must say so, and the final audit will keep the
clinical-educator comparison as a KNOWN LIMITATION — the tool never fabricates a
doctor sign-off that did not happen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.qa import ReviewRecord, promotion_allowed
from pipeline.case_v3.vocab import HUMAN_REVIEWED_STATES

VARIANTS = Path(__file__).resolve().parents[1].parent / "content" / "v3" / "variants"
RECORDS = Path(__file__).resolve().parents[1].parent / "content" / "v3" / "human_review_records.json"


def _set_status_yaml(vid: str, target: str) -> None:
    f = VARIANTS / f"{vid}.yaml"
    if not f.exists():
        raise SystemExit(f"variant file not found: {f}")
    txt = f.read_text(encoding="utf-8")
    new, n = re.subn(r"(?m)^status:\s*.*$", f"status: {target}", txt, count=1)
    if n != 1:
        raise SystemExit(f"could not rewrite status in {vid}.yaml")
    f.write_text(new, encoding="utf-8")


def load_records() -> list[dict]:
    if RECORDS.exists():
        return json.loads(RECORDS.read_text(encoding="utf-8"))
    return []


def save_records(records: list[dict]) -> None:
    RECORDS.parent.mkdir(parents=True, exist_ok=True)
    RECORDS.write_text(json.dumps(records, indent=2), encoding="utf-8")


def promote(ids: list[str], *, target: str, reviewer: str, role: str,
            notes: str = "") -> dict:
    reg = CaseRegistry.from_dir()
    records = load_records()
    promoted, refused = [], []

    for vid in ids:
        v = reg.variants.get(vid)
        if v is None:
            refused.append({"id": vid, "reason": "not found"})
            continue
        rec = ReviewRecord(reviewer_name=reviewer, reviewer_role=role,
                           date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                           notes=notes)
        ok, why = promotion_allowed(v, target, human_record=rec)
        if not ok:
            refused.append({"id": vid, "reason": why})
            continue
        _set_status_yaml(vid, target)
        records.append({
            "variant_id": vid, "from": v.status, "to": target,
            "reviewer": reviewer, "role": role,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "notes": notes, "clinical_educator_signed": "clinician" in role.lower(),
        })
        promoted.append(vid)

    save_records(records)
    return {"promoted": promoted, "refused": refused,
            "target": target, "reviewer": reviewer}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="+", required=True,
                    help="variant ids (or 'all' for every registry variant)")
    ap.add_argument("--target", required=True,
                    choices=["ai_generated", "research_complete", "in_review",
                             "clinically_reviewed", "pilot_verified", "published"])
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--notes", default="")
    a = ap.parse_args()
    reg = CaseRegistry.from_dir()
    ids = list(reg.variants.keys()) if a.ids == ["all"] else a.ids
    res = promote(ids, target=a.target, reviewer=a.reviewer, role=a.role, notes=a.notes)
    print(json.dumps(res, indent=2))