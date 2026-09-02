"""STEP 4 — Build the Qora SKD 2026 master catalog (planning backbone).

Takes the extracted Spektrum Penyakit catalog and enriches each entry with the
planning fields from 04_SKDI_CATALOG_AND_SPECIALTY_ROADMAP.md §2:

  - id (stable, slug)
  - system (SKD 2026 bucket)
  - category (tuntas | initial_management_and_referral)  [official 2026]
  - skd2026_name  (official wording preserved verbatim)
  - current_display_name (normalized, human-readable; may differ)
  - legacy SKDI 2012 crosswalk placeholders (null; populated in a later pass
    only when the same disease is verified in SKDI 2012 — never inferred)

The catalog is the planning backbone; it is NOT clinical-generation content.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str, system: str) -> str:
    s = _SLUG_RE.sub("-", name.lower()).strip("-")
    s = s[:80].strip("-")
    sys_prefix = system.split("_")[0] if system else "x"
    return f"{sys_prefix}_{s}"


def current_display(skd2026: str) -> str:
    """Normalized display name — can diverge from official wording WITHOUT
    touching the official `skd2026_name` (STEP 4 §4). Here we only clean
    punctuation/abbreviation whitespace; clinical normalization is a
    human/nomenclature-review task, so we keep it conservative."""
    s = re.sub(r"\s+", " ", skd2026).strip()
    # light normalization: expand common abbreviations only where safe/neutral
    return s


def enrich(entries: list[dict]) -> list[dict]:
    out = []
    used_ids: dict[str, int] = {}
    for e in entries:
        base = slugify(e["skd2026_name"], e["system"])
        n = used_ids.get(base, 0) + 1
        used_ids[base] = n
        cid = f"{base}__{n}" if n > 1 else base
        out.append({
            "id": cid,
            "system": e["system"],
            "category": e["category"],
            "skd2026_name": e["skd2026_name"],
            "current_display_name": current_display(e["skd2026_name"]),
            "source": {"standard": "SKD 2026",
                       "reference": "HK.01.02/KKI/2183/2026",
                       "doc": "Standar Kompetensi Dokter 2026",
                       "table": "4. Spektrum Penyakit",
                       "locator": e.get("locator", "")},
            "legacy_competency": {"standard": "SKDI 2012", "level": None,
                                  "mapping_confirmed": False,
                                  "note": "not yet crosswalked (requires SKDI 2012 verification)"},
            "candidate_family_status": "unclassified",
        })
    return out


def build(src_json: str, out_json: str, out_md: str) -> tuple[int, Path, Path]:
    entries = json.loads(Path(src_json).read_text(encoding="utf-8"))
    enriched = enrich(entries)
    ojp = Path(out_json)
    ojp.parent.mkdir(parents=True, exist_ok=True)
    ojp.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")

    # human-readable markdown report
    from collections import Counter
    by_sys = Counter(e["system"] for e in enriched)
    by_cat = Counter(e["category"] for e in enriched)
    lines = [
        "# Qora — SKD 2026 Master Catalog (planning backbone)",
        "",
        "Single primary competency authority: **SKD 2026 (HK.01.02/KKI/2183/2026)", "Tab.4 Spektrum Penyakit**. SKDI 2012 (3A/3B/4A) is a LEGACY crosswalk only.",
        "",
        f"Total entries: **{len(enriched)}**",
        "",
        "## By category (official 2026)",
        "",
    ]
    for k, v in sorted(by_cat.items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## By system", ""]
    for k in sorted(by_sys, key=lambda x: -by_sys[x]):
        lines.append(f"- **{k}**: {by_sys[k]}")
    lines += ["", "## Ambiguous / needs human review", ""]
    # duplicate normalized names in the same system+category → flag for review
    dup = {}
    for e in enriched:
        key = (e["system"], e["current_display_name"].strip().lower())
        dup.setdefault(key, []).append(e["id"])
    flagged = [ids for ids in dup.values() if len(ids) > 1]
    if flagged:
        for ids in flagged:
            lines.append(f"- possible duplicate: {ids}")
    else:
        lines.append("- none")
    omp = Path(out_md)
    omp.write_text("\n".join(lines), encoding="utf-8")
    return len(enriched), ojp, omp


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    src = ap.add_argument("--src", default="data/reports/skd2026_master_catalog.json")
    out = ap.add_argument("--out", default="content/v3/catalog/skd2026_master_catalog.json")
    md = ap.add_argument("--md", default="content/v3/catalog/skd2026_master_catalog.md")
    a = ap.parse_args()
    n, jp, mp = build(a.src, a.out, a.md)
    print(f"Master catalog: {n} entries")
    print(f"  JSON: {jp}")
    print(f"  MD:   {mp}")