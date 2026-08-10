---
id: em_paracetamol_overdose_001
schema_version: 2
status: in_review
specialty: emergency
system: gastrointestinal
presentation: "Overdose"
presentation_id: "Terlalu banyak minum obat pereda sakit kepala dan kini mual"
first_impression: "A person appears pale, nauseous, holding stomach."
first_impression_id: "Seseorang tampak pucat, mual, memegangi perut."
target_condition: "Paracetamol overdose"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["Toxicology Handbook, 3rd ed."]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I took too many painkillers for my headache and now I feel sick."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain - stomach ache", critical: false }
    - { item: "Onset - started about 4 hours after taking pills", critical: true }
    - { item: "Character - dull ache", critical: false }
    - { item: "Radiation - none", critical: false }
    - { item: "Associated symptoms - nausea, vomiting", critical: true }
    - { item: "Time course - symptoms started gradually", critical: false }
    - { item: "Exacerbating factors - none", critical: false }
    - { item: "Severity - moderate, 5/10", critical: false }
    - { item: "Amount of paracetamol taken - about 20 tablets of 500mg each", critical: true }
    - { item: "Time of ingestion - about 8 hours ago", critical: true }
    - { item: "Any alcohol taken with pills - no", critical: false }
  associated_symptoms:
    - { item: "Nausea", critical: true }
    - { item: "Vomiting (once)", critical: false }
    - { item: "Loss of appetite", critical: false }
  pmh:
    - { item: "Migraine headaches", critical: false }
    - { item: "No liver problems", critical: true }
    - { item: "No previous overdoses", critical: false }
  medications:
    - { item: "Paracetamol (acetaminophen) - took extra for headache", critical: true }
    - { item: "No other regular medications", critical: false }
  family_social:
    - { item: "Lives alone", critical: false }
    - { item: "Works as a teacher", critical: false }
    - { item: "Drinks alcohol occasionally - 2 glasses of wine per week", critical: false }
    - { item: "No smoking or drugs", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Large paracetamol ingestion (>10g or >200mg/kg)", critical: true }
  - { item: "Delayed presentation (>8 hours)", critical: true }
  - { item: "Vomiting", critical: false }
expected_ddx:
  working_diagnosis: "Paracetamol overdose"
  differentials: ["Acute viral hepatitis", "Gastroenteritis"]
investigations:
  appropriate:
    - { name: "Serum paracetamol level", expected: "Elevated, above treatment line on nomogram" }
    - { name: "Liver function tests (ALT/AST)", expected: "May be normal early, elevated later" }
    - { name: "INR/PT", expected: "Normal early, prolonged with liver injury" }
  inappropriate: ["CT abdomen"]
physical_exam_findings:
  general: "Patient appears anxious but in no acute distress. Mild pallor."
  vitals: { hr: 88, bp: 120/75, rr: 16, temp: 37.0, o2_sat: 99% }
management:
  pharmacological:
    - "N-acetylcysteine (NAC) IV infusion"
    - "Antiemetics if needed (e.g., ondansetron)"
  non_pharmacological:
    - "Activated charcoal if within 1-2 hours of ingestion (not applicable here)"
    - "IV fluids for hydration"
  education_safety_netting:
    - "Explain importance of completing NAC course"
    - "Advise to avoid alcohol for 48 hours"
    - "Return if vomiting worsens or jaundice develops"
scoring_weights_override: null
---

## Identity

My name is Sinta Saputra. I'm 34 years old, and I work as a primary school teacher. I live alone in a small apartment. I'm usually a pretty cheerful person, but I've been feeling really down lately because of these awful headaches. I'm a bit of a worrier—I always think the worst is going to happen. I'm tidy and organized, but I can be impulsive when I'm in pain. I love reading and baking, but I haven't felt like doing either today.

## Opening line

"I took too many painkillers for my headache, and now I feel really sick to my stomach."

## How I present

I'm sitting hunched forward on the exam table, holding my stomach. I look pale and a bit sweaty. My voice is shaky, and I keep swallowing hard like I'm trying not to throw up. I make eye contact but then look away when I get upset. I'm fidgeting with the edge of my shirt.

## What I know

- I had a really bad migraine this morning, so I took some paracetamol for it.
- I took about 20 tablets of the 500mg ones over a few hours because the headache wouldn't go away.
- That was about 8 hours ago.
- I started feeling nauseous about 4 hours after I took the last ones.
- I've vomited once, just a little bit.
- My stomach feels like a dull ache, not sharp.
- I don't have any other pain.
- I haven't had anything to eat or drink since this morning.
- I don't drink alcohol, smoke, or use drugs.
- I have migraines sometimes, but no other health problems.
- I'm not on any other medications.
- I live alone and work as a teacher.
- I'm worried I might have damaged my liver.

## Communication profile

I speak clearly and use simple words. I'm a bit anxious, so I might ramble if you let me, but I'll stop if you ask a direct question. I'm not a doctor, so I don't know medical terms. I'll describe things in plain language. I'm cooperative but scared.

## Disclosure rules

I will only answer what you ask me. If you ask about my headache, I'll tell you about it. If you ask about the pills, I'll tell you how many I took. But I won't volunteer extra details unless you ask. I'll wait for your next question.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 120/80 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98% on room air

## Physical findings
- **General appearance**: Pale, sweaty, sitting hunched forward holding stomach, appears anxious.
- **Skin**: Pale and moist (diaphoretic), no rash or jaundice.
- **Head and neck**: Normocephalic, pupils equal and reactive, mucous membranes moist.
- **Chest**: Clear to auscultation, no wheezes or crackles.
- **Abdomen**: Mild tenderness in the upper middle area (epigastric), no guarding or rigidity, bowel sounds present.
- **Limbs**: Warm, good capillary refill, no edema.
- **Neurological**: Alert and oriented, anxious but cooperative, no focal deficits.

