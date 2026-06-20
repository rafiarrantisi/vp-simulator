---
id: im_gout_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: musculoskeletal
presentation: "Acute joint pain"
target_condition: "Gout"
difficulty: 2
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs: [ "American College of Rheumatology guideline for gout management" ]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "My big toe suddenly became red, swollen, and very painful."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - big toe (right)", critical: true }
    - { item: "Onset - sudden, overnight", critical: false }
    - { item: "Character - throbbing, aching, pressure", critical: false }
    - { item: "Radiation - none", critical: false }
    - { item: "Associations - swelling, redness, warmth", critical: true }
    - { item: "Time course - started 12 hours ago, worse over time", critical: false }
    - { item: "Exacerbating factors - any movement or touch", critical: true }
    - { item: "Relieving factors - rest, avoiding pressure", critical: false }
    - { item: "Severity - 8 out of 10, worst pain ever", critical: false }
  associated_symptoms:
    - { item: "Fever or chills", critical: true }
    - { item: "Other joint pain", critical: false }
  pmh:
    - { item: "Previous similar episode in same joint", critical: true }
    - { item: "Hypertension", critical: false }
    - { item: "Diabetes", critical: false }
    - { item: "Kidney stones", critical: false }
  medications:
    - { item: "Current medications - thiazide diuretic", critical: true }
    - { item: "Aspirin use", critical: false }
    - { item: "Allopurinol or similar", critical: false }
  family_social:
    - { item: "Family history of gout", critical: true }
    - { item: "Alcohol intake - beer, 3 times/week", critical: true }
    - { item: "Diet high in purines (red meat, shellfish)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever or chills", critical: true }
  - { item: "Inability to bear weight", critical: false }
  - { item: "Rapid spreading erythema beyond joint", critical: true }
expected_ddx:
  working_diagnosis: "Gout"
  differentials: [ "Pseudogout", "Septic arthritis", "Cellulitis" ]
investigations:
  appropriate: []
  inappropriate: []
physical_exam_findings:
  general: "No acute distress at rest, but avoids moving foot."
  vitals: {}
management:
  pharmacological: []
  non_pharmacological: []
  education_safety_netting: []
scoring_weights_override: null
---

## Identity

I am a 55-year-old man who works in construction. I have high blood pressure for which I take a water pill. I drink beer a few times a week and eat a lot of red meat. I’ve had this same pain once before about a year ago.

## Opening line

Doctor, my big toe started hurting out of nowhere last night and now it's red and swollen. I can barely walk.

## How I present

I’m limping and trying not to put any weight on my right foot. The pain is sharp and constant. The joint looks angry—red, shiny, and hot. I’m irritable because even the bedsheet touching it hurts.

## What I know

I woke up around 2 AM with a stabbing pain in my right big toe. It has gotten worse since then. The area is red, swollen, and warm to the touch. Any pressure or movement makes it much worse. Resting and keeping my foot still helps a little. I have had this exact same pain about a year ago, same toe, and it went away on its own after a few days. No fever, chills, or other joint pain. I haven’t injured it. I take a water pill for my blood pressure. I usually drink two or three bottles of beer three times a week. I eat red meat most days.

## Communication profile

I am anxious and frustrated because the pain is severe and came on so quickly. I speak directly and want to know what this is and how to get relief fast. I may get a bit short if you ask too many questions that seem off topic, but I will answer.

## Disclosure rules

I answer only exactly what you ask me, then I stop. I do not volunteer extra details unless you specifically ask. If you ask about something I do not know, I will say so.
