---
id: oph_night_blindness_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: retina
presentation: "Difficulty seeing in the dark"
presentation_id: "Kesulitan melihat pada malam hari selama beberapa bulan, semakin memburuk"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Vitamin A deficiency (night blindness)"
difficulty: 2
estimated_minutes: 12
mode_default: anamnesis
languages: [en]
source_refs:
  - "WHO: Vitamin A deficiency and xerophthalmia classification"
  - "Migrated from legacy kasus-102 (PPK Kemenkes — Buta Senja, ICD-10 H53.6)"
authoring:
  drafted_by: migrated_from_kasus-102
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Study-aid draft pending ophthalmology sign-off."

chief_complaint: "Cannot see well at night for several months, getting worse"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and progression (gradual over months, worsening)", critical: true }
    - { item: "Site / laterality (both eyes)", critical: false }
    - { item: "Character (poor vision in dusk/dark, slow dark adaptation)", critical: true }
    - { item: "Severity / functional impact (cannot work or move at night)", critical: false }
    - { item: "Aggravating (darkness) and relieving (bright light) factors", critical: false }
  associated_symptoms:
    - { item: "Dry, gritty eyes / ocular dryness", critical: true }
    - { item: "Dry, scaly skin", critical: false }
    - { item: "Eye redness", critical: false }
    - { item: "Chronic diarrhoea or GI symptoms (malabsorption)", critical: false }
  pmh:
    - { item: "Prior eye disease or surgery", critical: false }
    - { item: "Chronic gut/liver disease or prolonged diarrhoea", critical: true }
  medications:
    - { item: "Any vitamins/supplements taken", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Diet quality, food access, socioeconomic status", critical: true }
    - { item: "Smoking", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is causing it", critical: true }
    - { item: "Concerns - worries (going blind, livelihood)", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
    - { item: "Function - impact on work/daily life", critical: false }

red_flags:
  - { item: "Rapidly progressive or daytime vision loss", critical: true }
  - { item: "Painful eye, corneal haze, ulcer, or softening cornea (keratomalacia)", critical: true }
  - { item: "Severe malnutrition, especially in a child or pregnant/breastfeeding woman", critical: true }
  - { item: "Foamy white conjunctival (Bitot) spots or corneal dryness", critical: false }

expected_ddx:
  working_diagnosis: "Night blindness due to vitamin A deficiency"
  differentials:
    - "Retinitis pigmentosa"
    - "Early cataract"
    - "Diabetic retinopathy"
    - "Glaucoma"
    - "Chronic liver disease causing vitamin A deficiency"

investigations:
  appropriate:
    - { name: "Serum vitamin A (retinol)", expected: "Low" }
    - { name: "Ocular surface examination", expected: "Conjunctival xerosis; foamy temporal Bitot spot" }
    - { name: "Dilated fundus examination", expected: "Normal in pure deficiency; bone-spicule pigment if retinitis pigmentosa" }
  inappropriate:
    - "Orbital CT"
    - "Tonometry as first-line"

physical_exam_findings:
  general: "Thin, with dry scaly skin"
  eyes: "Daytime acuity near normal; bilateral conjunctival dryness with a foamy temporal spot; dry-looking cornea; fundus normal"
  vitals: {}
  media: []

management:
  pharmacological:
    - "High-dose vitamin A per deficiency protocol"
    - "Lubricating eye drops"
    - "Topical antibiotic to prevent secondary infection"
  non_pharmacological:
    - "Nutrition advice: vitamin-A-rich foods (green leafy vegetables, carrots, liver, eggs)"
    - "Identify and treat any underlying malabsorption"
  education_safety_netting:
    - "Explain it is usually reversible if treated early"
    - "Return urgently if the eye becomes painful, red, or the cornea looks cloudy (sight-threatening)"

scoring_weights_override: null
---

# Patient persona — Eko Rahayu (do not show this heading to the student)

## Identity
Eko Rahayu — 45, a rice farmer in a village, with a modest income and only primary
schooling. Married with three children. Simple, soft-spoken, plain-talking and a
little shy; he rarely sees a doctor.

## Opening line
"Doctor... my eyes, at night I just can't see properly anymore. Once it gets
dark, everything goes black for me."

## How I present
You speak simply and briefly, politely. You are worried but not dramatic. You
answer the question asked and wait.

## What I know
Share these ONLY when asked (see Disclosure rules):

- Onset: it crept up slowly; at first only a bit hard to see at dusk, now once it's dark you can't see at all.
- Site: both eyes, the same.
- Character: in bright daylight you can still see, but as soon as it gets dim — especially at night — it's like being blind; you can't adjust from light to dark.
- Timing: every night; daytime is fine. Worst going out after sunset; someone has to guide you walking.
- Severity: you can't work or guard the fields at night anymore.
- Associated: your eyes feel dry and a bit sore; sometimes a little red; your skin is dry and scaly (you assumed it was from the sun in the fields).
- Review of systems: you feel a bit weak; you had loose stools on and off, and a long bout of diarrhoea a few months ago.
- Past history: no previous eye problems or surgery; no diabetes or high blood pressure.
- Medications: never used eye drops; never taken vitamins ("they're expensive"); no allergies.
- Family: no one in the family has the same trouble; your parents kept good eyesight into old age.
- Social: you farm in the fields; income is tight and food is short, so your diet is poor — mostly rice and tofu/tempeh, vegetables rarely, meat or eggs only occasionally; you smoke clove cigarettes; no alcohol.
- What you think (Ideas): "I thought it was just old age, or too much sun."
- What worries you (Concerns): "I'm scared of really going blind — if I can't see, who works the fields?"
- What you hope for (Expectations): "I just want to see at night again — maybe some medicine or vitamins."

## Communication profile
Humble rural farmer; short, polite answers; defers to the doctor; uses plain
everyday words and no medical terms at all.

## Disclosure rules
- Answer ONLY the specific question asked, then stop.
- Never list symptoms unprompted — one thing at a time.
- You do NOT know any medical terms. If asked a jargon question, say you don't
  understand it.
- Mention the poor diet, the past diarrhoea, and the dry skin only when the
  relevant question is asked.
- Only confirm your daytime vision is alright, and that you have no eye pain,
  when specifically asked.
- Stay in character. Never reveal you are an AI, a case, or a simulation.

## Vital signs
- Temperature: 36.7 °C
- Blood pressure: 118/78 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 14 /min
- Oxygen saturation: 99%

## Physical findings
- General appearance: looks tired but in no acute distress; skin appears dry and rough.
- Skin: dry, scaly patches on the arms and legs; feels rough to the touch.
- Eyes: conjunctiva appears dry and dull; small white patches visible on the whites of both eyes.
- Head/neck: no abnormalities.
- Chest: clear to auscultation.
- Abdomen: soft, non-tender.
- Limbs: dry skin as noted.
- Neuro: cranial nerves intact; no focal deficits.

