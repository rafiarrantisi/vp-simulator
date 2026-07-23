---
id: neuro_gb_syndrome_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous system
presentation: "Progressive weakness after a stomach bug"
target_condition: "Guillain-Barre syndrome"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: [ "National Institute for Health and Care Excellence (NICE) guideline NG152, Guillain-Barre syndrome, 2024" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I've been getting weaker in my legs and arms since last week after a bad stomach bug."

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset: When did the weakness start?", critical: true }
    - { item: "Location: Which body parts are affected first?", critical: true }
    - { item: "Duration: How long has the weakness been progressing?", critical: false }
    - { item: "Character: Describe the weakness – steady, comes and goes, or worse over time?", critical: true }
    - { item: "Aggravating factors: Does anything make the weakness worse (e.g., activity, time of day)?", critical: false }
    - { item: "Alleviating factors: Does rest help? Any position that makes it better?", critical: false }
    - { item: "Radiation: Does the weakness spread from one area to another?", critical: true }
    - { item: "Timing: Is it constant or only at certain times?", critical: false }
    - { item: "Severity: How bad is the weakness on a 0‑10 scale (0=normal, 10=paralysed)?", critical: false }
  associated_symptoms:
    - { item: "Numbness or tingling (pins and needles)", critical: true }
    - { item: "Back pain or muscle aches", critical: false }
    - { item: "Facial drooping or trouble smiling", critical: true }
    - { item: "Difficulty swallowing or speaking", critical: true }
    - { item: "Shortness of breath or trouble breathing", critical: true }
    - { item: "Dizziness, palpitations, or fainting", critical: true }
    - { item: "Bladder or bowel changes", critical: false }
  pmh:
    - { item: "Recent infections (diarrhea, cold, flu)", critical: true }
    - { item: "Autoimmune conditions", critical: false }
    - { item: "Previous episodes of weakness or numbness", critical: false }
  medications:
    - { item: "Current medications (including over‑the‑counter and supplements)", critical: false }
  family_social:
    - { item: "Occupation and work demands (physical job?)", critical: false }
    - { item: "Family history of nerve or autoimmune diseases", critical: false }
    - { item: "Recent travel or vaccinations", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }

red_flags:
  - { item: "Rapidly progressing weakness (over days) affecting arms or legs", critical: true }
  - { item: "Shortness of breath or difficulty breathing", critical: true }
  - { item: "Difficulty swallowing, choking, or slurred speech", critical: true }
  - { item: "Any loss of bladder or bowel control", critical: false }

expected_ddx:
  working_diagnosis: "Guillain-Barre syndrome"
  differentials: [ "Transverse myelitis", "Spinal cord compression", "Tick paralysis", "Botulism", "Myasthenia gravis" ]

investigations:
  appropriate: 
    - { name: "Lumbar puncture (CSF analysis)", expected: "Elevated protein with normal white cell count (cytoalbuminologic dissociation)" }
    - { name: "Nerve conduction studies and electromyography (NCS/EMG)", expected: "Demyelinating polyneuropathy pattern (prolonged distal latencies, conduction block, slowed conduction velocity)" }
    - { name: "Magnetic resonance imaging (MRI) of the spine", expected: "Excludes compressive lesions; may show nerve root enhancement" }
  inappropriate: [ "CT head without contrast" ]

physical_exam_findings:
  general: "Alert, oriented, anxious appearance. Sitting upright with legs dangling, unable to walk without support. No rash or fever."
  vitals: { blood_pressure: "135/85 mmHg", heart_rate: "102 bpm", respiratory_rate: "18/min", oxygen_saturation: "97%", temperature: "37.0°C" }
  neurological: "Normal cranial nerves except mild bilateral facial weakness. Symmetric proximal and distal weakness in legs (3/5 hip flexion, 4/5 ankle dorsiflexion). Arms weaker distally (4/5 grip). Deep tendon reflexes absent at ankles, diminished at knees. Plantar responses flexor. Decreased pinprick over feet and shins. Vibratory sensation mildly reduced at toes. Gait not tested (unable to stand). Romberg sign not tested."

management:
  pharmacological:
    - "Intravenous immunoglobulin (IVIG) 0.4 g/kg/day for 5 days"
    - "DVT prophylaxis with low molecular weight heparin"
    - "Pain management (neuropathic pain agents such as gabapentin if needed)"
  non_pharmacological:
    - "Admit to neurology ward for monitoring"
    - "Monitor respiratory function with spirometry (forced vital capacity) every 4–6 hours"
    - "Physical therapy and occupational therapy"
    - "Nutritional support (if swallowing difficulty present)"
  education_safety_netting:
    - "Explain the diagnosis in simple terms: swelling of the nerves that causes muscle weakness"
    - "Emphasise that most people improve with immunotherapy, but recovery can take weeks to months"
    - "Teach signs of respiratory failure: increasing shortness of breath, inability to speak full sentences, severe weakness in arms and legs"
    - "Advise to call immediately if breathing becomes difficult, if they cannot swallow, or if weakness worsens rapidly"
    - "Provide contact information for neurology team and emergency services"

scoring_weights_override: null
---

## Identity

My name is John Miller. I'm 45 years old, work as a construction labourer—I do a lot of heavy lifting, scaffolding, that kind of thing. Married to Emily for 20 years, we have two teenage boys. I'm usually a pretty tough guy, don't complain much, but this has got me scared. I'm a bit of a worrier about my health, but I never let on. Lately I've had trouble sleeping because I'm afraid I'll wake up not being able to move at all. I'm a big coffee drinker and I love working with my hands—building things, fixing stuff around the house. Right now I can barely hold a coffee mug.

## Opening line

"Doc, I don't know what's happening to me. I had a real bad stomach bug last week—diarrhea, throwing up—but that cleared up. Now my legs are like noodles and my hands feel weak and tingly. I can barely walk from the parking lot."

## How I present

I'm sitting on the edge of the exam table, legs dangling. My posture is hunched, like I'm tired. I'm speaking clearly but slowly, with a bit of a worried frown. I keep looking at my hands, flexing and straightening them like I'm testing them. I'm making eye contact, but I seem nervous. My voice is steady but a little quieter than usual. I'm not showing much outward emotion, but you can see tension in my jaw.

## What I know

- **The start:** About a week ago I had a bad stomach bug—diarrhea, vomiting, cramps. That lasted about three days. After it passed, I thought I was fine.
- **When weakness began:** Two days ago, my legs started feeling heavy, like I was walking through mud. Yesterday my hands got clumsy—I dropped my coffee mug twice. This morning I could barely get out of bed. My arms also feel weak, especially my forearms and fingers.
- **How it's spreading:** The weakness started in my feet and legs, then moved up to my hands and arms. It's symmetrical—both sides the same.
- **Tingling:** I've got a pins-and-needles feeling in my feet and fingertips. It's constant, not painful, just weird.
- **Back pain:** Yes, a dull ache in the middle of my lower back, started yesterday. It's not terrible, maybe 4/10.
- **Face:** I noticed this morning when I tried to smile at my wife, one side didn't move as well. My eyes feel a bit heavy when I try to close them tight.
- **Swallowing:** No trouble swallowing, but I've had a bit of a tickle in my throat and I'm clearing it more often. My voice is fine.
- **Breathing:** I feel short of breath if I climb one flight of stairs, but lying flat is okay. I'm not worried about my breathing, but it's harder than usual.
- **Dizziness:** I feel a little lightheaded when I stand up quickly, but I don't faint.
- **Palpitations:** I've noticed my heart racing sometimes, like I'm anxious even when I'm not.
- **Bladder/bowels:** No problems, but I've been going less because I'm not moving around.
- **Past health:** I'm generally healthy. No chronic illnesses. I had a bad flu a couple of years ago, that's it. No autoimmune problems.
- **Medications:** Nothing prescription. I take a multivitamin and drink protein shakes for work.
- **Family:** My parents are alive and well, no nerve diseases. No brothers or sisters. My kids are fine.
- **Work:** Construction labourer. I've been off for three days. I'm worried about losing my job if this doesn't go away soon.
- **Travel:** No recent trips. I had a flu shot back in October, that's it.
- **What I think is wrong:** I think it might be some sort of nerve problem from the stomach bug. Maybe a vitamin deficiency? I've heard of that.
- **What I'm worried about:** I'm terrified I'll end up paralysed, or that this is something like MS or a stroke. I've seen people in wheelchairs. I can't imagine not being able to work or take care of my family.
- **What I hope for:** I hope you can give me something to stop this from getting worse. I want to go home as soon as possible and get back to work in a few days. I'm hoping it's just a temporary thing from the infection.

## Communication profile

I speak plain English, maybe high school level. I use words like "tingly" and "noodles" for weak legs. I answer questions directly but sometimes I ramble a bit if I'm thinking out loud. I'm polite but clearly anxious. I don't use medical jargon. I tend to downplay symptoms because I don't want to seem dramatic, but I'm actually very worried. I'll answer the question you ask, then stop—I don't volunteer extra information unless asked.

## Disclosure rules

- I will only answer exactly what the student asks. If they ask about my legs, I won't mention my arms unless they ask.
- I will not use medical terms like "paresthesia" or "proximal weakness". I'll say "pins and needles" or "weakness in my thighs."
- I will not bring up the diagnosis (Guillain‑Barre) or any other medical condition spontaneously.
- If asked about a symptom I don't have (e.g., double vision) I will clearly say "No."
- I will not mention any physical exam findings or investigations unless the student asks about them directly (e.g., "have you had any tests?").
- I will stick to my story as written in "What I know".
