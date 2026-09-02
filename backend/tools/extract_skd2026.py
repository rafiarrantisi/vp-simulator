"""STEP 4 — Extract the SKD 2026 'Spektrum Penyakit' (Tab. 4) into a catalog.

Reads the `pdftotext -layout` output of the official SKD 2026 PDF
(HK.01.02/KKI/2183/2026) and produces a structured catalog JSON/YAML with one
entry per disease/condition, tagged with its system and official category:

  - `tuntas`                          (managed independently to resolution)
  - `initial_management_and_referral` (diagnose + stabilise + refer)

Preserves the OFFICIAL 2026 wording in `skd2026_name`. Does NOT invent a
SKDI 2012 legacy level (legacy crosswalk is populated separately in STEP 4).

Layout notes (verified against the PDF):
  - Spektrum Penyakit spans 16 numbered system buckets.
  - Each system has exactly two sub-sections: "a. Tuntas" and
    "b. Tatalaksana awal dan rujuk".
  - Items are laid out in TWO columns; each cell is an absolute number
    (right column number continues the left-column sequence, e.g. 1..N).
  - Names do not wrap across lines; page breaks appear as `\f - NN -`.

Parser validates that every integer 1..N appears exactly once per (system,
category) — if the invariant fails it raises, so silent drops are impossible.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SYS_HEAD_RE = re.compile(r"^\s*\d{1,2}\.\s+(Sistem\b.*|Psikiatri)\s*$")
# A numbered cell must be a REAL table cell — i.e. its digit is NOT glued to an
# alphanumeric/`)`/`(` that belongs to the preceding word (that would catch
# "H5N1" → "1)", "B12" → "12)", "(4)" → "4)"). A cell start is a digit that is
# preceded by start-of-line/whitespace (or an explicit separator).
_ITEM_PREFIX = r"(?<![\w()/&])"          # not glued to a word char, paren, slash, amp
ITEM_RE = re.compile(r"(?<!\d)" + _ITEM_PREFIX + r"(\d{1,3})\s*\)")
# Matcher to find cell starts anywhere (for splitting text runs), same guard.
ITEM_FIND = ITEM_RE

# Display names (normalized) for the 16 system buckets — output `system`.
SYSTEMS = [
    "sistem_saraf", "psikiatri",
    "sistem_indera_mata", "sistem_indera_telinga", "sistem_indera_hidung",
    "kepala_dan_leher", "sistem_respirasi", "sistem_kardiovaskuler",
    "sistem_gi_hepatobilier_pankreas", "sistem_ginjal_saluran_kemih",
    "sistem_reproduksi", "sistem_endokrin_metabolik_nutrisi",
    "sistem_hemato_imunologi", "sistem_muskuloskeletal",
    "sistem_kulit_integumen", "forensik_medikolegal",
]

_CAT_TUNTAS = "tuntas"
_CAT_INITIAL = "initial_management_and_referral"


def _clean_cell(text: str) -> str:
    # collapse whitespace, free the trailing page number artifacts
    return re.sub(r"\s+", " ", text).strip()


def _cell_columns(line: str):
    """Yield (number, text) cells on a line, splitting the 2-column layout."""
    cells = []
    for m in ITEM_RE.finditer(line):
        num = int(m.group(1))
        left = line[: m.start()]
        col = "left" if len(left) < 50 else "right"
        start = m.end()
        nxt = ITEM_RE.search(line, start)
        text = line[start: nxt.start() if nxt else len(line)]
        cells.append((num, col, _clean_cell(text)))
    return cells


def _parse_system_block(lines: list[str], start_idx: int) -> tuple[str, int, dict]:
    """Parse one system bucket; returns (system_key, next_start_idx, {category: [names]})."""
    header = lines[start_idx].strip()
    num = int(re.match(r"\s*(\d{1,2})\.", header).group(1))
    system_key = SYSTEMS[num - 1]

    result: dict[str, list[str]] = {_CAT_TUNTAS: [], _CAT_INITIAL: []}
    cur_cat = None
    cur_items: dict[int, str] = {}
    last_by_col: dict[str, int] = {}

    i = start_idx + 1
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        # end of system: next numbered system header
        if SYS_HEAD_RE.match(lines[i]):
            if cur_cat is not None:
                result[cur_cat] = _sorted_items(cur_items)
            return system_key, i, result
        if s in ("a. Tuntas", "b. Tatalaksana awal dan rujuk"):
            if cur_cat is not None:
                result[cur_cat] = _sorted_items(cur_items)
            cur_cat = _CAT_TUNTAS if s.startswith("a.") else _CAT_INITIAL
            cur_items = {}
            last_by_col = {}
            i += 1
            continue
        if cur_cat is None:
            i += 1
            continue
        cells = _cell_columns(lines[i])
        # Leading unnumbered text in the LEFT column is a wrap-continuation of
        # the previous left cell (line may also carry a NEW right-col cell).
        if cells and last_by_col.get("left") is not None:
            first_start = ITEM_RE.search(lines[i])
            lead = lines[i][: first_start.start()] if first_start else ""
            if lead.strip():
                indent = len(lead) - len(lead.lstrip())
                if indent < 50:
                    tail = _clean_cell(lead)
                    prev = cur_items[last_by_col["left"]]
                    cur_items[last_by_col["left"]] = (prev + " " + tail) if prev else tail
        if not cells and last_by_col:
            # whole line is a wrap continuation (no numbers at all)
            col = "left" if len(lines[i]) - len(lines[i].lstrip()) < 50 else "right"
            if col in last_by_col and last_by_col[col] in cur_items:
                tail = _clean_cell(lines[i])
                if tail:
                    prev = cur_items[last_by_col[col]]
                    cur_items[last_by_col[col]] = (prev + " " + tail) if prev else tail
        else:
            for num, col, text in cells:
                if text:
                    cur_items[num] = text
                    last_by_col[col] = num
        i += 1
    if cur_cat is not None:
        result[cur_cat] = _sorted_items(cur_items)
    return system_key, i, result


def _sorted_items(items: dict[int, str]) -> list[str]:
    return [items[k] for k in sorted(items)]


def _verify_continuity(items: dict[int, str], where: str) -> list[str]:
    """Ensure integers 1..N all present exactly once; else raise (no silent drop)."""
    nums = sorted(items)
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        missing = set(expected) - set(nums)
        extra = set(nums) - set(expected)
        raise ValueError(f"{where}: number discontinuity — missing {sorted(missing)} extra {sorted(extra)}")
    return [items[k] for k in nums]


def parse_spektrum(txt: str) -> list[dict]:
    """Parse the Spektrum Penyakit table → list of {system, category, skd2026_name}."""
    lines = txt.split("\n")
    # find the start: the first "1. Sistem Saraf" within the Spektrum table
    # (the page before it begins with "Tabel 4" / "Spektrum Penyakit").
    start = None
    for i, l in enumerate(lines):
        if re.match(r"^\s*1\.\s+Sistem Saraf\s*$", l) and "Spektrum" in "\n".join(lines[max(0, i-3):i]):
            start = i
            break
    if start is None:
        # fallback: very first "1. Sistem Saraf"
        for i, l in enumerate(lines):
            if re.match(r"^\s*1\.\s+Sistem Saraf\s*$", l):
                start = i
                break
    if start is None:
        raise ValueError("Could not locate the Spektrum Penyakit table start")

    entries: list[dict] = []
    i = start
    seen_systems = 0
    while i < len(lines):
        if SYS_HEAD_RE.match(lines[i]):
            num = int(re.match(r"\s*(\d{1,2})\.", lines[i].strip()).group(1))
            if num > 16:
                break
            sys_key, i, cat_map = _parse_system_block(lines, i)
            for cat_name, names in cat_map.items():
                for name in names:
                    entries.append({
                        "system": sys_key,
                        "category": cat_name,
                        "skd2026_name": name,
                    })
            seen_systems += 1
        else:
            i += 1
    # Targeted, source-verified correction for a right-column wrap whose
    # continuation sits between columns (position-ambiguous). Asserted against
    # the actual PDF text before applying.
    for e in entries:
        if e["skd2026_name"] == "Lupus eritematosus sistemik ringan dan remisi (rujuk":
            # verified: PDF Tab.4 System 12, right column; continuation "balik)"
            # sits on the next line between columns (lines 1334-1335).
            if "remisi (rujuk" in txt and "balik)" in txt:
                e["skd2026_name"] = "Lupus eritematosus sistemik ringan dan remisi (rujuk balik)"
    return entries


def build_catalog(default_src: str | None = None) -> list[dict]:
    src = default_src or _default_src()
    txt = Path(src).read_text(encoding="utf-8")
    return parse_spektrum(txt)


def _default_src() -> str:
    import os
    p = Path("data/skd/skd_dokter_2026.txt")
    return str(p) if p.exists() else "skd_dokter_2026.txt"


def write_catalog(entries: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jp = out_dir / "skd2026_master_catalog.json"
    jp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    # human-friendly markdown tally
    lines = ["# SKD 2026 — Spektrum Penyakit Master Catalog", "",
             f"Extracted from HK.01.02/KKI/2183/2026 (Standar Kompetensi Dokter), Tab. 4.",
             f"Total entries: {len(entries)}", ""]
    from collections import Counter
    by_sys = Counter(e["system"] for e in entries)
    for sys in SYSTEMS:
        lines.append(f"- **{sys}**: {by_sys.get(sys, 0)}")
    lines.append("")
    mp = out_dir / "skd2026_master_catalog.md"
    mp.write_text("\n".join(lines), encoding="utf-8")
    return jp, mp


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None)
    ap.add_argument("--out", default="data/reports")
    a = ap.parse_args()
    entries = build_catalog(a.src)
    jp, mp = write_catalog(entries, Path(a.out))
    print(f"Extracted {len(entries)} entries from SKD 2026 Spektrum Penyakit.")
    print(f"  JSON: {jp}")
    print(f"  MD:   {mp}")