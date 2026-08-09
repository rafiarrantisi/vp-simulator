"""Localize case personas: Indonesian age-appropriate names + add Vital signs &
Physical findings sections to Part B (schema-v2 cases).

Uses the backend LLM client (OpenRouter / LLM_MODEL = deepseek-v4-flash) — NOT
opencode. Run from backend/:

    .venv/bin/python -m tools.localize_cases --ids derm_cellulitis_001
    .venv/bin/python -m tools.localize_cases --limit 3
    .venv/bin/python -m tools.localize_cases            # all cases
    .venv/bin/python -m tools.localize_cases --dry-run  # preview only

Output is surgical: only name strings are replaced, two H2 sections are appended
to the body. Frontmatter (Part A) is never touched. Every file is re-linted.
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

_TASK = """You are localizing a virtual-patient case for an Indonesian medical-student market.

You are given the CURRENT persona body (Part B) of a case and its clinical context.

TASK — return ONE JSON object with exactly three keys:
1. "name_map": an object mapping EXACT original name strings (as they appear in the
   body — full names like "Sarah Johnson", first names like "Liam", spouse/relative
   names, and any foreign location names you localize) to Indonesian replacements.
   Names must be age-appropriate for the character:
     - elderly (60+): traditional names (Slamet, Siti, Sumarni, Kartini, Suparmi, Wagiman, Darmo...)
     - 35-59: mixed traditional/modern (Bambang, Ratna, Agus, Dewi, Hendra, Sri, Joko...)
     - 18-34: modern (Rizky, Alya, Dimas, Nadia, Fajar, Intan, Bayu...)
     - children: modern kids' names (Raka, Nadia, Bima, Aisyah, Fikri...)
   Keep occupations/roles but make them realistic for Indonesia when clearly foreign
   (e.g. "GP" -> "puskesmas doctor", "family doctor" -> "dokter puskesmas"). Do NOT
   change anything else — every other sentence must stay identical.
2. "vitals_md": markdown for a "## Vital signs" section — numbers the patient heard
   from a nurse: temperature (°C), blood pressure (mmHg), heart rate (bpm),
   respiratory rate (/min), oxygen saturation if relevant. MUST be clinically
   consistent with the condition and with each other, typical for the patient's age.
3. "findings_md": markdown for a "## Physical findings" section — per body area in
   semi-lay terms (general appearance, skin, head/neck, chest, abdomen, limbs, neuro).
   Only areas with findings relevant to the condition. MUST be consistent with the
   condition. NEVER include the diagnosis name, the word "diagnosis", or medical jargon.

RULES:
- Output ONLY the JSON object, no commentary, no markdown fences.
- In vitals_md/findings_md use "## Vital signs" and "## Physical findings" as the H2
  headers followed by bullet points.
- Never write the working diagnosis or condition name into the sections.
- name_map keys must be byte-exact substrings of the body below (copy them from the text).

CLINICAL CONTEXT (private — for consistency only, never echo it into the output):
- target_condition: {condition}
- difficulty: {difficulty}
- presentation: {presentation}

CURRENT PERSONA BODY:
=====
{body}
=====

Return ONLY the JSON object."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^json\s*", "", text, flags=re.I).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start : end + 1])


def _replace_names(body: str, name_map: dict) -> str:
    for old in sorted(name_map, key=len, reverse=True):
        new = str(name_map[old]).strip()
        if not old or not new or old == new:
            continue
        body = body.replace(old, new)
    return body


def process_one(fp: Path, dry_run: bool = False) -> tuple[str, str, int]:
    """Returns (case_id, status, n_changes). status: ok | skip | error:msg"""
    case = parse_case_v2(fp)
    cid = case.id
    body = case.body
    if "vital signs" in {h for h in case.body_sections}:
        return cid, "skip (already has vitals)", 0
    fm = case.frontmatter
    prompt = _TASK.format(
        condition=fm.get("target_condition", "?"),
        difficulty=fm.get("difficulty", "?"),
        presentation=fm.get("presentation", "?"),
        body=body,
    )
    client = get_llm_client()
    last_err = ""
    for attempt in (1, 2):
        try:
            raw = client.generate(
                "You output strict JSON only.",
                [{"role": "user", "content": prompt}],
                max_tokens=1800,
                temperature=0.2,
            )
            data = _extract_json(raw)
            if not isinstance(data.get("name_map"), dict):
                raise ValueError("missing name_map")
            break
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:200]
            time.sleep(2)
    else:
        return cid, f"error: LLM failed: {last_err}", 0

    name_map = data.get("name_map", {})
    new_body = _replace_names(body, name_map)
    new_body = new_body.rstrip() + "\n\n" + str(data.get("vitals_md", "")).strip() + "\n\n" + str(data.get("findings_md", "")).strip() + "\n"

    # sanity: body still parses + lints (write temp, lint, discard)
    tmp = fp.read_text().replace(body, new_body, 1)
    tmp_fp = fp.with_suffix(".tmp.md")
    tmp_fp.write_text(tmp)
    try:
        c2 = parse_case_v2(tmp_fp)
        lr = lint(c2)
        if not lr.ok:
            return cid, f"error: lint failed after edit: {lr.errors[:3]}", 0
    finally:
        tmp_fp.unlink(missing_ok=True)

    n = sum(len(name_map) for _ in [0]) + (1 if "## Vital signs" in new_body else 0) + (1 if "## Physical findings" in new_body else 0)
    if dry_run:
        return cid, f"ok (dry-run, {len(name_map)} names, +2 sections)", n
    fp.write_text(tmp)
    return cid, "ok", n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", help="comma-separated case ids to process")
    ap.add_argument("--limit", type=int, default=0, help="process only first N (sorted)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cases_dir = Path(get_settings().content_cases_dir)
    fps = sorted(cases_dir.glob("*.md"))
    if args.ids:
        wanted = {s.strip() for s in args.ids.split(",") if s.strip()}
        fps = [fp for fp in fps if fp.stem in wanted]
    if args.limit:
        fps = fps[: args.limit]

    print(f"processing {len(fps)} cases (dry_run={args.dry_run})")
    t0 = time.time()
    ok = err = skip = 0
    for i, fp in enumerate(fps, 1):
        cid, status, n = process_one(fp, dry_run=args.dry_run)
        if status.startswith("ok"):
            ok += 1
        elif status.startswith("skip"):
            skip += 1
        else:
            err += 1
        print(f"[{i}/{len(fps)}] {cid}: {status}")
        sys.stdout.flush()
    print(f"done in {time.time()-t0:.0f}s — ok={ok} skip={skip} error={err}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
