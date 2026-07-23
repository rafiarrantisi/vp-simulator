---
id: derm_cellulitis_001
schema_version: 2
status: in_review
specialty: dermatology
system: integumentary
presentation: "Hot red swollen leg"
target_condition: "Lower limb cellulitis"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["NICE guideline for cellulitis (2019)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My left leg is red, hot, and swollen, and it hurts to walk."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - left lower leg", critical: true }
    - { item: "Onset - started 3 days ago", critical: false }
    - { item: "Character - redness and swelling", critical: true }
    - { item: "Radiation - stays in the leg", critical: false }
    - { item: "Associations - feels hot to touch", critical: true }
    - { item: "Time course - getting worse", critical: false }
    - { item: "Exacerbating factors - walking or standing makes it hurt more", critical: false }
    - { item: "Severity - pain is 6/10", critical: false }
  associated_symptoms:
    - { item: "Fever and chills", critical: true }
    - { item: "Nausea", critical: false }
    - { item: "Red streaks going up the leg", critical: true }
  pmh:
    - { item: "Type 2 diabetes", critical: true }
    - { item: "Athlete's foot on the same foot", critical: true }
    - { item: "Previous leg injury (scraped it on a rock 2 weeks ago)", critical: false }
  medications:
    - { item: "Metformin for diabetes", critical: false }
    - { item: "Over-the-counter antifungal cream for athlete's foot", critical: false }
  family_social:
    - { item: "Lives alone, retired", critical: false }
    - { item: "No smoking or alcohol", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever and chills suggesting systemic infection", critical: true }
  - { item: "Rapid spread of redness or red streaks", critical: true }
expected_ddx:
  working_diagnosis: "Lower limb cellulitis"
  differentials: ["Deep vein thrombosis", "Erysipelas"]
investigations:
  appropriate:
    - { name: "Blood cultures", expected: "May show Streptococcus or Staphylococcus species" }
    - { name: "Full blood count", expected: "Elevated white cell count" }
    - { name: "C-reactive protein", expected: "Elevated" }
  inappropriate: ["Venous duplex ultrasound (unless DVT suspected)"]
physical_exam_findings: { general: "Patient appears unwell, flushed face, guarding the left leg.", vitals: { temperature: "38.5°C", heart_rate: "95 bpm", blood_pressure: "130/80 mmHg", respiratory_rate: "18/min", oxygen_saturation: "98% on room air" } }
management:
  pharmacological:
    - "Oral antibiotics (e.g., flucloxacillin or clindamycin if allergic)"
    - "Paracetamol for pain and fever"
  non_pharmacological:
    - "Elevate the leg to reduce swelling"
    - "Rest and avoid walking"
  education_safety_netting:
    - "Return if redness spreads, fever worsens, or you feel very unwell"
    - "Complete the full course of antibiotics even if you feel better"
scoring_weights_override: null
---

## Identity

My name is Margaret Thompson. I'm 68 years old, a retired schoolteacher. I live alone in a small flat with my cat, Whiskers. I'm usually a cheerful, independent person, but this leg thing has me scared. I'm a bit of a worrier, especially about my health since my husband passed a few years ago. I like to keep busy with gardening and reading, but now I can barely get to the kitchen.

## Opening line

"Doctor, my left leg is all red and swollen, and it's so hot it feels like it's on fire. I'm worried it's something serious."

## How I present

I'm sitting on the edge of the chair, leaning forward, with my left leg propped up on a stool. My face is flushed, and I'm sweating a little. I keep looking down at my leg and wincing when I move it. My voice is a bit shaky, and I'm speaking quickly because I'm anxious. I make eye contact, but I'm clearly distressed.

## What I know

- It started about three days ago. I noticed a small red patch on my lower left leg, near my ankle. It was a little itchy, but I didn't think much of it.
- The redness has spread up my leg over the last day. Now it covers from my ankle to just below my knee. It's bright red and feels hot to the touch.
- The leg is swollen, especially around my ankle. It's puffy and tight.
- It hurts when I walk or even stand. The pain is a dull ache, about a 6 out of 10. It's worse when I put weight on it.
- I've had a fever and chills since yesterday. I feel hot and cold at the same time, and I've been sweating at night.
- I've felt a bit sick to my stomach, but I haven't vomited.
- I noticed a red streak going up the inside of my leg yesterday. It's about as wide as a pencil and goes from the red area up toward my knee.
- I have type 2 diabetes, which I manage with metformin. I check my blood sugar sometimes, but it's usually okay.
- I've had athlete's foot on that same foot for a few weeks. It's itchy between my toes, and I've been using a cream from the pharmacy, but it hasn't cleared up.
- About two weeks ago, I scraped my leg on a rock while gardening. It was a small cut, and it seemed to heal fine. I didn't think anything of it.
- I live alone. I don't smoke or drink alcohol.
- I'm worried because my neighbor told me this could be a blood clot, and that scares me. I also think it might be an infection from the cut.
- I hope you can give me something to make the pain and swelling go down, and tell me it's not something dangerous.

## Communication profile

I have a high school education and I'm comfortable talking to doctors. I use simple, everyday words. I tend to ramble a bit when I'm nervous, but I'll answer your questions directly. I'm emotional right now—scared and a bit tearful—but I'm trying to stay calm. I'll tell you everything I know, but only if you ask.

## Disclosure rules

I will only answer what you ask me. If you ask about my leg, I'll tell you about the redness and swelling. If you ask about my fever, I'll tell you about that. I won't volunteer extra information unless you prompt me. For example, if you ask about the pain, I'll describe it, but I won't mention the red streak unless you ask about it. I'll stick to the facts I know.
