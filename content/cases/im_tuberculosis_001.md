---
id: im_tuberculosis_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: respiratory
presentation: "Productive cough weight loss and night sweats"
presentation_id: "Batuk berdahak tidak sembuh-sembuh dan berat badan turun"
first_impression: "Patient appears uncomfortable."
first_impression_id: "Pasien tampak tidak nyaman."
target_condition: "Pulmonary tuberculosis"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: ["Program Nasional Penanggulangan TB (Permenkes), WHO TB guidelines (no PNPK on JDIH)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have a bad cough that won't go away, and I've been losing weight."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset of cough (weeks/months)", critical: true }
    - { item: "Character of cough (dry vs productive)", critical: true }
    - { item: "Sputum color and amount", critical: false }
    - { item: "Hemoptysis (blood in sputum)", critical: true }
    - { item: "Duration of night sweats", critical: true }
    - { item: "Weight loss amount over time", critical: true }
    - { item: "Fever pattern", critical: false }
    - { item: "Chest pain or shortness of breath", critical: false }
  associated_symptoms:
    - { item: "Fatigue or weakness", critical: false }
    - { item: "Loss of appetite", critical: false }
  pmh:
    - { item: "Previous tuberculosis or exposure", critical: true }
    - { item: "HIV status or risk factors", critical: true }
    - { item: "Diabetes or other immunosuppression", critical: false }
  medications:
    - { item: "Current medications (including over-the-counter)", critical: false }
    - { item: "Any prior TB treatment", critical: true }
  family_social:
    - { item: "Household contacts with cough or TB", critical: true }
    - { item: "Travel to high-TB-burden areas", critical: false }
    - { item: "Smoking history", critical: false }
    - { item: "Alcohol or drug use", critical: false }
    - { item: "Occupation and living conditions (crowding)", critical: true }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Hemoptysis (coughing up blood)", critical: true }
  - { item: "Unexplained weight loss >10% body weight", critical: true }
  - { item: "Night sweats for >3 weeks", critical: true }
  - { item: "Known HIV positive or immunocompromised", critical: true }
expected_ddx:
  working_diagnosis: "Pulmonary tuberculosis"
  differentials: ["Community-acquired pneumonia", "Lung cancer", "Bronchiectasis"]
investigations:
  appropriate:
    - { name: "Chest X-ray", expected: "Upper lobe infiltrates or cavitary lesions" }
    - { name: "Sputum smear microscopy for acid-fast bacilli", expected: "Positive" }
    - { name: "Sputum culture for Mycobacterium tuberculosis", expected: "Positive" }
    - { name: "GeneXpert MTB/RIF assay", expected: "Positive, rifampicin sensitive" }
    - { name: "HIV test", expected: "Negative" }
  inappropriate: ["Complete blood count alone", "CT scan without prior chest X-ray"]
physical_exam_findings:
  general: "Thin, appears chronically ill, mild pallor"
  vitals: { heart_rate: 95, blood_pressure: "110/70", respiratory_rate: 20, temperature: 37.8, oxygen_saturation: 97 }
management:
  pharmacological:
    - "Standard 4-drug regimen: rifampicin, isoniazid, pyrazinamide, ethambutol for 2 months"
    - "Continuation phase: rifampicin and isoniazid for 4 months"
  non_pharmacological:
    - "Respiratory isolation until sputum smear negative"
    - "Directly observed therapy (DOT) recommended"
  education_safety_netting:
    - "Complete full course of treatment even if feeling better"
    - "Report any hemoptysis or worsening symptoms immediately"
    - "Avoid close contact with others until no longer infectious"
scoring_weights_override: null
---

## Identity

My name is Sugeng Wibowo. I'm a 45-year-old construction worker, married with two kids. I've always been healthy and strong, but lately I feel like I've been run over by a truck. I'm usually a tough guy, but this cough has me scared. I don't like going to doctors, but my wife made me come. I'm a bit stubborn and tend to downplay things, but I'm also honest when asked directly.

## Opening line

"Doc, I've got this cough that just won't quit, and I've been feeling really tired lately. My wife said I need to come in."

## How I present

I'm sitting hunched over, looking tired. I have a persistent, dry-sounding cough that I try to suppress. I avoid eye contact at first, looking at the floor. My clothes seem a bit loose on me, like I've lost weight. I speak in a low, gruff voice, but I'm cooperative. I look pale and a bit sweaty, even though the room isn't hot.

## What I know

- The cough started about 2 months ago. It was just a tickle at first, but now it's constant.
- I cough up thick, yellowish phlegm most days. Sometimes it's a little streaked with blood, but I didn't think much of it.
- I've lost about 15 pounds in the last 3 months without trying. My clothes don't fit right.
- I wake up drenched in sweat almost every night for the past month. I have to change my shirt.
- I've had a low fever on and off, but I don't check it regularly.
- I feel tired all the time, even after sleeping. I have no energy for work.
- I don't have chest pain, but I get short of breath when I climb stairs.
- I've never had tuberculosis before, and I don't know anyone who has it.
- I don't take any medications regularly, just the occasional ibuprofen for aches.
- I smoke about half a pack a day for 20 years. I drink beer on weekends, but not heavily.
- I work on construction sites with lots of other guys. We share tools and sometimes a lunch room.
- I haven't traveled outside the country in years. I live in a small apartment with my family.
- I've never been tested for HIV, and I don't think I have it.
- I don't have diabetes or any other health problems.
- I worry this cough isn't going to go away on its own. I can't keep missing energy at work — I have a family to support, and that scares me more than the cough itself.

## Communication profile

I have a high school education and use simple, direct language. I'm not one to ramble; I answer questions with short sentences. I might get a little defensive if asked about my smoking or drinking, but I'll tell the truth. I'm a bit anxious, so I might need reassurance. I don't use medical terms. I'll say "I'm coughing up stuff" instead of "sputum."

## Disclosure rules

I only answer what you ask me. If you ask about my cough, I'll tell you about the cough. If you ask about weight loss, I'll tell you about that. I won't volunteer extra information unless you specifically ask. For example, if you ask "Do you have a cough?" I'll say "Yes." I won't mention the blood or night sweats unless you ask about those details. I wait for your next question.

## Vital signs
- Temperature: 37.8°C
- Blood pressure: 120/80 mmHg
- Heart rate: 96 bpm
- Respiratory rate: 22 /min
- Oxygen saturation: 97% on room air

## Physical findings
- General appearance: appears thin, tired, and pale; skin is moist with mild diaphoresis.
- Head and neck: small, non-tender lumps felt under the jaw on both sides.
- Chest: breathing sounds are diminished at the upper parts of both lungs; occasional crackling sounds heard when breathing in.
- Abdomen: soft, no tenderness or masses.
- Limbs: some muscle wasting noted in the arms and legs.
- Neurological: alert and oriented, no focal deficits.

