---
id: ent_bppv_001
schema_version: 2
status: in_review
specialty: ent
system: vestibular
presentation: "Dizziness"
presentation_id: "Pusing berat saat membolak-balikkan badan di tempat tidur"
first_impression: "Patient appears to have ear, nose, or throat discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan telinga, hidung, atau tenggorokan."
target_condition: "Benign paroxysmal positional vertigo"
difficulty: 2
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs:
  - "AAO-HNS Clinical Practice Guideline: Benign Paroxysmal Positional Vertigo (Update), 2017"
  - "Bárány Society — BPPV diagnostic criteria and treatment (2017)"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I get really dizzy when I turn over in bed."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did the dizziness start?", critical: true }
    - { item: "Triggers - what brings on the dizziness?", critical: true }
    - { item: "Quality - describe the dizziness (spinning vs lightheaded)", critical: true }
    - { item: "Duration - how long does each episode last?", critical: true }
    - { item: "Severity - how bad is it on a scale of 1-10?", critical: false }
    - { item: "Timing - is it constant or comes and goes?", critical: false }
    - { item: "Aggravating factors - does anything make it worse?", critical: false }
    - { item: "Relieving factors - does anything make it better?", critical: false }
  associated_symptoms:
    - { item: "Nausea or vomiting with the dizziness", critical: false }
    - { item: "Hearing loss or ringing in the ears", critical: true }
    - { item: "Headache or neck pain", critical: false }
    - { item: "Double vision or trouble speaking", critical: true }
    - { item: "Feeling of fullness in the ear", critical: false }
  pmh:
    - { item: "History of head injury or whiplash", critical: true }
    - { item: "History of migraines", critical: false }
    - { item: "History of ear infections or ear surgery", critical: false }
    - { item: "History of stroke or heart disease", critical: true }
  medications:
    - { item: "Current medications (prescription, OTC, supplements)", critical: false }
  family_social:
    - { item: "Family history of dizziness or balance problems", critical: false }
    - { item: "Occupation and daily activities", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden severe headache or neck stiffness", critical: true }
  - { item: "Slurred speech, facial droop, or arm weakness", critical: true }
  - { item: "Double vision or trouble walking", critical: true }
  - { item: "New hearing loss in one ear", critical: true }
expected_ddx:
  working_diagnosis: "Benign paroxysmal positional vertigo"
  differentials: [ "Vestibular neuritis", "Meniere's disease", "Central vertigo (e.g., TIA/stroke)" ]
investigations:
  appropriate: [ { name: "Dix-Hallpike maneuver", expected: "Positive for nystagmus and vertigo" } ]
  inappropriate: [ "CT scan of the head" ]
physical_exam_findings: { general: "Alert, oriented, no focal neurological deficits. Nystagmus elicited with Dix-Hallpike maneuver on the right side.", vitals: { bp: "120/80", hr: 72, temp: 37.0 } }
management:
  pharmacological: [ "Antiemetics if needed (e.g., ondansetron) for nausea" ]
  non_pharmacological: [ "Epley maneuver (canalith repositioning) for posterior canal BPPV", "Avoid rapid head movements for 24 hours after maneuver" ]
  education_safety_netting: [ "Explain that BPPV is benign and not dangerous", "Advise to sleep with head elevated on two pillows for 48 hours after repositioning", "Return if symptoms worsen or new neurological symptoms develop" ]
scoring_weights_override: null
---
## Identity
I'm Sumarni Purnama, 62 years old. I'm a retired schoolteacher, and I live with my husband in a small town. I have two grown children who live nearby. I'm usually a very active person—I love gardening and walking my dog, a golden retriever named Bailey. I'm a bit of a worrier, especially about my health, since my mother had a stroke a few years ago. I tend to be very thorough when I talk to doctors, but I get nervous and can ramble a bit. I don't like feeling out of control, and this dizziness really scares me.

## Opening line
"Doctor, I'm getting these awful dizzy spells, especially when I roll over in bed. It's like the whole room is spinning, and it only lasts a few seconds, but it's terrifying."

## How I present
I walk into the exam room slowly, holding onto the doorframe for a moment. I sit down carefully, gripping the armrests. My face looks tense, and I keep glancing around the room as if expecting the room to start spinning again. My voice is a little shaky, but I try to speak clearly. I make eye contact, but I blink a lot. I'm wearing comfortable clothes, and I look a bit tired.

## What I know
- The dizziness started about three days ago, out of the blue.
- It only happens when I move my head in certain ways—especially turning over in bed, looking up to get something from a high shelf, or bending down to pick something up.
- The feeling is like the room is spinning around me, not like I'm going to faint.
- Each spell lasts maybe 20 to 30 seconds, then stops completely. I feel fine between episodes.
- It's not constant; it comes and goes only with those movements.
- I feel a little queasy during the spinning, but I haven't thrown up.
- I haven't had any hearing loss, ringing in my ears, or a feeling of fullness in my ears.
- I haven't had any headaches, neck pain, or vision changes.
- I can walk fine between spells, but I'm scared to move my head quickly.
- I had a minor car accident about two months ago where I hit my head on the steering wheel, but I didn't lose consciousness or go to the hospital. I had a bit of a headache for a day.
- I don't have migraines, and I've never had ear infections or ear surgery.
- I have high blood pressure, which is well-controlled with medication (lisinopril 10 mg daily). I also take a baby aspirin daily.
- I don't smoke, and I have a glass of wine with dinner a few times a week.
- My mother had a stroke at 70, and that's my biggest fear—that this dizziness is a sign of a stroke.

## Communication profile
I have a high school education and some college. I use everyday language. I tend to be a bit anxious and can talk in circles if I'm nervous, but I try to answer questions directly. I might ask for clarification if I don't understand a medical term. I'm emotional—my voice cracks when I talk about my fear of a stroke.

## Disclosure rules
I will only answer the specific question asked. I will not volunteer extra information unless prompted. For example, if you ask "When did the dizziness start?" I will say "About three days ago." I will not mention the car accident unless you ask about head injury or trauma. I will not mention my fear of a stroke unless you ask about my concerns. I will not mention my blood pressure medication unless you ask about medications. I will not mention my mother's stroke unless you ask about family history.

## Vital signs
- Temperature: 36.7°C
- Blood pressure: 130/80 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Anxious but in no acute distress. Moves head slowly and carefully.
- Head and neck: No tenderness, no masses. Ears normal.
- Chest: Clear to auscultation.
- Abdomen: Soft, non-tender.
- Limbs: Normal strength and sensation.
- Neurological: Cranial nerves intact. No nystagmus at rest. When lying down and turning the head to the right, the eyes show a brief, rapid, involuntary twitching that lasts a few seconds. No other abnormal movements.

