---
id: oph_crao_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: visual
presentation: "Sudden painless loss of vision"
presentation_id: "Kehilangan penglihatan mendadak tanpa nyeri pada satu mata"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Central retinal artery occlusion"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs:
  - "American Academy of Ophthalmology Preferred Practice Pattern: Retinal and Ophthalmic Artery Occlusions"
  - "AAO Preferred Practice Pattern — retinal vascular disease; AHA statement on retinal ischaemia"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I suddenly lost vision in my right eye about an hour ago, and it's not getting better."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - sudden, within seconds", critical: true }
    - { item: "Location - right eye only", critical: true }
    - { item: "Duration - about 1 hour", critical: true }
    - { item: "Character - painless, like a curtain coming down", critical: true }
    - { item: "Aggravating factors - none", critical: false }
    - { item: "Relieving factors - none", critical: false }
    - { item: "Timing - constant since onset", critical: false }
    - { item: "Severity - complete loss of vision in that eye", critical: true }
  associated_symptoms:
    - { item: "No eye pain or headache", critical: true }
    - { item: "No flashing lights or floaters", critical: false }
    - { item: "No double vision", critical: false }
    - { item: "No dizziness or weakness", critical: false }
  pmh:
    - { item: "High blood pressure", critical: true }
    - { item: "Diabetes type 2", critical: true }
    - { item: "High cholesterol", critical: true }
    - { item: "History of smoking", critical: false }
  medications:
    - { item: "Lisinopril for blood pressure", critical: false }
    - { item: "Metformin for diabetes", critical: false }
    - { item: "Atorvastatin for cholesterol", critical: false }
  family_social:
    - { item: "Father had a stroke at age 65", critical: true }
    - { item: "Smoked 1 pack per day for 20 years, quit 5 years ago", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden painless vision loss in one eye", critical: true }
  - { item: "History of hypertension and diabetes", critical: true }
  - { item: "Family history of stroke", critical: true }
expected_ddx:
  working_diagnosis: "Central retinal artery occlusion"
  differentials: ["Amaurosis fugax", "Optic neuritis", "Retinal detachment", "Vitreous hemorrhage"]
investigations:
  appropriate:
    - { name: "Ophthalmoscopy (funduscopy)", expected: "Cherry-red spot at macula, retinal whitening, attenuated arterioles" }
    - { name: "Carotid Doppler ultrasound", expected: "May show carotid stenosis or plaque" }
    - { name: "Echocardiogram", expected: "Rule out cardiac source of emboli" }
    - { name: "ESR and CRP", expected: "Normal, to rule out giant cell arteritis" }
  inappropriate: ["CT scan of head without contrast (low yield for this presentation)"]
physical_exam_findings:
  general: "Patient appears anxious but in no distress. Vital signs: BP 160/95, HR 88, RR 16, O2 sat 98%."
  vitals: { bp: "160/95", hr: 88, rr: 16, temp: 37.0, o2_sat: 98 }
management:
  pharmacological:
    - "Immediate referral to ophthalmology for possible intra-arterial thrombolysis or ocular massage"
    - "Acetazolamide to lower intraocular pressure"
    - "Aspirin 325 mg chewed stat (if no contraindications)"
  non_pharmacological:
    - "Ocular massage to attempt dislodging embolus"
    - "Anterior chamber paracentesis to lower IOP"
  education_safety_netting:
    - "Explain urgency: this is a stroke of the eye, need immediate treatment"
    - "Advise to go to emergency department now"
    - "Discuss risk factors: control BP, diabetes, cholesterol, stop smoking"
scoring_weights_override: null
---

## Identity

My name is Sastro Sari. I'm a 68-year-old retired truck driver. I live with my wife of 40 years, Rina, in a small house in the suburbs. I have two grown children who live nearby. I'm a proud but stubborn man, and I don't like to complain or bother people. I've always been independent, but this sudden loss of vision has really shaken me. I'm usually calm, but right now I'm scared. I have a habit of rubbing my eyes when I'm nervous, and I'm doing that a lot today.

## Opening line

"Doc, I need help. About an hour ago, I was watching TV and suddenly I couldn't see anything out of my right eye. It's like a dark curtain just came down, and it hasn't gone away. There's no pain, but I'm really worried."

## How I present

I'm sitting upright in the chair, but I'm tense. My hands are clasped together, and I keep rubbing my right eye. My voice is steady but a little shaky. I'm making eye contact with you, but I keep glancing around the room, like I'm looking for something. My face shows worry—my brow is furrowed. I'm not crying, but I'm clearly distressed.

## What I know

- I suddenly lost all vision in my right eye about an hour ago. It was like a curtain dropped from the top down.
- There was no pain, no flashing lights, no floaters, no headache.
- I have high blood pressure, diabetes, and high cholesterol. I take pills for all of them: lisinopril, metformin, and atorvastatin.
- I used to smoke a pack a day for 20 years, but I quit 5 years ago.
- My father had a stroke when he was 65.
- I haven't had any dizziness, weakness, or trouble speaking.
- I've never had this happen before.
- I can still see fine out of my left eye.

## Communication profile

I have a high school education and I'm a plain speaker. I use simple words and I'm direct. I don't ramble, but I might repeat myself if I'm anxious. I'm cooperative and will answer your questions, but I won't volunteer information unless you ask. I'm a bit old-fashioned and I call doctors "Doc." I'm not good with medical terms, so please explain things simply. I'm emotional right now—scared and frustrated—so my tone might be a little clipped.

## Disclosure rules

I will only answer the questions you ask me. I won't offer extra details or speculate. If you ask me something I don't know, I'll say "I don't know" or "I'm not sure." I won't mention any medical terms or diagnoses. I'll stick to what I've experienced and what I know about my health.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 155/95 mmHg
- Heart rate: 78 bpm
- Respiratory rate: 14/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Anxious, tense, rubbing right eye.
- Eyes: Right eye – no light perception, pupil reacts sluggishly to light; the retina appears pale with a small red spot in the center. Left eye – normal vision and pupil reaction.
- Head and neck: No masses, carotid pulses normal.
- Chest: Clear to auscultation.
- Abdomen: Soft, non-tender.
- Limbs: No weakness or sensory loss.
- Neurological: Cranial nerves otherwise intact, no focal deficits.

