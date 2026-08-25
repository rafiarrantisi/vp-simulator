---
id: em_dengue_001
schema_version: 2
status: in_review
specialty: emergency
system: infectious disease
presentation: Fever, headache and body aches for 3 days
presentation_id: Demam tinggi, sakit kepala berat, dan nyeri badan selama 3 hari
first_impression: Patient appears flushed, restless, and uncomfortable, rubbing her
  temples while seated.
first_impression_id: Pasien tampak kemerahan, gelisah, dan tidak nyaman, sambil mengusap
  pelipisnya.
target_condition: Dengue fever with warning signs
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages:
- en
source_refs:
- WHO SEARO dengue guidelines (2009/2011) — dengue fever with warning signs
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: Kurasi pilot candidate (plan §6.2). Belum ada clinical sign-off —
    WAJIB direview dokter/pendidik sebelum pilot_verified/published (§11).
chief_complaint: I have had a high fever and bad headache for three days.
anamnesis_checklist:
  hpi_socrates:
  - item: Site of pain
    critical: false
  - item: Onset of fever
    critical: true
  - item: Character of fever
    critical: false
  - item: Radiation of pain
    critical: false
  - item: Associated symptoms like vomiting or bleeding
    critical: true
  - item: Time course of symptoms over 3 days
    critical: false
  - item: Exacerbating factors
    critical: false
  - item: Severity of pain (scale 1-10)
    critical: false
  associated_symptoms:
  - item: Do you have abdominal pain or tenderness?
    critical: true
  - item: Have you vomited? How many times in the last 24 hours?
    critical: true
  - item: Any bleeding from nose, gums, or easy bruising?
    critical: true
  - item: Do you feel unusually tired or weak?
    critical: true
  - item: Any rash on your skin?
    critical: false
  - item: Any joint or muscle aches?
    critical: false
  - item: Any red spots on your skin?
    critical: false
  - item: Any dizziness or feeling faint when standing?
    critical: true
  pmh:
  - item: Any chronic illnesses like diabetes or hypertension?
    critical: false
  - item: Any history of dengue or other infections?
    critical: false
  - item: Any previous surgeries?
    critical: false
  medications:
  - item: What have you taken for the fever?
    critical: false
  - item: Any regular medications for chronic diseases?
    critical: false
  - item: Any allergies to medicines?
    critical: false
  family_social:
  - item: Does anyone in your household have similar symptoms?
    critical: false
  - item: Do you live in a dengue-prone area? Any recent mosquito bites?
    critical: true
  - item: What is your occupation and daily activities?
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Abdominal pain or tenderness
  critical: true
- item: Persistent vomiting (≥3 times in 24 hours)
  critical: true
- item: Mucosal bleeding (nose or gums)
  critical: true
- item: Lethargy or restlessness
  critical: true
- item: Dizziness on standing (possible hypovolemia)
  critical: false
expected_ddx:
  working_diagnosis: Dengue fever with warning signs
  differentials:
  - Typhoid fever
  - Viral upper respiratory tract infection
investigations:
  appropriate:
  - name: Complete blood count (including platelet and haematocrit)
    expected: Low platelet count (<150,000/mm³), rising haematocrit (>10% from baseline
      or >45%)
  - name: NS1 antigen test
    expected: Positive for dengue virus
  - name: Serology (IgM and IgG)
    expected: Positive IgM, indicative of acute infection
  - name: Tourniquet test (Rumpel-Leede test)
    expected: Positive (≥20 petechiae per square inch)
  inappropriate:
  - Widal test for typhoid as initial test
physical_exam_findings:
  general: Patient appears tired and in mild distress. Mucosa slightly dry. Conjunctival
    injection noted.
  vitals:
    temperature: 38.7
    blood_pressure: 100/70
    heart_rate: 110
    respiratory_rate: 22
    oxygen_saturation: 98
management:
  pharmacological:
  - Paracetamol for fever (avoid NSAIDs due to bleeding risk)
  - Oral rehydration salts (ORS) for fluid replacement
  non_pharmacological:
  - Monitor for bleeding signs (petechiae, ecchymosis, epistaxis)
  - Monitor vital signs (blood pressure, heart rate, temperature) every 4 hours
  - Encourage oral fluid intake (2-3 liters per day of clear fluids)
  education_safety_netting:
  - Return to the hospital immediately if vomiting worsens, severe abdominal pain
    develops, or any bleeding occurs
  - Avoid NSAIDs (like ibuprofen) as they increase bleeding risk
  - Ensure adequate rest at home
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

My name is Wahyuni Rahmawati. I am 38 years old. I work as a cashier at a minimarket in Bogor. I am married to Pak Agus, who drives an angkot. We have two children, a 12-year-old son, Dimas, and a 7-year-old daughter, Sinta. I usually take care of the household after work. I am a bit anxious by nature, especially when it comes to my health—I do not want to be a burden to my family. I have a nervous way of talking when I am worried, constantly looking at the doctor’s reactions. I live in a small house near a river where mosquitoes come out a lot in the evening.

## Opening line

"Dok, I’ve had a high fever for three days, and now my stomach hurts and I feel very weak."

## How I present

I am sitting forward on the edge of the chair, hoping the doctor will help me quickly. I look tired, my face is a little flushed from the fever. My voice is a bit shaky as I speak. I keep touching my forehead and wincing. I make good eye contact but my eyes are watery and worried. My clothes are a bit damp with sweat.

## What I know

- The fever started three days ago, very suddenly, and it has been high all the time, at night and morning, about 38-39 degrees Celsius.
- I feel a very bad headache, like something pressing behind my eyes, all the time.
- My muscles and joints ache all over my body, even my bones ache.
- After the second day of fever, I started feeling it in my belly, a dull ache right in the middle of the stomach. It is worse now.
- I have thrown up three times this morning, and once yesterday. The vomiting was mostly water and food. Now I feel nauseated just sitting up.
- I feel so weak, like I have no energy at all, even to walk from my bed to the bathroom.
- I noticed yesterday a few small red spots on my arms and chest, like tiny red dots.
- When I get up from sitting, I feel very dizzy, like the room spins and I almost fall.
- I have been taking some paracetamol I bought from the warung, but it doesn't really help much.
- Nobody else in my family is sick like this.
- I live near a river, so many mosquitoes around, especially at dusk. I often get bit.
- I have no other health problems, no allergies.
- I was given medicine by the nurse earlier. I do not know the name, but it was a white tablet. No injections.

## Communication profile

I finished senior high school, but I am not familiar with big medical words. I speak Indonesian, with some Sundanese words slipping in when I am nervous. I tend to give short answers, but I volunteer important details when asked. I can be a bit repetitive when I am anxious. I look at the doctor a lot to see if they look concerned. I answer clearly but only what the doctor asks.

## Disclosure rules

I answer only what the doctor specifically asks. I do not volunteer information the doctor has not requested. I do not use medical terminology.

## Vital signs

The nurse took my temperature: 38.7 degrees Celsius. My blood pressure: 100/70. My heart rate: 110. My breathing: 22 times a minute. My oxygen: 98 percent. They said it with a small machine on my finger.

## Physical findings

- **General appearance:** I look tired and flushed, with some sweat on my forehead. I move slowly and I am a bit shaky.
- **Skin:** There are small, flat red spots on my arms, chest, and a few on my legs. The doctor pressed on them and said it is a rash. He also did a test with a blood pressure cuff on my arm, and said there are small red dots under the skin.
- **Head/neck:** My eyes are a little red and feel sore. My neck doesn’t feel stiff.
- **Chest:** My breathing feels okay, not painful.
- **Abdomen:** There is a dull ache in the middle of my stomach, not one side more than the other. It hurts more when the doctor presses on it, but not sharp pain.
- **Limbs:** My arms and legs ache a lot, like a deep pain in the bones. My hands are warm.
- **Neurological:** When I stand up I get very dizzy and almost fall. I feel weak all over, but I am not confused. My muscles are not twitching.
