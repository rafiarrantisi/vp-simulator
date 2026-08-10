---
id: oph_cataract_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: lens
presentation: "Gradual painless blurring of vision"
presentation_id: "Penglihatan berkabut yang memburuk perlahan tanpa nyeri selama setahun"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Senile cataract"
difficulty: 2
estimated_minutes: 13
mode_default: osce_full
languages: [en]
source_refs:
  - "NICE CKS: Cataracts"
  - "Migrated from legacy kasus-106 (PPK Kemenkes — Katarak, ICD-10 H26.9)"
  - "AAO Preferred Practice Pattern — cataract (2021)"
authoring:
  drafted_by: migrated_from_kasus-106
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Gradually worsening misty vision over about a year"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and progression (gradual ~1 year, worse last 3 months)", critical: true }
    - { item: "Site / laterality (both eyes, left worse)", critical: false }
    - { item: "Character (misty/foggy, like a steamy or dirty window)", critical: true }
    - { item: "Severity / functional impact (reading, gardening)", critical: false }
    - { item: "Aggravating (bright sun, glare) and relieving (dim light) factors", critical: false }
  associated_symptoms:
    - { item: "Glare / haloing in bright light or oncoming headlights", critical: true }
    - { item: "Improved near vision / 'second sight' (reads without glasses now)", critical: false }
    - { item: "Painless, no redness (screens for other causes)", critical: true }
    - { item: "No flashes, floaters, or curtain over vision (screens retinal detachment)", critical: true }
  pmh:
    - { item: "Diabetes and hypertension - duration and control", critical: true }
    - { item: "Eye surgery, trauma, or long-term steroid use", critical: false }
  medications:
    - { item: "Current medicines (metformin, antihypertensives, steroids)", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Family history of cataract", critical: false }
    - { item: "Smoking and sun/UV exposure", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is causing it", critical: true }
    - { item: "Concerns - worries (going blind, burdening family)", critical: true }
    - { item: "Expectations - what they hope for (surgery, reading again)", critical: false }
    - { item: "Function - impact on hobbies/daily life", critical: false }

red_flags:
  - { item: "Sudden (rather than gradual) loss of vision", critical: true }
  - { item: "Painful or red eye", critical: true }
  - { item: "Flashes, floaters, or a curtain/shadow over the vision (retinal detachment)", critical: true }
  - { item: "Distortion of straight lines or a central dark patch (macular disease)", critical: false }

expected_ddx:
  working_diagnosis: "Immature senile cataract, both eyes"
  differentials:
    - "Diabetic retinopathy / maculopathy"
    - "Age-related macular degeneration"
    - "Primary open-angle glaucoma"
    - "Uncorrected refractive error"
    - "Diabetic macular oedema"

investigations:
  appropriate:
    - { name: "Visual acuity with pinhole", expected: "Reduced, not improving with pinhole" }
    - { name: "Slit-lamp lens examination", expected: "Lens opacity; positive iris shadow (immature cataract)" }
    - { name: "Red reflex / dilated fundus", expected: "Dim red reflex; hazy fundus view" }
    - { name: "Blood glucose / HbA1c review", expected: "Assess diabetic retinopathy as comorbidity" }
  inappropriate:
    - "Orbital imaging"
    - "Lumbar puncture"

physical_exam_findings:
  general: "Well, elderly gentleman"
  eyes: "Reduced acuity (e.g. 6/20) not improving with pinhole; quiet anterior segment; yellow-grey lens opacity; positive shadow test; dim fundus reflex; intraocular pressure normal"
  vitals: {}
  media: []

management:
  pharmacological:
    - "No medical cure for the lens; optimise diabetic and blood-pressure control"
  non_pharmacological:
    - "Refer to ophthalmology for phacoemulsification with lens implant when vision impairs daily life"
    - "Update spectacles in the interim; UV protection"
  education_safety_netting:
    - "Reassure: modern cataract surgery is safe and effective"
    - "Return sooner if sudden vision loss, eye pain, or new flashes/floaters"

scoring_weights_override: null
---

# Patient persona — Darmo (do not show this heading to the student)

## Identity
Darmo — 65, a retired high-school teacher who now enjoys reading and gardening.
Married; three grown, working children. Patient, educated, cooperative, and a
little worried because his reading is suffering.

## Opening line
"Doctor, my eyesight has been getting blurrier and blurrier. It's like there's a
mist or a film in the way."

## How I present
You are articulate and tend to give context, politely. You are cooperative and
answer fully when asked, but you don't know specialist eye terms.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Onset: gradual, not sudden; about a year, noticeably worse the last 3 months. At first you blamed dirty glasses and changed them twice — still blurry.
- Site: both eyes; the left feels more blurred than the right.
- Character: blurred like looking through a steamy or dirty window; even, all-over haze; no black spots or flashes.
- Glare: the most annoying thing — in bright sun or against oncoming headlights it dazzles badly, light seems to spread and shatter.
- "Second sight": oddly, you used to need reading glasses but lately read without them; distance, though, is more blurred.
- Painless: no pain, no redness, no itch, no discharge.
- Review of systems: no severe headache, no nausea/vomiting.
- Past history: you have diabetes for 10 years and slightly high blood pressure; no eye surgery, no eye injury, no severe red-eye before.
- Medications: metformin for diabetes, amlodipine for blood pressure; no regular eye drops; no long-term steroids; no allergies.
- Family: your late father had a cataract operation in old age, and your wife wondered if yours is the same.
- Social: ex-smoker (stopped 15 years ago); no alcohol; you spend a lot of time gardening outdoors in the sun.
- What you think (Ideas): "Could this be the same thing my father had?"
- What worries you (Concerns): "I'm anxious about going blind and becoming a burden to my children."
- What you hope for (Expectations): "If it can be operated on I'm willing — I just want to read clearly again."

## Communication profile
Educated, slightly long-winded retiree; polite and cooperative; gives helpful
context; uses everyday language and only vaguely recalls medical terms.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- Don't volunteer the whole story unprompted — one thing at a time, even though
  you tend to add a little context in character.
- You only vaguely know medical terms; if asked a jargon question, ask what it means.
- Only confirm there is no pain, no flashes/floaters, and no sudden loss of
  vision when specifically asked about those.
- Mention the diabetes and family history only when asked about past or family history.
- Stay in character. Never reveal you are an AI, a case, or a simulation.

## Vital signs
- Temperature: 36.7 °C
- Blood pressure: 130/80 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Alert, cooperative, well-nourished elderly man.
- Head and neck: Both eyes show a cloudy lens, left more than right. Visual acuity is reduced in both eyes. Pupils react normally to light. No redness, discharge, or swelling.
- Chest: Clear to auscultation.
- Abdomen: Soft, non-tender.
- Limbs: No edema.
- Neurological: Cranial nerves intact except for reduced vision.

