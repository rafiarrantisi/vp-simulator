"""Add presentation_id (Indonesian) to case files that lack it.

Qora's catalogue cards render the case `presentation` in English while the
first_impression description is already Indonesian — inconsistent for the
Indonesia-first market. This tool backfills `presentation_id` (a natural,
lay-language Indonesian translation of the presentation line) via the backend
LLM client (OpenRouter deepseek-v4-flash — NEVER opencode-go).

Usage (from backend/):
  python -m tools.add_presentation_id [--ids a,b,c] [--dry-run]
  # --ids absent → processes every case file missing presentation_id
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from app.config import get_settings
from app.rag.llm import get_llm_client
from pipeline.case_v2 import parse_case_v2, lint

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _REPO_ROOT / "content" / "cases"

_SYSTEM = (
    "You are a clinical education content editor for Qora, an Indonesian-first "
    "virtual-patient anamnesis trainer for medical students. You localize case "
    "titles into natural, lay-friendly Bahasa Indonesia."
)

_PROMPT = """Case: {case_id}
- Specialty: {specialty}
- Target condition: {target_condition}
- Presentation (current English title): {presentation}
- Chief complaint (patient's own words): {chief_complaint}

Write a presentation_id: the SAME clinical meaning as the English presentation,
as a natural Bahasa Indonesia phrase a medical student would recognise. Rules:
1. Lay-friendly but clinically recognisable (e.g. "Demam, sakit kepala, dan
   nyeri badan selama 3 hari").
2. Keep body-part/age cues when present (child/bayi/anak, elderly/lansia).
3. No quotation marks inside the string; no diagnosis name (it must stay a
   presentation, not a diagnosis).
4. 4-14 words.

Return ONLY a JSON object with exactly one key:
- "presentation_id": the Indonesian string

Example:
{{"presentation_id": "Demam, sakit kepala, dan nyeri badan selama 3 hari"}}"""


def _parse_json(raw: str) -> dict | None:
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        raw = m.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _sanitize(s: str) -> str:
    return re.sub(r'"', "'", " ".join(s.split())).strip()


def _add_fields(path: Path, client, model: str, dry_run: bool) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    if "presentation_id:" in text:
        return True, "already has presentation_id (skipped)"

    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return False, "no frontmatter"
    head = fm.group(1)
    fields = {
        k: (v.strip('"') if v else "")
        for k, v in re.findall(r"^(\w+):\s*(.*)$", head, re.M)
    }
    case_id = fields.get("id", path.stem)
    presentation = fields.get("presentation", "")
    if not presentation:
        return False, "no presentation line"

    prompt = _PROMPT.format(
        case_id=case_id,
        specialty=fields.get("specialty", "?"),
        target_condition=fields.get("target_condition", "?"),
        presentation=presentation,
        chief_complaint=fields.get("chief_complaint", "?"),
    )

    out = None
    for attempt in range(3):
        try:
            raw = client.generate(_SYSTEM, [{"role": "user", "content": prompt}],
                                  model=model, max_tokens=512, temperature=0.3)
        except RuntimeError:
            raw = ""
        out = _parse_json(raw) if raw else None
        if out and out.get("presentation_id"):
            break
        time.sleep(2)
    if not out or not out.get("presentation_id"):
        return False, "LLM returned no usable JSON after 3 attempts"
    pid = _sanitize(out["presentation_id"])
    if not pid:
        return False, "empty after sanitize"

    def _insert(m: re.Match) -> str:
        return f"{m.group(0)}\npresentation_id: \"{pid}\""

    new_text, n = re.subn(r"^(presentation: .*)$", _insert, text, count=1, flags=re.M)
    if n != 1:
        return False, "presentation line not found — aborting"

    if dry_run:
        return True, f"[dry-run] would insert presentation_id for {case_id}"

    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    try:
        case = parse_case_v2(tmp)
        res = lint(case)
        if not res.ok:
            return False, f"lint failed: {res.errors[:2]}"
    finally:
        tmp.unlink(missing_ok=True)
    path.write_text(new_text, encoding="utf-8")
    return True, f"wrote presentation_id for {case_id}"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Backfill presentation_id fields")
    ap.add_argument("--ids", help="comma-separated case ids to process")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    s = get_settings()
    client = get_llm_client()
    model = s.llm_model

    files = sorted(_CASES_DIR.glob("*.md"))
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
        files = [f for f in files if f.stem in wanted]

    ok = fail = 0
    for fp in files:
        done, msg = _add_fields(fp, client, model, args.dry_run)
        print(f"  {'✓' if done else '✗'} {fp.stem}: {msg}", flush=True)
        ok += done
        fail += not done

    print(f"\nProcessed {ok} ok; {fail} failed." + (" [dry-run, nothing written]" if args.dry_run else ""))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
