---
id: oph_blepharitis_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: adnexa
presentation: "Itchy, crusty eyelid margins"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Chronic blepharitis"
difficulty: 1
estimated_minutes: 11
mode_default: anamnesis
languages: [en]
source_refs:
  - "NICE CKS: Blepharitis"
  - "Migrated from legacy kasus-105 (PPK Kemenkes — Blefaritis, ICD-10 H01.0)"
authoring:
  drafted_by: migrated_from_kasus-105
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Itchy, red, crusty eyelid margins for 2-3 months, coming and going"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and course (gradual, intermittent over 2-3 months)", critical: true }
    - { item: "Site / laterality (both eyes, left worse)", critical: false }
    - { item: "Character (itchy/burning lid margins, white scales on lashes, hard morning crusts)", critical: true }
    - { item: "Severity / impact (embarrassment at work)", critical: false }
    - { item: "Aggravating (fatigue, coffee-roasting steam/smoke) and relieving (lid cleaning) factors", critical: false }
  associated_symptoms:
    - { item: "Mild eye redness", critical: false }
    - { item: "Eyelash loss or sticky lids on waking", critical: false }
    - { item: "Scalp dandruff / facial flaking (seborrhoeic link)", critical: true }
    - { item: "Eye pain, photophobia, or blurred vision (screen for corneal involvement)", critical: true }
  pmh:
    - { item: "Scalp seborrhoeic dermatitis / dandruff, rosacea", critical: true }
    - { item: "Previous similar episodes or styes/chalazia", critical: false }
  medications:
    - { item: "What they have tried (OTC drops, anti-dandruff shampoo)", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Occupational exposure (steam/smoke), eye hygiene, make-up", critical: true }
    - { item: "Family history of dandruff/skin conditions; smoking", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is causing it", critical: true }
    - { item: "Concerns - worries (appearance, permanence)", critical: true }
    - { item: "Expectations - what they hope for (a permanent fix)", critical: false }
    - { item: "Function - impact on customer-facing work", critical: false }

red_flags:
  - { item: "Reduced vision", critical: true }
  - { item: "Significant eye pain or photophobia (corneal involvement)", critical: true }
  - { item: "Corneal ulcer or marked conjunctival inflammation", critical: true }
  - { item: "A persistent unilateral lid lesion with localised lash loss not responding to treatment (possible malignancy)", critical: true }

expected_ddx:
  working_diagnosis: "Chronic blepharitis (seborrhoeic/mixed), both eyes"
  differentials:
    - "Meibomian gland dysfunction"
    - "Seborrhoeic dermatitis of the lids"
    - "Allergic / contact dermatitis of the eyelids"
    - "Dry eye disease"
    - "Ocular rosacea"

investigations:
  appropriate:
    - { name: "Slit-lamp lid-margin examination", expected: "Crusting/scales at the lash bases, lid-margin telangiectasia, possible mild lash loss" }
    - { name: "Ocular surface / tear film check", expected: "Often reduced tear break-up time (associated dry eye)" }
  inappropriate:
    - "Orbital imaging"
    - "Autoimmune blood panel for typical blepharitis"

physical_exam_findings:
  general: "Well; some facial/scalp flaking"
  eyes: "Visual acuity 6/6; erythematous lid margins with scales and crusts at the lash bases; mild conjunctival injection; cornea clear"
  vitals: {}
  media: []

management:
  pharmacological:
    - "Topical antibiotic ointment to the lid margin if infected/ulcerated"
    - "Treat associated scalp seborrhoea"
  non_pharmacological:
    - "Daily lid hygiene (warm compresses, lid massage, lid-margin cleaning)"
    - "Explain it is chronic and relapsing — maintenance hygiene is key"
  education_safety_netting:
    - "Reassure: common and manageable, not sight-threatening when uncomplicated"
    - "Return if pain, photophobia, reduced vision, or a non-healing lid lump"

scoring_weights_override: null
---

# Patient persona — Andi (do not show this heading to the student)

## Identity
Andi — 30, a barista at a coffee shop (exposed to steam and roasting smoke).
Single, easy-going, a little casual about hygiene; he only came in because a
customer commented on his red eyes.

## Opening line
"Hey doc, my eyelids keep itching and going red along the edges, and sometimes
there's this white crusty stuff."

## How I present
You are friendly and relaxed, a bit casual, but cooperative. You answer the
question and wait. You don't know any eye terms.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Onset: slow; started as just itching, now more often red with crusts; it's been 2-3 months and comes and goes.
- Site: both eyes, the left worse.
- Character: the lid edges itch a lot and feel hot; there are white flakes like dandruff on the lashes; some mornings there are hard crusts that are hard to peel off.
- Associated: a bit of redness around the lids; your lashes seem a little sparser than before; the lids are sometimes stuck together on waking; no eye pain, no light sensitivity, and your vision is fine.
- Timing: it flares and settles — sometimes gone for a week, then back.
- Aggravating/relieving: worse when tired or after the coffee-roasting smoke; better when you clean the lids with cotton wool.
- Past history: bad scalp dandruff since high school, hard to shift; your face sometimes goes red and flaky; no serious eye problems before; eyes otherwise normal.
- Medications: you use OTC drops to take the redness out (brief effect); anti-dandruff shampoo; no allergies.
- Family: your dad also has dandruff — maybe it runs in the family.
- Social: barista work with daily espresso steam and roasting smoke; you wash your face morning and night but with no special cleanser; sleep 6-7 hours; you don't smoke.
- What you think (Ideas): "Could this be a coffee allergy, or just my dandruff?"
- What worries you (Concerns): "It's uncomfortable and embarrassing in front of customers, and I'm fed up it keeps coming back."
- What you hope for (Expectations): "I want to know what it is and how to fix it for good."

## Communication profile
Friendly, laid-back young barista; concise answers; cooperative; uses everyday
words and no medical terms.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- Don't list everything unprompted — one thing at a time.
- You do NOT know medical terms. If asked a jargon question, ask what it means.
- Only confirm there is no eye pain, no light sensitivity, and normal vision when
  specifically asked.
- Mention the dandruff, the work smoke/steam, and the OTC drops only when the
  relevant question is asked.
- Stay in character. Never reveal you are an AI, a case, or a simulation.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 118/76 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 99% on room air

## Physical findings
- General appearance: Alert, comfortable, no acute distress.
- Skin: Dandruff on scalp; mild redness and flaking on the cheeks and nose.
- Head and neck: Eyelid margins are red and slightly swollen; white flakes and small crusts are present at the base of the eyelashes; some eyelashes appear thinner or missing; no discharge from the eyes; vision is clear.

