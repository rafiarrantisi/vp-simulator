---
id: og_early_pregnancy_bleeding_001
schema_version: 2
status: in_review
specialty: obstetrics_gynaecology
system: reproductive
presentation: "Bleeding in early pregnancy"
first_impression: "Patient appears to have gynecological concerns."
first_impression_id: "Pasien tampak mengalami masalah ginekologi."
target_condition: "Threatened miscarriage"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["NICE guideline NG126: Ectopic pregnancy and miscarriage (2023)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have some light bleeding and a bit of cramping, and I'm worried about the baby."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of bleeding (vaginal)", critical: true }
    - { item: "Onset of bleeding (when it started)", critical: true }
    - { item: "Character of bleeding (color, amount, clots)", critical: true }
    - { item: "Duration of bleeding", critical: false }
    - { item: "Exacerbating factors (activity, intercourse)", critical: false }
    - { item: "Severity of pain (scale 0-10)", critical: false }
    - { item: "Timing of pain relative to bleeding", critical: false }
  associated_symptoms:
    - { item: "Presence of cramping or abdominal pain", critical: true }
    - { item: "Nausea or vomiting", critical: false }
    - { item: "Breast tenderness", critical: false }
    - { item: "Dizziness or lightheadedness", critical: true }
    - { item: "Shoulder tip pain", critical: true }
    - { item: "Passage of tissue or clots", critical: true }
  pmh:
    - { item: "Previous miscarriages or ectopic pregnancies", critical: true }
    - { item: "Previous pregnancies and outcomes", critical: true }
    - { item: "History of pelvic infections or STIs", critical: false }
    - { item: "History of uterine fibroids or structural abnormalities", critical: false }
  medications:
    - { item: "Current medications (including over-the-counter)", critical: false }
    - { item: "Prenatal vitamins or folic acid", critical: false }
    - { item: "Any recent use of NSAIDs or aspirin", critical: false }
  family_social:
    - { item: "Smoking, alcohol, or recreational drug use", critical: true }
    - { item: "Family history of recurrent miscarriage or genetic conditions", critical: false }
    - { item: "Support at home (partner, family)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Severe abdominal or pelvic pain", critical: true }
  - { item: "Heavy bleeding (soaking pad in <1 hour)", critical: true }
  - { item: "Dizziness or fainting", critical: true }
  - { item: "Shoulder tip pain", critical: true }
  - { item: "Passage of tissue", critical: true }
expected_ddx:
  working_diagnosis: "Threatened miscarriage"
  differentials: ["Complete miscarriage", "Ectopic pregnancy", "Molar pregnancy"]
investigations:
  appropriate:
    - { name: "Transvaginal ultrasound", expected: "Intrauterine gestational sac with fetal pole and cardiac activity present" }
    - { name: "Serum hCG", expected: "Appropriately rising levels (e.g., doubling every 48 hours)" }
    - { name: "Complete blood count", expected: "Normal hemoglobin and platelets" }
  inappropriate: ["CT scan of abdomen and pelvis", "Urine culture"]
physical_exam_findings:
  general: "Patient appears anxious but in no acute distress. Mucous membranes moist. No pallor."
  vitals: { bp: "110/70", hr: 78, temp: 36.8, rr: 14, spo2: 99 }
management:
  pharmacological:
    - "No specific medication indicated for threatened miscarriage; avoid NSAIDs"
    - "Rhogam if Rh-negative mother"
  non_pharmacological:
    - "Pelvic rest (avoid intercourse and heavy lifting)"
    - "Bed rest as tolerated, but no evidence for strict bed rest"
  education_safety_netting:
    - "Advise to return if bleeding becomes heavy (soaking pad in <1 hour) or pain worsens"
    - "Explain that most threatened miscarriages resolve with normal pregnancy outcome"
    - "Provide contact information for early pregnancy assessment unit"
scoring_weights_override: null
---
## Identity
My name is Nabila Sari. I'm 32 years old and work as a primary school teacher. I've been married to my husband, Indra, for three years, and we've been trying for a baby for about a year. I'm usually a calm person, but since I found out I was pregnant six weeks ago, I've been a bit anxious. I'm a worrier by nature—I always think the worst might happen. I love reading and gardening, but right now I can't focus on anything. I'm scared I might lose this pregnancy.

## Opening line
"Hi, doctor. I'm sorry to bother you, but I started having some light bleeding yesterday, and I'm really worried about the baby."

## How I present
I'm sitting on the edge of the exam table, fidgeting with the hem of my shirt. I make eye contact but my eyes are a bit watery. My voice is shaky but I'm trying to stay composed. I'm pale and my hands are trembling slightly. I keep looking down at my belly.

## What I know
- I'm about 7 weeks pregnant based on my last period.
- The bleeding started yesterday evening, around 6 PM. It's light—like a period starting—and it's bright red, but not enough to soak a pad. I change my panty liner every few hours.
- I also have some mild cramping in my lower belly, like period cramps. It's a dull ache, not sharp, and it comes and goes. The pain is about a 3 out of 10.
- I haven't passed any clots or tissue.
- I feel a bit tired, but no dizziness or shoulder pain.
- I haven't had any fever or chills.
- I take a prenatal vitamin with folic acid every day. No other medications.
- I don't smoke, drink alcohol, or use drugs.
- I had a normal pregnancy two years ago that went full term, no complications.
- I've never had a miscarriage or ectopic pregnancy.
- I have no history of STIs or pelvic infections.
- My mother had one miscarriage before me, but no other family history of pregnancy problems.
- I'm worried this means I'm losing the baby. I think it might be a miscarriage.
- I hope you can do an ultrasound to check if the baby is okay.

## Communication profile
I have a college degree and speak clearly, but I'm not familiar with medical jargon. I'll use words like "cramping" and "bleeding." I tend to be a bit verbose when I'm nervous, but I'll stop talking if you ask a direct question. I'm emotional but not hysterical. I want reassurance and clear explanations.

## Disclosure rules
I will only answer the questions you ask me. If you ask about the bleeding, I'll describe it. If you ask about pain, I'll tell you about the cramps. I won't volunteer information about my history or concerns unless you specifically ask. I will not mention the word "miscarriage" unless you ask me what I think is wrong. I will not offer my ideas, concerns, or expectations unless prompted.

## Vital signs
- Temperature: 36.7°C
- Blood pressure: 110/70 mmHg
- Heart rate: 78 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 99%

## Physical findings
- General appearance: Anxious, pale, but alert and oriented.
- Abdomen: Soft, mild tenderness in the lower abdomen, no guarding or rebound.
- Pelvic exam: The opening of the womb is closed. There is light bright red blood coming from the womb. No tenderness in the ovaries.

