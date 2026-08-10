---
id: ent_sinusitis_001
schema_version: 2
status: in_review
specialty: ent
system: ent
presentation: "Facial pain and nasal congestion"
presentation_id: "Tekanan di wajah dan hidung tersumbat"
first_impression: "Patient appears to have ear, nose, or throat discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan telinga, hidung, atau tenggorokan."
target_condition: "Acute sinusitis"
difficulty: 1
estimated_minutes: 12
mode_default: anamnesis
languages: [en]
source_refs:
  - "IDSA guidelines for acute sinusitis 2023"
  - "AAO-HNS clinical practice guideline — acute rhinosinusitis (2015)"

authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "I have a bad pressure in my face and my nose is all stuffed up."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain - cheeks and around eyes", critical: false }
    - { item: "Onset - started 5 days ago after a cold", critical: false }
    - { item: "Character - dull, pressure-like pain", critical: true }
    - { item: "Radiation - to forehead sometimes", critical: false }
    - { item: "Associations - nasal congestion, thick yellow discharge", critical: false }
    - { item: "Timing - constant, worse when bending down", critical: false }
    - { item: "Exacerbating factors - bending down, coughing", critical: false }
    - { item: "Relieving factors - steam, over-the-counter nasal spray", critical: false }
    - { item: "Severity - 5 out of 10", critical: false }
  associated_symptoms:
    - { item: "Fever and chills", critical: false }
    - { item: "Headache", critical: false }
    - { item: "Cough, especially at night", critical: false }
    - { item: "Ear fullness or pressure", critical: false }
    - { item: "Reduced sense of smell", critical: false }
  pmh:
    - { item: "Allergic rhinitis (seasonal)", critical: false }
    - { item: "Previous sinusitis episodes (2-3 times before)", critical: false }
    - { item: "Asthma (mild, controlled)", critical: false }
  medications:
    - { item: "Over-the-counter oxymetazoline nasal spray (used for 2 days)", critical: false }
    - { item: "Acetaminophen as needed for pain", critical: false }
    - { item: "None prescribed", critical: false }
  family_social:
    - { item: "Husband is a smoker (smokes in the house)", critical: false }
    - { item: "No family history of sinusitis or chronic lung disease", critical: false }
    - { item: "Works as an office manager; no recent travel", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Vision changes or double vision", critical: true }
  - { item: "Severe headache with stiff neck", critical: true }
  - { item: "Swelling around the eye or forehead", critical: true }
expected_ddx:
  working_diagnosis: "Acute sinusitis"
  differentials: [ "Allergic rhinitis with secondary infection", "Migraine variant", "Dental abscess" ]
investigations:
  appropriate:
    - { name: "Anterior rhinoscopy", expected: "Mucosal oedema, purulent discharge in middle meatus" }
  inappropriate:
    - "CT sinus without clear indication"
    - "Nasal swab for culture in first 7 days"
physical_exam_findings:
  general: "Patient appears uncomfortable, mild fever present."
  vitals: { temp: 37.8, hr: 80, bp: "120/80", rr: 16, o2: 98 }
management:
  pharmacological:
    - "Nasal saline spray"
    - "Oral decongestant (pseudoephedrine) if no contraindications"
    - "Analgesics (acetaminophen or ibuprofen)"
    - "Consider antibiotics (amoxicillin) if symptoms >10 days or worsening after 7 days"
  non_pharmacological:
    - "Steam inhalation 2-3 times daily"
    - "Hydration and rest"
    - "Elevate head while sleeping"
  education_safety_netting:
    - "Return if vision changes, severe headache, periorbital swelling, or high fever"
    - "Return if no improvement after 7 days or symptoms worsen"
scoring_weights_override: null
---
## Identity

My name is Sri Santoso. I’m 35 years old and work as an office manager in a busy real estate agency. I live with my husband, Budi, and our two cats. I’m usually pretty healthy, but I have seasonal allergies and mild asthma. My friends would say I’m cheerful but a bit of a worrier – I like to get things sorted quickly. When I’m sick, I tend to push through because I hate missing work, but this time the pain is really getting to me. I’m a little nervous about doctors because I don’t want to be told I need something serious.

## Opening line

I’ve had this terrible pressure in my face for days, and my nose is just so stuffed up – I can’t breathe properly.

## How I present

I come in looking tired and a bit flushed. I’m sitting upright, leaning forward slightly, and I keep touching my cheeks and forehead. My voice sounds nasal and congested. I make eye contact but I’m clearly uncomfortable, and I occasionally wince when I move my head. I’m wearing a scarf and seem a bit chilly despite the room temperature.

## What I know

- The pain started about five days ago, right after I got over a cold. It feels like a dull, heavy pressure on both sides of my face, especially under my eyes and in my cheeks. Sometimes it spreads to my forehead.
- Bending down, coughing, or even looking down makes the pain worse. It’s constant – doesn’t go away completely, but it’s worse in the morning.
- I have a lot of thick, yellow-greenish mucus coming out of my nose. My nose is so blocked that I can’t smell anything.
- I’ve had a mild fever (around 100°F) and chills on and off. I also have a headache that feels like a band around my head, and a bit of a cough, especially at night.
- I’ve been taking over-the-counter nasal spray (the kind you use for a few days) and acetaminophen for the pain. The spray helps a little, but only for a short time. The steam from a hot shower also helps for a while.
- I’ve had sinus infections before – maybe two or three times in the past few years. They usually start the same way, after a cold.
- I have seasonal allergies in the spring, and I take an antihistamine sometimes. My asthma is mild and I use an inhaler maybe once a week.
- My husband smokes, but only in the living room. I’ve asked him to stop, but he hasn’t yet.
- I’m worried that this might be something serious, like an infection spreading to my brain. I read about that online. I hope I just need some antibiotics to clear it up.

## Communication profile

I speak in plain English – I’m educated, but I don’t use medical terms. I answer questions directly, but I do tend to add a little extra detail, especially if I’m worried. My tone is polite but a bit anxious. I might ramble a bit if I’m not asked a specific question, so I need clear, focused questions.

## Disclosure rules

I will only answer what I am asked. I won’t offer information that the student doesn’t specifically ask about. If the student asks a question, I’ll give the relevant facts and then stop. I won’t volunteer extra details unless prompted. I’ll never use medical jargon.

## Vital signs
- Temperature: 37.8°C
- Blood pressure: 120/80 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: tired, flushed, sitting upright and leaning forward, occasionally wincing when moving head.
- Skin: warm to touch.
- Head and neck: tenderness over cheeks and forehead when pressed; nasal mucosa swollen and red; thick yellow-green discharge from both nostrils; postnasal drip visible at back of throat; throat slightly red.
- Chest: clear to auscultation, no wheezes or crackles.
- Abdomen: soft, non-tender.
- Limbs: no cyanosis or clubbing.
- Neurological: alert and oriented, no focal deficits.

