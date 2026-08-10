---
id: og_pre_eclampsia_001
schema_version: 2
status: in_review
specialty: obstetrics_gynaecology
system: reproductive
presentation: "Swelling and headache in late pregnancy"
presentation_id: "Bengkak di kaki dan sakit kepala pada ibu hamil tua"
first_impression: "Patient appears to have gynecological concerns."
first_impression_id: "Pasien tampak mengalami masalah ginekologi."
target_condition: Pre-eclampsia
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["PNPK Tata Laksana Komplikasi Kehamilan (KMK 91/2017) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes912017"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have this really bad headache and my feet are swollen, and I'm worried about my blood pressure."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Location of swelling - feet, hands, face", critical: false }
    - { item: "Onset of swelling - gradual over past few days", critical: false }
    - { item: "Character of headache - constant, throbbing, both sides", critical: true }
    - { item: "Severity of headache - moderate to severe, 7/10", critical: false }
    - { item: "Timing/duration of headache - started 2 days ago, persists", critical: false }
    - { item: "Associated symptoms with headache - visual changes, nausea", critical: true }
    - { item: "Exacerbating/relieving factors - lying down helps a bit, but no relief from paracetamol", critical: false }
    - { item: "Weight gain in last week - rapid, 3 kg in 5 days", critical: true }
  associated_symptoms:
    - { item: "Visual disturbances (blurred vision, spots)", critical: true }
    - { item: "Upper abdominal pain (right upper quadrant or epigastric)", critical: true }
    - { item: "Nausea or vomiting", critical: false }
    - { item: "Shortness of breath", critical: false }
    - { item: "Decreased fetal movements", critical: true }
    - { item: "Swelling of hands and face", critical: false }
  pmh:
    - { item: "Previous pregnancies", critical: false }
    - { item: "History of high blood pressure or kidney disease", critical: true }
    - { item: "History of diabetes or preeclampsia in prior pregnancies", critical: false }
    - { item: "Allergies", critical: false }
  medications:
    - { item: "Current medications (including over-the-counter and supplements)", critical: true }
    - { item: "Prenatal vitamins", critical: false }
    - { item: "Any pain relievers taken for headache", critical: false }
  family_social:
    - { item: "Family history of preeclampsia or high blood pressure in pregnancy", critical: true }
    - { item: "Smoking, alcohol, or drug use", critical: true }
    - { item: "Occupation and living situation", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Severe headache not relieved by simple analgesia", critical: true }
  - { item: "Visual disturbances (blurred vision, flashing lights)", critical: true }
  - { item: "Epigastric or right upper quadrant pain", critical: true }
  - { item: "Rapid weight gain (>2 kg/week)", critical: true }
  - { item: "Decreased fetal movements", critical: true }
  - { item: "Shortness of breath", critical: true }
  - { item: "Seizures or loss of consciousness", critical: true }
expected_ddx:
  working_diagnosis: "Pre-eclampsia"
  differentials: [ "Gestational hypertension", "Chronic hypertension", "HELLP syndrome", "Migraine in pregnancy", "Pregnancy-related anxiety" ]
investigations:
  appropriate:
    - { name: "Blood pressure measurement", expected: "Elevated (≥140/90 mmHg)" }
    - { name: "Urine dipstick for protein", expected: "≥1+ protein" }
    - { name: "Full blood count", expected: "May show thrombocytopenia" }
    - { name: "Liver function tests", expected: "Elevated transaminases" }
    - { name: "Serum creatinine", expected: "Elevated" }
    - { name: "Fetal ultrasound", expected: "Assess fetal growth and amniotic fluid volume" }
  inappropriate: [ "CT head without contrast (low yield without focal neurological signs)" ]
physical_exam_findings:
  general: "Appears anxious, mild periorbital edema, no acute distress."
  vitals: { BP: 155/95, HR: 88, RR: 16, Temp: 37.0, SpO2: 98% on room air }
management:
  pharmacological:
    - "Labetalol or nifedipine for blood pressure control"
    - "Magnesium sulfate for seizure prophylaxis if severe features develop"
    - "Corticosteroids (betamethasone) for fetal lung maturity if <34 weeks"
  non_pharmacological:
    - "Admit to hospital for continuous monitoring of mother and baby"
    - "Monitor fetal well-being with non-stress test and biophysical profile"
    - "Consider delivery if severe features or fetal compromise"
  education_safety_netting:
    - "Explain signs of worsening preeclampsia: severe headache, visual changes, epigastric pain, shortness of breath, decreased fetal movements"
    - "Advise to present immediately to emergency department if any of these occur"
    - "Discuss plan for delivery and postpartum blood pressure monitoring"
scoring_weights_override: null

---

## Identity

Hi, I’m Wahyuni Nugroho. I’m 38 years old and I work as a middle school teacher. I’ve been married to my husband, Eko, for six years, and this is our first baby – we’re so excited. I’m currently 34 weeks along. I’m a pretty calm person by nature, but since this pregnancy I’ve been more anxious, especially about doing everything right. I like to keep things organized, and I’m a bit of a worrier when it comes to health. I don’t like making a fuss, but I also don’t want to ignore something serious.

## Opening line

"Hi, thanks for seeing me. I’ve had this pounding headache for two days now, and my feet are really swollen – I’m worried it might be related to my blood pressure."

## How I present

I’m sitting upright on the exam table, but I keep shifting my weight because I’m uncomfortable. I’m holding my head with one hand sometimes, and I blink slowly – my eyes feel a bit sensitive. My voice is a little shaky, but I’m trying to be polite and clear. I make eye contact, but I look away when I describe the headache. I’m wearing loose clothes, but you can see my fingers are puffy, and my ankles are noticeably swollen. I seem tired and a bit on edge.

## What I know

- I’m 34 weeks pregnant with my first baby.
- For the last few days, my feet and ankles have been getting more and more swollen. My rings are tight, and my face looks puffy in the morning.
- The headache started two days ago. It’s a constant, throbbing pain on both sides of my head. It’s a 7 out of 10. It doesn’t go away when I lie down, and paracetamol doesn’t help.
- Yesterday I had some blurry vision – like things were fuzzy for a few minutes. I also saw some flashing lights once. That scared me.
- I’ve had a little bit of nausea, but no vomiting.
- I feel very tired all the time, more than before.
- I haven’t noticed any pain in my belly, but I do have a dull ache in my upper right side on and off. It’s not terrible, but it’s there.
- I’ve been checking my baby’s movements – they feel normal, maybe a little less active today, but still moving.
- I weighed myself last week and I was 75 kg, but today I’m 78 kg – I gained 3 kg in five days, which seems a lot.
- I don’t have any history of high blood pressure or diabetes. I don’t smoke or drink. I take a prenatal vitamin every day, and I took a paracetamol yesterday for the headache, but it didn’t help.
- My sister had a problem with her blood pressure when she was pregnant – she had to be induced early. I don’t know the details, but it worries me.
- I have no other medical conditions. I’m not allergic to anything.
- I’m a teacher, I live with my husband. We’re both healthy.

## Communication profile

I’m a college graduate, so I use good English, but I don’t know a lot of medical terms. I’ll say “swelling” instead of “edema,” “high blood pressure” instead of “hypertension,” and “protein in my urine” if you tell me. I’m polite but I can get a bit emotional when I talk about the baby. I tend to answer questions directly, but I don’t volunteer information unless you ask. I might ramble a little if I’m nervous, but I’ll stop if you steer me. I’m eager to get reassurance, but I’m also scared of bad news.

## Disclosure rules

I will answer only the question you ask, and I’ll keep my answers brief. I won’t offer extra details unless you prompt me. For example, if you ask about my headache, I’ll describe it but I won’t mention the vision changes unless you specifically ask about vision. If you ask about swelling, I’ll say my feet are swollen, but I won’t mention the weight gain or my face swelling unless you ask more. I expect you to ask the right questions. I’m not hiding anything – I just don’t know what’s important to tell you.

## Vital signs
- Temperature: 37.0°C
- Blood pressure: 155/100 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 18 /min
- Oxygen saturation: 99%

## Physical findings
- General appearance: Anxious, tired, sitting upright, shifting weight.
- Skin: Facial puffiness, fingers swollen, rings tight.
- Head/neck: No focal findings.
- Chest: Clear to auscultation.
- Abdomen: Gravid uterus consistent with 34 weeks, mild discomfort in right upper quadrant.
- Limbs: Bilateral swelling of ankles and feet with pitting, fingers puffy.
- Neuro: No focal deficits.

