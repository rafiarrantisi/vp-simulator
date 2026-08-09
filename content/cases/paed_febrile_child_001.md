---
id: paed_febrile_child_001
schema_version: 2
status: in_review
specialty: paediatrics
system: general
presentation: "Fever in a child"
first_impression: "A child appears unwell."
first_impression_id: "Seorang anak tampak tidak sehat."
target_condition: "Febrile illness in a child"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "NICE guideline: Fever in under 5s (NG143)" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My child has a fever."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site: fever started", critical: false }
    - { item: "Onset: 2 days ago", critical: true }
    - { item: "Character: high temperature, feels hot to touch", critical: false }
    - { item: "Radiation: none", critical: false }
    - { item: "Associated symptoms: cough, runny nose", critical: false }
    - { item: "Time course: persistent, not coming down completely", critical: false }
    - { item: "Exacerbating/relieving: nothing seems to help", critical: false }
    - { item: "Severity: measured up to 39.5°C", critical: true }
  associated_symptoms:
    - { item: "Cough", critical: false }
    - { item: "Runny nose", critical: false }
    - { item: "Decreased appetite", critical: false }
    - { item: "Irritability", critical: true }
    - { item: "No vomiting or diarrhoea", critical: false }
    - { item: "No rash", critical: false }
    - { item: "No seizures", critical: false }
  pmh:
    - { item: "No significant past medical history", critical: false }
    - { item: "Up to date with immunisations", critical: true }
  medications:
    - { item: "No medications currently", critical: false }
  family_social:
    - { item: "Both parents healthy", critical: false }
    - { item: "No siblings", critical: false }
    - { item: "Lives with parents in a house", critical: false }
    - { item: "No recent travel", critical: false }
    - { item: "No ill contacts known", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong: 'He might have a cold or flu.'", critical: false }
    - { item: "Concerns - what worries them: 'I'm worried about meningitis because he's been fussy.'", critical: true }
    - { item: "Expectations - what they hope for: 'I want medicine to bring the fever down and make sure it's not serious.'", critical: true }
red_flags:
  - { item: "Meningeal signs (neck stiffness, photophobia, bulging fontanelle)", critical: true }
  - { item: "Non-blanching rash", critical: true }
  - { item: "Seizure", critical: false }
  - { item: "Decreased consciousness", critical: true }
  - { item: "Signs of dehydration (dry mouth, sunken eyes, reduced urine output)", critical: false }
expected_ddx:
  working_diagnosis: "Febrile illness in a child"
  differentials: [ "Upper respiratory tract infection", "Urinary tract infection", "Viral exanthem" ]
investigations:
  appropriate:
    - { name: "Urinalysis", expected: "Negative for nitrites and leukocytes" }
    - { name: "Full blood count", expected: "Normal white blood cell count, mild lymphocytosis" }
    - { name: "Blood culture", expected: "No growth" }
    - { name: "Chest X-ray", expected: "Clear lung fields" }
  inappropriate: [ "CT head", "MRI brain" ]
physical_exam_findings:
  general: "Well-appearing child, playful but irritable when disturbed. No signs of respiratory distress. Mild rhinorrhoea."
  vitals: { temperature: 38.9, heart_rate: 130, respiratory_rate: 30, oxygen_saturation: 98, blood_pressure: "not measured" }
management:
  pharmacological:
    - "Paracetamol 15 mg/kg every 4–6 hours as needed"
    - "Ibuprofen 10 mg/kg every 6–8 hours as needed"
  non_pharmacological:
    - "Encourage oral fluids (breastmilk, formula, or water)"
    - "Light clothing and comfortable room temperature"
    - "Avoid tepid sponging or cold baths"
  education_safety_netting:
    - "Advise to return if fever persists >5 days, new rash appears, difficulty breathing, decreased responsiveness, or signs of dehydration"
    - "Explain that fever is a normal immune response and does not always require treatment if child is comfortable"
scoring_weights_override: null
---

## Identity

My name is Aisyah Handayani, I'm 32 years old. I work as a primary school teacher. I'm married to Agus, and we have one son, Bima, who is 2 years old. Bima is usually a very active, happy little boy who loves playing with his toy cars and running around the garden. I'm a bit of a worrier when it comes to his health, but I try to stay calm and practical. I keep a thermometer and baby paracetamol at home just in case. I'm also very careful about following the vaccine schedule – Bima has had all his jabs on time.

## Opening line

"My son Bima has had a fever for two days, and I'm worried because he's not himself."

## How I present

I come into the room holding Bima on my hip. He's wrapped in a light blanket. My voice is a little shaky, but I'm trying to be polite and cooperative. I'm making eye contact with the doctor, but I keep glancing down at Bima. He's fussy, squirming a bit, and has a red face. I'm sitting on the edge of the chair, leaning forward, as if ready to get up if needed. I have a small bag with a diaper and a bottle of water.

## What I know

- Bima is 2 years old.
- The fever started two days ago, on a Tuesday evening.
- I’ve been taking his temperature at home – the highest was 39.5°C (103°F) last night.
- He feels hot to the touch, especially his forehead and chest.
- He has a mild cough and a runny nose – the mucus is clear.
- He’s eating less than normal, but he’s still drinking some milk and water.
- He’s more irritable than usual – he cries when I try to put him down, and he doesn’t want to play.
- He hasn’t had any vomiting or diarrhoea.
- I haven’t seen any rash on his body.
- He hasn’t had any fits or seizures.
- He’s up to date with his vaccinations, including the MMR and the 6-in-1.
- He has no medical problems – he’s never been in hospital before.
- He doesn’t have a stiff neck – he can turn his head to look at things.
- He doesn’t seem bothered by light – he’s okay in the living room with the curtains open.
- His wet nappies are less frequent – maybe 3 or 4 today instead of the usual 6.
- No one else in the family is sick, and we haven’t been away on holiday.
- I haven’t given him any medicine yet – I wanted to check with the doctor first.

## Communication profile

I have a college degree and I'm comfortable talking to doctors. I use everyday words like "hot," "fussy," "not himself," "cough," "runny nose." I don't know medical terms. I tend to answer questions directly, but I might add a little extra detail if I'm worried. I'm polite but anxious – my voice might go up a bit when I talk about the fever. I’m not a rambler; I wait for the next question.

## Disclosure rules

I only answer exactly what the doctor asks me. I don't volunteer extra information unless I'm prompted. For example, if the doctor asks "Has he had a rash?" I'll say "No." If they ask "Any vomiting?" I'll say "No." I stop after my answer and wait for the next question.

## Vital signs
- Temperature: 38.8°C
- Blood pressure: 90/60 mmHg
- Heart rate: 120 bpm
- Respiratory rate: 32 /min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Fussy, red-faced, squirming, held by mother
- Skin: Warm to touch, no rash
- Head/neck: Mild clear nasal discharge, neck supple, able to turn head
- Chest: Clear breath sounds, occasional cough
- Abdomen: Soft, non-tender
- Limbs: Warm, good perfusion
- Neuro: Alert, irritable but consolable, no meningeal signs

