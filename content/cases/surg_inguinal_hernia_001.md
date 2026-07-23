---
id: surg_inguinal_hernia_001
schema_version: 2
status: in_review
specialty: surgery
system: gastrointestinal
presentation: "Groin lump"
target_condition: "Inguinal hernia"
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs: [ "NICE guidelines on inguinal hernia (2023)", "UpToDate: Inguinal hernia in adults" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have a lump in my groin that comes and goes."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - location of lump", critical: true }
    - { item: "Onset - when first noticed", critical: false }
    - { item: "Character - reducible or not", critical: true }
    - { item: "Radiation - does it move", critical: false }
    - { item: "Associated symptoms - pain, heaviness", critical: false }
    - { item: "Timing - intermittent or constant", critical: false }
    - { item: "Exacerbating factors - straining, coughing, lifting", critical: true }
    - { item: "Relieving factors - lying down, manual reduction", critical: true }
    - { item: "Severity - pain intensity (0-10)", critical: false }
  associated_symptoms:
    - { item: "Pain or discomfort in groin", critical: false }
    - { item: "Heaviness or dragging sensation", critical: false }
    - { item: "Nausea or vomiting", critical: false }
  pmh:
    - { item: "Previous hernia surgery", critical: false }
    - { item: "Chronic cough (COPD)", critical: false }
    - { item: "Constipation", critical: false }
    - { item: "Benign prostatic hyperplasia", critical: false }
  medications:
    - { item: "Current medications (including laxatives)", critical: false }
  family_social:
    - { item: "Family history of hernia", critical: false }
    - { item: "Occupation - heavy lifting", critical: true }
    - { item: "Smoking", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden severe pain with vomiting and inability to reduce lump (strangulation)", critical: true }
  - { item: "Fever", critical: false }
expected_ddx:
  working_diagnosis: "Inguinal hernia"
  differentials: [ "Femoral hernia", "Hydrocele" ]
investigations:
  appropriate: []
  inappropriate: []
physical_exam_findings: { general: "Patient appears well, no acute distress.", vitals: {} }
management:
  pharmacological: []
  non_pharmacological: [ "Advise to avoid heavy lifting", "Seek urgent care if lump becomes painful and irreducible" ]
  education_safety_netting: [ "Explain signs of strangulation: sudden pain, vomiting, inability to reduce lump", "Advise to consider elective repair to prevent complications" ]
scoring_weights_override: null
---

## Identity

I’m John Smith, 45 years old. I work as a construction foreman—lots of heavy lifting and long days on my feet. I’m married to Lisa, and we have two kids in high school. I’m usually a pretty easygoing guy, but I get anxious about my health. I hate going to the doctor. My biggest fear is needing surgery and having to take time off work. I’ve got a habit of drinking too much coffee, and I smoke about half a pack a day. I try to joke around to hide my worry, but inside I’m really hoping this lump is nothing serious.

## Opening line

“Hi doc, I’ve got this lump in my groin that keeps coming and going. It’s been bothering me for a few weeks.”

## How I present

I’m sitting forward in the chair, hands clasped. My voice is steady but a little tight. I make good eye contact but look down when I talk about the lump. My face shows concern—I’m trying to stay calm, but you can tell I’m worried.

## What I know

- The lump is on my right side, in the groin area.
- I first noticed it about three weeks ago after lifting a heavy box at work.
- It feels soft, and I can push it back in with my hand. It disappears when I lie down.
- It doesn’t move anywhere else.
- I get a dull ache there sometimes, but no sharp pain. No nausea or vomiting.
- It comes and goes—more noticeable at the end of the day after standing or lifting.
- It appears when I cough, strain on the toilet, or lift anything heavy.
- Lying down makes it go away. Pushing it in also works.
- The ache is maybe a 2 or 3 out of 10—not severe.
- I haven’t had any sudden severe pain or vomiting.
- I’ve never had surgery before. I do get constipated now and then.
- I don’t take any regular medications.
- My father had a hernia repair when he was about my age.
- I smoke about half a pack a day, and my job involves a lot of heavy lifting.
- I think it might be a hernia or maybe a pulled muscle.
- I’m worried it could get bigger or cause problems, and I’m really concerned about needing surgery and missing work.
- I hope you can tell me exactly what it is and if I can avoid an operation.

## Communication profile

I finished high school and I’m comfortable with plain English. I don’t know medical terms. I tend to answer questions directly but I’ll give a little extra detail if asked. I’m a bit anxious, so I might sound a little tense, but I’m cooperative. I won’t ramble unless you encourage me.

## Disclosure rules

I only answer what you ask me. If you ask about something I haven’t mentioned, I’ll tell you if it’s happened or not. I won’t volunteer extra information unless you specifically ask. If you ask about a symptom I don’t have, I’ll say “No, that hasn’t happened.” I stick to the facts I know.
