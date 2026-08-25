---
id: em_bacterial_meningitis_001
schema_version: 2
status: ai_generated
specialty: emergency
system: nervous
presentation: High fever, severe headache and neck stiffness
presentation_id: Demam tinggi, sakit kepala hebat, dan kaku leher
first_impression: Patient lies still, grimacing, flushed and photophobic, avoiding
  light.
first_impression_id: Pasien tampak terbaring kaku, meringis, wajah memerah dan menghindari
  cahaya.
target_condition: Bacterial meningitis
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages:
- en
source_refs:
- WHO meningitis guideline (2019)
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: I have a terrible headache, high fever, and my neck feels stiff.
anamnesis_checklist:
  hpi_socrates:
  - item: Site of headache (whole head or specific location)
    critical: false
  - item: Onset of headache and fever (sudden or gradual)
    critical: true
  - item: Character of headache (throbbing, pressing, sharp)
    critical: false
  - item: Radiation of headache (if any)
    critical: false
  - item: 'Associated symptoms: nausea, vomiting, photophobia'
    critical: true
  - item: 'Time course: duration of symptoms, progression'
    critical: true
  - item: Exacerbating or relieving factors
    critical: false
  - item: Severity of headache on 0-10 scale
    critical: false
  associated_symptoms:
  - item: Fever pattern (continuous, intermittent)
    critical: false
  - item: Neck stiffness (difficulty touching chin to chest)
    critical: true
  - item: Photophobia (sensitivity to light)
    critical: true
  - item: Nausea or vomiting
    critical: false
  - item: Altered mental status (confusion, drowsiness)
    critical: true
  - item: Rash (any spots, especially non-blanching)
    critical: true
  - item: Seizures
    critical: true
  pmh:
  - item: Past medical history (hypertension, diabetes, etc.)
    critical: false
  - item: History of head trauma or surgery
    critical: false
  - item: History of meningitis or ear/sinus infections
    critical: true
  - item: Immunization history (especially pneumococcal, meningococcal, Hib)
    critical: true
  medications:
  - item: Current medications
    critical: false
  - item: Antibiotics taken recently
    critical: true
  - item: Analgesics taken for headache
    critical: false
  family_social:
  - item: Family history of meningitis or similar illness
    critical: false
  - item: Travel history (recent travel, especially to endemic areas)
    critical: true
  - item: Exposure to ill contacts (especially with similar symptoms)
    critical: true
  - item: Living conditions (crowding, dormitory, barracks)
    critical: false
  - item: Occupation (exposure to animals or chemicals)
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Neck stiffness with fever and headache
  critical: true
- item: Altered mental status
  critical: true
- item: Non-blanching rash
  critical: true
- item: Photophobia
  critical: false
- item: Seizures
  critical: true
expected_ddx:
  working_diagnosis: Bacterial meningitis
  differentials:
  - Viral meningitis
  - Subarachnoid hemorrhage
  - Cerebral malaria
  - Typhoid fever
investigations:
  appropriate:
  - name: Lumbar puncture with CSF analysis
    expected: Elevated white blood cell count (neutrophils), low glucose, high protein;
      Gram stain positive for bacteria
  - name: Blood cultures
    expected: Positive for causative organism (e.g., Neisseria meningitidis, Streptococcus
      pneumoniae)
  - name: CBC with differential
    expected: Leukocytosis with left shift
  - name: CT head before LP (if indicated)
    expected: No mass lesion or elevated ICP
  - name: CRP and procalcitonin
    expected: Elevated
  inappropriate:
  - MRI brain without contrast (not first-line in acute setting)
  - EEG
  - Urine culture
physical_exam_findings:
  general: Patient appears acutely ill, lying still with eyes closed, photophobic.
    Speech is coherent but slow. No visible rash.
  vitals:
    temperature: 39.5 °C
    blood_pressure: 120/80 mmHg
    heart_rate: 110 bpm
    respiratory_rate: 20 /min
    oxygen_saturation: 98%
management:
  pharmacological:
  - 'Empiric intravenous antibiotics: ceftriaxone 2 g IV every 12 hours + vancomycin
    15-20 mg/kg IV every 8-12 hours'
  - Dexamethasone 0.15 mg/kg IV every 6 hours for 4 days (start before or with first
    antibiotic dose)
  - Acetaminophen for fever
  - IV fluids for hydration
  non_pharmacological:
  - Admit to ICU or high-dependency unit
  - Isolation precautions until meningococcal ruled out
  - Close monitoring of neurological status and vital signs
  education_safety_netting:
  - Explain need for urgent lumbar puncture and antibiotics
  - Discuss signs of deterioration (worsening headache, seizures, decreasing consciousness)
  - Advise family to report any new rash or change in breathing
scoring_weights_override: null
---
## Identity

My name is Agus Santoso. I am 42 years old and work as a welder in a small factory in Bekasi, West Java. I live with my wife, Dewi (38), who is a housewife, and our two children: a son, Adi (14), and a daughter, Sari (8). I am a practical man, not one to complain easily. I have a high school education and I speak Indonesian with a bit of Sundanese when I’m around family. I am usually calm and patient, but this illness has made me very scared and irritable. I hate being in hospitals and I fear needles, especially the thought of a spinal tap. I’m also worried about not being able to work and support my family.

## Opening line

*“Dok, I have a very bad headache, high fever, and my neck feels so stiff I can’t touch my chin to my chest.”*

## How I present

I am lying on the examination bed, very still, with the lights dimmed. I have my eyes mostly closed, and I flinch when someone walks past the bed. My voice is quiet and strained. I look pale, and my face is sweaty. I am holding my head with both hands. I seem anxious and slightly irritable. I move slowly, and when I try to sit up, I groan and stop because of the neck pain. I am not fully alert — I sometimes take a few seconds to answer questions, but I can still talk and understand.

## What I know

- **Headache**: It started two days ago, gradually at first, then became very bad yesterday. It is a constant, pressing pain all over my head, but worst at the back of my head and behind my eyes. It feels like a tight band. On a scale of 0 to 10, it is a 9. Nothing makes it better — not even lying down or taking paracetamol.
- **Fever**: I first noticed it yesterday evening. I felt hot and cold. I measured my temperature at home — it was 39.5°C. The fever has been continuous, and I have been sweating a lot. I took paracetamol, but it only helped a little for a short time.
- **Neck stiffness**: This started yesterday evening too. I can’t bend my neck forward to touch my chin to my chest — it feels like something is blocking it. When I try, it hurts at the back of my neck and down my shoulders. I also feel like my whole body is stiff.
- **Photophobia**: Light hurts my eyes. I closed the curtains at home, and here in the emergency room I keep my eyes shut. The overhead light makes my headache worse.
- **Nausea and vomiting**: I have felt very nauseated since last night. I vomited twice this morning — once a little, then again after drinking water.
- **Altered mental status**: I feel very tired and drowsy. I have trouble concentrating, and sometimes I feel confused about what day it is. My wife says I have been slow to respond.
- **Rash**: No, I have not seen any spots or rash on my skin.
- **Seizures**: No, I have not had any fits.
- **Past medical history**: I am healthy, no diabetes or high blood pressure. I never had surgery. I had a sinus infection once, about two years ago, but it went away with medicine. I never had meningitis before.
- **Immunizations**: I got my childhood vaccines, but I don’t remember which ones. I never had shots for meningitis.
- **Medications**: I only took paracetamol for the fever and headache. No antibiotics.
- **Family history**: No one in my family has had meningitis. My mother had high blood pressure.
- **Travel**: I did not travel anywhere recently. I just go to work and back home.
- **Exposure**: My wife and children are fine. Some of my coworkers have had coughs and colds, but no one with a fever like mine.
- **Living conditions**: We live in a small house in a crowded area. My family of four shares one bedroom.
- **Occupation**: I work in a factory, welding metal parts. I wear a mask and gloves, but sometimes the air is smoky. I don’t think my work is related to this illness.
- **Ideas**: I think I might have a severe infection, maybe a brain infection or something like that. I’ve heard of meningitis on TV.
- **Concerns**: I am very worried that I might die or become permanently brain damaged. I am also scared of the spinal tap procedure — I’ve heard it can cause paralysis. I am worried about leaving my family without income if I stay in the hospital too long.
- **Expectations**: I hope the doctors can give me strong antibiotics and make me better quickly. I want to avoid the spinal tap if possible, but I will do what the doctor says is best.

## Communication profile

I have a high school education and speak Indonesian with a simple vocabulary. I am not used to medical terms, so I describe things in everyday words. I am usually patient, but right now I am uncomfortable and scared, so I may become irritable or repeat myself. I tend to be a bit terse — I answer only what is asked, but sometimes I ramble about my worries. I need the doctor to speak slowly and clearly, and to explain things in simple language.

## Disclosure rules

- I will answer only the question that is asked, and then stop. I will not volunteer extra information unless the doctor specifically asks a follow-up.
- If the doctor asks about a symptom I do not have, I will say “No, I don’t have that.”
- I will not mention that I think I have meningitis unless the doctor asks my ideas.
- I will only describe my symptoms as I have experienced them. I will not use medical terms like “meningismus” or “Kernig sign” — I don’t know those words.
- If the doctor asks about my neck stiffness, I will demonstrate by trying to touch my chin to my chest and wincing, saying “It hurts when I try.”

## Vital signs

- Temperature: 39.5°C (the nurse told me)
- Blood pressure: 120/80 mmHg
- Heart rate: 110 beats per minute
- Respiratory rate: 20 breaths per minute
- Oxygen saturation: 98% on room air

## Physical findings

*I can describe what the doctor might find when examining me, but only if asked. I will describe it in my own words.*

- **General appearance**: I look very sick, lying still with my eyes closed. I am sweating and my face is flushed.
- **Head and neck**: My neck feels stiff and painful when I try to bend it forward. The doctor can check by trying to turn my head — it will be hard to move. I also have a lot of pain when I try to lift my head while lying down.
- **Chest**: My breathing is normal, no cough.
- **Abdomen**: No pain, no tenderness.
- **Limbs**: No weakness, no rash. My arms and legs move normally.
- **Neurological**: I am drowsy and slow to respond, but I can follow commands. I do not have any seizure activity. The doctor might check my reflexes — they are normal as far as I know.
