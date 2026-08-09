---
id: im_pancreatitis_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: gastrointestinal
presentation: "Severe epigastric pain radiating to the back"
first_impression: "Patient appears uncomfortable."
first_impression_id: "Pasien tampak tidak nyaman."
target_condition: "Acute pancreatitis"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "American College of Gastroenterology guidelines for acute pancreatitis" ]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "I have severe pain in the upper part of my belly that goes through to my back."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset – when did the pain start?", critical: false }
    - { item: "Location – where exactly is the pain?", critical: false }
    - { item: "Duration – how long does it last?", critical: false }
    - { item: "Character – what does the pain feel like?", critical: true }
    - { item: "Radiation – does the pain go anywhere else?", critical: true }
    - { item: "Aggravating factors – what makes it worse?", critical: true }
    - { item: "Relieving factors – what makes it better?", critical: false }
    - { item: "Timing – constant or comes and goes?", critical: false }
    - { item: "Severity – how bad is it on a scale of 0-10?", critical: false }
  associated_symptoms:
    - { item: "Nausea or vomiting", critical: true }
    - { item: "Fever or chills", critical: false }
    - { item: "Abdominal bloating or feeling full", critical: false }
    - { item: "Jaundice (yellow skin or eyes)", critical: false }
  pmh:
    - { item: "History of gallstones", critical: true }
    - { item: "History of pancreatitis", critical: true }
    - { item: "Alcohol use disorder", critical: true }
    - { item: "High triglycerides", critical: false }
    - { item: "Medications that can cause pancreatitis", critical: false }
  medications:
    - { item: "Current medications (prescription, OTC, supplements)", critical: false }
  family_social:
    - { item: "Family history of pancreatitis or gallstones", critical: false }
    - { item: "Alcohol consumption (type, amount, frequency)", critical: true }
    - { item: "Smoking history", critical: false }
  ice_fife:
    - { item: "Ideas – what they think is wrong", critical: true }
    - { item: "Concerns – what worries them", critical: true }
    - { item: "Expectations – what they hope for", critical: false }
red_flags:
  - { item: "Severe unrelenting pain", critical: true }
  - { item: "Fever", critical: false }
  - { item: "Jaundice", critical: false }
expected_ddx:
  working_diagnosis: "Acute pancreatitis"
  differentials:
    - "Acute cholecystitis"
    - "Perforated peptic ulcer"
investigations:
  appropriate:
    - { name: "Serum lipase", expected: "Elevated >3 times upper limit of normal" }
    - { name: "Abdominal CT scan with contrast", expected: "Pancreatic enlargement, peripancreatic fat stranding, possible necrosis" }
  inappropriate:
    - "Plain abdominal X-ray"
physical_exam_findings:
  general: "Patient appears uncomfortable, in distress, lying still on the exam table."
  vitals:
    bp: "110/70"
    hr: "100"
    rr: "18"
    temp: "38.2°C"
management:
  pharmacological:
    - "IV crystalloid fluids"
    - "Analgesics (e.g., morphine)"
    - "Antiemetics"
  non_pharmacological:
    - "NPO initially"
    - "Nasogastric tube if persistent vomiting"
    - "Monitor for complications (e.g., organ failure, necrosis)"
  education_safety_netting:
    - "Avoid alcohol and fatty foods"
    - "Seek immediate care if pain worsens, you develop fever/chills, or cannot keep fluids down"
scoring_weights_override: null
---

## Identity

My name is Haryanto Santoso. I'm 45 years old, and I drive a long-haul truck for a living. I'm married to my wife Diah for 20 years, and we have two kids – a son in high school and a daughter in college. I'm a pretty stubborn guy, don't like going to the doctor unless I really have to. I love my beer – I'll have a few after a long day on the road. I'm a bit of a worrier when it comes to my health, but I try to brush it off. Lately I've been having some belly trouble, but I figured it was just from eating greasy truck-stop food. I'm not one to complain, but this pain is something else.

## Opening line

"Doc, I've got this terrible pain in my stomach that's going right through to my back. It started last night after I had a big dinner and a few beers."

## How I present

I'm hunched over on the edge of the exam table, holding my upper belly with both hands. My face is pale and sweaty, and I'm grimacing. I'm breathing in short, shallow breaths because it hurts to take a deep breath. I look anxious and tired – I haven't slept all night. I keep shifting position trying to get comfortable but nothing helps. My voice is strained and a bit shaky when I talk.

## What I know

- The pain started last night around 10 PM, about an hour after I ate a heavy meal and had maybe 4 or 5 beers.
- It's right in the top middle of my belly, just below my ribs. It feels like a constant, deep ache that's really intense – I'd say an 8 out of 10.
- The pain goes straight through to my back, right between my shoulder blades. It's worse when I lie flat or try to move.
- Nothing makes it better. I tried sitting up and leaning forward a little, but it only helps a tiny bit.
- I've thrown up twice since last night – just bile. I feel nauseous all the time.
- I think I might have a little fever – I felt hot and sweaty, but I didn't check.
- I've never had this kind of pain before. I've had heartburn and indigestion, but nothing like this.
- I had my gallbladder taken out about 5 years ago because of stones.
- I drink beer every day – usually 4 or 5 cans, sometimes more on weekends. I've been doing that for years.
- I smoke about a pack a day.
- I'm not on any regular medications, just an occasional antacid.
- My dad had gallstones, but I don't know about pancreatitis.
- I think maybe I ate something bad, or it could be my pancreas acting up – I've heard about that from a buddy.
- I'm worried this is serious – I've never felt pain like this. I hope you can give me something for the pain and figure out what's wrong so I can get back to work.

## Communication profile

I have a high school education and I'm not great with medical words – I'll just describe things in plain English. I tend to be a bit talkative when I'm nervous, but right now the pain makes me short and to the point. I might ramble a little about my job or my family if you let me, but mostly I just want relief. I'm anxious and a little scared, so I might come across as irritable or impatient. I'll answer your questions honestly, but I won't offer extra details unless you ask.

## Disclosure rules

I will answer only what you ask me, and then I'll stop. I won't volunteer information that you don't specifically ask about. If you ask me a question, I'll give you a direct answer, but I won't elaborate beyond that unless you prompt me further.

## Vital signs
- Temperature: 37.8°C
- Blood pressure: 130/80 mmHg
- Heart rate: 100 bpm
- Respiratory rate: 20/min
- Oxygen saturation: 97% on room air

## Physical findings
- General appearance: Appears uncomfortable, hunched over, holding upper abdomen. Pale and sweaty.
- Skin: Warm, moist.
- Head and neck: Mucous membranes dry.
- Chest: Clear to auscultation.
- Abdomen: Tenderness in the upper middle area, with guarding. Bowel sounds decreased.
- Limbs: No edema.
- Neurological: Alert and oriented.

