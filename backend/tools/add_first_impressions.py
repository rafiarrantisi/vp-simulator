"""Add first_impression + first_impression_id to case files that lack them.

Qora's case cards render `first_impression_id || first_impression ||
chief_complaint`, but the author pipeline does not emit first_impression, so
newly generated cases fall back to the chief complaint. This tool backfills
both fields (EN + ID, vivid visual observation, no diagnosis) via the backend
LLM client (OpenRouter deepseek-v4-flash — NEVER opencode-go).

Usage (from backend/):
  python -m tools.add_first_impressions [--ids a,b,c] [--dry-run]
  # --ids absent → processes every case file missing first_impression
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
    "virtual-patient anamnesis trainer for medical students. You write crisp, "
    "vivid, realistic first impressions shown on case cards and the session "
    "prep screen."
)

_PROMPT = """Case file: {case_id}
- Specialty: {specialty}
- Presentation: {presentation}
- Target condition: {target_condition}
- Difficulty (1=pre-clinical, 2=clinical, 3=residency): {difficulty}
- Chief complaint (patient's own words): {chief_complaint}
- Patient identity (from persona): {identity}

Write a first_impression: ONE brief (12-22 words) visual observation a student
would make walking into the room BEFORE asking anything — demeanour, posture,
facial expression, visible physical signs. Requirements:
1. Must match the condition and be clinically consistent (e.g. febrile patient
   appears flushed and restless, not calm and pink).
2. MUST NOT reveal the diagnosis or list detailed symptoms.
3. If the case is paediatric (0-18), describe the CHILD's appearance and the
   parent's demeanour if it adds realism.
4. No quotation marks inside the strings; plain ASCII apostrophes allowed.

Return ONLY a JSON object with exactly two keys:
- "first_impression": English version
- "first_impression_id": natural Indonesian version, starting with "Pasien tampak ..." (or "Anak tampak ..." / "Bayi tampak ..." for paediatrics)

Example:
{{"first_impression": "Patient appears anxious, clutching chest, pale and diaphoretic.", "first_impression_id": "Pasien tampak cemas, memegangi dada, pucat dan berkeringat dingin."}}"""


def _frontmatter_identity(text: str, case_id: str) -> str:
    """Grab the first ~300 chars of the ## Identity section for context."""
    m = re.search(r"## Identity\s*\n(.*?)(?=\n## )", text, re.S)
    if not m:
        return "(not found)"
    return " ".join(m.group(1).split())[:300]


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
    if "first_impression:" in text:
        return True, "already has first_impression (skipped)"

    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return False, "no frontmatter"
    head = fm.group(1)
    fields = {
        k: (v.strip('"') if v else "")
        for k, v in re.findall(r"^(\w+):\s*(.*)$", head, re.M)
    }
    case_id = fields.get("id", path.stem)
    body = text[fm.end():]

    identity = _frontmatter_identity(body, case_id)
    prompt = _PROMPT.format(
        case_id=case_id,
        specialty=fields.get("specialty", "?"),
        presentation=fields.get("presentation", "?"),
        target_condition=fields.get("target_condition", "?"),
        difficulty=fields.get("difficulty", "?"),
        chief_complaint=fields.get("chief_complaint", "?"),
        identity=identity,
    )

    out = None
    for attempt in range(3):
        try:
            raw = client.generate(_SYSTEM, [{"role": "user", "content": prompt}],
                                  model=model, max_tokens=200, temperature=0.3)
        except RuntimeError:
            raw = ""
        out = _parse_json(raw) if raw else None
        if out and out.get("first_impression") and out.get("first_impression_id"):
            break
        time.sleep(2)
    if not out or not out.get("first_impression") or not out.get("first_impression_id"):
        return False, "LLM returned no usable JSON after 3 attempts"

    fi = _sanitize(out["first_impression"])
    fid = _sanitize(out["first_impression_id"])
    if not fi or not fid:
        return False, "empty fields after sanitize"

    # Insert after the `presentation:` line, preserving the rest verbatim.
    def _insert(m: re.Match) -> str:
        return f"{m.group(0)}\nfirst_impression: \"{fi}\"\nfirst_impression_id: \"{fid}\""

    new_text, n = re.subn(r"^(presentation: .*)$", _insert, text, count=1, flags=re.M)
    if n != 1:
        return False, "presentation line not found — aborting (no silent insert)"

    if dry_run:
        return True, f"[dry-run] would insert first_impression for {case_id}"

    # Verification loop: tmp file must parse + lint before we touch the real file.
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    try:
        case, res = parse_case_v2(tmp), None
        res = lint(case)
        if not res.ok:
            return False, f"lint failed: {res.errors[:2]}"
    finally:
        tmp.unlink(missing_ok=True)
    path.write_text(new_text, encoding="utf-8")
    return True, f"wrote first_impression for {case_id}"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Backfill first_impression fields")
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
        print(f"  {'✓' if done else '✗'} {fp.stem}: {msg}")
        ok += done
        fail += not done

    print(f"\nProcessed {ok} ok; {fail} failed." + (" [dry-run, nothing written]" if args.dry_run else ""))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
