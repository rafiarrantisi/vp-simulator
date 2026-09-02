"""STEP 5 — lint all v3 case families/variants via the automated content linter."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.lint import lint_variant


def main() -> int:
    reg = CaseRegistry.from_dir()
    n_errors = 0
    for fid in sorted(reg.families):
        fam = reg.families[fid]
        vids = reg.variants_for_family(fid)
        if len(vids) < 3:
            print(f"[warning] family {fid}: {len(vids)} variants (expect >=3)")
        for v in vids:
            rep = lint_variant(v)
            for iss in rep.issues:
                print(iss)
            if rep.errors:
                n_errors += len(rep.errors)
    print(f"\nLinted {len(reg.variants)} variants · {n_errors} error(s).")
    return 1 if n_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())