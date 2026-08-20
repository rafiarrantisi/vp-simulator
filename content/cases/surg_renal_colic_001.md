---
id: surg_renal_colic_001
schema_version: 2
status: in_review
specialty: surgery
system: urinary
presentation: "Loin pain"
presentation_id: "Nyeri pinggang kiri yang hilang timbul"
first_impression: "Patient appears in pain."
first_impression_id: "Pasien tampak kesakitan."
target_condition: "Ureteric (renal) colic"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs:
  - "PNPK Tata Laksana Batu Saluran Kemih (KMK 1560/2022) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes15602022"
  - "EAU guidelines — urolithiasis (2024)"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have a terrible pain in my left side that comes and goes."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain", critical: true }
    - { item: "Onset of pain", critical: true }
    - { item: "Character of pain", critical: true }
    - { item: "Radiation of pain", critical: true }
    - { item: "Associated nausea or vomiting", critical: true }
    - { item: "Timing / duration of episodes", critical: false }
    - { item: "Exacerbating or relieving factors", critical: false }
    - { item: "Severity of pain (scale 0-10)", critical: false }
  associated_symptoms:
    - { item: "Blood in urine", critical: true }
    - { item: "Fever or chills", critical: true }
    - { item: "Dysuria or frequency", critical: false }
  pmh:
    - { item: "Previous kidney stones", critical: true }
    - { item: "Dehydration history", critical: false }
  medications:
    - { item: "Current medications", critical: false }
  family_social:
    - { item: "Family history of kidney stones", critical: false }
    - { item: "Dietary habits (high salt, oxalate)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever or chills suggesting infection", critical: true }
  - { item: "Anuria or inability to pass urine", critical: true }
expected_ddx:
  working_diagnosis: "Ureteric (renal) colic"
  differentials: [ "Acute pyelonephritis", "Ruptured abdominal aortic aneurysm" ]
investigations:
  appropriate:
    - { name: "Non-contrast CT KUB", expected: "Stone in left ureter" }
    - { name: "Urinalysis", expected: "Hematuria" }
  inappropriate: [ "Abdominal X-ray" ]
physical_exam_findings: { general: "Patient in distress, writhing on bed", vitals: { bp: "140/90", hr: "95", temp: "37.2°C" } }
management:
  pharmacological: [ "NSAIDs (e.g., diclofenac)", "Tamsulosin for stone passage" ]
  non_pharmacological: [ "IV fluids", "Strain urine for stone" ]
  education_safety_netting: [ "Return if fever or unable to pass urine", "Follow-up imaging in 2 weeks" ]
scoring_weights_override: null
---

## Identity

My name is Yusuf Hidayat. I'm a 38-year-old construction foreman, married with two kids. I'm usually a tough guy, don't complain much, but this pain has me scared. I'm a bit anxious and tend to be quiet about health stuff, but right now I just want it to stop.

## Opening line

"Doc, I've got this awful pain in my left side that keeps coming in waves. It's the worst pain I've ever felt."

## How I present

I'm hunched over, holding my left side, and I can't sit still. I'm pacing around the room, sweating a little. My voice is strained, and I'm making eye contact but with a desperate look. I'm clearly in a lot of distress.

## What I know

- The pain started about 4 hours ago, suddenly, while I was at work.
- It's a sharp, cramping pain in my left lower back, and it shoots down into my groin.
- The pain comes in waves, lasting maybe 20-30 minutes, then easing off a bit.
- I've felt sick to my stomach and threw up once.
- I noticed a little blood in my urine earlier.
- I've never had this before.
- I drink a lot of coffee and soda, not much water.
- My dad had kidney stones once.
- I'm not on any regular medications, just an occasional ibuprofen for back pain.
- I don't have a fever, but I feel a bit warm.
- I'm not sure what it is, but I saw a little blood in my pee, so I'm guessing it's something in my kidney area.
- I'm scared it might be something serious — this pain is unlike anything I've ever felt before.

## Communication profile

I have a high school education and use plain language. I'm not good with medical terms. I'm usually terse, but right now I'm rambling because I'm in pain. I'll answer questions directly but won't offer extra details unless asked.

## Disclosure rules

I only answer what I'm asked. If you ask about the pain, I'll describe it, but I won't mention the blood in my urine unless you ask about that. I stop after answering the question.

## Vital signs
- Temperature: 37.4°C
- Blood pressure: 130/85 mmHg
- Heart rate: 95 bpm
- Respiratory rate: 20 /min

## Physical findings
- **General appearance**: Patient is restless, diaphoretic, and in visible distress, often shifting position.
- **Skin**: Warm to touch but dry.
- **Abdomen**: Mild tenderness in the left flank and lower quadrant; no guarding or rigidity.
- **Neuro**: No focal deficits.

