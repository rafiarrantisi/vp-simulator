---
id: em_hypertensive_emergency_001
schema_version: 2
status: ai_generated
specialty: emergency
system: cardiovascular
presentation: Severe headache and blurred vision with very high blood pressure
presentation_id: Sakit kepala parah dan penglihatan kabur dengan tekanan darah sangat
  tinggi
first_impression: Patient sits rigidly, squinting and pressing temples, looks uncomfortable
  and distressed.
first_impression_id: Pasien tampak duduk kaku, menyipitkan mata dan menekan pelipis,
  tampak tidak nyaman dan gelisah.
target_condition: Hypertensive emergency
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages:
- en
source_refs:
- PNPK Hipertensi Dewasa (KMK 4634/2021) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes46342021
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: I have a very bad headache and my vision is blurry.
anamnesis_checklist:
  hpi_socrates:
  - item: Onset (when did the headache start?)
    critical: false
  - item: Location (where exactly is the headache?)
    critical: false
  - item: Quality (what does the headache feel like?)
    critical: false
  - item: Severity (how bad is the pain on a scale of 0-10?)
    critical: false
  - item: Timing (is it constant or comes and goes?)
    critical: false
  - item: Aggravating factors (does anything make it worse?)
    critical: false
  - item: Relieving factors (does anything make it better?)
    critical: false
  - item: Associated symptoms (blurred vision, nausea, chest pain, shortness of breath?)
    critical: true
  associated_symptoms:
  - item: Nausea or vomiting
    critical: false
  - item: Chest pain or tightness
    critical: true
  - item: Shortness of breath
    critical: true
  - item: Numbness or weakness in arms or legs
    critical: true
  - item: Difficulty speaking
    critical: true
  pmh:
  - item: History of high blood pressure
    critical: true
  - item: History of diabetes
    critical: false
  - item: History of kidney disease
    critical: false
  - item: History of stroke or heart attack
    critical: true
  medications:
  - item: Current blood pressure medications
    critical: true
  - item: Medication adherence (do you take them regularly?)
    critical: true
  - item: Any other medications or supplements
    critical: false
  family_social:
  - item: Family history of high blood pressure or stroke
    critical: false
  - item: Smoking history
    critical: false
  - item: Alcohol use
    critical: false
  - item: Occupation and daily activities
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Severe headache with blurred vision
  critical: true
- item: Blood pressure >180/120 mmHg
  critical: true
- item: Chest pain or shortness of breath
  critical: true
- item: Neurological symptoms (weakness, numbness, speech difficulty)
  critical: true
expected_ddx:
  working_diagnosis: Hypertensive emergency
  differentials:
  - Hypertensive urgency
  - Acute ischemic stroke
  - Migraine with aura
investigations:
  appropriate:
  - name: Blood pressure measurement
    expected: '>180/120 mmHg'
  - name: Fundoscopy
    expected: Papilledema or retinal hemorrhages
  - name: ECG
    expected: Left ventricular hypertrophy or ischemia
  - name: Serum creatinine
    expected: Elevated (if renal involvement)
  - name: Urinalysis
    expected: Proteinuria or hematuria
  inappropriate:
  - Carotid ultrasound
physical_exam_findings:
  general: Anxious, in moderate distress, holding head with both hands
  vitals:
    bp: 210/130
    hr: 100
    rr: 18
    temp: 36.8
    spo2: 98
management:
  pharmacological:
  - IV nicardipine or labetalol for controlled blood pressure reduction
  - IV fluids if needed, but avoid overhydration
  non_pharmacological:
  - Admit to intensive care unit (ICU) for continuous monitoring
  - Reduce mean arterial pressure by no more than 25% in the first hour
  education_safety_netting:
  - Explain the importance of strict blood pressure control to prevent organ damage
  - Instruct to return immediately if symptoms worsen or new symptoms appear
  - Emphasize medication adherence and regular follow-up
scoring_weights_override: null
---
## Identity

My name is Suryanto Setiawan. I am 58 years old, a retired civil servant. Now I run a small warung in front of my house in Yogyakarta. I am married to Dewi, and we have two grown children who live in Jakarta. I am usually a calm person, but I get worried when my body feels strange. I like to drink strong coffee every morning. My biggest fear is having a stroke like my father did.

## Opening line

Dok, kepala saya sakit sekali, dan penglihatan saya kabur.

## How I present

I am sitting hunched over on the exam table, holding my head with both hands. My face is grimacing. I speak softly because the light hurts my eyes. I look anxious and tired.

## What I know

- The headache started about 2 hours ago, while I was sitting at the warung.
- It came on slowly and got worse. Now it is very severe, like a pounding inside my head.
- The pain is mostly at the back of my head, but it spreads to the whole head.
- It is constant, not going away.
- Nothing makes it better. Bright light makes it worse.
- My vision is blurry, like looking through fog.
- I do not feel nauseous or dizzy.
- I have no chest pain or trouble breathing.
- I have had high blood pressure for about 10 years.
- I take amlodipine 5 mg, but sometimes I forget to take it, especially when I feel fine.
- My father had a stroke at age 65.
- I used to smoke, but I quit 5 years ago. I do not drink alcohol.
- I think maybe my blood pressure is very high again. I am worried I might have a stroke like my father. I hope you can give me medicine to bring it down quickly and make me feel better.

## Communication profile

I finished high school. I speak Indonesian with a Javanese accent. I tend to answer only what is asked, and I don't volunteer extra information. I am polite but anxious. I may pause to think before answering.

## Disclosure rules

I will answer only the question the doctor asks, and then I will stop. I will not add details unless asked.

## Vital signs

The nurse told me my numbers: temperature 36.8°C, blood pressure 210 over 130, heart rate 100 beats per minute, breathing 18 times per minute, and oxygen level 98% on room air.

## Physical findings

- **General appearance:** I look anxious and in pain. I am holding my head.
- **Skin:** Normal, no rashes.
- **Head and neck:** My head hurts all over, especially the back. My eyes feel blurry, but they are not red. The light bothers me.
- **Chest:** No pain or tightness. Breathing feels normal.
- **Abdomen:** No pain.
- **Limbs:** No weakness or numbness. I can move my arms and legs normally.
- **Nervous system:** I feel clear-headed, no confusion. No trouble speaking. No tingling.
