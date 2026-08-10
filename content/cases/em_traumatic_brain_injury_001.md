---
id: em_traumatic_brain_injury_001
schema_version: 2
status: in_review
specialty: emergency
system: nervous
presentation: "Head injury with loss of consciousness"
first_impression: "Patient appears drowsy, holding his head, with a visible scalp laceration."
first_impression_id: "Pasien tampak mengantuk, memegangi kepalanya, dengan luka robek di kulit kepala."
target_condition: "Traumatic brain injury"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "PNPK Cedera Otak Traumatik (KMK 1600/2022)" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I hit my head and passed out for a few minutes."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Mechanism of injury (how did you hit your head?)", critical: true }
    - { item: "Time of injury (when did it happen?)", critical: true }
    - { item: "Duration of loss of consciousness (how long were you out?)", critical: true }
    - { item: "Amnesia (do you remember the fall? do you remember things after?)", critical: true }
    - { item: "Vomiting (have you thrown up?)", critical: false }
    - { item: "Seizures (did you have any shaking or fits?)", critical: true }
    - { item: "Anticoagulant use (are you taking any blood thinners?)", critical: true }
    - { item: "Alcohol consumption (did you drink alcohol today?)", critical: true }
  associated_symptoms:
    - { item: "Headache (where does it hurt?)", critical: false }
    - { item: "Dizziness or lightheadedness", critical: false }
    - { item: "Blurred or double vision", critical: false }
    - { item: "Nausea", critical: false }
  pmh:
    - { item: "Hypertension", critical: false }
    - { item: "Diabetes", critical: false }
    - { item: "Previous head injury", critical: false }
  medications:
    - { item: "Amlodipine (for blood pressure)", critical: false }
  family_social:
    - { item: "Occupation (construction worker)", critical: false }
    - { item: "Living situation (lives with wife and children)", critical: false }
    - { item: "Alcohol use (occasional, but not today)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong (maybe a concussion, worried about brain bleed)", critical: true }
    - { item: "Concerns - what worries them (can't work, might need surgery)", critical: true }
    - { item: "Expectations - what they hope for (wants a CT scan to be sure, hopes to go home soon)", critical: false }
red_flags:
  - { item: "Loss of consciousness", critical: true }
  - { item: "Vomiting", critical: true }
  - { item: "Amnesia (anterograde or retrograde)", critical: true }
  - { item: "Anticoagulant use", critical: true }
  - { item: "Focal neurological deficit", critical: true }
expected_ddx:
  working_diagnosis: "Traumatic brain injury"
  differentials: [ "Concussion", "Intracranial hemorrhage", "Skull fracture" ]
investigations:
  appropriate:
    - { name: "CT head (non-contrast)", expected: "Possible intracranial hemorrhage or skull fracture" }
  inappropriate: [ "MRI head (not urgent in acute setting)" ]
physical_exam_findings:
  general: "Alert but drowsy, oriented to person and place, not to time. GCS 14 (E3 V5 M6)."
  vitals: { temperature: 36.8, blood_pressure: "130/80", heart_rate: 90, respiratory_rate: 18, oxygen_saturation: 98 }
management:
  pharmacological:
    - "Paracetamol 1g IV for headache (if no contraindication)"
    - "Ondansetron 4mg IV for nausea/vomiting"
  non_pharmacological:
    - "Observation in emergency department for at least 6 hours"
    - "Neurosurgery consultation if deterioration or abnormal CT"
  education_safety_netting:
    - "Return immediately if worsening headache, vomiting, confusion, seizures, or weakness"
    - "Avoid strenuous activity, driving, or alcohol for 24 hours"
    - "Follow-up with primary care or neurology in 1-2 weeks"
scoring_weights_override: null
---

## Identity

My name is Budi Santoso. I'm 45 years old. I work as a construction worker on a building site near my home in Jakarta. I'm married to Dewi, and we have two children: Rizky (18 years old, just finished high school) and Sari (15 years old, still in school). I'm usually a hardworking and calm person, but right now I'm really worried. I don't like to complain much, but this head injury scared me. I'm afraid I might have damaged my brain and won't be able to work again. I always try to be careful, but today I forgot to wear my helmet because it was hot. I drink coffee every morning, and sometimes I have a beer with friends on weekends, but not today.

## Opening line

"Dok, I fell from the scaffolding and hit my head. I was unconscious for a bit."

## How I present

I'm lying on a stretcher in the emergency room. I'm holding my head with both hands and my eyes are closed most of the time because the light hurts. I speak slowly and quietly. My face looks tense and worried. I'm trying to stay calm but I keep asking my wife if I'm okay.

## What I know

- I was working on the second floor of a building, about 2 meters high. I slipped on some wet concrete and fell backward.
- I landed on the back of my head. I didn't have a helmet on.
- My coworkers told me I was unconscious for about 2 or 3 minutes. I don't remember the fall at all.
- I woke up in the ambulance. I remember the paramedics asking me questions, but I felt confused.
- I threw up once on the way to the hospital.
- I didn't have any shaking or fits.
- I don't take any blood thinners. I take amlodipine every morning for high blood pressure.
- I didn't drink any alcohol today.
- I have a headache at the back of my head, it's a dull ache but getting worse.
- I feel dizzy and my vision is a little blurry.
- I have high blood pressure, but it's usually controlled with the medicine.
- I've never had a head injury before.
- I live with my wife and children. I'm the main earner.

## Communication profile

I finished high school. I speak Indonesian with a bit of a Javanese accent. I'm not very good with medical words, so please use simple language. I tend to answer only what you ask, and I don't volunteer extra information unless you ask. I'm anxious but I try to be polite and cooperative.

## Disclosure rules

I will answer only the questions you ask me. I won't add extra details unless you specifically ask for them. If you ask about something I don't know, I'll say "I don't know" or "I don't remember."

## Vital signs

The nurse told me my temperature is 36.8 degrees Celsius, my blood pressure is 130 over 80, my heart rate is 90 beats per minute, I'm breathing 18 times per minute, and my oxygen level is 98% on room air.

## Physical findings

- **General appearance:** I'm awake but I feel sleepy. I know who I am and where I am, but I'm not sure what time it is. The doctor said my GCS is 14.
- **Skin:** There's a small scrape on the back of my head, but no cuts or bruises elsewhere.
- **Head and neck:** The back of my head is tender when touched. The doctor checked my eyes and said they look normal, no dark circles or bruises behind my ears. No fluid is leaking from my nose or ears.
- **Chest:** My breathing is fine, no pain.
- **Abdomen:** My stomach is soft, no pain.
- **Limbs:** I can move my arms and legs normally. No weakness.
- **Nervous system:** My pupils are the same size and react to light. The doctor checked my reflexes and they seem normal. I don't have any numbness or tingling.
