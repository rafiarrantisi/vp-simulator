"""Gov: kurasi set pilot pre-pilot & normalisasi review-state (master plan §6/§11).

Deterministik + idempotent, no-LLM. Memodifikasi frontmatter schema-v2:
  1. status: in_review -> ai_generated  (semua 92: AI-drafted, belum review klinis)
  2. Set kurasi pilot -> status in_review + pilot_candidate:true + blok `competency`
     (SKDI version-aware, level diisi reviewer — §6.2 jangan isi level dari memori)
     + authoring.review_notes penanda "pending clinical sign-off".

Run:
  python -m tools.pilot_curate_v2 --apply     # lakukan migrasi
  python -m tools.pilot_curate_v2 --dry-run  # print perubahan tanpa menulis

Verifikasi setelahnya: `python -m tools.lint_case --all` -> 0 error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _REPO_ROOT / "content" / "cases"

# Set pilot: 24 kasus, merata 6 spesialisasi inti koas/OSCE (plan §6.2), utamakan
# mode osce_full + yang sudah grounded PNPK bila ada. Level SKDI dibiarkan null
# (reviwer klinis yang mengisi, per §6.2/§6.2 requirement 6).
PILOT_SET = [
    # internal_medicine (4)
    "im_ckd_001", "im_community_acquired_pneumonia_001", "im_tuberculosis_001",
    "im_typhoid_001",
    # emergency (4)
    "em_acs_001", "em_dengue_001", "em_diabetic_ketoacidosis_001",
    "em_status_asthmaticus_001",
    # paediatrics (4)
    "paed_acute_gastroenteritis_001", "paed_febrile_child_001",
    "paed_bronchiolitis_001", "paed_stunting_001",
    # neurology (4)
    "neuro_acute_stroke_001", "neuro_first_seizure_001", "neuro_tia_001",
    "neuro_migraine_001",
    # surgery (4)
    "surg_acute_cholecystitis_001", "surg_renal_colic_001",
    "surg_inguinal_hernia_001", "surg_testicular_torsion_001",
    # obstetrics & gynaecology (4)
    "og_pre_eclampsia_001", "og_early_pregnancy_bleeding_001",
    "og_pelvic_inflammatory_disease_001", "og_menorrhagia_001",
]

COMPETENCY_BLOCK = {
    "standard": "SKDI",          # Standar Kompetensi Dokter Indonesia
    "authority": "Konsil Kesehatan Indonesia (KKI)",
    "version": "2012",           # versi SKDI terakhir yang dipublikasikan KKI
    "level": None,               # Wajib diisi reviewer klinis — §6.2 forbids agent-assigned
    "status": "pending_review",  # versi-aware: perlu pengecekan ke sumber mutakhir
}

PENDING_NOTE = (
    "Kurasi pilot candidate (plan §6.2). Belum ada clinical sign-off — WAJIB direview "
    "dokter/pendidik sebelum pilot_verified/published (§11)."
)


def _split(fp: Path) -> tuple[dict, str, bool]:
    text = fp.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text, False
    # Frontmatter = `---\n<yaml>\n---\n<body>`.
    m = re.match(r"^---\n(.*?)\n---\n([\s\S]*)$", text, re.DOTALL)
    if not m:
        return {}, text, False
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, text, False
    if not isinstance(fm, dict):
        return {}, text, False
    return dict(fm), m.group(2), True


def _join_md_return(fm: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n" + body


def migrate(apply: bool) -> dict:
    changed_any = 0
    pilot_changed = 0
    missing = []
    for fp in sorted(_CASES_DIR.glob("*.md")):
        fm, body, ok = _split(fp)
        if not ok:
            continue
        cid = str(fm.get("id") or fp.stem)
        before = dict(fm)

        # Stage 1: normalkan status lahir = ai_generated (belum direview).
        if fm.get("status", "in_review") == "in_review":
            fm["status"] = "ai_generated"

        # Stage 2: set pilot.
        if cid in PILOT_SET:
            fm["status"] = "in_review"          # di-flag menuju clinical review
            fm["pilot_candidate"] = True
            fm.setdefault("competency", COMPETENCY_BLOCK)
            au = fm.setdefault("authoring", {})
            if not isinstance(au, dict):
                au = fm["authoring"] = {}
            au["review_notes"] = PENDING_NOTE
            pilot_changed += 1

        if fm == before:
            continue
        changed_any += 1
        if apply:
            _CASES_DIR.joinpath(f"{cid}.md").write_text(
                _join_md_return(fm, body), encoding="utf-8")

    for cid in PILOT_SET:
        if not _CASES_DIR.joinpath(f"{cid}.md").exists():
            missing.append(cid)
    return {"changed": changed_any, "pilot_curated": pilot_changed, "missing": missing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Kurasi set pilot + normalisasi review-state schema-v2")
    ap.add_argument("--apply", action="store_true", help="Tulis perubahan ke file (default: dry-run)")
    args = ap.parse_args(argv)
    res = migrate(apply=args.apply)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] files diubah: {res['changed']} · pilot dikurasi: {res['pilot_curated']}")
    if res["missing"]:
        print("WARN: id pilot tidak ketemu:", res["missing"])
    print("Verifikasi lanjutan: python -m tools.lint_case --all  (harus 0 error)")
    return 0


if __name__ == "__main__":
    sys.exit(main())