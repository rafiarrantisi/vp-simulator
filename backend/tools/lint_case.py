"""Case linter CLI (BUILD_PLAN_pivot_v4 §5.5) — quality gate for schema v2.

  python -m tools.lint_case --all                 # lint content/cases/*.md
  python -m tools.lint_case path/to/case.md ...    # lint specific files
  python -m tools.lint_case --all --strict         # warnings also fail

Exit codes: 0 = all clean (no errors); 1 = at least one case has errors.
Designed to run in CI and inside the authoring pipeline (Phase 2).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.case_v2 import lint, parse_case_v2

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _REPO_ROOT / "content" / "cases"


def _files(args) -> list[Path]:
    if args.paths:
        return [Path(p) for p in args.paths]
    return sorted(_CASES_DIR.glob("*.md"))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Schema-v2 case linter")
    ap.add_argument("paths", nargs="*", help="case files (default: --all)")
    ap.add_argument("--all", action="store_true", help="lint all cases in content/cases/")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args(argv)

    if not args.paths and not args.all:
        ap.error("pass case file paths or --all")

    files = _files(args)
    if not files:
        print(f"No case files found (looked in {_CASES_DIR}).")
        return 1

    total_err = total_warn = failed = 0
    for fp in files:
        try:
            case = parse_case_v2(fp)
            res = lint(case)
        except Exception as e:  # noqa: BLE001 — a broken file must not abort the batch
            print(f"  ✗ {fp.name}: PARSE CRASH — {type(e).__name__}: {e}")
            failed += 1
            continue
        total_err += len(res.errors)
        total_warn += len(res.warnings)
        bad = res.errors or (args.strict and res.warnings)
        mark = "✗" if bad else "✓"
        print(f"  {mark} {res.case_id} ({fp.name})")
        for e in res.errors:
            print(f"      ERROR: {e}")
        for w in res.warnings:
            print(f"      warn:  {w}")
        if bad:
            failed += 1

    print(
        f"\nLinted {len(files)} case(s): {failed} failed · "
        f"{total_err} error(s) · {total_warn} warning(s)."
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
