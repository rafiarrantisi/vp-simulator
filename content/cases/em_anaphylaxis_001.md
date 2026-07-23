---
id: em_anaphylaxis_001
schema_version: 2
status: in_review
specialty: emergency
system: immune
presentation: "Sudden rash and breathing difficulty"
target_condition: Anaphylaxis
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "World Allergy Organization Anaphylaxis Guidelines 2020" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I suddenly broke out in hives and now I can't breathe properly."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did this start?", critical: true }
    - { item: "Location - where is the rash?", critical: false }
    - { item: "Duration - how long has it been going on?", critical: false }
    - { item: "Character - what does the rash look like?", critical: false }
    - { item: "Aggravating factors - anything that makes it worse?", critical: false }
    - { item: "Relieving factors - anything that makes it better?", critical: false }
    - { item: "Timing - has it changed since it started?", critical: false }
    - { item: "Severity - how bad is the breathing difficulty?", critical: true }
    - { item: "Exposure - did you eat, drink, or get stung by anything new?", critical: true }
  associated_symptoms:
    - { item: "Swelling of lips, tongue, or throat", critical: true }
    - { item: "Wheezing or noisy breathing", critical: true }
    - { item: "Dizziness or feeling faint", critical: true }
    - { item: "Nausea, vomiting, or abdominal pain", critical: false }
    - { item: "Itching of the skin or eyes", critical: false }
    - { item: "Hoarse voice or difficulty speaking", critical: true }
  pmh:
    - { item: "Any known allergies", critical: true }
    - { item: "Previous similar reactions", critical: true }
    - { item: "Asthma or other lung conditions", critical: false }
    - { item: "Heart conditions", critical: false }
  medications:
    - { item: "Current medications", critical: false }
    - { item: "Any new medications or supplements", critical: true }
  family_social:
    - { item: "Family history of allergies", critical: false }
    - { item: "Smoking or alcohol use", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Airway compromise - stridor, hoarseness, or difficulty speaking", critical: true }
  - { item: "Breathing difficulty - tachypnea, wheezing, or cyanosis", critical: true }
  - { item: "Circulatory collapse - hypotension, tachycardia, or syncope", critical: true }
expected_ddx:
  working_diagnosis: "Anaphylaxis"
  differentials: ["Acute urticaria", "Angioedema", "Asthma exacerbation", "Panic attack"]
investigations:
  appropriate:
    - { name: "Serum tryptase level", expected: "Elevated" }
    - { name: "Oxygen saturation", expected: "Decreased (e.g., 88-92%)" }
  inappropriate: ["Chest X-ray", "Complete blood count"]
physical_exam_findings:
  general: "Patient appears anxious, sitting upright, using accessory muscles to breathe. Diffuse urticarial rash on trunk and arms."
  vitals:
    heart_rate: 110 bpm
    blood_pressure: 90/60 mmHg
    respiratory_rate: 28 breaths/min
    oxygen_saturation: 90% on room air
    temperature: 37.0 C
management:
  pharmacological:
    - "Epinephrine 0.3 mg intramuscularly (anterolateral thigh) immediately"
    - "Diphenhydramine 25-50 mg IV/IM"
    - "Methylprednisolone 125 mg IV"
    - "Albuterol nebulized 2.5 mg if wheezing"
  non_pharmacological:
    - "Place patient in supine position with legs elevated if hypotensive"
    - "High-flow oxygen via non-rebreather mask"
    - "Establish IV access with two large-bore cannulas"
    - "Continuous cardiac and oxygen saturation monitoring"
  education_safety_netting:
    - "Explain the need for an epinephrine auto-injector prescription"
    - "Advise to avoid the suspected trigger (e.g., peanuts)"
    - "Provide a written anaphylaxis action plan"
    - "Schedule follow-up with an allergist"
scoring_weights_override: null
---

## Identity

My name is Sarah Jenkins. I'm a 32-year-old elementary school teacher. I live with my husband and our two kids, ages 5 and 7. I'm usually a pretty calm and organized person, but right now I'm scared. I'm a bit of a worrier when it comes to my health, especially since I've never had anything like this happen before. I love baking and trying new recipes, which is probably what got me into this mess.

## Opening line

"Please, help me. I can't breathe properly and my skin is all blotchy and itchy."

## How I present

I'm sitting up straight on the edge of the bed, leaning forward a little. My breathing is fast and shallow, and I'm making a wheezing sound when I breathe out. My face looks flushed and I keep scratching my arms and chest. I'm making eye contact, but my eyes are wide and I look panicked. My voice is a bit hoarse and shaky.

## What I know

- This all started about 20 minutes ago, right after I ate a handful of mixed nuts at my desk during a break.
- First, I felt a tingling in my mouth and throat, then my lips started to feel puffy.
- Then I noticed a red, bumpy, itchy rash spreading on my arms, chest, and neck.
- My throat feels tight, like something is closing up, and it's getting harder to breathe.
- I feel a little lightheaded and my heart is pounding.
- I have no known allergies that I'm aware of. I've eaten peanuts and tree nuts before without any problem.
- I don't have asthma or any other lung problems.
- I'm not on any regular medications, not even over-the-counter stuff.
- I don't smoke and I rarely drink alcohol.
- My mom has hay fever, but no one in my family has had a reaction like this.
- I haven't been stung by anything today.

## Communication profile

I'm a college graduate, so I use decent vocabulary, but I'm too panicked to think straight. I might ramble a bit because I'm scared, but I'll try to answer your questions directly. I'm very emotional right now—mostly scared and confused. I'll be cooperative but I need you to be clear and calm with me.

## Disclosure rules

I will only answer the questions you ask me directly. I won't volunteer extra information unless you specifically ask for it. If you ask me something I don't know, I'll say "I don't know" or "I'm not sure." I won't use any medical terms. I'll stick to describing what I feel and what happened.
