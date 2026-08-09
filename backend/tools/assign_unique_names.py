"""Deterministic unique-name assignment for all Qora cases (Indonesian market).

Main-character names are assigned PROGRAMMATICALLY from age-bucketed Indonesian
name pools (unique per case, by construction). The LLM only APPLIES the assigned
name to the body and fixes colliding family names — it never chooses the main
name, so collisions cannot be reintroduced.

Usage (from backend/):
  python -m tools.assign_unique_names [--dry-run] [--ids a,b,c]
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

FEM_POOLS = {
    "elderly": ["Siti", "Sumarni", "Kartini", "Suparmi", "Tukiyem", "Painem",
                "Sriyati", "Mulyani", "Tumini", "Marni", "Ngatini", "Karsinem"],
    "adult": ["Ratna", "Dewi", "Sri", "Yanti", "Endang", "Wahyuni", "Retno", "Tatik",
              "Rini", "Maya", "Rina", "Lina", "Nurul", "Wati", "Tuti", "Wulan",
              "Erna", "Yulia", "Fitri", "Sari"],
    "young": ["Alya", "Nadia", "Intan", "Citra", "Sinta", "Tiara", "Ayu", "Rahma",
              "Vina", "Dina", "Putri", "Mega", "Nabila", "Aulia", "Salsa", "Gita",
              "Tasya", "Kania", "Zahra", "Sekar", "Kiran", "Keysha", "Aisyah",
              "Naura", "Syifa", "Farah", "Nisa", "Winda", "Amanda", "Raisa", "Alisha"],
    "kid": ["Aisyah", "Keysha", "Zahra", "Salsa", "Sekar", "Kayla", "Kiran", "Nadia"],
}
MASC_POOLS = {
    "elderly": ["Slamet", "Sumarno", "Wagiman", "Darmo", "Sastro", "Parto",
                "Sutrisno", "Hartono", "Supriyadi", "Suyanto", "Sukardi", "Hardjo"],
    "adult": ["Bambang", "Agus", "Hendra", "Joko", "Suryanto", "Haryanto", "Sugeng",
              "Budi", "Eko", "Dodi", "Anton", "Iwan", "Yusuf", "Hadi", "Wawan",
              "Gatot", "Rudi", "Edi", "Suparman", "Karto"],
    "young": ["Rizky", "Dimas", "Fajar", "Bayu", "Raka", "Gilang", "Fikri", "Dwi",
              "Andi", "Yoga", "Ardi", "Rio", "Bima", "Kevin", "Zaki", "Reno",
              "Rangga", "Wisnu", "Alif", "Rafi", "Arka", "Dava", "Fahri", "Hafiz",
              "Ilham", "Satria", "Taufik", "Yudha", "Daffa", "Farhan"],
    "kid": ["Bima", "Fikri", "Alif", "Arka", "Rafi", "Dava", "Raka", "Wisnu"],
}

SURNAMES = [
    "Pratama", "Wijaya", "Sari", "Putri", "Lestari", "Rahayu", "Nugroho",
    "Saputra", "Maharani", "Kusuma", "Purnama", "Utami", "Hidayat", "Santoso",
    "Wibowo", "Anggraini", "Setiawan", "Permata", "Handayani", "Susanto",
]

_FEM_NAMES = {n for p in FEM_POOLS.values() for n in p} | {
    "Ratih", "Dian", "Rani", "Sari", "Dewi", "Wati", "Sri", "Alya", "Nadia",
    "Ratna", "Rina", "Maya", "Citra", "Intan", "Sinta", "Tiara", "Ayu", "Rahma",
    "Vina", "Dina", "Putri", "Mega", "Nabila", "Aulia", "Salsa", "Gita", "Tasya",
    "Kania", "Zahra", "Sekar", "Kiran", "Keysha", "Aisyah", "Yanti", "Endang",
    "Wahyuni", "Retno", "Tatik", "Rini", "Lina", "Nurul", "Tuti", "Wulan", "Erna",
    "Yulia", "Fitri", "Mulyani", "Marni", "Suparmi", "Tukiyem", "Painem",
    "Sriyati", "Tumini", "Ngatini", "Karsinem", "Sarah", "Emily", "Jane", "Mary",
    "Linda", "Susan", "Karen", "Lisa", "Maria", "Anna", "Emma", "Olivia", "Chloe",
    "Dewi", "Siti", "Sumarni", "Kartini", "Ratna", "Yuni", "Rina", "Tini",
    "Wulandari", "Sumiyati", "Indah", "Yanti", "Wahyuni", "Endang", "Retno",
    "Tatik", "Nurul", "Tuti", "Erna", "Yulia", "Fitri", "Rani", "Dian", "Ratih",
    "Citra", "Maya", "Intan", "Putri", "Ayu", "Rahma", "Sinta", "Tiara", "Kania",
    "Tasya", "Sekar", "Zahra", "Keysha", "Aisyah", "Nabila", "Aulia", "Salsa",
    "Gita", "Kiran", "Kayla", "Vina", "Dina", "Mega", "Lina", "Rini", "Wati",
    "Sri", "Sari", "Wulan", "Sinta", "Marni", "Mulyani", "Suparmi", "Tukiyem",
    "Painem", "Tumini", "Ngatini", "Karsinem", "Siti", "Sumarni", "Kartini",
}
_MASC_NAMES = {n for p in MASC_POOLS.values() for n in p} | {
    "Rizky", "Dimas", "Bambang", "Slamet", "Agus", "Hendra", "Joko", "Suryanto",
    "Haryanto", "Sugeng", "Budi", "Eko", "Dodi", "Anton", "Iwan", "Yusuf", "Hadi",
    "Wawan", "Gatot", "Rudi", "Edi", "Suparman", "Karto", "Bayu", "Fajar", "Raka",
    "Gilang", "Fikri", "Dwi", "Andi", "Yoga", "Ardi", "Rio", "Bima", "Kevin",
    "Zaki", "Reno", "Rangga", "Wisnu", "Alif", "Rafi", "Arka", "Dava", "Adi",
    "Aditya", "John", "Mike", "David", "Liam", "James", "Robert", "William",
    "Richard", "Thomas", "Mark", "Paul", "Daniel", "Kevin", "Sutrisno", "Hartono",
    "Supriyadi", "Suyanto", "Sukardi", "Hardjo", "Wagiman", "Darmo", "Sastro",
    "Parto", "Sumarno", "Budi", "Joko",
}

_APPLY_TASK = """You are applying a pre-assigned Indonesian name to a virtual-patient case.

The main character's NEW name has already been chosen (uniqueness across the
library is managed programmatically): {assigned}

CURRENT MAIN CHARACTER NAME IN BODY: {current}

TASK — return ONE JSON object with exactly one key:
- "name_map": object mapping EXACT original name strings in the body to new strings:
  1. The main character's FULL name and FIRST name -> "{assigned}" and "{assigned_first}"
     (use the exact assigned forms).
  2. Any spouse / children / relatives names that would duplicate names used in
     OTHER cases (likely candidates: the top reused names {hot_names}) -> rename to
     fresh Indonesian names that do NOT equal "{assigned_first}" and do not repeat
     within this same body.
- Keys must be byte-exact substrings of the body (include possessive forms as the
  bare name, e.g. map "Nadia" not "Nadia's"). Do NOT change anything else.

CURRENT BODY:
=====
{body}
=====

Return ONLY the JSON object."""

_ADD_TASK = """You are inserting a pre-assigned Indonesian name into a virtual-patient case whose
Identity section has no name.

ASSIGNED NAME: {assigned} (already chosen — do not deviate)

TASK — return ONE JSON object with exactly one key:
- "name_map": object mapping EXACT original strings in the body to new strings that
  INTRODUCE "{assigned}" as the patient's name (age-appropriate: prefix "Pak"/"Bu"
  if elderly). Example: {{"a 55-year-old man who works in construction": "Pak {assigned_first}, a 55-year-old man who works in construction"}}.
  Keys must be byte-exact substrings. Do NOT change anything else.

CURRENT BODY:
=====
{body}
=====

Return ONLY the JSON object."""


def _norm(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'")


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start : end + 1])


def _age_bucket(body: str) -> str:
    b = _norm(body)
    idt = b.split("## Identity", 1)[1].split("##", 1)[0] if "## Identity" in b else b
    first_line = idt.strip().split("\n")[0]
    m = (
        re.search(r"(\d{1,2})\s*(?:-year-old|years?\s+old)", first_line)
        or re.search(r"[—–]\s*(\d{1,2})\s*,", first_line)
        or re.search(r"(\d{1,2})\s*,\s*[a-z]", first_line)
        or re.search(r"(\d{1,2})\s*[-–]\s*(?:year|tahun)", first_line, re.I)
    )
    if not m:
        return "adult"
    a = int(m.group(1))
    if a >= 60:
        return "elderly"
    if a >= 35:
        return "adult"
    if a >= 13:
        return "young"
    return "kid"


def _current_main_name(body: str) -> str | None:
    m = re.search(r"## Identity\s*\n+(.*)", body)
    if not m:
        return None
    line = m.group(1).strip().split("\n")[0]
    m2 = re.search(r"(?:I'?m|I am|My name is|You are)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", _norm(line))
    if m2:
        return m2.group(1)
    m3 = re.match(r"^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[—–]\s*\d+", _norm(line))
    if m3:
        return m3.group(1)
    return None


def _gender(body: str, current_name: str | None) -> str:
    if current_name:
        fn = current_name.split()[0].replace("Pak", "").replace("Bu", "").strip()
        if fn in _FEM_NAMES:
            return "f"
        if fn in _MASC_NAMES:
            return "m"
    b = _norm(body[:2400]).lower()
    f = sum(b.count(w) for w in ("mom", "mother", "wife", "housewife", "stay-at-home mom",
                                 "sister", "daughter", "mrs", "ibu", "she ", " her ", "woman"))
    m = sum(b.count(w) for w in ("dad", "father", "husband", "brother", "son", "mr",
                                 "bapak", "he ", " him ", "man"))
    return "f" if f >= m else "m"


def assign_names(fps: list[Path]) -> dict[str, tuple[str, str]]:
    used_f: list[str] = []
    used_m: list[str] = []
    order = {"elderly": ["elderly", "adult", "young"],
             "adult": ["adult", "young", "elderly"],
             "young": ["young", "adult", "elderly"],
             "kid": ["kid", "young", "adult"]}
    out: dict[str, tuple[str, str]] = {}
    for fp in fps:
        body = fp.read_text()
        bucket = _age_bucket(body)
        gender = _gender(body, _current_main_name(body))
        pools = (FEM_POOLS if gender == "f" else MASC_POOLS)
        used = used_f if gender == "f" else used_m
        first = None
        for b in order[bucket]:
            first = next((n for n in pools[b] if n not in used), None)
            if first:
                break
        if first is None:  # total exhaustion: any unused same-gender name
            all_g = [n for p in pools.values() for n in p]
            first = next((n for n in all_g if n not in used), None) or f"Pasien{len(used) + 1}"
        used.append(first)
        surname = SURNAMES[len(used) % len(SURNAMES)]
        out[fp.stem] = (first, f"{first} {surname}")
    return out


def hot_names(assigned: dict[str, tuple[str, str]]) -> list[str]:
    cnt = Counter(v[0] for v in assigned.values())
    return [n for n, _ in cnt.most_common(12)]


def apply_one(fp: Path, first: str, full: str, hot: list[str], dry_run: bool) -> str:
    body = fp.read_text()
    current = _current_main_name(body)
    if current:
        prompt = _APPLY_TASK.format(
            assigned=full, assigned_first=first, current=current,
            hot_names=", ".join(hot), body=body,
        )
    else:
        prompt = _ADD_TASK.format(assigned=full, assigned_first=first, body=body)
    client = get_llm_client()
    last = ""
    for _ in (1, 2, 3):
        try:
            raw = client.generate(
                "You output strict JSON only.",
                [{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.2,
            )
            data = _extract_json(raw)
            nm = data.get("name_map")
            if not isinstance(nm, dict) or not nm:
                raise ValueError("empty name_map")
            break
        except Exception as e:  # noqa: BLE001
            last = str(e)[:150]
            time.sleep(2)
    else:
        return f"error: LLM: {last}"
    new_body = body
    for old in sorted(nm, key=len, reverse=True):
        new_body = new_body.replace(old, str(nm[old]))
    tmp_fp = fp.with_suffix(".tmp.md")
    tmp_fp.write_text(new_body)
    try:
        lr = lint(parse_case_v2(tmp_fp))
        if not lr.ok:
            return f"error: lint: {lr.errors[:2]}"
    finally:
        tmp_fp.unlink(missing_ok=True)
    # verify the assigned first name actually landed
    if first not in new_body:
        return "error: assigned name NOT found in output body"
    if not dry_run:
        fp.write_text(new_body)
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ids", help="comma-separated case ids to process")
    ap.add_argument("--map", help="explicit assignments: stem:Full Name,stem2:Full Name2 (overrides auto-assign)")
    args = ap.parse_args()

    cases_dir = Path(get_settings().content_cases_dir)
    all_fps = sorted(cases_dir.glob("*.md"))
    fps = all_fps
    if args.ids:
        wanted = {s.strip() for s in args.ids.split(",") if s.strip()}
        fps = [fp for fp in all_fps if fp.stem in wanted]

    assigned = assign_names(fps)
    if args.map:
        for pair in args.map.split(","):
            stem, full = pair.split(":", 1)
            stem, full = stem.strip(), full.strip()
            first = full.split()[0]
            assigned[stem] = (first, full)
    hot = hot_names(assign_names(all_fps))
    print(f"assigning {len(fps)} cases (hot names to avoid: {len(hot)})")
    ok = err = 0
    for i, fp in enumerate(fps, 1):
        first, full = assigned[fp.stem]
        status = apply_one(fp, first, full, hot, args.dry_run)
        ok += status == "ok"
        err += status != "ok"
        print(f"[{i}/{len(fps)}] {fp.stem}: {status} -> {full}")
        sys.stdout.flush()

    # verify uniqueness of main names across the WHOLE library
    final: Counter = Counter()
    for fp in all_fps:
        n = _current_main_name(fp.read_text())
        if n:
            final[n] += 1
    dups = {k: v for k, v in final.items() if v > 1}
    print(f"done — ok={ok} error={err}; sisa duplikat MAIN name: {dups if dups else 'TIDAK ADA'}")
    return 0 if err == 0 and not dups else 1


if __name__ == "__main__":
    sys.exit(main())
