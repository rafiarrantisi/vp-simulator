---
id: neuro_acute_stroke_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous
presentation: "Sudden weakness of the right side of the body"
presentation_id: "Kelemahan mendadak pada lengan dan kaki kanan sejak pagi"
first_impression: "Elderly man sitting slumped in wheelchair, right arm limp and face slightly drooping."
first_impression_id: "Pasien tampak duduk letih di kursi roda, lengan kanan lemas dan wajah sedikit mencong."
target_condition: "Acute ischaemic stroke in thrombolysis window"
difficulty: 3
estimated_minutes: 25
mode_default: osce_full
languages: [en]
source_refs:
  - "PPK Kemenkes (Panduan Praktik Klinis) untuk Stroke Iskemik — 2021"
  - "PNPK Tata Laksana Stroke (KMK 304/2026) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes3042026"
  - "AHA/ASA acute ischaemic stroke guidelines (2019)"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I suddenly couldn't move my right arm and leg this morning."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset — when did it start?", critical: true }
    - { item: "Location — which body parts are affected?", critical: true }
    - { item: "Duration — how long has it been going on?", critical: true }
    - { item: "Character — describe the weakness (e.g., complete, partial)", critical: false }
    - { item: "Aggravating/relieving factors — anything that makes it better or worse?", critical: false }
    - { item: "Timing — constant or comes and goes?", critical: false }
    - { item: "Severity — how bad is it on a scale of 1-10?", critical: false }
    - { item: "Context — what were you doing when it started?", critical: false }
  associated_symptoms:
    - { item: "Headache", critical: true }
    - { item: "Vomiting", critical: false }
    - { item: "Loss of consciousness", critical: true }
    - { item: "Difficulty speaking or understanding speech", critical: true }
    - { item: "Facial droop", critical: true }
    - { item: "Visual disturbance (blurred vision, double vision, loss of vision)", critical: false }
    - { item: "Chest pain or palpitations", critical: false }
  pmh:
    - { item: "Hypertension", critical: true }
    - { item: "Diabetes mellitus", critical: true }
    - { item: "Atrial fibrillation or other heart disease", critical: true }
    - { item: "Previous stroke or transient ischaemic attack (TIA)", critical: true }
    - { item: "Smoking history", critical: false }
  medications:
    - { item: "Antihypertensives (e.g., amlodipine, captopril)", critical: true }
    - { item: "Antidiabetics (e.g., metformin, insulin)", critical: true }
    - { item: "Antiplatelets (e.g., aspirin, clopidogrel) or anticoagulants (e.g., warfarin)", critical: true }
    - { item: "Statins", critical: false }
  family_social:
    - { item: "Family history of stroke or heart disease", critical: false }
    - { item: "Smoking or alcohol use", critical: false }
  ice_fife:
    - { item: "Ideas — what do you think is wrong?", critical: true }
    - { item: "Concerns — what worries you most?", critical: true }
    - { item: "Expectations — what do you hope we can do for you?", critical: false }
red_flags:
  - { item: "Sudden onset of focal neurological deficit (unilateral weakness)", critical: true }
  - { item: "Time of onset known and within 4.5 hours (thrombolysis window)", critical: true }
  - { item: "No clear contraindications to thrombolysis (e.g., recent surgery, bleeding)", critical: true }
expected_ddx:
  working_diagnosis: "Acute ischaemic stroke in thrombolysis window"
  differentials:
    - "Intracerebral haemorrhage"
    - "Subarachnoid haemorrhage"
    - "Seizure with Todd's paresis"
    - "Hypoglycaemia"
    - "Migraine with aura (hemiplegic migraine)"
investigations:
  appropriate:
    - { name: "Non-contrast CT head", expected: "No evidence of intracranial haemorrhage; possible early ischaemic signs (e.g., loss of grey-white differentiation, hyperdense artery sign)" }
    - { name: "Blood glucose", expected: "Normal (e.g., 5.6 mmol/L) — excludes hypoglycaemia" }
    - { name: "ECG", expected: "Possible atrial fibrillation or normal sinus rhythm" }
    - { name: "INR/PTT", expected: "Normal (unless on anticoagulants)" }
  inappropriate:
    - "MRI brain without prior CT"
    - "Lumbar puncture"
physical_exam_findings:
  general: "Alert, anxious, sitting in wheelchair. Right-sided weakness noted. Mild dysarthria. Right facial droop."
  vitals:
    blood_pressure: "165/95 mmHg"
    heart_rate: "82 bpm"
    respiratory_rate: "18/min"
    oxygen_saturation: "97% on room air"
    temperature: "36.7°C"
management:
  pharmacological:
    - "Intravenous alteplase (tPA) if within 4.5 hours and no contraindications"
    - "Aspirin 300 mg after haemorrhage excluded (if not given tPA)"
    - "Antihypertensives if BP >185/110 mmHg (e.g., labetalol or nicardipine)"
  non_pharmacological:
    - "Admit to stroke unit or intensive care"
    - "Swallow assessment before oral intake"
    - "Physiotherapy and occupational therapy"
  education_safety_netting:
    - "Explain signs of deterioration (worsening weakness, decreased consciousness, headache)"
    - "Importance of early treatment to minimise brain damage"
    - "Lifestyle modifications: diet, exercise, medication adherence"
scoring_weights_override: null
---

## Identity

My name is Hartono. I am 68 years old, a retired civil servant. I live in a small house in Yogyakarta with my wife, Rini, who is 65. We have two children, both married and living in Jakarta. I used to work at the local government office for 35 years. Now I spend my days gardening, drinking coffee at the warung, and watching TV. I am a quiet man, but I get worried easily about my health. My biggest fear is becoming a burden to my family, especially if I can't walk or take care of myself. I like things to be simple and clear. I don't like long explanations.

## Opening line

Doctor, suddenly my right arm and leg cannot move. It happened this morning while I was having coffee.

## How I present

I am sitting in a wheelchair that a nurse brought me in. My right arm is limp on my lap, and my right leg is stretched out and heavy. I look anxious — my forehead is sweaty, and I keep glancing at my right side. My speech is a little slurred, like my mouth is not working properly. I make eye contact but I blink a lot. I am trying to stay calm, but inside I am very scared.

## What I know

- The weakness started at about 7:00 AM, right after I finished my first cup of coffee. I was sitting at the kitchen table.
- It came on all at once. I tried to lift my right arm to put down the cup, but it just flopped down. My right leg felt like a log.
- I have not had any headache, vomiting, or loss of consciousness. I did not hit my head.
- My speech is a bit thick — my wife said I sound like I have a mouthful of rice.
- The right side of my face feels droopy. When I try to smile, only the left side moves.
- I can see clearly — no double vision or blurring.
- I have high blood pressure and diabetes. I take amlodipine 10 mg every morning and metformin 500 mg twice a day.
- I do not smoke or drink alcohol. I never have.
- My father died of a heart attack at 70, but no one in my family had a stroke.
- I am worried this might be a stroke. My neighbour had one and never walked again. I hope you can give me medicine to make it better.

## Communication profile

I finished high school. I speak Indonesian at home, but I can understand and speak simple English. I am not a talker — I answer exactly what you ask and then stop. I might look at my wife for reassurance if I am unsure. I am polite but direct. I do not use medical words. I will say "heavy" or "numb" or "can't move". I am anxious, so I may repeat myself.

## Disclosure rules

I will answer only what the doctor asks. If the doctor asks about my arm, I will talk about my arm. If the doctor asks about my face, I will talk about my face. I will not volunteer extra information unless prompted. I will not guess or make up answers. If I do not understand a question, I will ask for it to be repeated.

## Vital signs

The nurse told me my numbers: temperature 36.7, blood pressure 165 over 95, heart rate 82, breathing 18 times a minute, and oxygen 97%.

## Physical findings

- **General appearance:** I am awake and alert. I look worried. My right arm and leg are completely still.
- **Skin:** My skin feels normal — warm and dry.
- **Head and neck:** No bumps or bruises. My pupils look the same size, the nurse said.
- **Chest:** My breathing is easy. No cough or pain.
- **Abdomen:** Soft, no pain.
- **Limbs:** My right arm and leg feel heavy and weak. I cannot lift my right arm off the bed at all. My right hand cannot grip anything. My right leg also cannot lift. The left side is strong and normal.
- **Neurological:** The doctor said my right side of the face droops when I smile. My speech is slurred. When the doctor touched my right arm and leg, I could barely feel it — it feels like it is wrapped in thick cloth. The doctor checked my reflexes and said my right foot turned upward when he scratched the bottom.
