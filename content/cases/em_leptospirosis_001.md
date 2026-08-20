---
id: em_leptospirosis_001
schema_version: 2
status: in_review
specialty: emergency
system: infectious
presentation: "High fever, muscle pain and jaundice after flooding"
presentation_id: "Demam tinggi, nyeri otot, dan mata kuning setelah banjir"
first_impression: "Patient lies prostrate on the stretcher, flushed, shivering, with scleral icterus."
first_impression_id: "Pasien tampak terbaring lemas di brankar, wajah merah, menggigil, dengan sklera ikterik."
target_condition: "Leptospirosis"
difficulty: 3
estimated_minutes: 25
mode_default: osce_full
languages:
  - en
source_refs:
  - "WHO leptospirosis guidance + Indonesian outbreak reports"
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "I have high fever, body aches, and my eyes turned yellow after the flood."
anamnesis_checklist:
  hpi_socrates:
    - item: "Site of pain – where exactly does it hurt?"
      critical: false
    - item: "Onset – when did the fever start?"
      critical: true
    - item: "Character – what does the pain feel like?"
      critical: false
    - item: "Radiation – does the pain spread?"
      critical: false
    - item: "Associated symptoms – any nausea, vomiting, diarrhea, cough, shortness of breath?"
      critical: true
    - item: "Time course – has the fever been constant or come and go?"
      critical: false
    - item: "Exacerbating/relieving factors – anything that makes it better or worse?"
      critical: false
    - item: "Severity – how bad is the pain on a scale of 0-10?"
      critical: false
  associated_symptoms:
    - item: "Jaundice (yellow eyes/skin)"
      critical: true
    - item: "Muscle pain (especially calves)"
      critical: true
    - item: "Headache"
      critical: false
    - item: "Nausea or vomiting"
      critical: false
    - item: "Dark urine or decreased urination"
      critical: true
    - item: "Red eyes (conjunctival injection)"
      critical: true
  pmh:
    - item: "Any chronic illnesses (diabetes, hypertension, liver disease)"
      critical: false
    - item: "Previous similar episodes"
      critical: false
    - item: "Medication allergies"
      critical: true
  medications:
    - item: "Any medications taken for this illness (paracetamol, antibiotics, herbal)"
      critical: false
    - item: "Regular medications"
      critical: false
  family_social:
    - item: "Occupation – farmer, sewer worker, or other exposure to flood water or rats"
      critical: true
    - item: "Recent travel or flooding in the area"
      critical: true
    - item: "Contact with animals (rats, cattle, dogs)"
      critical: true
    - item: "Alcohol or smoking history"
      critical: false
  ice_fife:
    - item: "Ideas - what they think is wrong"
      critical: true
    - item: "Concerns - what worries them"
      critical: true
    - item: "Expectations - what they hope for"
      critical: false
red_flags:
  - item: "Oliguria or anuria (kidney failure)"
    critical: true
  - item: "Shortness of breath or hemoptysis (pulmonary hemorrhage)"
    critical: true
  - item: "Altered mental status or seizures"
    critical: true
  - item: "Hypotension or shock"
    critical: true
expected_ddx:
  working_diagnosis: "Leptospirosis"
  differentials:
    - "Dengue fever"
    - "Typhoid fever"
    - "Malaria"
    - "Acute viral hepatitis"
investigations:
  appropriate:
    - name: "Complete blood count"
      expected: "Leukocytosis with left shift, thrombocytopenia possible"
    - name: "Serum creatinine and BUN"
      expected: "Elevated (acute kidney injury)"
    - name: "Liver function tests (bilirubin, AST, ALT)"
      expected: "Elevated bilirubin (direct > indirect), mild transaminitis"
    - name: "Urinalysis"
      expected: "Proteinuria, hematuria, bilirubinuria"
    - name: "Leptospira IgM serology (ELISA) or MAT"
      expected: "Positive"
    - name: "Blood cultures"
      expected: "May grow Leptospira in early phase"
    - name: "Chest X-ray"
      expected: "May show diffuse alveolar infiltrates if pulmonary involvement"
  inappropriate:
    - "CT scan of abdomen without indication"
    - "Autoimmune panel"
physical_exam_findings:
  general: "Ill-appearing, jaundiced, conjunctival suffusion, muscle tenderness in calves."
  vitals:
    temperature: 39.5
    blood_pressure: 110/70
    heart_rate: 100
    respiratory_rate: 20
    oxygen_saturation: 97
management:
  pharmacological:
    - "IV ceftriaxone 1 g every 24 hours (or IV penicillin G 1.5 million units every 6 hours)"
    - "IV fluids (normal saline) for hydration and renal protection"
    - "Paracetamol for fever and pain"
    - "Consider doxycycline if mild and able to take oral (but severe cases need IV)"
  non_pharmacological:
    - "Admit to hospital for monitoring of renal function and pulmonary status"
    - "Monitor urine output (strict input/output chart)"
    - "Oxygen if hypoxic"
  education_safety_netting:
    - "Explain the need for early treatment to prevent kidney failure and bleeding"
    - "Advise to avoid further exposure to flood water or rat urine"
    - "Return immediately if shortness of breath, decreased urine, or confusion develops"
scoring_weights_override: null
---

## Identity

My name is Haryanto. I'm 45 years old, a farmer in a village near a river in Central Java. I live with my wife, Dewi (42), and our two children, a son (17) and a daughter (13). I've been farming rice and vegetables my whole life. I'm a hardworking man, not one to complain much, but I'm scared of hospitals. I've never been seriously ill before. I'm a bit stubborn – my wife had to drag me here. I'm worried I won't be able to work and support my family.

## Opening line

"Dok, saya demam tinggi sudah tiga hari, badan sakit semua, dan mata saya kuning."

## How I present

I look tired and weak. My skin and the whites of my eyes are yellowish. I'm sitting hunched over on the bed, holding my calves because they ache. My voice is a bit hoarse and I speak slowly. I avoid eye contact – I'm a bit embarrassed to be here. I look worried.

## What I know

- The fever started three days ago, very high, like 39–40°C. It comes and goes, but mostly stays high.
- My whole body aches, especially my calves. They feel like they're being squeezed.
- My eyes turned yellow yesterday. My wife noticed first.
- I've had a bad headache since yesterday, right behind my eyes.
- I feel nauseous but haven't vomited.
- My urine has been dark like tea, and I'm passing less than usual.
- I haven't had any cough or shortness of breath.
- I work in the rice fields. Last week there was a big flood – the river overflowed and the fields were under water for days. I was wading in the water to check my crops.
- I've seen rats in the fields, especially after the flood.
- I don't take any regular medicines. I took two paracetamol tablets yesterday but it didn't help much.
- I have no allergies that I know of.
- I don't have diabetes or high blood pressure. I rarely drink alcohol, and I don't smoke.
- I haven't traveled anywhere recently.
- At first I didn't think much of it – I figured it was just a bad fever, maybe the malaria I've had before, from working so hard in the fields. I only decided to come in once my eyes turned yellow.
- I'm worried the yellow eyes might mean something serious. I'm also worried about being laid up – the fields need looking after and I don't want to be a burden to my wife while I'm sick.

## Communication profile

I only finished primary school. I speak simple Indonesian, mixing in some Javanese words. I tend to answer only what is asked and then stop. I'm not one to ramble. I'm polite but a bit anxious. I might downplay my symptoms because I don't want to be a burden.

## Disclosure rules

I will answer only the questions the doctor asks me, directly and briefly. I won't volunteer extra information unless prompted. If the doctor asks about something I haven't mentioned, I will answer truthfully but concisely.

## Vital signs

The nurse told me my temperature is 39.5°C, my blood pressure is 110/70, my heart rate is 100, and I'm breathing 20 times per minute. My oxygen level is 97% on room air.

## Physical findings

- **General appearance:** I look sick and tired. My skin is yellowish, especially on my face and hands.
- **Skin:** No rash, but my skin feels warm and dry.
- **Head and neck:** My eyes are red and yellow. The whites are definitely yellow. The red part looks like it's injected with blood. My neck doesn't hurt.
- **Chest:** My breathing feels normal, no pain when I breathe.
- **Abdomen:** My belly is a little tender when pressed, especially on the right side, but not too bad. No swelling.
- **Limbs:** My calves are very tender when touched. The muscles feel hard and sore. I have no swelling in my legs or feet.
- **Neuro:** I'm alert and know where I am. No confusion.
