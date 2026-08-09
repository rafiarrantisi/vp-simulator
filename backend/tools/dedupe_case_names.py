"""De-duplicate patient names across the case library.

Pass 1 (localize_cases.py) produced heavy first-name reuse (Alya x10, Nadia x10,
Bambang x7...). This pass renames colliding MAIN characters (and any family names
that collide) so each first name appears once. Uses the backend LLM client
(OpenRouter / deepseek-v4-flash) — not opencode.

Run from backend/:
    .venv/bin/python -m tools.dedupe_case_names [--dry-run] [--ids a,b,c]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from app.config import get_settings
from app.rag.llm import get_llm_client
from pipeline.case_v2 import parse_case_v2, lint

_NAME_RE = re.compile(r"(?:I'?m|My name is|I am)\s+([A-Z][a-z]+)(?:\s+([A-Z][a-z]+))?")

_RENAME_TASK = """You are renaming the main character of a virtual-patient case so that names are
unique across a library of 82 cases.

CURRENT MAIN CHARACTER NAME: {current_name}
ALREADY-USED FIRST NAMES (avoid ALL of these — pick a first name NOT in this list): {forbidden}

TASK — return ONE JSON object with exactly one key:
- "name_map": object mapping EXACT original name strings in the body to their new
  Indonesian forms:
  1. The main character's FULL name and FIRST name -> a NEW Indonesian name whose
     FIRST name is NOT in ALREADY-USED and is age-appropriate for the character
     (elderly 60+ -> traditional like Slamet/Siti/Sumarni/Kartini; 35-59 -> mixed
     like Bambang/Ratna/Agus/Dewi; 18-34 -> modern like Rizky/Alya/Dimas/Nadia
     EXCEPT the forbidden ones; children -> modern kids' names).
  2. Any spouse / children / relatives names that appear in ALREADY-USED -> also
     rename them to fresh Indonesian names (also not in ALREADY-USED).
- Map EVERY occurrence string the LLM sees in the body (full name, first name,
  possessive forms like "Nadia's" as the bare name "Nadia", etc.). Keys must be
  byte-exact substrings of the body.
- Do NOT change anything else — every other word must stay identical.

CURRENT BODY:
=====
{body}
=====

Return ONLY the JSON object."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start : end + 1])


_DASH_RE = re.compile(r"^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[—–]\s*\d+")


def _norm(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def main_name(fp: Path) -> str | None:
    t = _norm(fp.read_text())
    m = re.search(r"## Identity\s*\n+(.*)", t)
    if not m:
        return None
    first_line = m.group(1).strip().split("\n")[0]
    m2 = _NAME_RE.search(first_line)
    if m2:
        first = m2.group(1)
        full = (m2.group(1) + (" " + m2.group(2) if m2.group(2) else ""))
        return first + "|" + full
    m3 = _DASH_RE.match(first_line)
    if m3:
        first = m3.group(1).split()[0]
        return first + "|" + m3.group(1).strip()
    return None


_NAME_ADD_TASK = """You are adding a patient name to a virtual-patient case whose Identity section
currently has NO name.

ALREADY-USED FIRST NAMES (avoid ALL of these — pick a first name NOT in this list): {forbidden}

TASK — return ONE JSON object with exactly one key:
- "name_map": object mapping EXACT original strings in the body to new strings that
  INTRODUCE an age-appropriate Indonesian name for the main character (elderly 60+
  -> traditional like Slamet/Siti/Sumarni; 35-59 -> mixed like Bambang/Ratna/Agus;
  18-34 -> modern like Rizky/Alya/Dimas — EXCEPT forbidden ones; children ->
  modern kids' names). Example: {{"a 55-year-old man who works in construction":
  "Slamet, a 55-year-old man who works in construction"}} or {{"I am a 55-year-old
  man": "I am Pak Slamet, a 55-year-old man"}}. Adjust ANY first-person references
  that should carry the name. Keys must be byte-exact substrings. Do NOT change
  anything else.

CURRENT BODY:
=====
{body}
=====

Return ONLY the JSON object."""


def add_name_case(fp: Path, forbidden: list[str], dry_run: bool) -> tuple[str, str]:
    body = fp.read_text()
    prompt = _NAME_ADD_TASK.format(forbidden=", ".join(sorted(forbidden)), body=body)
    client = get_llm_client()
    last = ""
    for _ in (1, 2):
        try:
            raw = client.generate(
                "You output strict JSON only.",
                [{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )
            data = _extract_json(raw)
            nm = data.get("name_map")
            if not isinstance(nm, dict) or not nm:
                raise ValueError("empty name_map")
            break
        except Exception as e:  # noqa: BLE001
            last = str(e)[:160]
            time.sleep(2)
    else:
        return f"error: LLM: {last}", "?"
    new_body = body
    for old in sorted(nm, key=len, reverse=True):
        new_body = new_body.replace(old, str(nm[old]))
    tmp_fp = fp.with_suffix(".tmp.md")
    tmp_fp.write_text(new_body)
    try:
        lr = lint(parse_case_v2(tmp_fp))
        if not lr.ok:
            return f"error: lint: {lr.errors[:2]}", "?"
    finally:
        tmp_fp.unlink(missing_ok=True)
    if not dry_run:
        fp.write_text(new_body)
    return f"ok: name added -> {list(nm.values())[0]}", "?"


def rename_case(fp: Path, forbidden: list[str], dry_run: bool) -> tuple[str, str]:
    body = fp.read_text()
    case = parse_case_v2(fp)
    info = main_name(fp)
    first, full = info.split("|", 1) if info else ("?", "?")
    prompt = _RENAME_TASK.format(
        current_name=full, forbidden=", ".join(sorted(forbidden)), body=body
    )
    client = get_llm_client()
    last = ""
    for _ in (1, 2):
        try:
            raw = client.generate(
                "You output strict JSON only.",
                [{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.3,
            )
            data = _extract_json(raw)
            nm = data.get("name_map")
            if not isinstance(nm, dict) or not nm:
                raise ValueError("empty name_map")
            break
        except Exception as e:  # noqa: BLE001
            last = str(e)[:160]
            time.sleep(2)
    else:
        return f"error: LLM: {last}", first

    new_body = body
    for old in sorted(nm, key=len, reverse=True):
        new_body = new_body.replace(old, str(nm[old]))

    tmp_fp = fp.with_suffix(".tmp.md")
    tmp_fp.write_text(new_body)
    try:
        c2 = parse_case_v2(tmp_fp)
        lr = lint(c2)
        if not lr.ok:
            return f"error: lint: {lr.errors[:2]}", first
    finally:
        tmp_fp.unlink(missing_ok=True)

    if not dry_run:
        fp.write_text(new_body)
    return f"ok: {full} -> {list(nm.values())[0]}", first


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ids", help="comma-separated case ids to force-rename")
    args = ap.parse_args()

    cases_dir = Path(get_settings().content_cases_dir)
    all_fps = sorted(cases_dir.glob("*.md"))
    fps = all_fps
    if args.ids:
        wanted = {s.strip() for s in args.ids.split(",") if s.strip()}
        fps = [fp for fp in all_fps if fp.stem in wanted]

    # first-name -> [case ids] computed over the WHOLE library (keep first
    # occurrence, rename the rest)
    usage: dict[str, list[str]] = {}
    for fp in all_fps:
        info = main_name(fp)
        if not info:
            continue
        first, _ = info.split("|", 1)
        usage.setdefault(first, []).append(fp.stem)

    todo = []
    for first, ids in usage.items():
        if len(ids) > 1:
            for cid in ids[1:]:
                if cid in {f.stem for f in fps}:
                    todo.append(cid)
    todo = sorted(set(todo))
    if not todo:
        print("TIDAK ADA duplikat yang perlu direname.")
        return 0

    # dynamic forbidden list = all current first names
    forbidden = set(usage.keys())
    print(f"merename {len(todo)} kasus (forbidden pool awal: {len(forbidden)} nama)")

    ok = err = 0
    for i, cid in enumerate(todo, 1):
        fp = cases_dir / f"{cid}.md"
        status, old_first = rename_case(fp, sorted(forbidden), args.dry_run)
        if status.startswith("ok"):
            ok += 1
            # update pool: old first name may now be unique (still allowed) —
            # keep it forbidden to prevent re-collision with remaining cases
        else:
            err += 1
        print(f"[{i}/{len(todo)}] {cid}: {status}")
        sys.stdout.flush()

    # final collision check
    final: Counter = Counter()
    for fp in fps:
        info = main_name(fp)
        if info:
            final[info.split("|", 1)[0]] += 1
    dups = {k: v for k, v in final.items() if v > 1}

    # name-add pass for cases with no detectable name
    nameless = [fp for fp in fps if main_name(fp) is None]
    if nameless and not args.dry_run:
        print(f"\nname-add pass: {len(nameless)} kasus tanpa nama")
        for i, fp in enumerate(nameless, 1):
            status, _ = add_name_case(fp, sorted(final.keys()), False)
            print(f"  [{i}/{len(nameless)}] {fp.stem}: {status}")
            sys.stdout.flush()
    elif nameless:
        print(f"\nname-add pass (dry): {len(nameless)} kasus tanpa nama")

    print(f"done — ok={ok} error={err}; sisa duplikat: {dups if dups else 'TIDAK ADA'}")
    return 0 if err == 0 and not dups else 1


if __name__ == "__main__":
    sys.exit(main())
