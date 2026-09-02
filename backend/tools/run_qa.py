"""STEP 8 — QA gate: run the full automated clinical-QA battery over case_v3.

  * automated content linter (STEP 5 §10)  → lint_variant
  * canonical-truth consistency (§4)        → consistency_issues
  * scoring fixtures (§5)                   → scoring_fixture_issues
  * patient red-team (§3)                   → run_red_team
  * source QA (§7)                          → source_issues
  * promotion gate (§13): reports which cases are eligible for human review;
    NEVER self-promotes.

Outputs a per-variant QA report (JSON+MD) + a promotion-eligible summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.lint import lint_variant
from pipeline.case_v3.qa import consistency_issues, scoring_fixture_issues
from pipeline.case_v3.redteam import run_red_team
from pipeline.case_v3.sourceqa import source_issues


def _human_reviewed_ids() -> set[str]:
    """Named-human-review authorisations (from promote_cases.py records)."""
    p = Path(__file__).resolve().parents[1].parent / "content" / "v3" / "human_review_records.json"
    if p.exists():
        try:
            return {r.get("variant_id") for r in json.loads(p.read_text(encoding="utf-8")) if r.get("variant_id")}
        except Exception:  # noqa: BLE001
            return set()
    return set()


def run_all(reg: CaseRegistry) -> dict:
    report = {"variants": {}, "summary": {"total": 0, "errors": 0, "warnings": 0}}
    auth = _human_reviewed_ids()
    for v in reg.variants.values():
        checks = {
            "lint": [str(x) for x in lint_variant(v, authorized_reviewed_ids=auth).issues],
            "consistency": [str(x) for x in consistency_issues(v)],
            "scoring_fixtures": [str(x) for x in scoring_fixture_issues(v)],
            "source": [str(x) for x in source_issues(v)],
            "red_team": [__str__c for __str__c in run_red_team(v) if not __str__c.ok],
        }
        errors = sum(1 for k in ("lint", "consistency", "scoring_fixtures", "source")
                     for s in checks[k] if s.startswith("[error]"))
        report["variants"][v.id] = {
            "family_id": v.family_id,
            "status": v.status,
            "errors": errors,
            "checks": checks,
            "passes": errors == 0,
        }
        report["summary"]["total"] += 1
        report["summary"]["errors"] += errors
    # promotion-eligible summary (only reachable states; human still gated on eligibility)
    report["summary"]["eligible_for_clinical_review"] = [
        v.id for v in reg.variants.values()
        if report["variants"][v.id]["passes"] and v.status in ("in_review", "research_complete", "ai_generated")
    ]
    return report


def render_md(report: dict) -> str:
    lines = ["# STEP 8 — Clinical QA gate report", ""]
    s = report["summary"]
    lines.append(f"- Variants: {s['total']} | errors: {s['errors']} | eligible for human review: {len(s['eligible_for_clinical_review'])}")
    lines.append("")
    lines.append("**NOTE:** Passing this technical gate does NOT make a case clinically verified. "
                 "clinically_reviewed / pilot_verified require an authorised human reviewer "
                 "(STEP 8 §6, §12-13).")
    lines.append("")
    for vid, v in report["variants"].items():
        flag = "PASS" if v["passes"] else "FAIL"
        lines.append(f"## {vid} — {flag} (status={v['status']})")
        for k, items in v["checks"].items():
            if items:
                lines.append(f"- **{k}**:")
                for it in items:
                    lines.append(f"    - {it}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="write MD report (+ .json) here")
    a = ap.parse_args()
    out = a.out
    reg = CaseRegistry.from_dir()
    rep = run_all(reg)
    print(json.dumps({"summary": rep["summary"]}, indent=2))
    if out:
        op = Path(out)
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(render_md(rep), encoding="utf-8")
        Path(str(op).replace(".md", ".json")).write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print("report ->", op)