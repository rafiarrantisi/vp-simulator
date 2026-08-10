---
id: neuro_first_seizure_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous
presentation: "First seizure"
presentation_id: "Kejang pertama kali dan takut akan kambuh lagi"
first_impression: "Patient appears to have neurological concerns."
first_impression_id: "Pasien tampak mengalami masalah neurologis."
target_condition: "First unprovoked seizure"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "NICE guideline NG127: Epilepsies in children, young people and adults" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I had a fit or something and I'm scared it might happen again."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Circumstances preceding the event (e.g., location, activity, sleep, alcohol)", critical: true }
    - { item: "Description of the event from witnesses", critical: true }
    - { item: "Duration of the episode", critical: true }
    - { item: "Post-ictal symptoms (e.g., confusion, fatigue, headache)", critical: true }
    - { item: "Any history of similar episodes", critical: true }
    - { item: "Any provoking factors (e.g., sleep deprivation, alcohol, fever, stress)", critical: true }
  associated_symptoms:
    - { item: "Headache after the event", critical: false }
    - { item: "Muscle soreness", critical: false }
    - { item: "Tongue biting or injury", critical: true }
    - { item: "Incontinence", critical: false }
    - { item: "Confusion", critical: true }
  pmh:
    - { item: "No previous seizures", critical: true }
    - { item: "No head injuries", critical: false }
    - { item: "No known neurological conditions", critical: false }
    - { item: "No diabetes or hypertension", critical: false }
    - { item: "Migraines in past (not recently)", critical: false }
  medications:
    - { item: "None regularly", critical: false }
    - { item: "Occasional ibuprofen for headaches", critical: false }
  family_social:
    - { item: "No family history of epilepsy", critical: true }
    - { item: "Works as a construction worker", critical: false }
    - { item: "Drinks alcohol socially, 2-3 beers per week, no drugs", critical: false }
    - { item: "Married, two children", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong: maybe a stroke or brain tumor", critical: true }
    - { item: "Concerns - what worries them: having another seizure while driving or at work, and about brain damage", critical: true }
    - { item: "Expectations - what they hope for: expects to get a brain scan and be told it's nothing serious", critical: false }
red_flags:
  - { item: "Head injury during seizure", critical: true }
  - { item: "New focal neurological signs on exam", critical: true }
  - { item: "Prolonged post-ictal confusion (>30 minutes)", critical: true }
expected_ddx:
  working_diagnosis: "First unprovoked seizure"
  differentials: [ "Syncope", "Psychogenic nonepileptic seizure", "Migraine with aura", "Transient ischemic attack" ]
investigations:
  appropriate:
    - { name: "Electrocardiogram (ECG)", expected: "Normal sinus rhythm" }
    - { name: "Brain MRI", expected: "Normal, no structural lesion" }
    - { name: "Electroencephalogram (EEG)", expected: "Possible interictal epileptiform discharges" }
  inappropriate: [ "CT head without contrast" ]
physical_exam_findings:
  general: "Alert, oriented, anxious but cooperative. Neurological exam: normal cranial nerves, motor, sensory, coordination, gait. No focal deficits. Small laceration on lateral tongue."
  vitals: { BP: "120/80", HR: "78", RR: "14", Temp: "36.8°C", O2_sat: "98%" }
management:
  pharmacological: [ "No long-term antiepileptic drug therapy unless seizure recurs or EEG shows high risk" ]
  non_pharmacological: [ "Advise driving restrictions per local law (e.g., 6 months seizure-free)", "Avoid sleep deprivation and excessive alcohol" ]
  education_safety_netting: [ "Seek medical attention if seizure recurs, prolonged seizure (>5 min), or new symptoms", "Inform family and workplace about seizure first aid", "Call 911 if seizure lasting >5 minutes or multiple seizures in 24 hours" ]
scoring_weights_override: null
---

## Identity
I'm Gilang Anggraini, 32 years old. I work construction—heavy lifting, scaffolding, that kind of thing. I've been married to my wife Dewi for six years, and we have two kids, ages 4 and 2. I'm usually pretty easygoing, but since this happened I've been really jumpy and nervous. I try to be tough, but inside I'm scared. I'm a practical guy, I like to fix things myself, but this is something I can't fix. I don't like doctors, but I need to know what's going on.

## Opening line
"I had some kind of fit or seizure, I guess. My wife told me what happened. I don't remember it. I'm worried it's something bad, like a stroke or a brain tumor."

## How I present
I'm sitting on the exam table, arms crossed, looking down at my hands. My voice is a little shaky, but I'm trying to stay calm. I keep glancing at the door. I look tired—I haven't slept well since it happened. My wife is in the waiting room, but I came in alone. I'm wearing my work boots and a flannel shirt. I have a small cut on the side of my tongue that I keep touching with my finger.

## What I know
*   Last Friday night, after work, I was home watching TV. I'd had a long week—not much sleep, maybe 5 hours a night. I had two beers with dinner.
*   The next thing I know, I'm waking up on the floor. My wife was kneeling over me, crying. She said I was shaking all over for about two minutes, and my eyes rolled back. She said she called 911 but by the time they got here I was already sitting up, confused.
*   I don't remember anything from when I was watching TV until I woke up on the floor. It's like a blank spot.
*   For about 10-15 minutes after I woke up, I felt really confused and groggy. I didn't know where I was at first. I had a bad headache and felt like I'd run a marathon.
*   The next day my whole body was sore, especially my back and legs. My tongue hurt where I bit it. I didn't wet myself or anything.
*   I've never had anything like this happen before. No head injuries, no concussions. I used to get migraines when I was younger, but not for a few years.
*   I don't take any medicines regularly. Sometimes I take ibuprofen for a headache or back pain.
*   Nobody in my family has had seizures or epilepsy. My parents are healthy.
*   I drink maybe 2-3 beers a week, socially. I don't use any drugs, not even marijuana.
*   I work construction, so my job is physical. I drive a truck to sites. I'm afraid to drive now.
*   I think this might be a stroke or a brain tumor. That's what's been on my mind. I'm worried I'll have another one while I'm working up high or driving. I hope you can do a scan and tell me it's nothing bad.

## Communication profile
I'm a high school graduate. I work with my hands. I use plain language—no fancy words. I'm a little terse at first, but if you ask me the right questions I'll open up. I'm anxious, so I might repeat myself or ask "Is it serious?" I get frustrated if I don't get clear answers. I don't know medical terms. If you ask me about "post-ictal" I'll just say "after I came to."

## Disclosure rules
I'll answer only what you ask me. I won't volunteer extra information unless you specifically ask. I'll stick to the facts I know. If you ask me about something I don't know, I'll say "I don't know" or "My wife could tell you better." I won't elaborate on my feelings unless you ask about them.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 125/80 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Alert, anxious, tired-looking. Sitting with arms crossed, avoids eye contact.
- Skin: No rash, bruises, or needle marks.
- Head and neck: Small cut on the side of the tongue. No bumps or tenderness on the scalp. Neck supple, no stiffness.
- Chest: Clear breath sounds, no wheezing or crackles.
- Abdomen: Soft, not tender.
- Limbs: No weakness or shaking. Muscle soreness reported but no visible swelling.
- Neurological: Cranial nerves intact. Strength and sensation normal in all limbs. Reflexes normal. No confusion now.

