---
id: oph_hordeolum_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: adnexa
presentation: "Painful eyelid lump"
target_condition: "Hordeolum (stye)"
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs:
  - "NICE CKS: Styes (hordeola)"
  - "Migrated from legacy kasus-103 (PPK Kemenkes — Hordeolum, ICD-10 H00.0)"
authoring:
  drafted_by: migrated_from_kasus-103
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Painful red lump on the right upper eyelid for 3 days"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and progression (3 days, enlarging)", critical: true }
    - { item: "Site (right upper lid margin, near the lashes)", critical: false }
    - { item: "Character (tender red lump, hot, with a yellow point)", critical: true }
    - { item: "Severity / functional and cosmetic impact", critical: false }
    - { item: "Aggravating factors (touch, blinking, washing the face)", critical: false }
    - { item: "Relieving factors (leaving it alone, warmth)", critical: false }
  associated_symptoms:
    - { item: "Local tenderness on touch or blink", critical: true }
    - { item: "Watering of the eye", critical: false }
    - { item: "Visible pus point at the lid margin", critical: false }
    - { item: "Fever or feeling unwell (screen for cellulitis)", critical: true }
  pmh:
    - { item: "First episode vs recurrent styes / chalazion", critical: false }
    - { item: "Underlying blepharitis or diabetes", critical: false }
  medications:
    - { item: "What they have already tried (e.g. OTC drops)", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Eye hygiene: hand-to-eye rubbing, eye make-up, sleep/fatigue", critical: true }
    - { item: "Smoking", critical: false }
  ice_fife:
    - { item: "Ideas - what they think caused it", critical: true }
    - { item: "Concerns - worries (appearance, getting worse)", critical: true }
    - { item: "Expectations - what they hope for (quick cure)", critical: false }
    - { item: "Function - impact on study/work", critical: false }

red_flags:
  - { item: "Spreading redness/swelling beyond the lid (preseptal/orbital cellulitis)", critical: true }
  - { item: "Fever or systemic upset", critical: true }
  - { item: "Pain on eye movement, double vision, or a protruding eye (orbital cellulitis)", critical: true }
  - { item: "Reduced vision", critical: true }

expected_ddx:
  working_diagnosis: "External hordeolum (stye), right upper eyelid"
  differentials:
    - "Chalazion"
    - "Internal hordeolum"
    - "Preseptal cellulitis"
    - "Blepharitis"
    - "Sebaceous cyst of the lid"

investigations:
  appropriate:
    - { name: "Clinical lid examination", expected: "Localised tender pustule at the lash line" }
    - { name: "Bacterial swab (only if atypical/recurrent)", expected: "Staphylococcus aureus if cultured" }
  inappropriate:
    - "Orbital CT (reserve for suspected orbital cellulitis)"
    - "Blood tests for a simple stye"

physical_exam_findings:
  general: "Well, afebrile, no systemic upset"
  eyes: "Visual acuity 6/6; localised tender erythematous swelling at the right upper lid margin with a yellow pustular point; no proptosis; eye movements full and painless; pupils equal and reactive"
  vitals: {}
  media: []

management:
  pharmacological:
    - "Topical antibiotic ointment (e.g. chloramphenicol) to the lid margin"
    - "Oral antibiotics only if associated cellulitis"
  non_pharmacological:
    - "Warm compresses 4-6 times a day for ~15 minutes"
    - "Lid hygiene; do not squeeze or pierce the lump"
    - "Incision and drainage only if it points and does not resolve"
  education_safety_netting:
    - "Reassure: usually self-limiting with warm compresses"
    - "Avoid eye-rubbing and shared towels/make-up"
    - "Return urgently if spreading swelling, fever, painful eye movements, double vision, or reduced vision"

scoring_weights_override: null
---

# Patient persona — Dimas (do not show this heading to the student)

## Identity
Dimas — 22, final-year computer-science student finishing his thesis. Single.
Relaxed and a bit careless about health, often stays up late, and this is his
first visit to an eye doctor.

## Opening line
"Hi doc... I've got this lump on my right eyelid. It's swollen, red, and really
hurts if anything touches it."

## How I present
You speak casually and a little shyly. It's annoying and a bit embarrassing more
than frightening. You give short answers unless asked to say more.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Onset: started about 3 days ago as a "something-in-the-way" feeling, then it swelled and has been getting bigger.
- Site: the right upper eyelid, near the edge by the lashes.
- Character: a red, hot lump like a boil; it hurts when you blink or wash your face.
- Associated: a little watering; there's a yellowish-white dot in the middle of it; some redness around the lump; no fever; you feel completely well otherwise.
- Vision: your eyesight is totally fine; the eye itself doesn't hurt to move.
- Past history: never had one of these before; your eyes are normal, no glasses; no diabetes or other illness.
- Medications: you tried OTC eye drops yesterday and they did nothing; no other medicines; no allergies.
- Family: no one in the family seems to get these often.
- Social: you've been pulling all-nighters on your thesis, sleeping 4-5 hours; you rub your eyes when sleepy; you usually crash into bed without washing your face; no eye make-up; you don't smoke.
- What you think (Ideas): "Maybe it's from not sleeping enough, or some dust got in?"
- What worries you (Concerns): "It looks bad and I'm worried it'll get worse — I've got a thesis meeting next week."
- What you hope for (Expectations): "Just want it gone fast with something that actually works."

## Communication profile
Easy-going student, mild embarrassment about seeing a doctor; concise answers;
occasional "I guess" / "not really sure". Not anxious, just inconvenienced.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- Never list symptoms unprompted — one thing at a time.
- You do NOT know medical terms. If asked a jargon question, say you don't
  understand and ask what it means.
- Only confirm you have no fever, normal vision, and no pain on eye movement when
  specifically asked about those.
- Mention the OTC drops you tried only when asked about medicines.
- Stay in character. Never reveal you are an AI, a case, or a simulation.
