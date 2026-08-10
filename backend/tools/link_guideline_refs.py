"""Ground every Qora case with authoritative source_refs (PNPK Kemenkes where
one exists, else the standard international guideline). Deterministic — the
mapping is curated in REF_MAP (from docs/PPK_RESEARCH.md 18 verified PNPK +
standard guideline knowledge); no LLM, so nothing can hallucinate.

Usage (from backend/):
  python -m tools.link_guideline_refs [--ids a,b,c] [--dry-run]

REF_MAP: case_id -> [(dedup_token, full_ref_string), ...]
- dedup_token: distinctive substring; if it already appears in the case's
  source_refs, the ref is SKIPPED (idempotent).
- Handles both `source_refs: [...]` (inline) and `source_refs:\n  - "..."` (block).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pipeline.case_v2 import parse_case_v2, lint

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _REPO_ROOT / "content" / "cases"

# ── PNPK Kemenkes (verified on JDIH 9 Aug 2026 — docs/PPK_RESEARCH.md) ──
_PNPK = {
    "stroke": "PNPK Tata Laksana Stroke (KMK 304/2026) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes3042026",
    "dm_t2": "PNPK Tata Laksana Diabetes Melitus Tipe 2 Dewasa (KMK 603/2020) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107m6032020",
    "htn": "PNPK Tata Laksana Hipertensi Dewasa (KMK 4634/2021) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes46342021",
    "glaucoma": "PNPK Tata Laksana Glaukoma (KMK 1488/2023) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14882023",
    "angina": "PNPK Tata Laksana Angina Pektoris Stabil (KMK 1419/2023) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14192023",
    "stunting": "PNPK Tata Laksana Stunting (KMK 1928/2022) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes19282022",
    "tbi": "PNPK Tata Laksana Cedera Otak Traumatik (KMK 1600/2022) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes16002022",
    "bsk": "PNPK Tata Laksana Batu Saluran Kemih (KMK 1560/2022) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes15602022",
    "kehamilan": "PNPK Tata Laksana Komplikasi Kehamilan (KMK 91/2017) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes912017",
    "skizofrenia": "PNPK Tata Laksana Skizofrenia (KMK 970/2025) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes9702025",
    "perdarahan_cerna": "PNPK Tata Laksana Perdarahan Saluran Cerna (KMK 2162/2023) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes21622023",
}

# ── Curation: case_id -> [(dedup_token, ref)] ──
REF_MAP: dict[str, list[tuple[str, str]]] = {
    # ── Dermatology ──
    "derm_cellulitis_001": [("IDSA", "IDSA Skin and Soft Tissue Infections guideline (Stevens et al., 2014)")],
    "derm_eczema_001": [("EDF", "EDF 2022 atopic dermatitis guideline; NICE atopic eczema guidance")],
    "derm_psoriasis_001": [("AAD-NPF", "AAD-NPF psoriasis clinical guidelines (2019); NICE psoriasis CG153")],
    "derm_rosacea_001": [("AAD", "National Rosacea Society / AAD rosacea guidelines (2017)")],
    "derm_suspected_melanoma_001": [("NG14", "NICE NG14 — Melanoma: assessment and management")],
    "derm_tinea_001": [("CKS", "NICE CKS — fungal skin infection (tinea corporis)")],
    "derm_urticaria_001": [("urticaria guideline", "EAACI/GA²LEN/EDF/WAO urticaria guideline (2021)")],
    # ── Emergency ──
    "em_acs_001": [("KMK 1419/2023", _PNPK["angina"]), ("ESC", "ESC guidelines — acute coronary syndromes (2020)")],
    "em_anaphylaxis_001": [("WAO", "WAO Anaphylaxis Guidance (2020)")],
    "em_bacterial_meningitis_001": [("WHO meningitis", "WHO — meningitis outbreak response guidelines")],
    "em_dengue_001": [("WHO", "WHO SEARO dengue guidelines (2009/2011) — dengue fever with warning signs")],
    "em_diabetic_ketoacidosis_001": [("KMK 603/2020", _PNPK["dm_t2"]), ("ISPAD", "ISPAD Clinical Practice Consensus Guidelines — diabetic ketoacidosis (2022)")],
    "em_heat_stroke_001": [("Bouchama", "Bouchama A, Knochel JP. Heat stroke. N Engl J Med 2002")],
    "em_hypertensive_emergency_001": [("KMK 4634/2021", _PNPK["htn"])],
    "em_leptospirosis_001": [("WHO leptospirosis", "WHO leptospirosis guidance + Indonesian outbreak reports")],
    "em_paracetamol_overdose_001": [("NPIS", "UK NPIS/TOXBASE — paracetamol overdose management guidance")],
    "em_pulmonary_embolism_001": [("ESC", "ESC 2019 Guidelines — acute pulmonary embolism")],
    "em_status_asthmaticus_001": [("GINA", "GINA Global Strategy for Asthma Management (2023)")],
    "em_traumatic_brain_injury_001": [("KMK 1600/2022", _PNPK["tbi"])],
    # ── ENT ──
    "ent_bppv_001": [("Bárány", "Bárány Society — BPPV diagnostic criteria and treatment (2017)")],
    "ent_epistaxis_001": [("ENT-UK", "ENT-UK / NICE CKS — epistaxis management")],
    "ent_hearing_loss_001": [("NG98", "NICE NG98 — Hearing loss in adults")],
    "ent_hoarseness_001": [("NG12", "NICE NG12 — suspected head and neck cancer (hoarseness)")],
    "ent_otitis_media_001": [("AAP", "AAP clinical practice guideline — acute otitis media (2013)")],
    "ent_sinusitis_001": [("AAO-HNS", "AAO-HNS clinical practice guideline — acute rhinosinusitis (2015)")],
    "ent_tonsillitis_001": [("NG84", "NICE NG84 — Sore throat (acute)")],
    # ── Internal Medicine ──
    "im_ana_macrocytic_001": [("BSH", "British Committee for Standards in Haematology — vitamin B12/folate (2014)")],
    "im_ckd_001": [("KMK 4634/2021", _PNPK["htn"]), ("KDIGO", "KDIGO 2024 Clinical Practice Guideline — CKD")],
    "im_community_acquired_pneumonia_001": [("ATS/IDSA", "ATS/IDSA community-acquired pneumonia guideline (2019)")],
    "im_gi_appendicitis_001": [("WSES", "WSES Jerusalem guidelines — acute appendicitis (2020)")],
    "im_gord_001": [("ACG", "ACG clinical guideline — gastroesophageal reflux disease (2022)")],
    "im_gout_001": [("ACR", "ACR gout treatment guideline (2020)")],
    "im_hyperthyroid_001": [("ATA", "ATA guidelines — hyperthyroidism (2016)")],
    "im_new_t2dm_001": [("KMK 603/2020", _PNPK["dm_t2"]), ("ADA", "American Diabetes Association Standards of Care (2023)")],
    "im_pancreatitis_001": [("IAP/APA", "IAP/APA evidence-based guidelines — acute pancreatitis (2013)")],
    "im_pye_001": [("IDSA", "IDSA — acute uncomplicated pyelonephritis (2011)")],
    "im_tuberculosis_001": [("WHO", "WHO consolidated TB guidelines; program nasional TB Kemenkes")],
    "im_typhoid_001": [("WHO typhoid", "WHO typhoid fever guidance; Pedoman Pengendalian Demam Tifoid Kemenkes (KMK 364/2006)")],
    "im_uta_001": [("CHEST", "CHEST guideline — antithrombotic therapy for VTE (2021)")],
    # ── Neurology ──
    "neuro_acute_stroke_001": [("KMK 304/2026", _PNPK["stroke"]), ("AHA/ASA", "AHA/ASA acute ischaemic stroke guidelines (2019)")],
    "neuro_first_seizure_001": [("NG127", "NICE NG127 — Epilepsies: first unprovoked seizure")],
    "neuro_gb_syndrome_001": [("Lancet", "Lancet Seminar — Guillain-Barré syndrome (2016)")],
    "neuro_migraine_001": [("ICHD-3", "ICHD-3 diagnostic criteria; AHS migraine position statement (2019)")],
    "neuro_multiple_sclerosis_001": [("NG144", "NICE NG144 — Multiple sclerosis")],
    "neuro_parkinsons_001": [("NG71", "NICE NG71 — Parkinson's disease")],
    "neuro_tia_001": [("KMK 304/2026", _PNPK["stroke"]), ("AHA/ASA", "AHA/ASA guideline — transient ischaemic attack (2009)")],
    # ── Obstetrics & Gynaecology ──
    "og_early_pregnancy_bleeding_001": [("KMK 91/2017", _PNPK["kehamilan"]), ("NG126", "NICE NG126 — Ectopic pregnancy and miscarriage")],
    "og_endometriosis_001": [("ESHRE", "ESHRE guideline — endometriosis (2022)")],
    "og_menorrhagia_001": [("NG88", "NICE NG88 — Heavy menstrual bleeding")],
    "og_pelvic_inflammatory_disease_001": [("CDC", "CDC STI treatment guidelines — pelvic inflammatory disease (2021)")],
    "og_pre_eclampsia_001": [("KMK 91/2017", _PNPK["kehamilan"]), ("NG133", "NICE NG133 — Hypertension in pregnancy")],
    # ── Ophthalmology ──
    "oph_acute_angle_closure_001": [("KMK 1488/2023", _PNPK["glaucoma"])],
    "oph_anterior_uveitis_001": [("AAO", "AAO Preferred Practice Pattern — anterior uveitis")],
    "oph_bacterial_conjunctivitis_001": [("AAO", "AAO Preferred Practice Pattern — conjunctivitis (2018)")],
    "oph_blepharitis_001": [("AAO", "AAO Preferred Practice Pattern — blepharitis")],
    "oph_cataract_001": [("AAO", "AAO Preferred Practice Pattern — cataract (2021)")],
    "oph_crao_001": [("AAO", "AAO Preferred Practice Pattern — retinal vascular disease; AHA statement on retinal ischaemia")],
    "oph_dry_eye_001": [("DEWS", "TFOS DEWS II report (2017) — dry eye")],
    "oph_episcleritis_001": [("AAO", "AAO Preferred Practice Pattern — episcleritis/scleritis")],
    "oph_hordeolum_001": [("AAO", "AAO Preferred Practice Pattern — hordeolum and chalazion")],
    "oph_hyphaema_001": [("AAO", "AAO Preferred Practice Pattern — ocular trauma (hyphaema)")],
    "oph_night_blindness_001": [("WHO", "WHO — vitamin A deficiency (xerophthalmia) management")],
    "oph_optic_neuritis_001": [("ONTT", "Optic Neuritis Treatment Trial (ONTT) — evidence base")],
    "oph_posterior_vitreous_001": [("AAO", "AAO Preferred Practice Pattern — posterior vitreous detachment")],
    "oph_strabismus_001": [("AAO", "AAO Preferred Practice Pattern — strabismus")],
    "oph_trichiasis_001": [("WHO", "WHO trachoma guidelines — trichiasis surgery")],
    # ── Paediatrics ──
    "paed_acute_gastroenteritis_001": [("WHO diarrhoea", "WHO diarrhoea treatment guidelines (ORT, zinc)")],
    "paed_asthma_001": [("GINA", "GINA Global Strategy for Asthma Management (2023)")],
    "paed_bronchiolitis_001": [("AAP", "AAP clinical practice guideline — bronchiolitis (2014)")],
    "paed_coeliac_001": [("ESPGHAN", "ESPGHAN guidelines — coeliac disease (2020)")],
    "paed_febrile_child_001": [("NG143", "NICE NG143 — Fever in under 5s")],
    "paed_febrile_seizure_001": [("NG143", "NICE NG143 — feverish illness; AAP febrile seizures (1996)")],
    "paed_hpylori_001": [("ESPGHAN/NASPGHAN", "ESPGHAN/NASPGHAN — Helicobacter pylori management (2016)")],
    "paed_kawasaki_001": [("AHA", "AHA scientific statement — Kawasaki disease (2017)")],
    "paed_measles_001": [("WHO measles", "WHO measles position paper; IDAI measles guidance")],
    "paed_stunting_001": [("KMK 1928/2022", _PNPK["stunting"]), ("WHO growth", "WHO Child Growth Standards — height-for-age")],
    "paed_uti_001": [("AAP", "AAP — UTI in children guideline (2011); NICE NG224")],
    # ── Psychiatry ──
    "psych_adhd_001": [("NG87", "NICE NG87 — Attention deficit hyperactivity disorder")],
    "psych_alcohol_misuse_001": [("CG115", "NICE CG115 — Alcohol-use disorders")],
    "psych_bipolar_001": [("CG185", "NICE CG185 — Bipolar disorder")],
    "psych_depression_001": [("NG222", "NICE NG222 — Depression in adults")],
    "psych_generalised_anxiety_001": [("CG113", "NICE CG113 — Generalised anxiety disorder")],
    "psych_ocd_001": [("CG31", "NICE CG31 — Obsessive-compulsive disorder")],
    "psych_panic_001": [("CG113", "NICE CG113 — Panic disorder")],
    # ── Surgery ──
    "surg_acute_cholecystitis_001": [("Tokyo", "Tokyo Guidelines (TG18) — acute cholecystitis")],
    "surg_breast_lump_001": [("NG101", "NICE NG101 — Early and locally advanced breast cancer")],
    "surg_diverticulitis_001": [("ASCRS", "ASCRS clinical practice guideline — diverticulitis (2020)")],
    "surg_inguinal_hernia_001": [("EHS", "European Hernia Society — inguinal hernia guideline")],
    "surg_renal_colic_001": [("KMK 1560/2022", _PNPK["bsk"]), ("EAU", "EAU guidelines — urolithiasis (2024)")],
    "surg_testicular_torsion_001": [("EAU", "EAU paediatric urology — testicular torsion")],
    "surg_thyroid_nodule_001": [("ATA", "ATA — thyroid nodule management (2015)")],
    "surg_varicose_veins_001": [("CG168", "NICE CG168 — Varicose veins")],
}


def _current_refs(head: str) -> list[str]:
    """Extract existing refs (block or inline) from the frontmatter text."""
    refs: list[str] = []
    inline = re.search(r"^source_refs:\s*\[(.*)\]$", head, re.M)
    if inline:
        refs = re.findall(r'"([^"]+)"', inline.group(1))
    else:
        # block: lines `  - "ref"` directly under `source_refs:`
        m = re.search(r"^source_refs:\s*\n((?:[ \t]+- .*\n?)+)", head, re.M)
        if m:
            refs = [l.split('"')[1] if '"' in l else l.strip()[3:].strip().strip('"')
                    for l in m.group(1).splitlines() if l.strip().startswith("-")]
    return refs


def _apply(path: Path, pairs: list[tuple[str, str]], dry_run: bool) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    fm = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return False, "no frontmatter"
    head = fm.group(1)
    existing = _current_refs(head)
    existing_joined = "\n".join(existing)

    to_add: list[str] = []
    for token, ref in pairs:
        if token in existing_joined:
            continue
        if ref in existing_joined:
            continue
        to_add.append(ref)
    if not to_add:
        return True, "already grounded (no additions)"

    # Insert new refs into the source_refs list (block format).
    inline = re.search(r"^source_refs:\s*\[(.*)\]$", head, re.M)
    if inline:
        # convert inline -> block, preserving existing refs
        existing_inline = re.findall(r'"([^"]+)"', inline.group(1))
        new_block = "source_refs:\n" + "".join(f'  - "{r}"\n' for r in existing_inline + to_add)
        new_head = head[: inline.start()] + new_block + head[inline.end():]
    else:
        m = re.search(r"^source_refs:\s*\n((?:[ \t]+- .*\n?)+)", head, re.M)
        if not m:
            return False, "source_refs block not found"
        add_lines = "".join(f'  - "{r}"\n' for r in to_add)
        new_head = head[: m.end()] + add_lines + head[m.end():]

    new_text = text[: fm.start()] + "---\n" + new_head + "\n---" + text[fm.end():]

    if dry_run:
        return True, f"[dry-run] would add {len(to_add)} ref(s)"

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
    return True, f"added {len(to_add)} ref(s): {', '.join(t[:40] for t, _ in pairs if t not in existing_joined)}"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Ground source_refs with PNPK/guidelines")
    ap.add_argument("--ids", help="comma-separated case ids")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    files = sorted(_CASES_DIR.glob("*.md"))
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
        files = [f for f in files if f.stem in wanted]

    ok = fail = added_total = 0
    unmapped: list[str] = []
    for fp in files:
        pairs = REF_MAP.get(fp.stem)
        if not pairs:
            unmapped.append(fp.stem)
            continue
        done, msg = _apply(fp, pairs, args.dry_run)
        print(f"  {'✓' if done else '✗'} {fp.stem}: {msg}", flush=True)
        ok += done
        fail += not done
        if "added" in msg:
            added_total += 1

    print(f"\nProcessed {ok} ok; {fail} failed; {added_total} cases got new refs.")
    if unmapped:
        print("NOT in mapping (skipped):", ", ".join(unmapped))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
