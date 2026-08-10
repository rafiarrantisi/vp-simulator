---
id: im_hyperthyroid_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: endocrine
presentation: "Tremor weight loss and palpitations"
presentation_id: "Tremor, penurunan berat badan, dan jantung berdebar"
first_impression: "Patient appears uncomfortable."
first_impression_id: "Pasien tampak tidak nyaman."
target_condition: "Hyperthyroidism"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "American Thyroid Association Guidelines for the Diagnosis and Management of Hyperthyroidism (2016)" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I've been losing weight without trying and I feel shaky and my heart races."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset – when did these symptoms start (gradual vs sudden)", critical: true }
    - { item: "Duration – how long have they been present", critical: false }
    - { item: "Severity – how bad is the tremor and palpitations", critical: false }
    - { item: "Timing – constant or intermittent", critical: false }
    - { item: "Aggravating factors – stress, caffeine, exercise", critical: false }
    - { item: "Relieving factors – rest, lying down", critical: false }
  associated_symptoms:
    - { item: "Heat intolerance or excessive sweating", critical: true }
    - { item: "Increased appetite or change in eating habits", critical: false }
    - { item: "Fatigue or weakness", critical: false }
    - { item: "Insomnia or difficulty sleeping", critical: false }
    - { item: "Emotional lability, anxiety, irritability", critical: false }
    - { item: "Palpitations – fluttering, pounding, or irregular heartbeat", critical: true }
    - { item: "Weight loss despite normal or increased appetite", critical: true }
    - { item: "Tremor – fine shaking of hands", critical: true }
    - { item: "Change in bowel habits (more frequent stools)", critical: false }
    - { item: "Menstrual changes (women): lighter or less frequent periods", critical: false }
    - { item: "Eye symptoms: bulging, gritty, double vision, lid lag", critical: false }
  pmh:
    - { item: "Previous thyroid problems (e.g., goiter, nodules)", critical: true }
    - { item: "Recent illness or infection", critical: false }
    - { item: "Autoimmune conditions (e.g., type 1 diabetes, pernicious anemia)", critical: false }
    - { item: "Pregnancy or postpartum status", critical: false }
  medications:
    - { item: "Current prescription medications (including amiodarone, lithium, iodine supplements)", critical: true }
    - { item: "Over-the-counter supplements or herbal remedies", critical: false }
    - { item: "Beta-blockers or other heart medications", critical: false }
  family_social:
    - { item: "Family history of thyroid disease (hyperthyroidism, hypothyroidism, goiter)", critical: true }
    - { item: "Smoking status (worsens Graves' ophthalmopathy)", critical: false }
    - { item: "Stressful life events", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Unexplained weight loss", critical: true }
  - { item: "Palpitations at rest or with minimal exertion", critical: true }
  - { item: "Signs of thyroid storm: fever, altered mental status, chest pain, vomiting", critical: true }
  - { item: "Eye symptoms (proptosis, vision changes) indicating possible optic neuropathy", critical: true }
expected_ddx:
  working_diagnosis: "Hyperthyroidism"
  differentials: [ "Anxiety disorder", "Pheochromocytoma", "Diabetes mellitus (uncontrolled)", "Malignancy (lymphoma, carcinoma)" ]
investigations:
  appropriate:
    - { name: "TSH (thyroid-stimulating hormone)", expected: "Suppressed (low)" }
    - { name: "Free T4 (thyroxine)", expected: "Elevated" }
    - { name: "Free T3 (triiodothyronine)", expected: "Elevated (may be normal in early disease)" }
    - { name: "Thyroid peroxidase antibodies (TPO) and thyroglobulin antibodies", expected: "Positive (in Graves' disease)" }
    - { name: "TSH receptor antibody (TRAb)", expected: "Positive in Graves' disease" }
    - { name: "Thyroid ultrasound with Doppler", expected: "Diffusely enlarged, hypervascular gland (Graves') or nodule(s) if toxic adenoma" }
    - { name: "Radioactive iodine uptake and scan", expected: "Diffusely increased uptake (Graves') or focal uptake (toxic nodule)" }
    - { name: "Complete blood count", expected: "Normal (baseline for antithyroid drug therapy)" }
    - { name: "Liver function tests", expected: "Normal (baseline for methimazole)" }
  inappropriate:
    - { name: "CT scan of the neck without clear indication" }
    - { name: "Serum calcium and PTH for workup of hyperthyroidism" }
physical_exam_findings:
  general: "Thin, anxious-appearing woman in mild distress. Warm, moist skin. Fine tremor of outstretched hands. Tachycardic. Possible mild exophthalmos and lid lag. Thyroid gland diffusely enlarged (goiter), palpable thrill or audible bruit. Hyperreflexia."
  vitals: { pulse: 110, blood_pressure: 140/80, respiratory_rate: 16, temperature: 37.2, oxygen_saturation: 98 }
management:
  pharmacological:
    - "Antithyroid drug: Methimazole (start 10–20 mg daily, then adjust)"
    - "Beta-blocker: Propranolol (10–40 mg QID) for symptom control"
    - "Consider radioactive iodine (RAI) or thyroidectomy if definitive therapy needed"
  non_pharmacological:
    - "Low-iodine diet (avoid shellfish, iodized salt, supplements)"
    - "Counsel on smoking cessation (reduces progression of Graves' ophthalmopathy)"
    - "Stress reduction techniques"
  education_safety_netting:
    - "Educate about signs of thyroid storm: fever, rapid irregular pulse, confusion, vomiting – seek immediate care"
    - "Medication adherence and monitoring of side effects (agranulocytosis, hepatotoxicity) – report sore throat, fever, jaundice"
    - "Regular follow-up with endocrinology for dose adjustments and monitoring of thyroid function"
    - "If pregnant or planning pregnancy, discuss risks and management"
scoring_weights_override: null
---

## Identity

I am Dina Permata, a 32-year-old graphic designer. I’m married to a high school teacher and we have two kids, ages 5 and 7. I come from a close‑knit family; my parents are both alive and healthy, but my mother has a “thyroid condition” she takes pills for — I don’t know the details. I’ve always been energetic and a little bit of a worrier, but lately I feel like I’ve been running on high speed all the time. I’m afraid something is really wrong with my heart, or maybe I have cancer. I get anxious about my health and I tend to search online, which only makes me more scared. I’m usually very organized and talkative, but now I’m shaky and can’t sit still.

## Opening line

I can’t stop losing weight, and I’m always shaking… my heart races even when I’m just sitting down.

## How I present

I’m sitting on the edge of the exam chair, fidgeting with my hands. I speak quickly, sometimes jumping from one symptom to another. My skin feels warm to the touch — I’m sweating even though the room is cool. I make good eye contact but my eyes look a little wide and staring. I seem anxious and maybe a bit irritable. My hands are trembling when I hold them out.

## What I know

- Over the past three months, I’ve lost about 15 pounds without changing my diet or exercise. I actually eat more than usual.
- I’m always hungry, even after a full meal.
- My heart pounds in my chest, sometimes feels like it flutters or skips a beat. It happens several times a day.
- I have a fine tremor in my hands — it’s worse when I try to hold a cup of coffee or write.
- I feel hot all the time, even when others are comfortable. I sweat a lot, especially at night.
- I have trouble falling asleep and wake up often. I feel tired but also wired.
- My bowels are more frequent — I go two or three times a day, sometimes loose.
- I’m more irritable than usual, and I find myself snapping at my kids.
- My periods have become lighter and less frequent — I used to have a regular cycle, now it’s irregular.
- I don’t have any eye pain or double vision, but my husband says my eyes look “bigger” lately.
- I have not been sick recently. I don’t take any prescription medications or supplements. I don’t smoke or drink alcohol.
- There is no history of radiation to my neck.
- I’m very worried that I might have a serious heart problem or cancer.

## Communication profile

I have a bachelor’s degree in fine arts, so I’m comfortable with words but not medical jargon. I’m articulate and tend to describe my symptoms in detail. I can be a bit rambling because I’m anxious, but I can stay on track if I’m asked direct questions. I’m cooperative and want to understand what’s happening. I might ask “What does that mean?” if I hear a medical term.

## Disclosure rules

I will answer only what is asked, and then stop. I will not volunteer extra information unless the student specifically asks for it. I will not use any medical terms for my condition. I will not reveal my diagnosis. I will stay in the role of a real patient who does not know what she has.

## Vital signs
- Temperature: 37.2°C
- Blood pressure: 130/70 mmHg
- Heart rate: 112 bpm
- Respiratory rate: 20/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Anxious, restless, sitting on the edge of the chair, fidgeting with hands.
- Skin: Warm and moist to the touch.
- Head/neck: Eyes appear slightly prominent; no redness or pain. There is a slight fullness in the front of the neck that moves when swallowing.
- Chest: Heart rate is rapid and regular; no murmurs heard.
- Abdomen: Bowel sounds are active.
- Limbs: Fine tremor of outstretched hands; palms are warm and moist.

