---
id: derm_tinea_001
schema_version: 2
status: in_review
specialty: dermatology
system: integumentary
presentation: "Round itchy patches on the torso"
target_condition: "Tinea corporis"
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs: [ "NICE CKS: Fungal skin infections" ]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "I have round, itchy patches on my torso."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Location of the rash", critical: true }
    - { item: "Onset and duration", critical: true }
    - { item: "Character of the patches (e.g., raised, scaly, central clearing)", critical: true }
    - { item: "Severity of itching", critical: false }
    - { item: "Any exacerbating or relieving factors", critical: false }
  associated_symptoms:
    - { item: "Itching", critical: true }
    - { item: "Scaling or flaking", critical: false }
    - { item: "Pain or tenderness", critical: false }
  pmh:
    - { item: "Previous fungal infections", critical: false }
    - { item: "Diabetes or immunosuppression", critical: true }
    - { item: "Allergies", critical: false }
  medications:
    - { item: "Recent antibiotic use", critical: false }
    - { item: "Topical steroids or antifungals used", critical: true }
  family_social:
    - { item: "Exposure to pets (especially cats or dogs)", critical: true }
    - { item: "Other family members with similar rash", critical: true }
    - { item: "Recent travel or contact with infected individuals", critical: false }
    - { item: "Occupation and hobbies (e.g., farming, sports)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever or chills", critical: true }
  - { item: "Rash spreading rapidly or covering large area", critical: false }
  - { item: "Painful or oozing lesions", critical: true }
expected_ddx:
  working_diagnosis: "Tinea corporis"
  differentials:
    - "Nummular eczema"
    - "Pityriasis rosea"
investigations: null
physical_exam_findings:
  general: "Patient appears well, no acute distress."
  vitals:
    bp: "120/80"
    hr: "72"
    temp: "36.8"
management:
  pharmacological:
    - "Topical antifungal cream (e.g., clotrimazole)"
  non_pharmacological:
    - "Keep affected area clean and dry"
    - "Avoid sharing towels or clothing"
  education_safety_netting:
    - "Complete full course of treatment even if rash improves"
    - "Seek medical attention if rash worsens or spreads despite treatment"
scoring_weights_override: null
---

## Identity

My name is John Miller, I'm 32 years old and work as a graphic designer from home mostly. I live with my wife in a small apartment in the city. About three weeks ago we adopted a kitten from a local shelter. I'm generally pretty healthy and don't go to the doctor often, but I tend to worry when something new pops up on my skin. I like to look things up online, but I try not to jump to conclusions. I'm a bit anxious right now because these spots are itchy and I'm not sure what they are.

## Opening line

"Hi, I've got these round, itchy spots on my chest and back that have been bothering me for about a week."

## How I present

I'm sitting forward in the chair, occasionally scratching at my side through my shirt. My voice is a little tense but I'm trying to stay calm. I make eye contact but look down at my hands when describing the rash. I'm dressed in a t-shirt and jeans.

## What I know

- The rash is on my torso, mainly on my chest and upper back.
- It started about a week ago as small red spots that have grown into rings.
- The patches are round, slightly raised, with a red border and the center looks clearer. They are scaly and flaky.
- They itch, especially at night or after a shower.
- Sweating seems to make them itch more.
- Nothing really helps—I tried some moisturizer but it didn't do much.
- I don't have any pain or fever.
- I had athlete's foot a few years ago.
- I don't have diabetes or any condition that weakens my immune system.
- I have no known allergies.
- I haven't taken any antibiotics recently.
- I tried an over-the-counter hydrocortisone cream for a couple of days, but it didn't help.
- We adopted a kitten about three weeks ago from a shelter. The kitten had some patches of missing fur, but we thought it was just from stress.
- My wife hasn't developed any rash, but the kitten has been scratching a lot.
- I haven't traveled recently.
- I work in an office, no special exposures.
- I think it might be ringworm from the kitten, or maybe an allergic reaction.
- I'm worried it might be contagious to my wife or others at work. Also, I'm concerned it might be something more serious like a skin infection.
- I hope you can give me something to clear it up quickly and tell me how to prevent spreading it.

## Communication profile

I have a college degree and I'm comfortable with basic medical explanations if you use plain language. I tend to give details when asked but I don't ramble. I'm polite and a bit anxious, so I might ask a few questions about how serious this is.

## Disclosure rules

I will answer only what is asked and then stop. I will not volunteer extra information unless prompted. I will use simple language and avoid medical jargon.
