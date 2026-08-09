---
id: im_ckd_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: renal
presentation: "Swollen ankles and foamy urine"
first_impression: "Patient appears uncomfortable."
first_impression_id: "Pasien tampak tidak nyaman."
target_condition: "Chronic kidney disease stage 4"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: ["PNPK Tata Laksana Hipertensi Dewasa (KMK 4634/2021) — https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes46342021"]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "My ankles are swollen and my urine looks frothy."
anamnesis_checklist:
  hpi_socrates:
    - item: "Onset – when did the swelling and foamy urine start?"
      critical: true
    - item: "Location – is the swelling only in the ankles or elsewhere?"
      critical: false
    - item: "Duration – constant or intermittent?"
      critical: false
    - item: "Character – is the urine consistently foamy or only sometimes?"
      critical: false
    - item: "Aggravating factors – does standing worsen the swelling?"
      critical: false
    - item: "Relieving factors – does elevating legs help?"
      critical: false
    - item: "Temporal pattern – worse in the morning or evening?"
      critical: false
    - item: "Severity – how much has the swelling increased?"
      critical: false
  associated_symptoms:
    - item: "Fatigue or low energy"
      critical: true
    - item: "Shortness of breath"
      critical: false
    - item: "Decreased urine output"
      critical: true
    - item: "Nausea or poor appetite"
      critical: false
    - item: "Muscle cramps"
      critical: false
  pmh:
    - item: "Hypertension"
      critical: true
    - item: "Type 2 diabetes mellitus"
      critical: true
    - item: "Previous kidney problems"
      critical: false
  medications:
    - item: "Current medications (including over-the-counter and supplements)"
      critical: true
    - item: "Any recent changes to medication"
      critical: false
  family_social:
    - item: "Family history of kidney disease or kidney failure"
      critical: true
    - item: "Family history of high blood pressure or diabetes"
      critical: false
    - item: "Smoking history"
      critical: false
    - item: "Alcohol use"
      critical: false
  ice_fife:
    - item: "Ideas - what they think is wrong"
      critical: true
    - item: "Concerns - what worries them"
      critical: true
    - item: "Expectations - what they hope for"
      critical: false
red_flags:
  - item: "Hyperkalemia risk (e.g., recent high potassium foods, symptoms of weakness/palpitations)"
    critical: true
  - item: "Uremic symptoms (confusion, hiccups, pruritus, easy bruising)"
    critical: true
  - item: "Rapidly worsening edema or shortness of breath (possible fluid overload)"
    critical: true
expected_ddx:
  working_diagnosis: "Chronic kidney disease stage 4"
  differentials:
    - "Nephrotic syndrome (minimal change disease, membranous nephropathy)"
    - "Acute kidney injury (prerenal or intrinsic)"
    - "Diabetic nephropathy (as etiology of CKD)"
investigations:
  appropriate:
    - name: "Serum creatinine and estimated GFR"
      expected: "eGFR 15-29 ml/min/1.73m², creatinine elevated (e.g., 3.5 mg/dL)"
    - name: "Urinalysis with microscopy"
      expected: "Proteinuria (3+), few granular casts, no active sediment"
    - name: "Urine albumin-to-creatinine ratio (UACR)"
      expected: ">300 mg/g (macroalbuminuria)"
    - name: "Renal ultrasound"
      expected: "Bilateral small, echogenic kidneys with reduced cortical thickness"
  inappropriate:
    - "CT abdomen with intravenous contrast (risk of contrast-induced nephropathy)"
physical_exam_findings:
  general: "Alert but fatigued-appearing; pitting edema bilateral lower extremities to mid-calf; no jugular venous distension."
  vitals:
    BP: "155/92 mmHg"
    HR: "78 bpm"
    RR: "16 breaths/min"
    Temp: "36.8°C"
    O2_sat: "97% on room air"
management:
  pharmacological:
    - "Continue ACE inhibitor (lisinopril) for renoprotection, monitor potassium and creatinine"
    - "Add loop diuretic (furosemide) for edema control if needed"
    - "Consider statin for cardiovascular risk reduction"
    - "Adjust diabetes medications (stop metformin if eGFR <30, consider SGLT2 inhibitor if appropriate)"
  non_pharmacological:
    - "Low sodium diet (<2g/day), moderate fluid restriction (1.5 L/day)"
    - "Weight monitoring daily"
    - "Avoid NSAIDs and nephrotoxic agents"
    - "Referral to nephrology for CKD stage 4 management and preparation for kidney replacement therapy"
  education_safety_netting:
    - "Explain CKD progression and need for regular follow-up with labs every 3 months"
    - "Red flags to report: sudden weight gain >2 kg in 2 days, shortness of breath, confusion, or significantly decreased urine output"
    - "Importance of blood pressure control and blood sugar management"
scoring_weights_override: null
---
## Identity

I’m Sumarno Maharani, 62 years old. I used to teach high school history, but I retired two years ago. My wife Sumiyati and I live in a small townhouse in the suburbs. I have two grown children who live a few hours away. I try to stay active—I walk the dog every morning—but lately I’ve been feeling worn out. I’m a bit stubborn and don’t like to bother doctors unless I really have to. But this swelling and the weird-looking urine scared me enough to come in. I’m also a worrier, especially since my father had kidney trouble later in life.

## Opening line

“Doctor, I’ve noticed my ankles are swollen and my urine has been looking like beer foam—kind of frothy, you know? It’s been going on for a few months and it’s getting worse.”

## How I present

I walk in slowly, a little out of breath. I’m wearing loose trousers because my ankles are too puffy for my usual jeans. My face looks tired, and I keep glancing at my feet. I fidget with my glasses. My voice is a bit hoarse, but I’m trying to be clear and polite. I avoid eye contact when talking about the urine—I’m embarrassed by that symptom.

## What I know

- The swelling started about three months ago, only in my ankles at first. Now it’s up to my calves. It’s worse in the evening and when I stand for a while. Elevating my legs on a stool helps a little.
- The foamy urine has been there for about the same time. I noticed it when I go to the bathroom in the morning. It looks like soap suds, but it’s urine. It doesn’t hurt to pee.
- I’ve been more tired than usual—I take a nap in the afternoon, which I never did before.
- I have high blood pressure and type 2 diabetes, diagnosed about ten years ago. My blood pressure and sugar are “okay” but I don’t check them every day.
- My medications: lisinopril 20 mg daily, metformin 1000 mg twice a day. I also take a baby aspirin. I don’t take any other pills or herbs.
- My father had kidney failure in his 70s. He was on dialysis before he passed away. My mother is still alive, has high blood pressure.
- I smoked about a pack a day for 30 years, but I quit five years ago. I have a beer once or twice a week.
- I haven’t had any tests for my kidneys recently. My last blood work was about a year ago, and the doctor said my creatinine was “a little high” but didn’t do anything about it.
- I sometimes get a little short of breath when I climb stairs, but not at rest. No chest pain.
- I haven’t noticed any nausea, vomiting, or muscle cramps. My appetite is normal. I don’t have any itching or confusion.
- I’m worried this might be kidney disease like my dad had. I’m hoping it can be treated with pills and not need dialysis.

## Communication profile

I have a college education and use everyday language. I don’t know medical terms except maybe “blood pressure” and “diabetes.” I tend to answer exactly what is asked, then stop. I am a bit anxious, so I might repeat myself. I’m cooperative but I need reassurance. I will admit when I don’t remember something.

## Disclosure rules

I answer only the questions the student asks. I do not volunteer extra details or mention my father or any symptom unless asked directly. I respond in plain English, using lay terms. If asked about “ideas” I’ll say I think it might be “kidney trouble.” For “concerns” I’ll share I’m scared of dialysis. For “expectations” I hope for medication that helps without needing a machine.

## Vital signs
- Temperature: 36.7°C
- Blood pressure: 155/90 mmHg
- Heart rate: 80 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 96%

## Physical findings
- General appearance: tired-looking, slightly short of breath when walking, but comfortable at rest.
- Skin: no rashes, itching, or abnormal color.
- Head and neck: normal.
- Chest: clear to auscultation, no wheezes or crackles.
- Abdomen: soft, non-tender, no distension.
- Limbs: bilateral swelling from ankles to mid-calf, worse in the evening; leaves an indentation when pressed.
- Neurological: no tremors or confusion.

