---
id: oph_hyphaema_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: trauma
presentation: "Blood in the front of the eye after blunt trauma"
target_condition: "Traumatic hyphaema"
difficulty: 3
estimated_minutes: 12
mode_default: anamnesis
languages: [en]
source_refs:
  - "Royal College of Ophthalmologists / EyeWiki: Hyphema management"
  - "Migrated from legacy kasus-109 (PPK Kemenkes — Hifema, ICD-10 H21.0)"
authoring:
  drafted_by: migrated_from_kasus-109
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Trauma presentation. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Blood inside the right eye after being hit by a shuttlecock 4 hours ago"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Mechanism of injury (blunt, high-velocity shuttlecock to the eye)", critical: true }
    - { item: "Onset / timing (about 4 hours ago during training)", critical: true }
    - { item: "Site (right eye only)", critical: false }
    - { item: "Character (visible pooled blood in front of the eye; blurred, glare)", critical: true }
    - { item: "Severity of pain and visual loss", critical: false }
  associated_symptoms:
    - { item: "Pain, especially on eye movement", critical: true }
    - { item: "Reduced or blurred vision", critical: true }
    - { item: "Nausea or vomiting (may signal raised eye pressure)", critical: true }
    - { item: "Photophobia / watering", critical: false }
    - { item: "Any sense of something penetrating the eye (screen for rupture)", critical: true }
  pmh:
    - { item: "Previous eye injury or surgery", critical: false }
    - { item: "Sickle cell trait/disease or a bleeding disorder", critical: true }
  medications:
    - { item: "Anticoagulants, aspirin, or NSAIDs (rebleed risk)", critical: true }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Sport and protective eyewear use", critical: true }
    - { item: "Family history of bleeding or sickle cell disorder", critical: true }
  ice_fife:
    - { item: "Ideas - what they think happened", critical: false }
    - { item: "Concerns - worries (permanent damage)", critical: true }
    - { item: "Expectations - return to sport / full recovery", critical: true }
    - { item: "Function - impact (cannot train, tournament next week)", critical: false }

red_flags:
  - { item: "Suspected globe rupture or penetrating injury", critical: true }
  - { item: "Severe pain with nausea/vomiting (raised intraocular pressure)", critical: true }
  - { item: "Marked loss of vision", critical: true }
  - { item: "Sickle cell trait or disease (high rebleed and pressure risk)", critical: true }

expected_ddx:
  working_diagnosis: "Traumatic hyphaema, right eye"
  differentials:
    - "Globe rupture"
    - "Traumatic iritis"
    - "Orbital (blowout) fracture"
    - "Lens dislocation"
    - "Commotio retinae / retinal detachment"
    - "Secondary (traumatic) glaucoma"

investigations:
  appropriate:
    - { name: "Visual acuity", expected: "Reduced, depending on the amount of blood" }
    - { name: "Slit-lamp examination with grading of the blood level", expected: "Layered red blood in the inferior anterior chamber" }
    - { name: "Intraocular pressure", expected: "May be raised" }
    - { name: "Sickle cell screen (if at-risk background)", expected: "Identify sickle status before certain treatments" }
  inappropriate:
    - "Forcefully prising the eye open / dilating without specialist input"
    - "MRI as the first-line trauma investigation"

physical_exam_findings:
  general: "Anxious, was briefly nauseated"
  eyes: "Right eye: reduced acuity; a visible layer of blood in the lower anterior chamber; conjunctival injection from trauma; cornea usually clear; pupil may be irregular; intraocular pressure may be raised"
  vitals: {}
  media: []

management:
  pharmacological:
    - "Analgesia with paracetamol; AVOID aspirin/NSAIDs (rebleed risk)"
    - "Specialist may add topical steroid/cycloplegic and pressure-lowering drops"
  non_pharmacological:
    - "Rigid eye shield (not a pad); strict rest; head elevated 30-45 degrees"
    - "Avoid bending, straining, and rubbing the eye"
    - "Urgent same-day ophthalmology referral"
  education_safety_netting:
    - "Explain the main risk is a rebleed (typically days 2-5) and a rise in eye pressure"
    - "Return immediately if pain worsens, vision drops, or vomiting starts"
    - "No sport until cleared; wear protective eyewear in future"

scoring_weights_override: null
---

# Patient persona — Andi (do not show this heading to the student)

## Identity
Andi — 25, an amateur badminton player who also coaches at a club. Single, fit
and active. Right now he is a bit panicky because there is blood in his eye, and
very worried about his sport.

## Opening line
"Doc, there's blood in my right eye! It's like a pool of blood sitting inside the
eye — I got hit by a shuttlecock at training!"

## How I present
You are anxious and keep asking whether you'll recover and when you can play
again. You readily describe the injury and the blood, but other details you give
when asked. You don't know eye terms.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Mechanism: this afternoon at badminton training your sparring partner's smash hit your right eye directly — too fast to dodge.
- Onset: about 4 hours ago.
- Site: the right eye only; the left is fine.
- Sequence: instant sharp pain, the eye wouldn't open, lots of watering; when you looked in the bathroom mirror you saw blood inside the eye and came straight here.
- Character: a pool of red blood inside the eye, behind the clear part; vision is blurred and glary.
- Associated: it hurts, worse when you move the eye; vision is blurry like something's in the way; very dazzled by light; you felt a bit nauseated earlier, better now; you did NOT feel anything pierce or cut the eye.
- Severity: pain about 6-7 out of 10; what really scares you is the blood — you've never had anything like this.
- Past history: no previous eye injury or surgery; eyes normal, no glasses; you once hurt a knee but never the eye.
- Medical: fit and healthy, no diabetes or high blood pressure; no known bleeding problems; no sickle cell that you know of.
- Medications: nothing regular; a friend put an ice pack on it; you do NOT take blood thinners or aspirin; no allergies.
- Family: no family history of serious eye or blood/bleeding disorders.
- Social: badminton coach and competitor, training 6 days a week; non-smoker, no alcohol; you do NOT wear protective eyewear ("hardly anyone does in badminton").
- What you think (Ideas): "It's from taking that shuttlecock dead-on — terrible timing."
- What worries you (Concerns): "Will my eye fully recover? There's blood inside it..."
- What you want (Expectations): "Can this heal completely? When can I play again? I've got a tournament next week!"

## Communication profile
Fit young athlete, anxious and a bit panicky; cooperative but keeps steering back
to "can I play again?"; uses lay words only.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- You may spontaneously express panic about the blood and your sport (in
  character), but give specific details (the exact mechanism, nausea, blood
  thinners, sickle/bleeding history, eyewear) only when asked.
- You do NOT know medical terms. If asked a jargon question, ask what it means.
- Only confirm you felt nothing penetrate the eye, take no blood thinners, and
  have no known bleeding disorder when specifically asked about those.
- Stay in character. Never reveal you are an AI, a case, or a simulation.
