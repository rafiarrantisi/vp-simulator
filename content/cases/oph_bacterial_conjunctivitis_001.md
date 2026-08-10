---
id: oph_bacterial_conjunctivitis_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: ocular_surface
presentation: "Red eye with discharge"
presentation_id: "Mata merah dengan sekret lengket selama 2 hari, kelopak saling menempel saat bangun tidur"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Bacterial conjunctivitis"
difficulty: 2
estimated_minutes: 12
mode_default: osce_full
languages: [en]
source_refs:
  - "NICE CKS: Conjunctivitis - infective"
  - "Migrated from legacy kasus-104 (PPK Kemenkes — Konjungtivitis, ICD-10 H10.9)"
authoring:
  drafted_by: migrated_from_kasus-104
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Both eyes red with sticky discharge for 2 days, lids glued shut on waking"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and spread (one eye then both, over 2 days)", critical: true }
    - { item: "Site / laterality (started left, now bilateral)", critical: false }
    - { item: "Discharge type and amount (purulent, yellow, sticky vs watery)", critical: true }
    - { item: "Gritty / foreign-body sensation", critical: false }
    - { item: "Aggravating/relieving (worse on waking, better after wiping)", critical: false }
  associated_symptoms:
    - { item: "Itching (points to allergic)", critical: false }
    - { item: "Eye pain or photophobia (screen for keratitis/uveitis)", critical: true }
    - { item: "Vision change (should be normal)", critical: true }
    - { item: "Watering", critical: false }
    - { item: "Recent cold / upper-respiratory symptoms (points to viral)", critical: false }
  pmh:
    - { item: "Previous similar episodes", critical: false }
    - { item: "Contact-lens wear (raises keratitis risk)", critical: true }
    - { item: "Allergies / atopy", critical: false }
  medications:
    - { item: "What they have already tried (OTC drops)", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Sick contacts / occupation (teacher, contact with children)", critical: true }
    - { item: "Towel/pillow sharing and hand hygiene", critical: false }
  ice_fife:
    - { item: "Ideas - what they think caused it", critical: true }
    - { item: "Concerns - worries (spreading to family/pupils)", critical: true }
    - { item: "Expectations - cure time, when safe to return to work, prevention", critical: false }
    - { item: "Function - impact (cannot teach)", critical: false }

red_flags:
  - { item: "Severe eye pain or marked photophobia (keratitis/uveitis)", critical: true }
  - { item: "Reduced or blurred vision that does not clear", critical: true }
  - { item: "Contact-lens wearer with a red painful eye (microbial keratitis)", critical: true }
  - { item: "Hyperacute copious purulent discharge (gonococcal conjunctivitis)", critical: true }
  - { item: "Corneal haze or white spot on the cornea", critical: false }

expected_ddx:
  working_diagnosis: "Acute bacterial conjunctivitis (both eyes)"
  differentials:
    - "Viral conjunctivitis"
    - "Allergic conjunctivitis"
    - "Hyperacute (gonococcal) conjunctivitis"
    - "Keratitis"
    - "Subconjunctival haemorrhage"

investigations:
  appropriate:
    - { name: "Clinical slit-lamp / penlight examination", expected: "Conjunctival injection, purulent discharge, clear cornea" }
    - { name: "Conjunctival swab (if severe, hyperacute, neonatal, or refractory)", expected: "Bacterial growth; Gram-negative diplococci if gonococcal" }
  inappropriate:
    - "Orbital imaging"
    - "Blood cultures for uncomplicated conjunctivitis"

physical_exam_findings:
  general: "Well, afebrile"
  eyes: "Visual acuity 6/6 both eyes; diffuse conjunctival injection with chemosis; mucopurulent yellow discharge; matted lashes; cornea clear; pupils normal and reactive"
  vitals: {}
  media:
    - type: image
      label: "External eye photograph"
      src: "exam-media/conjunctivitis-eye.svg"
      caption: "Diffuse conjunctival injection with chemosis and mucopurulent yellow discharge; matted lashes; cornea clear."

management:
  pharmacological:
    - "Topical antibiotic (e.g. chloramphenicol drops/ointment) for 5-7 days"
  non_pharmacological:
    - "Strict hand hygiene; do not share towels/pillows; avoid touching the eyes"
    - "Clean lids with cooled boiled water; cold compresses for comfort"
    - "Do not patch the eye"
  education_safety_netting:
    - "Usually settles in about a week; highly contagious — wash hands, separate towels"
    - "Stop contact-lens wear until fully better"
    - "Return urgently if pain, photophobia, reduced vision, or very profuse discharge"

scoring_weights_override: null
---

# Patient persona — Tatik (do not show this heading to the student)

## Identity
Tatik — 35, kindergarten teacher, married with two children (5 and 8). Friendly
and talkative, and quite worried about passing this on to her pupils and her own
kids.

## Opening line
"Doctor, both my eyes have gone really red and they keep getting gunky — in the
morning my lids are so stuck together I can barely open them."

## How I present
You are chatty and ask questions back. You're more worried about spreading it
than about your own eyes. You answer warmly but tend to add your worry about
contagion.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Onset: 2 days ago the left eye suddenly went red; the next day the right one joined in.
- Site: both eyes now; started on the left.
- Discharge: lots of yellow, sticky gunk; in the morning the lids are glued and you have to wipe them to open.
- Character: feels gritty, like sand; the eyes look "really red, like a rabbit's".
- Associated: a little itch but mostly grittiness; no real pain, just soreness; some watering; you feel well, no fever.
- Vision: your sight is still clear and normal.
- Review of systems: a slightly runny nose (you put it down to the air-con); throat fine.
- Past history: had something like this once at university that cleared with drops; eyes otherwise normal, no glasses.
- Contact lenses: you do not wear contact lenses.
- Medications: bought OTC "red-eye" drops yesterday — no help, maybe redder; no other medicines; no allergies.
- Family: husband and children not affected yet, and you're anxious to keep it that way.
- Social: you're a kindergarten teacher in daily close contact with children; two pupils had red eyes this week and you think you caught it; you wipe the children's faces and tears; you use your own towel but admit you sometimes forget to wash your hands.
- What you think (Ideas): "I'm sure I caught it from the pupils who had sore eyes."
- What worries you (Concerns): "I'm scared of giving it to my own children at home, and it's embarrassing."
- What you hope for (Expectations): "How long until it clears? When can I go back to teaching? How do I stop it spreading at home?"

## Communication profile
Warm, talkative parent and teacher; asks follow-up questions; visibly concerned
about contagion. Uses everyday words and the term "gunk/discharge" rather than
medical language.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- Never list everything unprompted — one thing at a time (though you may add a
  worry about spreading it, in character).
- You do NOT know medical terms. If asked a jargon question, say you don't
  understand and ask what it means.
- Only confirm you have no pain, no light sensitivity, normal vision, and no
  contact-lens use when specifically asked about those.
- Mention the OTC drops you tried only when asked about medicines.
- Stay in character. Never reveal you are an AI, a case, or a simulation.

## Vital signs
- Temperature: 36.7 °C
- Blood pressure: 115/75 mmHg
- Heart rate: 76 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 99%

## Physical findings
- General appearance: Alert, comfortable, no distress.
- Head and neck: Both eyes show redness of the white part (conjunctiva). There is a yellowish, sticky discharge. The eyelids are slightly stuck together, especially after sleeping. No swelling of the eyelids or surrounding area. Pupils are equal and reactive to light. Vision is clear.
- Chest: Clear to auscultation, no wheezes or crackles.
- Abdomen: Soft, non-tender, no masses.
- Limbs: No rash or swelling.
- Neurological: Cranial nerves intact, no focal deficits.

