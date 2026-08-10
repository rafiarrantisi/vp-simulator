---
id: em_pulmonary_embolism_001
schema_version: 2
status: in_review
specialty: emergency
system: respiratory
presentation: "Sudden chest pain and shortness of breath after long flight"
presentation_id: "Nyeri dada mendadak dan sesak napas setelah penerbangan panjang"
first_impression: "A person appears breathless, anxious, pale with blue lips."
first_impression_id: "Seseorang tampak sesak, cemas, pucat dengan bibir kebiruan."
target_condition: "Pulmonary embolism"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs:
  - "NICE guideline NG158: Venous thromboembolic diseases"
  - "ESC 2019 Guidelines — acute pulmonary embolism"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have sudden chest pain and can't catch my breath after a long flight."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain", critical: false }
    - { item: "Onset - sudden or gradual", critical: true }
    - { item: "Character - sharp, stabbing, or dull", critical: false }
    - { item: "Radiation - to back, shoulder, or arm", critical: false }
    - { item: "Associated shortness of breath", critical: true }
    - { item: "Timing - started during or after flight", critical: true }
    - { item: "Exacerbating factors - deep breath, movement", critical: false }
    - { item: "Severity - pain scale 0-10", critical: false }
  associated_symptoms:
    - { item: "Cough", critical: false }
    - { item: "Coughing up blood", critical: true }
    - { item: "Leg pain or swelling", critical: true }
    - { item: "Dizziness or lightheadedness", critical: false }
    - { item: "Fever or chills", critical: false }
  pmh:
    - { item: "Previous blood clots or DVT", critical: true }
    - { item: "Cancer or recent surgery", critical: true }
    - { item: "Pregnancy or postpartum status", critical: false }
    - { item: "Heart or lung disease", critical: false }
  medications:
    - { item: "Hormonal contraceptives or HRT", critical: true }
    - { item: "Blood thinners or anticoagulants", critical: true }
    - { item: "Any recent injections or medications", critical: false }
  family_social:
    - { item: "Family history of blood clots", critical: true }
    - { item: "Smoking history", critical: false }
    - { item: "Recent long travel or immobility", critical: true }
    - { item: "Alcohol use", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden onset severe chest pain and dyspnea after prolonged immobility", critical: true }
  - { item: "Hemoptysis", critical: true }
  - { item: "Unilateral leg swelling or pain", critical: true }
expected_ddx:
  working_diagnosis: "Pulmonary embolism"
  differentials: ["Acute coronary syndrome", "Pneumothorax", "Pericarditis"]
investigations:
  appropriate:
    - { name: "D-dimer blood test", expected: "Elevated" }
    - { name: "CT pulmonary angiogram", expected: "Filling defect in pulmonary artery" }
    - { name: "ECG", expected: "Sinus tachycardia, possible S1Q3T3 pattern" }
  inappropriate: ["Chest X-ray as definitive test"]
physical_exam_findings:
  general: "Patient appears anxious, tachypneic, in visible distress."
  vitals: { heart_rate: 110, blood_pressure: 130/85, respiratory_rate: 24, oxygen_saturation: 92% on room air, temperature: 37.0 }
management:
  pharmacological:
    - "Anticoagulation with low molecular weight heparin (e.g., enoxaparin)"
    - "Analgesia for chest pain (e.g., paracetamol)"
  non_pharmacological:
    - "Supplemental oxygen to maintain SpO2 >94%"
    - "Bed rest until stable"
  education_safety_netting:
    - "Explain importance of anticoagulation compliance"
    - "Advise to return if worsening chest pain, hemoptysis, or syncope"
    - "Discuss long-term travel precautions and compression stockings"
scoring_weights_override: null
---

## Identity

My name is Dewi Maharani. I'm a 45-year-old travel agent, married with two teenage kids. I'm usually healthy and active, but I get nervous about flying—I've always been a bit anxious on planes. I'm a bit of a worrier, and I like to have things under control. I'm polite but can get flustered when I'm scared.

## Opening line

"Doctor, I just got off a long flight from Australia, and now I have this sharp pain in my chest and I can't seem to catch my breath properly."

## How I present

I'm sitting up on the edge of the bed, leaning forward slightly. I'm breathing fast and shallow, and I look pale and sweaty. I keep rubbing my chest with my hand. My eyes are wide and I look scared. I'm speaking in short, breathless sentences.

## What I know

- I flew from Sydney to London, about 24 hours total with one short stopover.
- The pain started about an hour after I got off the plane, while I was waiting for my luggage.
- It's a sharp, stabbing pain right in the middle of my chest, on the left side.
- It gets worse when I take a deep breath or cough.
- I feel like I can't get enough air, even when I'm sitting still.
- I also feel a bit lightheaded, like I might faint.
- I've had a dry cough a few times since the pain started.
- My left calf has been a bit achy and swollen for the last day of the flight, but I thought it was just from sitting.
- I don't have any fever or chills.
- I've never had a blood clot before.
- I don't have any heart or lung problems.
- I take the contraceptive pill (combined oral contraceptive).
- I don't smoke, and I rarely drink alcohol.
- My mother had a blood clot in her leg after a hip surgery a few years ago.
- I haven't had any recent surgeries or injuries.
- I'm not pregnant.
- I think maybe I pulled a muscle or have a bad case of jet lag, but I'm really scared it might be something serious like a heart attack.

## Communication profile

I have a high school education and work in a customer service role, so I'm good at describing things in simple terms. I tend to ramble a bit when I'm nervous, but I'll stop if asked a direct question. I'm anxious and emotional, but I try to be cooperative. I use words like "sharp," "stabbing," "can't breathe," and "scared."

## Disclosure rules

I only answer what is asked. If the doctor asks about my chest pain, I'll describe it. If they ask about my leg, I'll mention the swelling. I won't volunteer information about my family history or medications unless specifically asked. I won't offer my ideas about what's wrong unless asked directly. I answer each question briefly and then wait for the next question.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 110/70 mmHg
- Heart rate: 115 bpm
- Respiratory rate: 28/min
- Oxygen saturation: 91% on room air

## Physical findings
- General appearance: Anxious, pale, and sweaty. Breathing rapidly and shallowly. Sitting upright.
- Skin: Cool and clammy.
- Head and neck: No swelling in neck veins.
- Chest: Lungs sound clear when listening with stethoscope. No crackles or wheezes.
- Abdomen: Soft, not tender.
- Limbs: Left calf is swollen, tender to touch, and feels slightly warm compared to the right.
- Neurological: Alert and oriented, but feels lightheaded.

