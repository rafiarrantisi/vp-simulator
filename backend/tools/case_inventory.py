"""STEP 1 — Legacy case inventory, quarantine & migration foundation.

Read-only audit tool. Scans BOTH case banks:
  - `content/cases/*.md`   → schema-v2 prototype bank (CaseV2)
  - `data-kasus/*.md`      → legacy ophthalmology pair (ParsedCase)

Produces:
  - JSON inventory (machine-readable)
  - Markdown summary (human-readable)
  - duplicate-ID detection (no silent overwrite guard)
  - duplicated-truth risk heuristics (valit/exam facts repeated across frontmatter
    & persona prose — the STEP 1 warning, NOT a rewrite)

NEVER writes, deletes or mutates any case file. Output goes to
`backend/data/reports/step1_inventory.{json,md}` by default.

Usage (from backend/):
    .venv/bin/python -m tools.case_inventory [--outdir data/reports] [--json-only]
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from app.config import get_settings  # noqa: E402
from pipeline.case_v2 import CaseV2, lint, parse_case_v2  # noqa: E402
from pipeline.parser import parse_file, validate  # noqa: E402

# ── duplicated-truth detectors (STEP 1 §4) ─────────────────────────────────
# Heuristic signal extraction; we REPORT, we never change clinical facts.

def _numbers(text: str) -> list[str]:
    return re.findall(r"\b(\d{1,3}(?:\.\d{1,2})?)\s*(?:°?C|bpm|mmHg?|%|kg|mo|yr|hr|d)\b", text.lower())


@dataclass
class DuplicatedTruthFlag:
    case_id: str
    kind: str
    detail: str


def _duplicated_truth(c: CaseV2) -> list[DuplicatedTruthFlag]:
    flags: list[DuplicatedTruthFlag] = []
    fm = c.frontmatter
    body = c.body.lower()

    # 1) Vitals in frontmatter vs vitals in persona prose / physical findings.
    pef = fm.get("physical_exam_findings") or {}
    vitals = pef.get("vitals") if isinstance(pef, dict) else None
    if isinstance(vitals, dict):
        for k, v in vitals.items():
            if not isinstance(v, (int, float)) or v is None:
                continue
            # A numeric vital appearing in Part A (scoring) should be grounded
            # in Part B persona/prose, but must not CONTRADICT (two sets).
            needle = re.escape(str(v))
            # just flag presence of the same number in a different section;
            # deeper contradiction checks are Phase-2 (LLM/graph) work.
            if str(v) in body:
                flags.append(DuplicatedTruthFlag(c.id, "vital_in_both_parts",
                    f"vital `{k}={v}` appears in Part A and persona body"))

    # 2) Age in metadata (identity) vs persona prose age.
    identity = c.find_section("identity").lower()
    au = fm.get("authoring") or {}
    # prototype has no age in frontmatter centrally; check target_condition
    # against working_diagnosis (metadata vs prompt truth).

    # 3) target_condition vs expected_ddx.working_diagnosis mismatch.
    wd = (fm.get("expected_ddx") or {}).get("working_diagnosis") or ""
    tc = fm.get("target_condition") or ""
    if wd and tc and wd.strip().lower() != tc.strip().lower():
        flags.append(DuplicatedTruthFlag(c.id, "diagnosis_mismatch",
            f"target_condition='{tc}' != expected_ddx.working_diagnosis='{wd}'"))

    # 4) chief_complaint echoed in opening line (contradiction risk check).
    opening = c.find_section("opening line").lower()
    cc = (fm.get("chief_complaint") or "").lower().strip().strip(".").strip()
    if cc and opening and cc not in opening and cc.split() and all(
            w in body for w in cc.split()[:3]):
        flags.append(DuplicatedTruthFlag(c.id, "chief_complaint_not_in_opening",
            "chief_complaint wording not reflected in opening line"))

    return flags


@dataclass
class InventoryEntry:
    id: str
    filename: str
    bank: str  # "v2" | "legacy-opth"
    specialty: str
    system: str
    presentation: str
    target_condition: str
    difficulty: object
    status: str
    schema_origin: str
    is_legacy: bool
    source_refs: bool
    competency: bool
    clinical_reviewer: str
    source_count: int
    lint_ok: bool
    warnings: list
    errors: list
    duplicated_truth: list = field(default_factory=list)


def _scan_v2(dir_: Path, out: list[InventoryEntry], flags: list[DuplicatedTruthFlag]) -> None:
    for fp in sorted(dir_.glob("*.md")):
        try:
            c = parse_case_v2(fp)
        except Exception as e:  # noqa: BLE001
            out.append(InventoryEntry(fp.stem, fp.name, "v2", "", "", "", "", None,
                                       "malformed", "unknown", True, False, False, "",
                                       0, False, [], [str(e)], []))
            continue
        res = lint(c)
        lr = _duplicated_truth(c)
        flags.extend(lr)
        fm = c.frontmatter
        out.append(InventoryEntry(
            id=c.id, filename=fp.name, bank="v2",
            specialty=fm.get("specialty") or "", system=fm.get("system") or "",
            presentation=fm.get("presentation") or "",
            target_condition=fm.get("target_condition") or "",
            difficulty=fm.get("difficulty"), status=fm.get("status") or "",
            schema_origin=c.schema_origin(), is_legacy=c.is_legacy(),
            source_refs=bool(c.source_refs()),
            competency=bool(c.competency()),
            clinical_reviewer=c.reviewed_by(),
            source_count=len(c.source_refs()),
            lint_ok=res.ok, warnings=res.warnings, errors=res.errors,
            duplicated_truth=[asdict(f) for f in lr],
        ))


def _scan_legacy(dir_: Path, out: list[InventoryEntry]) -> None:
    for fp in sorted(dir_.glob("*.md")):
        try:
            pc = parse_file(fp)
        except Exception as e:  # noqa: BLE001
            out.append(InventoryEntry(fp.stem, fp.name, "legacy-opth", "", "", "", "",
                                       None, "malformed", "legacy", True, False, False,
                                       "", 0, False, [], [str(e)], []))
            continue
        errs = validate(pc)
        authoring = getattr(pc, "reviewed_by", "")  # not in ParsedCase; safe
        out.append(InventoryEntry(
            id=pc.case_id, filename=fp.name, bank="legacy-opth",
            specialty="ophthalmology", system="ophthalmology",
            presentation=pc.title_en or pc.title_id, target_condition=pc.title_id,
            difficulty=None, status="legacy", schema_origin="legacy", is_legacy=True,
            source_refs=bool(pc.references), competency=bool(pc.skdi),
            clinical_reviewer="", source_count=len(pc.references),
            lint_ok=not errs, warnings=[], errors=errs,
        ))


def _find_duplicate_ids(entries: list[InventoryEntry]) -> list[dict]:
    seen: dict[str, list[str]] = {}
    for e in entries:
        seen.setdefault(e.id, []).append(e.filename)
    return [{"id": k, "files": v} for k, v in seen.items() if len(v) > 1]


def build() -> tuple[dict, list]:
    settings = get_settings()
    v2_dir = Path(settings.content_cases_dir)
    legacy_dir = Path(settings.cases_dir)
    entries: list[InventoryEntry] = []
    flags: list[DuplicatedTruthFlag] = []

    if v2_dir.exists():
        _scan_v2(v2_dir, entries, flags)
    if legacy_dir.exists():
        _scan_legacy(legacy_dir, entries)

    dup_ids = _find_duplicate_ids(entries)

    v2_only = [e for e in entries if e.bank == "v2"]
    legacy_n = sum(1 for e in entries if e.bank == "legacy-opth")
    malformed = [e for e in entries if not e.lint_ok]
    source_backed = [e for e in entries if e.source_refs]
    reviewed = [e for e in entries if e.clinical_reviewer]
    not_legacy = [e for e in entries if not e.is_legacy]

    summary = {
        "total_cases": len(entries),
        "v2_bank": len(v2_only),
        "legacy_ophthalmology_bank": legacy_n,
        "legacy_cohort": sum(1 for e in entries if e.is_legacy),
        "non_legacy": len(not_legacy),
        "source_backed": len(source_backed),
        "with_clinical_reviewer": len(reviewed),
        "structural_issues": len(malformed),
        "duplicate_ids": dup_ids,
        "duplicated_truth_flags": [asdict(f) for f in flags],
    }
    report = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "entries": [asdict(e) for e in entries],
    }
    return report, flags


def write_report(report: dict, flags: list, outdir: Path) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    jp = outdir / "step1_inventory.json"
    jp.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    s = report["summary"]
    lines = [f"# STEP 1 — Case Inventory Report", "",
             f"- Total cases: **{s['total_cases']}**",
             f"- v2 prototype bank (`content/cases`): {s['v2_bank']}",
             f"- legacy ophthalmology bank (`data-kasus`): {s['legacy_ophthalmology_bank']}",
             f"- Legacy cohort (is_legacy): {s['legacy_cohort']}",
             f"- Non-legacy: {s['non_legacy']}",
             f"- Source-backed: {s['source_backed']}",
             f"- With clinical reviewer: {s['with_clinical_reviewer']}",
             f"- Structural issues / lint-fail: {s['structural_issues']}", ""]
    if s["duplicate_ids"]:
        lines.append("## Duplicate IDs (no-silent-overwrite guard)")
        for d in s["duplicate_ids"]:
            lines.append(f"- `{d['id']}`: {', '.join(d['files'])}")
        lines.append("")
    if s["duplicated_truth_flags"]:
        lines.append("## Duplicated-truth risk flags (STEP 1 §4 — report only, not rewritten)")
        for f in s["duplicated_truth_flags"]:
            lines.append(f"- [{f['kind']}] {f['case_id']}: {f['detail']}")
        lines.append("")
    lines.append("## Per-case inventory")
    lines.append("| id | bank | specialty | status | schema | legacy | source_count | reviewer | lint_ok |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for e in report["entries"]:
        lines.append(f"| {e['id']} | {e['bank']} | {e['specialty']} | {e['status'] or '-'} | "
                     f"{e['schema_origin']} | {'L' if e['is_legacy'] else '.'} | "
                     f"{e['source_count']} | {e['clinical_reviewer'] or '-'} | "
                     f"{'OK' if e['lint_ok'] else 'FAIL'} |")
    lines.append("")
    mp = outdir / "step1_inventory.md"
    mp.write_text("\n".join(lines), encoding="utf-8")
    return jp, mp


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(REPO / "data" / "reports"))
    args = ap.parse_args()
    report, flags = build()
    jp, mp = write_report(report, flags, Path(args.outdir))
    s = report["summary"]
    print("STEP 1 inventory written.")
    print(f"  total={s['total_cases']} v2={s['v2_bank']} legacy-opth={s['legacy_ophthalmology_bank']}")
    print(f"  legacy_cohort={s['legacy_cohort']} source_backed={s['source_backed']} reviewer={s['with_clinical_reviewer']}")
    print(f"  structural_issues={s['structural_issues']} duplicate_ids={len(s['duplicate_ids'])}")
    print(f"  duplicated_truth_flags={len(s['duplicated_truth_flags'])}")
    print(f"  JSON: {jp}")
    print(f"  MD:   {mp}")