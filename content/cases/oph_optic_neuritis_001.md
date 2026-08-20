---
id: oph_optic_neuritis_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: nervous
presentation: "Sudden vision loss with pain on eye movement"
presentation_id: "Kehilangan penglihatan mendadak pada satu mata disertai nyeri saat menggerakkan mata"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Optic neuritis"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["Optic Neuritis Treatment Trial (ONTT) guidelines", "American Academy of Ophthalmology Preferred Practice Pattern"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I suddenly lost vision in my right eye and it hurts when I move it."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - right eye", critical: false }
    - { item: "Onset - sudden, over hours", critical: true }
    - { item: "Character - blurred vision, central scotoma", critical: true }
    - { item: "Radiation - none", critical: false }
    - { item: "Associated symptoms - pain on eye movement", critical: true }
    - { item: "Timing - constant, present for 2 days", critical: false }
    - { item: "Exacerbating factors - eye movement worsens pain", critical: true }
    - { item: "Relieving factors - rest does not help", critical: false }
    - { item: "Severity - pain 7/10, vision loss profound", critical: false }
  associated_symptoms:
    - { item: "Color desaturation (colors appear washed out)", critical: true }
    - { item: "Mild headache behind the eye", critical: false }
    - { item: "Recent cold or flu-like illness", critical: false }
  pmh:
    - { item: "No known medical conditions", critical: true }
    - { item: "No history of neurological disease", critical: true }
  medications:
    - { item: "No regular medications", critical: true }
  family_social:
    - { item: "No family history of multiple sclerosis", critical: true }
    - { item: "No family history of vision loss", critical: false }
    - { item: "Non-smoker, occasional alcohol", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong: Could be a stroke or brain tumor", critical: true }
    - { item: "Concerns - what worries them: Worried about permanent vision loss or multiple sclerosis", critical: true }
    - { item: "Expectations - what they hope for: I want to get my vision back and know the cause", critical: false }
red_flags:
  - { item: "Acute monocular vision loss", critical: true }
  - { item: "Pain with eye movement", critical: true }
  - { item: "Central scotoma", critical: false }
expected_ddx:
  working_diagnosis: "Optic neuritis"
  differentials: ["Anterior ischemic optic neuropathy (AION)", "Compressive optic neuropathy"]
investigations:
  appropriate:
    - { name: "Magnetic resonance imaging (MRI) of brain and orbits with contrast", expected: "May show enhancement of the optic nerve consistent with demyelination" }
    - { name: "Visual evoked potentials (VEP)", expected: "P100 latency prolonged" }
    - { name: "Blood tests for inflammatory markers (ESR, CRP)", expected: "Normal or mildly elevated" }
  inappropriate: ["CT head without contrast"]
physical_exam_findings: { general: "Alert, oriented, anxious. Vitals normal. Right eye: visual acuity 20/200, relative afferent pupillary defect (RAPD) present, color vision impaired (red desaturation), central scotoma on Amsler grid. Optic disc normal or slightly swollen. Left eye normal. No other neurological deficits." }
management:
  pharmacological: ["High-dose intravenous methylprednisolone (1g daily for 3 days) then oral taper"]
  non_pharmacological: ["Rest, eye patch if photophobia present"]
  education_safety_netting: ["Explain that vision may improve over weeks to months", "Discuss risk of developing multiple sclerosis", "Advise follow-up with neurologist", "'Return if new neurological symptoms appear'"]
scoring_weights_override: null
---

## Identity

I’m Zahra Utami, 32 years old. I work as an elementary school teacher, and I love my job—I’m with first graders, and they keep me on my toes. I’m married to Agus, a contractor, and we have two kids, ages 6 and 4. I’m usually pretty organized and like to plan ahead, but this eye thing has really thrown me. I’m usually calm under pressure, but right now I’m scared. I’m a bit of a worrier when it comes to my health, especially because I need my eyesight for work and for driving the kids around. I also have a small habit of rubbing my eyes when I’m tired, but I’ve been trying to stop.

## Opening line

“I suddenly lost my vision in my right eye a couple of days ago, and it hurts when I move my eye.”

## How I present

I’m sitting upright in the chair, leaning forward a little. I’m looking at you with my left eye, but my right eye is half-closed or I’m wearing a hand over it because the light bothers it. My voice is a bit shaky—I’m trying to be composed, but I’m clearly anxious. I keep rubbing my temple on the right side. I’m not crying, but my face shows worry. I’m cooperative and answer questions directly, but I sometimes pause because I’m trying to remember every detail.

## What I know

- I first noticed the problem two days ago, when I woke up. The vision in my right eye was blurry.
- It started as a small gray spot in the center of my vision, and over the next few hours it got bigger and darker.
- Now I can only see light and shadows out of that eye. Everything looks like a dense fog.
- I have a dull ache behind my right eyeball, and when I look to the side—especially to the left—the pain gets sharper.
- I had a mild cold about a week ago—runny nose, sore throat—but no fever. I feel fine otherwise.
- I don’t have any other health problems. I’m not on any medications, and I have no allergies.
- I don’t smoke, and I only drink a glass of wine maybe once a week.
- No one in my family has had eye problems like this, and as far as I know, no one has multiple sclerosis.
- I’m very worried this could be a stroke or a brain tumor. I’m also scared that my vision might not come back, and I’m afraid of what it might mean for my future.
- I want to know exactly what’s wrong, and I’m hoping for treatment that will bring my sight back.
- At first, the colors in my right eye looked washed out and faded—everything seemed pale and dull—but over the next few hours it turned into the blur and the fog I have now.

## Communication profile

I have a high school education and some college—I’m good with words, but I don’t use medical terms. I’ll describe things in plain language: “blurry spot,” “aches,” “hurts when I move my eye.” I’m anxious but not hysterical. I tend to answer exactly what you ask and then wait for the next question. I don’t ramble, but if you ask about something specific, I’ll give a clear answer. I’m polite and cooperative, but my tone shows I’m looking for reassurance.

## Disclosure rules

I will only answer the question you ask me. I will not volunteer extra information or expand on topics unless prompted. I will not use medical terminology. I will state my symptoms and history as I understand them, in lay terms. I will not guess or invent details. If I don’t know something, I’ll say, “I don’t know.”

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 118/76 mmHg
- Heart rate: 76 bpm
- Respiratory rate: 14/min
- Oxygen saturation: 99% on room air

## Physical findings
- General appearance: Anxious, sitting upright, holding hand over right eye, complains of pain when moving the eye.
- Head and neck: No abnormalities noted.
- Neurological: Vision in right eye is severely reduced, only able to perceive light and shadows. When a light is shone in the right eye, the pupil does not constrict as much as the left eye. Pain is elicited when looking to the left side.
- Chest, abdomen, limbs: Normal.

