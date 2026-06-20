"""Authoring CLI (BUILD_PLAN_pivot_v4 §5.3) — draft schema-v2 cases via the
author model, self-correct against the linter, and land them in `in_review`.

  # single case
  python -m tools.author_case --specialty internal_medicine --slug gout \
      --presentation "Acute joint pain" --condition "Gout" --difficulty 2 --mode anamnesis

  # batch from the backlog CSV (columns: specialty,slug,presentation,target_condition,difficulty,mode)
  python -m tools.author_case --batch ../content/scaffold/cases_backlog.csv

Requires a real LLM_API_KEY (+ optional AUTHOR_MODEL). StubLLM cannot author
clinical content. Each accepted case is written to content/cases/<id>.md with
status: in_review for light human review before publishing.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from pipeline import author
from pipeline.case_v2 import make_case_id

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _REPO_ROOT / "content" / "cases"
_MAX_ATTEMPTS = 2


def _author_one(spec: dict) -> tuple[bool, str]:
    """Draft + lint-correct one case. Returns (ok, message)."""
    specialty = spec["specialty"].strip()
    mode = (spec.get("mode") or "anamnesis").strip()
    bad = author.validate_inputs(specialty, mode)
    if bad:
        return False, "; ".join(bad)

    case_id = make_case_id(specialty, spec["slug"], int(spec.get("n", 1) or 1))
    difficulty = int(spec.get("difficulty", 2) or 2)
    errors: list[str] | None = None
    markdown = ""
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        markdown = author.draft_case(
            case_id, specialty, spec["presentation"], spec["target_condition"],
            difficulty, mode, spec.get("reference_text", ""), fix_errors=errors,
        )
        _case, res = author.lint_markdown(markdown)
        if res.ok:
            out = _CASES_DIR / f"{case_id}.md"
            out.write_text(markdown + "\n", encoding="utf-8")
            warn = f"  ({len(res.warnings)} warning(s))" if res.warnings else ""
            return True, f"wrote {out.relative_to(_REPO_ROOT)} [attempt {attempt}]{warn}"
        errors = res.errors
    return False, f"lint failed after {_MAX_ATTEMPTS} attempts: {errors}"


def _rows(args) -> list[dict]:
    if args.batch:
        with open(args.batch, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    ref = ""
    if args.reference:
        ref = Path(args.reference).read_text(encoding="utf-8")
    return [{
        "specialty": args.specialty, "slug": args.slug,
        "presentation": args.presentation, "target_condition": args.condition,
        "difficulty": args.difficulty, "mode": args.mode, "reference_text": ref,
    }]


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Schema-v2 case author")
    ap.add_argument("--batch", help="CSV backlog of cases to draft")
    ap.add_argument("--specialty")
    ap.add_argument("--slug")
    ap.add_argument("--presentation")
    ap.add_argument("--condition")
    ap.add_argument("--difficulty", type=int, default=2)
    ap.add_argument("--mode", default="anamnesis")
    ap.add_argument("--reference", help="path to guideline excerpt to ground facts")
    args = ap.parse_args(argv)

    if not args.batch and not (args.specialty and args.slug and args.presentation and args.condition):
        ap.error("provide --batch, or --specialty/--slug/--presentation/--condition")

    _CASES_DIR.mkdir(parents=True, exist_ok=True)
    rows = _rows(args)
    ok = fail = 0
    for spec in rows:
        try:
            done, msg = _author_one(spec)
        except RuntimeError as e:  # e.g. StubLLM — abort the whole batch cleanly
            print(f"  ✗ {spec.get('slug', '?')}: {e}")
            return 1
        except Exception as e:  # noqa: BLE001 — one bad row must not kill the batch
            done, msg = False, f"{type(e).__name__}: {e}"
        mark = "✓" if done else "✗"
        print(f"  {mark} {spec.get('specialty','?')}/{spec.get('slug','?')}: {msg}")
        ok += done
        fail += not done

    print(f"\nAuthored {ok} case(s); {fail} failed. New cases are status=in_review "
          f"— review then run the linter before publishing.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
