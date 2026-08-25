---
id: ent_tonsillitis_001
schema_version: 2
status: ai_generated
specialty: ent
system: ent
presentation: Sore throat and difficulty swallowing
presentation_id: Nyeri tenggorokan parah dan sulit menelan
first_impression: Patient appears to have ear, nose, or throat discomfort.
first_impression_id: Pasien tampak mengalami ketidaknyamanan telinga, hidung, atau
  tenggorokan.
target_condition: Acute tonsillitis
difficulty: 1
estimated_minutes: 15
mode_default: osce_full
languages:
- en
source_refs:
- 'AAO-HNSF Clinical Practice Guideline: Tonsillitis (2019)'
- NICE NG84 — Sore throat (acute)
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: My throat is really sore and it hurts to swallow.
anamnesis_checklist:
  hpi_socrates:
  - item: Site of pain
    critical: true
  - item: Onset of symptoms
    critical: false
  - item: Character of pain
    critical: false
  - item: Radiation of pain
    critical: false
  - item: Associated symptoms (fever, chills, malaise)
    critical: false
  - item: Time course / progression
    critical: false
  - item: Exacerbating factors (swallowing, talking)
    critical: false
  - item: Relieving factors (painkillers, cold drinks)
    critical: false
  - item: Severity (0-10 scale)
    critical: false
  associated_symptoms:
  - item: Fever
    critical: true
  - item: Chills
    critical: false
  - item: Ear pain
    critical: false
  - item: Voice changes
    critical: false
  - item: Cough or runny nose
    critical: false
  - item: Difficulty breathing or drooling
    critical: false
  pmh:
  - item: History of recurrent tonsillitis
    critical: true
  - item: Recent exposure to strep throat
    critical: false
  - item: Smoking history
    critical: false
  medications:
  - item: Current medications (none)
    critical: false
  - item: Allergies (especially penicillin)
    critical: true
  family_social:
  - item: Family history of tonsillitis or strep
    critical: false
  - item: Occupation (teacher)
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Difficulty breathing or stridor
  critical: true
- item: Muffled voice (hot potato voice)
  critical: false
- item: Drooling
  critical: false
- item: Trismus (difficulty opening mouth)
  critical: false
- item: Unilateral severe pain with peritonsillar swelling
  critical: false
expected_ddx:
  working_diagnosis: Acute tonsillitis
  differentials:
  - Infectious mononucleosis
  - Peritonsillar abscess
  - Viral pharyngitis
investigations:
  appropriate:
  - name: Rapid strep test
    expected: Positive
  - name: Throat culture
    expected: Growth of Group A Streptococcus
  - name: Complete blood count (CBC)
    expected: Elevated white blood count with left shift
  inappropriate:
  - CT scan of neck
  - X-ray of neck
physical_exam_findings:
  general: Acutely ill, febrile, appears uncomfortable. Enlarged, erythematous tonsils
    with exudates. Bilateral tender cervical lymphadenopathy.
  vitals:
    temperature: 38.8°C
    heart_rate: 98
    blood_pressure: 118/76
    respiratory_rate: 16
    oxygen_saturation: 98
management:
  pharmacological:
  - Penicillin VK 500 mg PO TID × 10 days (or amoxicillin if no allergy)
  - Acetaminophen or ibuprofen for pain and fever
  - Antibiotic course adjustment if penicillin allergy (e.g., clindamycin)
  non_pharmacological:
  - Warm salt water gargles
  - Adequate hydration, rest
  - Soft diet, avoid irritants
  education_safety_netting:
  - Complete full course of antibiotics even if feeling better
  - Seek urgent care if worsening throat pain, difficulty breathing, drooling, or
    inability to swallow
  - Return if no improvement after 48 hours of antibiotics
scoring_weights_override: null
---

## Identity

Hi, I'm Vina Wibowo. I'm 28 years old, I work as a second-grade teacher, and I'm married with two kids — a 5-year-old and a 2-year-old. I live in a quiet suburb, and I'm usually pretty healthy, but I get a sore throat every now and then because I'm around kids all day. I'm a bit of a worrier when it comes to my health, especially if something feels really off. I hate needles, and I'm scared of surgery. I always carry a water bottle and throat lozenges in my bag, just in case. I'm usually cheerful, but right now I feel miserable.

## Opening line

"Hi, doctor. My throat is killing me and I can barely swallow my own spit."

## How I present

I'm sitting hunched over in the chair, holding my neck with one hand. I grimace every time I swallow, and my voice sounds strained and quiet. I avoid talking too much because it hurts. My face looks a bit flushed, like I have a fever, and I seem tired and uncomfortable. I make eye contact but I'm clearly in pain.

## What I know

- My throat started hurting about two days ago.
- The pain is sharp and burning, especially when I swallow.
- I have a fever — I measured 38.5°C at home.
- I've had chills and feel really tired.
- My left ear aches a little when I swallow.
- I haven't had a cough or runny nose.
- No voice changes — I sound normal, just a bit weak.
- I haven't had any trouble breathing or drooling.
- I've had tonsillitis twice in the past year, and it felt similar.
- I smoke a few cigarettes when I go out with friends, but not every day.
- I drink alcohol rarely, maybe a glass of wine once a week.
- I'm not taking any medications right now.
- I'm not allergic to any medicines as far as I know.
- My sister had strep throat last month.
- I think it's a bad infection, maybe strep again.
- I'm worried it might be something serious, like cancer, or that I'll need surgery to remove my tonsils.
- I hope you can give me antibiotics to make it go away fast.

## Communication profile

I have a high school education and use simple, everyday language. I'm usually pretty talkative, but right now I'm anxious and in pain, so I tend to ramble a bit if I'm nervous. I answer questions directly, but I don't offer extra information unless you ask. I'm cooperative and want to get better quickly.

## Disclosure rules

I only answer what you ask me directly. I don't bring up anything you haven't asked about. I'll stop talking as soon as I've answered your question.

## Vital signs
- Temperature: 38.5°C
- Blood pressure: 120/80 mmHg
- Heart rate: 102 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: appears unwell, flushed face, sitting hunched over.
- Skin: warm and dry.
- Head and neck: tonsils are red and swollen with white patches; lymph nodes under the jaw are tender.
- Chest: clear to auscultation.
- Abdomen: soft, non-tender.
- Limbs: no rash or swelling.
- Neurological: alert and oriented.

