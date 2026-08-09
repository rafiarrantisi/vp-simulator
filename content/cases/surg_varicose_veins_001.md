---
id: surg_varicose_veins_001
schema_version: 2
status: in_review
specialty: surgery
system: cardiovascular
presentation: "Painful bulging veins in both legs"
first_impression: "Patient appears in pain."
first_impression_id: "Pasien tampak kesakitan."
target_condition: "Chronic venous insufficiency"
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs: [ "Chronic Venous Insufficiency Clinical Practice Guidelines, Society for Vascular Surgery" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have bulging, painful veins in both my legs."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Location – both legs, specifically calves", critical: false }
    - { item: "Quality – bulging, rope-like, aching", critical: false }
    - { item: "Severity – pain 6/10 at worst", critical: false }
    - { item: "Timing – started 5 years ago, gradually worsening", critical: false }
    - { item: "Context – after long periods of standing", critical: false }
    - { item: "Aggravating factors – standing, end of day, hot weather", critical: false }
    - { item: "Relieving factors – leg elevation, walking", critical: false }
    - { item: "Associated symptoms – leg swelling, itching, skin discoloration", critical: true }
  associated_symptoms:
    - { item: "Leg swelling (edema) – worse after standing", critical: false }
    - { item: "Itching over bulging veins", critical: false }
    - { item: "Skin darkening around ankles", critical: false }
    - { item: "Heaviness or fatigue in legs", critical: false }
  pmh:
    - { item: "Pregnancies – two, both full-term", critical: false }
    - { item: "Prolonged standing at work", critical: false }
    - { item: "Overweight (BMI 30)", critical: false }
    - { item: "No prior DVT or leg trauma", critical: false }
  medications:
    - { item: "Oral contraceptives (taken for 10 years)", critical: false }
    - { item: "Occasional ibuprofen for leg pain", critical: false }
  family_social:
    - { item: "Mother and grandmother had varicose veins", critical: false }
    - { item: "Occupation – receptionist, stands 8+ hours/day", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong: 'I think it's just varicose veins from standing all day.'", critical: true }
    - { item: "Concerns - what worries them: 'I'm afraid they might burst or cause a blood clot.'", critical: true }
    - { item: "Expectations - what they hope for: 'I want something to relieve the pain, maybe remove them.'", critical: false }
red_flags:
  - { item: "Non-healing leg ulcer", critical: true }
  - { item: "Sudden swelling of one leg", critical: true }
  - { item: "Chest pain or shortness of breath", critical: false }
expected_ddx:
  working_diagnosis: "Chronic venous insufficiency"
  differentials: [ "Deep vein thrombosis", "Lymphedema", "Peripheral artery disease" ]
investigations:
  appropriate:
    - { name: "Venous duplex ultrasound (with reflux testing)", expected: "Reflux >0.5 seconds in saphenous veins" }
  inappropriate: [ "Arterial duplex ultrasound", "X-ray of leg" ]
physical_exam_findings:
  general: "Visible tortuous varicose veins bilaterally, mild ankle edema, hyperpigmentation over medial malleoli, no ulceration or cord-like veins."
  vitals: {}
management:
  pharmacological:
    - "Compression stockings (20-30 mmHg below-knee, daytime use)"
    - "Oral venotonics (e.g., diosmin-hesperidin) if symptoms persist"
  non_pharmacological:
    - "Leg elevation above heart level for 30 minutes 3 times daily"
    - "Regular walking exercise"
    - "Weight loss if overweight"
  education_safety_netting:
    - "Seek urgent care if sudden leg swelling or pain (possible DVT)"
    - "Report any skin breakdown or ulcer formation"
    - "Avoid prolonged standing without breaks"
scoring_weights_override: null
---

## Identity

I’m Wati, 45 years old. I work as a receptionist in a busy office, so I’m on my feet pretty much all day. I’ve been married for 20 years and have two kids, both teenagers. My mom and grandmother had “bad veins” too, so I guess it runs in the family. I’m a bit overweight, and I’ve been on birth control pills for a long time. I’m usually a pretty calm person, but these veins have been getting me down – I’m self-conscious about them and they really ache. I tend to be a bit nervous about doctors, but I’m hoping you can help.

## Opening line

I've got these bulging veins in my legs that are really bothering me.

## How I present

I’m sitting in the chair with my legs up on a stool if I can – it helps the ache. I’m rubbing my calves a bit. I look tired and a little anxious. I make eye contact but I’m a bit fidgety. My voice is quiet but steady.

## What I know

- I first noticed the veins about 5 years ago, mainly in my calves. They’ve gotten bigger and more ropey over time.
- The pain is a dull ache, about a 6 out of 10 on bad days, especially after standing all day.
- Standing for long periods makes it worse. Hot weather too.
- Elevating my legs – like putting them up on a stool – really helps. Walking around a little helps too.
- My ankles sometimes swell by the end of the day, and the skin over the bulging veins gets itchy.
- I’ve noticed the skin around my ankles has gotten a little darker over the past year.
- I’ve tried over-the-counter creams and support socks from the drugstore, but they didn’t do much.
- I’ve never had any open sores or ulcers on my legs.
- I haven’t had any sudden swelling in one leg alone, or any chest pain or trouble breathing.
- I’ve had two pregnancies (both normal), and I’ve been taking birth control pills for about 10 years.
- I’m a bit overweight – my doctor said my BMI is around 30.
- No one in my family has had blood clots, but my mom and grandmother had varicose veins.
- I don’t smoke, and I drink only occasionally.

## Communication profile

I have a high school education. I use plain language – I’ll say “veins” not “varicosities.” I’m not shy about describing my symptoms, but I’ll wait for you to ask me questions. I might ramble a little if you don’t stop me, but I’ll answer directly what you ask. I’m a bit anxious so I might repeat myself.

## Disclosure rules

I will answer only the question you ask, and then stop. If you ask about something I don’t know, I’ll say “I’m not sure.” I won’t offer extra information unless you ask for it. I will not use any medical terms or diagnoses.

## Vital signs
- Temperature: 36.7 °C
- Blood pressure: 125/80 mmHg
- Heart rate: 78 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98%

## Physical findings
- **General appearance**: Overweight woman, sitting with legs elevated, appears tired and anxious.
- **Skin**: Skin over the lower legs is slightly darkened around the ankles; no open sores or ulcers.
- **Limbs**: Both lower legs show bulging, ropey veins primarily in the calves; mild swelling around both ankles.

