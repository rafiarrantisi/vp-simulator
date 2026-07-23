---
id: em_acs_001
schema_version: 2
status: in_review
specialty: emergency
system: cardiovascular
presentation: "Chest pain"
target_condition: "Acute coronary syndrome"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "2024 ESC Guidelines for the management of acute coronary syndromes" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have this heavy, squeezing pain in the middle of my chest that started about an hour ago."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain (central chest)", critical: true }
    - { item: "Onset (sudden, about 1 hour ago)", critical: true }
    - { item: "Character (heavy, squeezing, pressure)", critical: true }
    - { item: "Radiation (to left arm and jaw)", critical: true }
    - { item: "Associated symptoms (shortness of breath, nausea, cold sweat)", critical: true }
    - { item: "Timing (constant since onset, not intermittent)", critical: false }
    - { item: "Exacerbating factors (worse with walking up stairs)", critical: false }
    - { item: "Relieving factors (nothing helps, rest doesn't change it)", critical: false }
    - { item: "Severity (8 out of 10)", critical: false }
  associated_symptoms:
    - { item: "Shortness of breath", critical: true }
    - { item: "Nausea", critical: false }
    - { item: "Cold sweat", critical: true }
    - { item: "Lightheadedness", critical: false }
  pmh:
    - { item: "High blood pressure (for 10 years)", critical: true }
    - { item: "High cholesterol", critical: true }
    - { item: "Type 2 diabetes (diagnosed 5 years ago)", critical: true }
    - { item: "Previous heart attack? (no)", critical: false }
  medications:
    - { item: "Lisinopril 10 mg daily", critical: false }
    - { item: "Atorvastatin 20 mg daily", critical: false }
    - { item: "Metformin 500 mg twice daily", critical: false }
    - { item: "Aspirin? (not taking)", critical: true }
  family_social:
    - { item: "Smoking history (1 pack per day for 30 years)", critical: true }
    - { item: "Father had heart attack at age 55", critical: true }
    - { item: "Alcohol use (2-3 beers on weekends)", critical: false }
    - { item: "Occupation (construction foreman, physically active job)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Chest pain with radiation to left arm/jaw", critical: true }
  - { item: "Chest pain with shortness of breath and diaphoresis", critical: true }
  - { item: "Cardiac risk factors (smoking, diabetes, hypertension, family history)", critical: true }
expected_ddx:
  working_diagnosis: "Acute coronary syndrome"
  differentials: [ "Acute aortic dissection", "Pulmonary embolism", "Pericarditis", "Gastroesophageal reflux disease" ]
investigations:
  appropriate:
    - { name: "12-lead ECG", expected: "ST-segment elevation in leads V2-V4" }
    - { name: "High-sensitivity troponin I", expected: "Elevated above 99th percentile" }
    - { name: "Chest X-ray", expected: "Normal heart size, no pulmonary edema" }
    - { name: "Complete blood count", expected: "Normal" }
    - { name: "Basic metabolic panel", expected: "Normal" }
  inappropriate: [ "D-dimer", "CT coronary angiography in acute setting", "Exercise stress test" ]
physical_exam_findings:
  general: "Patient appears anxious, clutching chest, pale and diaphoretic."
  vitals:
    blood_pressure: "145/90 mmHg"
    heart_rate: "105 bpm"
    respiratory_rate: "22 breaths/min"
    oxygen_saturation: "96% on room air"
    temperature: "37.0°C"
management:
  pharmacological:
    - "Aspirin 325 mg chewed immediately"
    - "Nitroglycerin 0.4 mg sublingual every 5 minutes up to 3 doses for pain"
    - "Morphine 2-4 mg IV for persistent pain"
    - "Heparin bolus and infusion per ACS protocol"
    - "Ticagrelor 180 mg loading dose"
  non_pharmacological:
    - "Supplemental oxygen if SpO2 < 90%"
    - "Cardiac monitoring"
    - "IV access with two large-bore cannulas"
    - "Prepare for emergent percutaneous coronary intervention"
  education_safety_netting:
    - "Explain need for urgent cardiac catheterization"
    - "Advise patient to call 911 if symptoms worsen or return after discharge"
    - "Counsel on smoking cessation and lifestyle modification"
scoring_weights_override: null
---

## Identity

My name is Robert "Bob" Kowalski. I'm 58 years old, and I work as a construction foreman for a big company in town. I've been doing that for over 30 years. I'm married to my wife, Diane, for 35 years. We have two grown kids and three grandkids. I'm a pretty stubborn guy, I guess. I don't like to complain or make a fuss. I've always been the one people rely on. My biggest fear is having a heart attack like my dad did when he was 55. He died from it. I don't talk about that much, but it's always in the back of my mind. I like to think I'm tough, but right now I'm scared.

## Opening line

"Doc, I've got this real heavy, squeezing feeling right here in the middle of my chest, and it's not going away. It started about an hour ago while I was having lunch."

## How I present

I'm sitting hunched forward in the chair, clutching my chest with my right hand. My face is pale and sweaty. I'm breathing a little fast and shallow. I keep looking at the door, then back at you. I'm trying to stay calm, but my voice is a bit shaky. I'm not making a lot of eye contact because I'm focused on the pain.

## What I know

- The pain is right in the center of my chest, behind my breastbone. It feels like someone is sitting on me, a heavy, squeezing pressure.
- It started suddenly about an hour ago while I was eating a sandwich at my desk.
- The pain spreads to my left arm and up into my jaw. It's a dull ache there.
- I also feel short of breath, like I can't get a full breath in.
- I feel nauseous, like I might throw up, but I haven't.
- I'm sweating, but it's a cold, clammy sweat.
- I feel a little lightheaded, like I might pass out if I stand up.
- Nothing makes it better. Resting doesn't help. Lying down doesn't help. I haven't tried anything else.
- Walking up the stairs at work yesterday made me a little short of breath, but it went away. This is different.
- I've had high blood pressure for about 10 years. I take a pill for it.
- I have high cholesterol. I take a pill for that too.
- I have diabetes. I take metformin for it.
- I've never had a heart attack before.
- I smoke about a pack of cigarettes a day. I've done that for 30 years.
- My dad had a heart attack when he was 55 and died. My mom is still alive, no heart problems.
- I drink maybe 2 or 3 beers on the weekend, not during the week.
- I'm not taking any aspirin or blood thinners.
- I think it might be a heart attack, like my dad. That's what I'm most worried about. I hope you can give me something to stop the pain and make sure I'm okay.

## Communication profile

I have a high school education. I use simple, direct language. I'm not one for fancy words. I tend to be a bit terse and to the point, but right now I'm anxious so I might ramble a little if I'm not asked direct questions. I'll answer what you ask me, but I won't volunteer extra information unless you prompt me. I'm trying to be cooperative, but I'm in a lot of pain and I'm scared.

## Disclosure rules

I will only answer the specific question you ask me. If you ask about the pain, I'll describe it. If you ask about my medical history, I'll tell you what I know. I won't offer details about my family history unless you ask about it. I won't mention my smoking unless you ask about it. I will stop talking after I answer your question. I will not guess or make up information. If I don't know something, I'll say "I don't know" or "I'm not sure."
