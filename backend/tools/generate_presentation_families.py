"""Phase 4 continuation — presentation families (reuse variant refs, zero duplication)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml

CONTENT = ROOT.parent / "content" / "v3"

PRESENTATIONS: list[dict] = [
dict(id="fam_pres_chest_pain", tid="Nyeri Dada", ten="Chest Pain",
     complaints=["Chest pain", "Chest pressure"],
     refs=["acs_typical_stemi", "acs_atypical_elderly", "gerd_chestpain_ruleout",
           "hf_edema_workup", "hf_chronic_recog"],
     obj=["Triage cardiac vs non-cardiac chest pain", "Apply ECG/troponin pathway thinking",
          "Refer ACS-pattern cases without delay"]),
dict(id="fam_pres_dyspnea", tid="Sesak Napas", ten="Shortness of Breath",
     complaints=["Shortness of breath", "Difficulty breathing"],
     refs=["cap_moderate_admit", "copd_exacerbation", "asthma_exacerbation",
           "hf_acute_decomp", "status_asthma_severe", "anaphylaxis_typical_food"],
     obj=["Grade severity with vitals/SpO2", "Separate cardiac vs respiratory vs anaphylaxis patterns",
          "Stabilize and refer severe cases"]),
dict(id="fam_pres_fever", tid="Demam", ten="Fever",
     complaints=["Fever", "Prolonged fever"],
     refs=["typhoid_uncomplicated", "malaria_uncomplicated", "dengue_001_mild",
           "uti_adult_002", "measles_uncomplicated", "typhoid_prolonged"],
     obj=["Map fever pattern + exposures", "Choose first-line tests per pattern",
          "Detect warning signs needing admission"]),
dict(id="fam_pres_abdomen", tid="Nyeri Perut", ten="Abdominal Pain",
     complaints=["Abdominal pain", "Stomach ache"],
     refs=["appendicitis_typical", "gastritis_acute_nsaid", "cholecystitis_acute",
           "ectopic_stable_workup", "gastroenteritis_watery_mild", "gerd_typical"],
     obj=["Localize pain + peritoneal signs", "Separate surgical vs medical abdomen",
          "Refer surgical patterns early"]),
dict(id="fam_pres_headache", tid="Sakit Kepala", ten="Headache",
     complaints=["Headache", "Severe headache"],
     refs=["tension_headache_episodic", "migraine_without_aura", "meningitis_early_subtle",
           "htn_crisis_urgency"],
     obj=["Screen headache red flags first", "Distinguish primary vs secondary patterns",
          "Refer thunderclap/meningitis patterns emergently"]),
dict(id="fam_pres_vaginal_bleed", tid="Perdarahan Vagina", ten="Vaginal Bleeding",
     complaints=["Vaginal bleeding", "Bleeding in pregnancy"],
     refs=["abortion_threatened", "ectopic_stable_workup", "aub_heavy_stable"],
     obj=["Quantify bleeding + pregnancy test first", "Separate obstetric vs gynecologic causes",
          "Resuscitate heavy bleeders + refer"]),
dict(id="fam_pres_red_eye", tid="Mata Merah", ten="Red Eye",
     complaints=["Red eye", "Painful red eye"],
     refs=["conjunctivitis_bacterial", "conjunctivitis_viral", "conjunctivitis_allergic",
           "keratitis_lens_related", "glaucoma_subacute"],
     obj=["Separate benign vs sight-threatening red eye", "Check vision/pain/halos triad",
          "Refer keratitis/glaucoma patterns same-day"]),
dict(id="fam_pres_rash", tid="Ruam", ten="Rash",
     complaints=["Skin rash", "Itchy rash with fever"],
     refs=["measles_uncomplicated", "chickenpox_typical", "drug_eruption_morbilliform",
           "scabies_household", "atopic_child_flexural"],
     obj=["Describe morphology + distribution", "Link drugs/exposures/household spread",
          "Detect blistering/erythroderma emergencies"]),
dict(id="fam_pres_joint", tid="Nyeri Sendi", ten="Joint Pain",
     complaints=["Painful swollen joint", "Joint pain"],
     refs=["gout_acute_podagra", "oa_early", "septic_joint_knee", "gout_recurrent_hyperu"],
     obj=["Separate mono vs poly patterns", "Treat hot joint as emergency until proven otherwise",
          "Plan gout vs OA long-term care"]),
]


def main() -> int:
    from pipeline.case_v3.loader import CaseRegistry
    reg = CaseRegistry.from_dir()
    n = 0
    for p in PRESENTATIONS:
        missing = [r for r in p["refs"] if r not in reg.variants]
        if missing:
            raise SystemExit(f"{p['id']} refs missing variants: {missing}")
        fam = dict(
            id=p["id"], family_type="presentation",
            title_id=p["tid"], title_en=p["ten"],
            primary_specialty="internal_medicine",
            cross_specialty_tags=["emergency", "paediatrics"],
            presenting_complaints=list(p["complaints"]),
            population_tags=["adult", "child"],
            target_stages=["preclinical", "koas"],
            skdi_mappings={},
            learning_objectives=list(p["obj"]),
            common_differentials=[],
            active_variant_ids=list(p["refs"]),
            source_governance=dict(
                policy="presentation umbrella — reuses canonical disease variants, holds no clinical truth of its own",
                version="2026-09"),
            status="in_review")
        (CONTENT / "families" / f"{p['id']}.yaml").write_text(
            yaml.safe_dump(fam, allow_unicode=True, sort_keys=False), encoding="utf-8")
        n += 1
    print(f"presentation families={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
