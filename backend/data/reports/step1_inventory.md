# STEP 1 — Case Inventory Report

- Total cases: **123**
- v2 prototype bank (`content/cases`): 92
- legacy ophthalmology bank (`data-kasus`): 31
- Legacy cohort (is_legacy): 123
- Non-legacy: 0
- Source-backed: 123
- With clinical reviewer: 0
- Structural issues / lint-fail: 0

## Duplicated-truth risk flags (STEP 1 §4 — report only, not rewritten)
- [chief_complaint_not_in_opening] derm_cellulitis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] derm_eczema_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] derm_psoriasis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] derm_suspected_melanoma_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] derm_tinea_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] em_acs_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] em_bacterial_meningitis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_dengue_001: vital `temperature=38.7` appears in Part A and persona body
- [vital_in_both_parts] em_dengue_001: vital `heart_rate=110` appears in Part A and persona body
- [vital_in_both_parts] em_dengue_001: vital `respiratory_rate=22` appears in Part A and persona body
- [vital_in_both_parts] em_dengue_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_dengue_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_diabetic_ketoacidosis_001: vital `HR=110` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_diabetic_ketoacidosis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_hypertensive_emergency_001: vital `hr=100` appears in Part A and persona body
- [vital_in_both_parts] em_hypertensive_emergency_001: vital `rr=18` appears in Part A and persona body
- [vital_in_both_parts] em_hypertensive_emergency_001: vital `temp=36.8` appears in Part A and persona body
- [vital_in_both_parts] em_hypertensive_emergency_001: vital `spo2=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_hypertensive_emergency_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_leptospirosis_001: vital `temperature=39.5` appears in Part A and persona body
- [vital_in_both_parts] em_leptospirosis_001: vital `heart_rate=100` appears in Part A and persona body
- [vital_in_both_parts] em_leptospirosis_001: vital `respiratory_rate=20` appears in Part A and persona body
- [vital_in_both_parts] em_leptospirosis_001: vital `oxygen_saturation=97` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_leptospirosis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_paracetamol_overdose_001: vital `hr=88` appears in Part A and persona body
- [vital_in_both_parts] em_paracetamol_overdose_001: vital `rr=16` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_paracetamol_overdose_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_pulmonary_embolism_001: vital `heart_rate=110` appears in Part A and persona body
- [vital_in_both_parts] em_pulmonary_embolism_001: vital `respiratory_rate=24` appears in Part A and persona body
- [vital_in_both_parts] em_status_asthmaticus_001: vital `RR=32` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_status_asthmaticus_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] em_traumatic_brain_injury_001: vital `temperature=36.8` appears in Part A and persona body
- [vital_in_both_parts] em_traumatic_brain_injury_001: vital `heart_rate=90` appears in Part A and persona body
- [vital_in_both_parts] em_traumatic_brain_injury_001: vital `respiratory_rate=18` appears in Part A and persona body
- [vital_in_both_parts] em_traumatic_brain_injury_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] em_traumatic_brain_injury_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] ent_bppv_001: vital `hr=72` appears in Part A and persona body
- [chief_complaint_not_in_opening] ent_bppv_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] ent_epistaxis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] ent_hearing_loss_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] ent_hoarseness_001: vital `temp=36.8` appears in Part A and persona body
- [chief_complaint_not_in_opening] ent_hoarseness_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] ent_otitis_media_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] ent_sinusitis_001: vital `temp=37.8` appears in Part A and persona body
- [vital_in_both_parts] ent_sinusitis_001: vital `hr=80` appears in Part A and persona body
- [vital_in_both_parts] ent_sinusitis_001: vital `o2=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] ent_sinusitis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] ent_tonsillitis_001: vital `heart_rate=98` appears in Part A and persona body
- [vital_in_both_parts] ent_tonsillitis_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] ent_tonsillitis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_ana_macrocytic_001: vital `respiratory_rate=16` appears in Part A and persona body
- [chief_complaint_not_in_opening] im_ana_macrocytic_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] im_ckd_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_community_acquired_pneumonia_001: vital `temperature=38.5` appears in Part A and persona body
- [vital_in_both_parts] im_community_acquired_pneumonia_001: vital `respiratory_rate=22` appears in Part A and persona body
- [vital_in_both_parts] im_community_acquired_pneumonia_001: vital `oxygen_saturation=94` appears in Part A and persona body
- [chief_complaint_not_in_opening] im_community_acquired_pneumonia_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_gi_appendicitis_001: vital `hr=98` appears in Part A and persona body
- [vital_in_both_parts] im_gi_appendicitis_001: vital `rr=18` appears in Part A and persona body
- [diagnosis_mismatch] im_gi_appendicitis_001: target_condition='Appendicitis' != expected_ddx.working_diagnosis='Acute appendicitis'
- [chief_complaint_not_in_opening] im_gord_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] im_gout_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_hyperthyroid_001: vital `temperature=37.2` appears in Part A and persona body
- [vital_in_both_parts] im_hyperthyroid_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [vital_in_both_parts] im_new_t2dm_001: vital `rr=16` appears in Part A and persona body
- [vital_in_both_parts] im_new_t2dm_001: vital `weight=90` appears in Part A and persona body
- [chief_complaint_not_in_opening] im_new_t2dm_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] im_pye_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_tuberculosis_001: vital `respiratory_rate=20` appears in Part A and persona body
- [vital_in_both_parts] im_tuberculosis_001: vital `temperature=37.8` appears in Part A and persona body
- [vital_in_both_parts] im_tuberculosis_001: vital `oxygen_saturation=97` appears in Part A and persona body
- [chief_complaint_not_in_opening] im_tuberculosis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] im_typhoid_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] im_uta_001: vital `heart_rate=88` appears in Part A and persona body
- [vital_in_both_parts] im_uta_001: vital `respiratory_rate=16` appears in Part A and persona body
- [vital_in_both_parts] im_uta_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] im_uta_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] neuro_first_seizure_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] neuro_gb_syndrome_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] neuro_multiple_sclerosis_001: vital `o2=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] neuro_multiple_sclerosis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] neuro_parkinsons_001: vital `hr=72` appears in Part A and persona body
- [chief_complaint_not_in_opening] neuro_parkinsons_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] neuro_tia_001: vital `RR=16` appears in Part A and persona body
- [chief_complaint_not_in_opening] neuro_tia_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] og_early_pregnancy_bleeding_001: vital `hr=78` appears in Part A and persona body
- [vital_in_both_parts] og_early_pregnancy_bleeding_001: vital `spo2=99` appears in Part A and persona body
- [chief_complaint_not_in_opening] og_early_pregnancy_bleeding_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] og_endometriosis_001: vital `temp=36.8` appears in Part A and persona body
- [chief_complaint_not_in_opening] og_endometriosis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] og_menorrhagia_001: vital `temp=36.8` appears in Part A and persona body
- [chief_complaint_not_in_opening] og_menorrhagia_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] og_pelvic_inflammatory_disease_001: vital `heart_rate=95` appears in Part A and persona body
- [vital_in_both_parts] og_pelvic_inflammatory_disease_001: vital `respiratory_rate=18` appears in Part A and persona body
- [chief_complaint_not_in_opening] og_pelvic_inflammatory_disease_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] og_pre_eclampsia_001: vital `HR=88` appears in Part A and persona body
- [vital_in_both_parts] og_pre_eclampsia_001: vital `Temp=37.0` appears in Part A and persona body
- [chief_complaint_not_in_opening] og_pre_eclampsia_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_acute_angle_closure_001: target_condition='Acute angle-closure glaucoma' != expected_ddx.working_diagnosis='Acute primary angle-closure glaucoma, right eye'
- [chief_complaint_not_in_opening] oph_acute_angle_closure_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] oph_anterior_uveitis_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_bacterial_conjunctivitis_001: target_condition='Bacterial conjunctivitis' != expected_ddx.working_diagnosis='Acute bacterial conjunctivitis (both eyes)'
- [chief_complaint_not_in_opening] oph_bacterial_conjunctivitis_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_blepharitis_001: target_condition='Chronic blepharitis' != expected_ddx.working_diagnosis='Chronic blepharitis (seborrhoeic/mixed), both eyes'
- [diagnosis_mismatch] oph_cataract_001: target_condition='Senile cataract' != expected_ddx.working_diagnosis='Immature senile cataract, both eyes'
- [vital_in_both_parts] oph_crao_001: vital `o2_sat=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] oph_crao_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_dry_eye_001: target_condition='Dry eye disease' != expected_ddx.working_diagnosis='Dry eye disease (evaporative, screen-use related)'
- [chief_complaint_not_in_opening] oph_dry_eye_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_episcleritis_001: target_condition='Episcleritis' != expected_ddx.working_diagnosis='Simple episcleritis, right eye'
- [chief_complaint_not_in_opening] oph_episcleritis_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_hordeolum_001: target_condition='Hordeolum (stye)' != expected_ddx.working_diagnosis='External hordeolum (stye), right upper eyelid'
- [diagnosis_mismatch] oph_hyphaema_001: target_condition='Traumatic hyphaema' != expected_ddx.working_diagnosis='Traumatic hyphaema, right eye'
- [chief_complaint_not_in_opening] oph_hyphaema_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_night_blindness_001: target_condition='Vitamin A deficiency (night blindness)' != expected_ddx.working_diagnosis='Night blindness due to vitamin A deficiency'
- [chief_complaint_not_in_opening] oph_optic_neuritis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] oph_posterior_vitreous_001: chief_complaint wording not reflected in opening line
- [diagnosis_mismatch] oph_strabismus_001: target_condition='Strabismus' != expected_ddx.working_diagnosis='Strabismus (esotropia)'
- [chief_complaint_not_in_opening] oph_strabismus_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] oph_trichiasis_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] paed_acute_gastroenteritis_001: vital `temperature=37.8` appears in Part A and persona body
- [vital_in_both_parts] paed_acute_gastroenteritis_001: vital `heart_rate=130` appears in Part A and persona body
- [vital_in_both_parts] paed_acute_gastroenteritis_001: vital `respiratory_rate=30` appears in Part A and persona body
- [vital_in_both_parts] paed_acute_gastroenteritis_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] paed_bronchiolitis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] paed_coeliac_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] paed_febrile_child_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] paed_febrile_seizure_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] paed_hpylori_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] paed_kawasaki_001: vital `heart_rate=140` appears in Part A and persona body
- [vital_in_both_parts] paed_kawasaki_001: vital `respiratory_rate=28` appears in Part A and persona body
- [chief_complaint_not_in_opening] paed_measles_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] paed_stunting_001: vital `temperature=36.5` appears in Part A and persona body
- [vital_in_both_parts] paed_stunting_001: vital `heart_rate=100` appears in Part A and persona body
- [vital_in_both_parts] paed_stunting_001: vital `respiratory_rate=24` appears in Part A and persona body
- [vital_in_both_parts] paed_stunting_001: vital `oxygen_saturation=98` appears in Part A and persona body
- [chief_complaint_not_in_opening] paed_stunting_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] psych_adhd_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] psych_bipolar_001: vital `temp=36.8` appears in Part A and persona body
- [chief_complaint_not_in_opening] psych_bipolar_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] psych_ocd_001: vital `hr=92` appears in Part A and persona body
- [vital_in_both_parts] psych_ocd_001: vital `rr=16` appears in Part A and persona body
- [vital_in_both_parts] psych_ocd_001: vital `o2sat=99` appears in Part A and persona body
- [vital_in_both_parts] psych_panic_001: vital `hr=88` appears in Part A and persona body
- [vital_in_both_parts] psych_panic_001: vital `rr=16` appears in Part A and persona body
- [chief_complaint_not_in_opening] psych_panic_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_acute_cholecystitis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_breast_lump_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_diverticulitis_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_inguinal_hernia_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_renal_colic_001: chief_complaint wording not reflected in opening line
- [vital_in_both_parts] surg_thyroid_nodule_001: vital `hr=78` appears in Part A and persona body
- [vital_in_both_parts] surg_thyroid_nodule_001: vital `rr=14` appears in Part A and persona body
- [chief_complaint_not_in_opening] surg_thyroid_nodule_001: chief_complaint wording not reflected in opening line
- [chief_complaint_not_in_opening] surg_varicose_veins_001: chief_complaint wording not reflected in opening line

## Per-case inventory
| id | bank | specialty | status | schema | legacy | source_count | reviewer | lint_ok |
|---|---|---|---|---|---|---|---|---|
| derm_cellulitis_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| derm_eczema_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| derm_psoriasis_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| derm_rosacea_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| derm_suspected_melanoma_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| derm_tinea_001 | v2 | dermatology | ai_generated | v2-legacy | L | 1 | - | OK |
| derm_urticaria_001 | v2 | dermatology | ai_generated | v2-legacy | L | 2 | - | OK |
| em_acs_001 | v2 | emergency | in_review | v2-legacy | L | 2 | - | OK |
| em_anaphylaxis_001 | v2 | emergency | ai_generated | v2-legacy | L | 2 | - | OK |
| em_bacterial_meningitis_001 | v2 | emergency | ai_generated | v2-legacy | L | 1 | - | OK |
| em_dengue_001 | v2 | emergency | in_review | v2-legacy | L | 1 | - | OK |
| em_diabetic_ketoacidosis_001 | v2 | emergency | in_review | v2-legacy | L | 3 | - | OK |
| em_heat_stroke_001 | v2 | emergency | ai_generated | v2-legacy | L | 2 | - | OK |
| em_hypertensive_emergency_001 | v2 | emergency | ai_generated | v2-legacy | L | 1 | - | OK |
| em_leptospirosis_001 | v2 | emergency | ai_generated | v2-legacy | L | 1 | - | OK |
| em_paracetamol_overdose_001 | v2 | emergency | ai_generated | v2-legacy | L | 2 | - | OK |
| em_pulmonary_embolism_001 | v2 | emergency | ai_generated | v2-legacy | L | 2 | - | OK |
| em_status_asthmaticus_001 | v2 | emergency | in_review | v2-legacy | L | 1 | - | OK |
| em_traumatic_brain_injury_001 | v2 | emergency | ai_generated | v2-legacy | L | 1 | - | OK |
| ent_bppv_001 | v2 | ent | ai_generated | v2-legacy | L | 2 | - | OK |
| ent_epistaxis_001 | v2 | ent | ai_generated | v2-legacy | L | 2 | - | OK |
| ent_hearing_loss_001 | v2 | ent | ai_generated | v2-legacy | L | 2 | - | OK |
| ent_hoarseness_001 | v2 | ent | ai_generated | v2-legacy | L | 1 | - | OK |
| ent_otitis_media_001 | v2 | ent | ai_generated | v2-legacy | L | 1 | - | OK |
| ent_sinusitis_001 | v2 | ent | ai_generated | v2-legacy | L | 2 | - | OK |
| ent_tonsillitis_001 | v2 | ent | ai_generated | v2-legacy | L | 2 | - | OK |
| im_ana_macrocytic_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_ckd_001 | v2 | internal_medicine | in_review | v2-legacy | L | 2 | - | OK |
| im_community_acquired_pneumonia_001 | v2 | internal_medicine | in_review | v2-legacy | L | 2 | - | OK |
| im_gi_appendicitis_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 3 | - | OK |
| im_gord_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_gout_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_hyperthyroid_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_new_t2dm_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_pancreatitis_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_pye_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| im_tuberculosis_001 | v2 | internal_medicine | in_review | v2-legacy | L | 1 | - | OK |
| im_typhoid_001 | v2 | internal_medicine | in_review | v2-legacy | L | 1 | - | OK |
| im_uta_001 | v2 | internal_medicine | ai_generated | v2-legacy | L | 2 | - | OK |
| neuro_acute_stroke_001 | v2 | neurology | in_review | v2-legacy | L | 3 | - | OK |
| neuro_first_seizure_001 | v2 | neurology | in_review | v2-legacy | L | 1 | - | OK |
| neuro_gb_syndrome_001 | v2 | neurology | ai_generated | v2-legacy | L | 2 | - | OK |
| neuro_migraine_001 | v2 | neurology | in_review | v2-legacy | L | 1 | - | OK |
| neuro_multiple_sclerosis_001 | v2 | neurology | ai_generated | v2-legacy | L | 2 | - | OK |
| neuro_parkinsons_001 | v2 | neurology | ai_generated | v2-legacy | L | 1 | - | OK |
| neuro_tia_001 | v2 | neurology | in_review | v2-legacy | L | 2 | - | OK |
| og_early_pregnancy_bleeding_001 | v2 | obstetrics_gynaecology | in_review | v2-legacy | L | 2 | - | OK |
| og_endometriosis_001 | v2 | obstetrics_gynaecology | ai_generated | v2-legacy | L | 2 | - | OK |
| og_menorrhagia_001 | v2 | obstetrics_gynaecology | in_review | v2-legacy | L | 1 | - | OK |
| og_pelvic_inflammatory_disease_001 | v2 | obstetrics_gynaecology | in_review | v2-legacy | L | 1 | - | OK |
| og_pre_eclampsia_001 | v2 | obstetrics_gynaecology | in_review | v2-legacy | L | 2 | - | OK |
| oph_acute_angle_closure_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_anterior_uveitis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 1 | - | OK |
| oph_bacterial_conjunctivitis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_blepharitis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_cataract_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_crao_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| oph_dry_eye_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_episcleritis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_hordeolum_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_hyphaema_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 3 | - | OK |
| oph_night_blindness_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| oph_optic_neuritis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| oph_posterior_vitreous_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| oph_strabismus_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| oph_trichiasis_001 | v2 | ophthalmology | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_acute_gastroenteritis_001 | v2 | paediatrics | in_review | v2-legacy | L | 1 | - | OK |
| paed_asthma_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 1 | - | OK |
| paed_bronchiolitis_001 | v2 | paediatrics | in_review | v2-legacy | L | 2 | - | OK |
| paed_coeliac_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_febrile_child_001 | v2 | paediatrics | in_review | v2-legacy | L | 1 | - | OK |
| paed_febrile_seizure_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_hpylori_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_kawasaki_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_measles_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| paed_stunting_001 | v2 | paediatrics | in_review | v2-legacy | L | 2 | - | OK |
| paed_uti_001 | v2 | paediatrics | ai_generated | v2-legacy | L | 2 | - | OK |
| psych_adhd_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 1 | - | OK |
| psych_alcohol_misuse_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 2 | - | OK |
| psych_bipolar_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 1 | - | OK |
| psych_depression_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 2 | - | OK |
| psych_generalised_anxiety_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 2 | - | OK |
| psych_ocd_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 2 | - | OK |
| psych_panic_001 | v2 | psychiatry | ai_generated | v2-legacy | L | 2 | - | OK |
| surg_acute_cholecystitis_001 | v2 | surgery | in_review | v2-legacy | L | 2 | - | OK |
| surg_breast_lump_001 | v2 | surgery | ai_generated | v2-legacy | L | 2 | - | OK |
| surg_diverticulitis_001 | v2 | surgery | ai_generated | v2-legacy | L | 2 | - | OK |
| surg_inguinal_hernia_001 | v2 | surgery | in_review | v2-legacy | L | 3 | - | OK |
| surg_renal_colic_001 | v2 | surgery | in_review | v2-legacy | L | 2 | - | OK |
| surg_testicular_torsion_001 | v2 | surgery | in_review | v2-legacy | L | 2 | - | OK |
| surg_thyroid_nodule_001 | v2 | surgery | ai_generated | v2-legacy | L | 2 | - | OK |
| surg_varicose_veins_001 | v2 | surgery | ai_generated | v2-legacy | L | 2 | - | OK |
| kasus-01 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-02 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-03 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-04 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-05 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-06 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-07 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-08 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-09 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-10 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-101 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-102 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-103 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-104 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-105 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-106 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-107 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-108 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-109 | legacy-opth | ophthalmology | legacy | legacy | L | 1 | - | OK |
| kasus-11 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-12 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-13 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-14 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-15 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-16 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-17 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-18 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-19 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-20 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-21 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
| kasus-22 | legacy-opth | ophthalmology | legacy | legacy | L | 3 | - | OK |
