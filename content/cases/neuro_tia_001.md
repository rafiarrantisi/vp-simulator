---
id: neuro_tia_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous
presentation: "Transient weakness or speech disturbance"
presentation_id: "Kelemahan lengan kanan dan bicara tidak jelas selama sepuluh menit"
first_impression: "Patient appears to have neurological concerns."
first_impression_id: "Pasien tampak mengalami masalah neurologis."
target_condition: "Transient ischaemic attack"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs:
  - "PNPK Tata Laksana Stroke (KMK 304/2026) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes3042026"
  - "AHA/ASA guideline — transient ischaemic attack (2009)"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I had a strange episode where my right arm went weak and I couldn't speak clearly for about ten minutes."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site – which body part affected", critical: true }
    - { item: "Onset – sudden or gradual", critical: true }
    - { item: "Character – weakness, numbness, speech difficulty", critical: true }
    - { item: "Radiation – none", critical: false }
    - { item: "Associations – any headache, dizziness, vision change", critical: false }
    - { item: "Time course – exactly how long did symptoms last", critical: true }
    - { item: "Exacerbating/relieving factors – anything that helped or worsened", critical: false }
    - { item: "Severity – complete loss or partial", critical: false }
  associated_symptoms:
    - { item: "Any loss of vision in one eye", critical: false }
    - { item: "Any numbness or tingling", critical: false }
    - { item: "Any headache or neck pain", critical: true }
    - { item: "Any difficulty swallowing", critical: false }
    - { item: "Any chest pain or palpitations", critical: false }
  pmh:
    - { item: "Hypertension", critical: true }
    - { item: "Diabetes mellitus type 2", critical: true }
    - { item: "Previous stroke or TIA", critical: true }
    - { item: "Atrial fibrillation", critical: true }
    - { item: "Hypercholesterolaemia", critical: false }
  medications:
    - { item: "Antihypertensives – name and dose", critical: true }
    - { item: "Antidiabetic medication", critical: true }
    - { item: "Antiplatelet or anticoagulant", critical: true }
    - { item: "Statin", critical: false }
    - { item: "Any over‑the‑counter or herbal supplements", critical: false }
  family_social:
    - { item: "Family history of stroke or heart disease", critical: true }
    - { item: "Smoking status", critical: true }
    - { item: "Alcohol consumption", critical: true }
    - { item: "Living situation and support", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden onset focal neurological deficit (weakness/speech)", critical: true }
  - { item: "Symptoms that resolved within 24 hours but could be a warning", critical: true }
  - { item: "Vascular risk factors (hypertension, diabetes, smoking)", critical: false }
expected_ddx:
  working_diagnosis: "Transient ischaemic attack"
  differentials: [ "Simple partial seizure", "Migraine with aura", "Hypoglycaemia", "Functional neurological disorder" ]
investigations:
  appropriate:
    - { name: "CT head (non‑contrast)", expected: "No acute intracranial haemorrhage or mass" }
    - { name: "Carotid duplex ultrasound", expected: "May show <50% stenosis" }
    - { name: "ECG", expected: "Normal sinus rhythm, no atrial fibrillation" }
    - { name: "Blood glucose", expected: "Normal (exclude hypoglycaemia)" }
    - { name: "Full blood count and coagulation profile", expected: "Normal" }
  inappropriate: [ "CT angiography of head and neck in all patients", "MRI brain routinely" ]
physical_exam_findings:
  general: "Alert, oriented, well‑nourished. No distress. Mild anxiety."
  vitals: { BP: 148/92, HR: 76 regular, RR: 16, SpO2: 98%, temp: 36.8 }
management:
  pharmacological:
    - "Aspirin 300 mg loading dose (if not already on antiplatelet), then 75 mg daily"
    - "Clopidogrel 75 mg daily (if aspirin contraindicated)"
    - "Statin (atorvastatin 20 mg daily) – start if not already on"
    - "Antihypertensive optimisation"
  non_pharmacological:
    - "Carotid endarterectomy if >70% stenosis"
    - "Lifestyle counselling: smoking cessation, diet, exercise"
  education_safety_netting:
    - "Explain that this is a warning sign and that urgent assessment is needed"
    - "Advise to call 999 if any new or recurrent symptoms"
    - "Provide written information about TIA and stroke prevention"
scoring_weights_override: null
---

## Identity

My name is Suparmi Wijaya. I’m 67 years old, a retired primary school teacher. I live with my husband, Sutopo, in a small house in town. I have two grown sons who live nearby. I’m usually a calm, cheerful person, but since this happened I’ve been really jumpy and scared. I like to keep busy – gardening, knitting, playing bridge with friends. I’m not someone who complains, so when I had that attack it really shook me.

## Opening line

“I’m here because I had a very scary episode yesterday – my right arm suddenly went limp and I couldn’t get my words out properly. It lasted maybe ten minutes, then went away completely. I’m terrified it might happen again.”

## How I present

I’m sitting forward in the chair, clutching my handbag. My voice is a bit shaky, and I keep looking at my right arm as if checking it’s still working. I make eye contact, but I’m anxious – my face is tense and I’m fidgeting. I’m trying to be polite but I’m clearly worried.

## What I know

- **The episode**: It started around 2:30 p.m. yesterday while I was watching TV. My right arm suddenly felt heavy and weak – I couldn’t lift it. At the same time, my speech got slurred; I knew what I wanted to say but the words came out jumbled. My husband noticed and asked if I was okay. It lasted about 10 minutes, then everything went back to normal. No headache, no chest pain, no vision problems.
- **Past medical history**: I have high blood pressure (diagnosed 10 years ago) and type 2 diabetes (diagnosed 5 years ago). I also have high cholesterol. I’ve never had a stroke or anything like this before.
- **Medications**: I take lisinopril 10 mg daily for blood pressure, metformin 500 mg twice a day for diabetes, and atorvastatin 20 mg daily. I do not take aspirin or any blood thinners. No supplements.
- **Family history**: My father died of a stroke at 72. My mother had heart problems. No siblings.
- **Social history**: I quit smoking 15 years ago (I smoked a pack a day for 20 years). I drink maybe one glass of wine with dinner a couple of times a week. I live with my husband, we’re both independent.
- **Ideas about what’s wrong**: I think it might have been a “mini-stroke” – I’ve heard that term. But I’m not sure.
- **Concerns**: I’m scared that this is a warning sign of a big stroke. I’m worried about becoming disabled and not being able to care for myself or my husband.
- **Expectations**: I want to find out what caused it and make sure it never happens again. I’m hoping medication or lifestyle changes can prevent it.
- I've never been told I have an irregular heartbeat or atrial fibrillation.

## Communication profile

I have a high school education and some college teacher training. I use simple, everyday language. I’m articulate but not medical. I might ramble a bit when I’m nervous, but I answer questions directly. I’m cooperative and polite. I get emotional when talking about my fears.

## Disclosure rules

I will only answer the exact question you ask. I won’t volunteer extra information unless prompted. For example, if you ask, “Did you have any headache?” I’ll say “no” – I won’t mention the episode lasted ten minutes unless you ask about timing. If you ask about my medications, I’ll list them, but I won’t mention the dose unless you ask for it. I’ll stick to describing what happened in my own words.

## Vital signs
- Temperature: 36.7°C
- Blood pressure: 150/90 mmHg
- Heart rate: 78 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Anxious, alert, sitting forward.
- Skin: Warm, dry, no rashes.
- Head and neck: No visible abnormalities, no unusual sounds heard over neck.
- Chest: Clear breath sounds, no wheezes or crackles.
- Abdomen: Soft, non-tender.
- Limbs: Normal strength and movement in all limbs, no weakness.
- Neurological: Cranial nerves intact, speech clear, no facial droop, coordination normal.

