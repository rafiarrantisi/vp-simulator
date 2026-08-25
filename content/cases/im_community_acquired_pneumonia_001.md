---
id: im_community_acquired_pneumonia_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: respiratory
presentation: Cough and breathlessness
presentation_id: Batuk dan sesak napas selama beberapa hari
first_impression: Patient appears uncomfortable.
first_impression_id: Pasien tampak tidak nyaman.
target_condition: Community-acquired pneumonia
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages:
- en
source_refs:
- British Thoracic Society guidelines for community-acquired pneumonia
- ATS/IDSA community-acquired pneumonia guideline (2019)
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: Kurasi pilot candidate (plan §6.2). Belum ada clinical sign-off —
    WAJIB direview dokter/pendidik sebelum pilot_verified/published (§11).
chief_complaint: I've had a bad cough and feel short of breath for the past few days.
anamnesis_checklist:
  hpi_socrates:
  - item: Site - where is the discomfort
    critical: false
  - item: Onset - when did it start
    critical: false
  - item: Character - what does the cough feel like
    critical: false
  - item: Radiation - does pain spread
    critical: false
  - item: Associated symptoms - fever, chills, sputum
    critical: true
  - item: Time course - has it gotten worse
    critical: false
  - item: Exacerbating/relieving factors - what makes it better or worse
    critical: false
  - item: Severity - how bad is the breathlessness
    critical: true
  associated_symptoms:
  - item: Fever or chills
    critical: true
  - item: Cough with phlegm
    critical: true
  - item: Chest pain when breathing
    critical: false
  - item: Fatigue or weakness
    critical: false
  pmh:
  - item: Any chronic lung conditions like asthma or COPD
    critical: false
  - item: Diabetes
    critical: false
  - item: Recent hospitalisation or surgery
    critical: false
  medications:
  - item: Current medications
    critical: false
  - item: Any antibiotics recently
    critical: false
  family_social:
  - item: Smoking history
    critical: true
  - item: Alcohol use
    critical: false
  - item: Recent travel or sick contacts
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Chest pain or difficulty breathing at rest
  critical: true
- item: Confusion or drowsiness
  critical: true
- item: Coughing up blood
  critical: true
expected_ddx:
  working_diagnosis: Community-acquired pneumonia
  differentials:
  - Acute bronchitis
  - Influenza
investigations:
  appropriate:
  - name: Chest X-ray
    expected: Consolidation in the right lower lobe
  - name: Full blood count
    expected: Elevated white cell count with neutrophilia
  - name: C-reactive protein
    expected: Elevated
  - name: Sputum culture
    expected: Streptococcus pneumoniae
  inappropriate:
  - CT chest without contrast
physical_exam_findings:
  general: Patient appears unwell, flushed, and slightly tachypnoeic.
  vitals:
    temperature: 38.5
    heart_rate: 100
    respiratory_rate: 22
    blood_pressure: 120/80
    oxygen_saturation: 94
management:
  pharmacological:
  - Amoxicillin 500 mg three times daily for 7 days
  - Paracetamol 1 g four times daily as needed for fever
  non_pharmacological:
  - Rest and increase fluid intake
  - Monitor temperature and breathing
  education_safety_netting:
  - Return if breathlessness worsens or fever persists after 48 hours
  - Avoid smoking and second-hand smoke
scoring_weights_override: null
pilot_candidate: true
competency:
  standard: SKDI
  authority: Konsil Kesehatan Indonesia (KKI)
  version: '2012'
  level: null
  status: pending_review
---

## Identity

My name is Yanti. I'm 58 years old, and I work as a receptionist at a busy dental practice. I live with my husband, Sutrisno, in a small house with a garden. I have two grown children who live nearby. I'm usually a cheerful, chatty person, but I've been feeling really rough lately. I'm a bit of a worrier, especially about my health, and I tend to get anxious when I feel unwell. I like to keep busy, so being stuck at home is frustrating. I don't like taking medicine unless I really have to.

## Opening line

"Doctor, I've had this terrible cough for about four days now, and I can't seem to catch my breath properly."

## How I present

I'm sitting forward on the edge of the chair, looking a bit pale and flushed in the cheeks. I'm breathing a little fast and I cough a few times during the conversation. My voice sounds a bit hoarse and strained. I'm making good eye contact but I look tired and worried. I'm holding a tissue and I have a small bottle of water with me.

## What I know

- The cough started about four days ago. It began as a dry tickle, but now it's a deep, hacking cough.
- For the past two days, I've been bringing up thick, yellowish-green phlegm when I cough.
- I feel short of breath just walking from the living room to the kitchen. Climbing stairs is out of the question.
- I've had a high fever on and off, with chills and sweating at night. My temperature was 38.5°C last night.
- I have a sharp pain in my right side when I take a deep breath or cough. It feels like a stitch.
- I feel very tired and achy all over, like I have the flu.
- I don't have any long-term lung problems like asthma or COPD. I've never been told I have diabetes.
- I haven't been in hospital recently or had any surgery.
- I take a small blood pressure pill every morning—I think it's called lisinopril. I don't take any other regular medicines.
- I haven't taken any antibiotics in the last few months. I tried some over-the-counter cough syrup but it didn't help.
- I used to smoke about 10 cigarettes a day, but I quit 5 years ago. My husband still smokes in the house sometimes.
- I have a glass of wine with dinner maybe twice a week, no more.
- I haven't travelled anywhere recently. My daughter had a cold last week, but she's fine now.
- I think I might have a bad chest infection or maybe the flu. I'm worried it could turn into something more serious like pneumonia, because my father had that when he was older and he ended up in hospital.
- I hope you can give me something to help me breathe easier and get rid of this cough. I don't want to end up in hospital if I can avoid it.

## Communication profile

I have a high school education and I work in a front-desk job, so I'm comfortable talking to people. I use everyday language, not medical terms. I tend to give a bit more detail than asked, but I'll stop if you cut me off. I'm polite but I can get a bit emotional when I talk about how scared I am. I'll answer questions directly, but I might add a little extra story if I'm nervous.

## Disclosure rules

I will only answer the specific question you ask me. If you ask about my cough, I'll describe it, but I won't volunteer about the phlegm or the pain unless you ask. If you ask about my temperature, I'll tell you, but I won't mention the chills unless you ask about fever symptoms. I will not offer any information about my smoking history or family unless you ask directly. I will not tell you what I think is wrong unless you ask me my ideas. I will not mention my father's pneumonia unless you ask about concerns. I will only give the facts that are in my "What I know" section.

## Vital signs
- Temperature: 38.3°C
- Blood pressure: 130/80 mmHg
- Heart rate: 98 bpm
- Respiratory rate: 22/min
- Oxygen saturation: 94% on room air

## Physical findings
- General appearance: Looks unwell, sitting forward, breathing fast. Face is pale with flushed cheeks.
- Skin: Warm and moist.
- Head and neck: No swollen glands.
- Chest: Breathing sounds are louder and harsher on the right side. Crackling sounds heard on the right when listening. The right side of the chest moves less than the left with breathing.
- Abdomen: Soft, no tenderness.
- Limbs: No swelling or bluish discoloration.
- Neurological: Alert and oriented.

