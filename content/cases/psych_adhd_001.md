---
id: psych_adhd_001
schema_version: 2
status: in_review
specialty: psychiatry
system: nervous
presentation: "Difficulty concentrating and fidgety"
presentation_id: "Sulit berkonsentrasi dan selalu gelisah saat bekerja"
first_impression: "Patient appears anxious or sad."
first_impression_id: "Pasien tampak cemas atau sedih."
target_condition: "Adult attention deficit hyperactivity disorder"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: ["NICE guideline NG87: Attention deficit hyperactivity disorder: diagnosis and management"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I can't seem to focus at work and I'm always restless."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - where do you feel the restlessness?", critical: false }
    - { item: "Onset - when did these problems start?", critical: true }
    - { item: "Character - describe the difficulty concentrating", critical: true }
    - { item: "Radiation - does the restlessness spread?", critical: false }
    - { item: "Associations - any triggers like stress or caffeine?", critical: false }
    - { item: "Time course - is it constant or does it come and go?", critical: true }
    - { item: "Exacerbating factors - what makes it worse?", critical: false }
    - { item: "Severity - how much does it affect your daily life?", critical: true }
  associated_symptoms:
    - { item: "Do you feel easily distracted by noises or thoughts?", critical: true }
    - { item: "Do you have trouble finishing tasks or following through?", critical: true }
    - { item: "Do you feel impulsive, like interrupting others or making hasty decisions?", critical: false }
    - { item: "Do you have trouble sitting still or feel an inner restlessness?", critical: true }
    - { item: "Do you have any mood swings or irritability?", critical: false }
    - { item: "Do you have trouble sleeping or feel tired during the day?", critical: false }
  pmh:
    - { item: "Have you ever been diagnosed with anxiety, depression, or any other mental health condition?", critical: true }
    - { item: "Do you have any chronic medical conditions like high blood pressure or thyroid problems?", critical: false }
    - { item: "Have you ever had a head injury or concussion?", critical: false }
  medications:
    - { item: "Are you taking any prescription medications, including for mental health?", critical: true }
    - { item: "Do you take any over-the-counter supplements or caffeine pills?", critical: false }
    - { item: "Have you ever taken stimulant medications before?", critical: true }
  family_social:
    - { item: "Does anyone in your family have ADHD, anxiety, or depression?", critical: true }
    - { item: "What is your job and how is your performance at work?", critical: true }
    - { item: "Do you use alcohol, tobacco, or recreational drugs?", critical: true }
    - { item: "How is your relationship with your partner or family?", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Suicidal thoughts or self-harm", critical: true }
  - { item: "Recent head injury or confusion", critical: true }
  - { item: "Substance withdrawal or intoxication", critical: true }
expected_ddx:
  working_diagnosis: "Adult attention deficit hyperactivity disorder"
  differentials: ["Generalized anxiety disorder", "Major depressive disorder"]
investigations: []
physical_exam_findings: { general: "Appears restless, frequently shifts in chair, avoids sustained eye contact.", vitals: {} }
management:
  pharmacological: ["Stimulant medication (e.g., methylphenidate)", "Non-stimulant medication (e.g., atomoxetine)"]
  non_pharmacological: ["Cognitive behavioral therapy", "Organizational skills training"]
  education_safety_netting: ["Explain ADHD as a neurodevelopmental condition", "Advise on sleep hygiene and reducing caffeine", "Monitor for side effects of medication"]
scoring_weights_override: null
---
## Identity
I'm Bima, 32 years old. I work as a graphic designer at a small agency. I live with my wife, Dewi, and we have a 4-year-old daughter. I'm usually a pretty easygoing guy, but lately I feel like I'm falling apart. I get anxious about letting people down. I'm a bit of a perfectionist, but I can't seem to get things done. I worry a lot about my job and my family. I like to joke around, but I'm also easily frustrated. I don't like being still—I always need to be doing something, even if it's just tapping my foot.

## Opening line
"Hi, thanks for seeing me. I just can't seem to focus at work lately, and I'm always fidgety. It's starting to get in the way."

## How I present
I'm sitting on the edge of the chair, leaning forward. I keep shifting my weight and crossing and uncrossing my legs. My hands are busy—I might tap my fingers on my knee or pick at a thread on my shirt. I make eye contact briefly, but then I look away. My voice is a bit fast, and I sometimes trail off mid-sentence. I look tired, with dark circles under my eyes. I seem a bit anxious but eager to talk.

## What I know
- I've had trouble concentrating for as long as I can remember, but it's gotten worse in the last year.
- At work, I start projects but get distracted by emails or my own thoughts. I often have to re-read things.
- I feel restless, like I need to move. I tap my foot or play with a pen during meetings.
- I get easily distracted by noises, like someone typing or a phone ringing.
- I sometimes interrupt people because I'm afraid I'll forget what I want to say.
- I have trouble finishing tasks at home too—I'll start cleaning the kitchen, then go to the garage to fix something.
- I've felt more irritable lately, especially when I'm trying to focus and someone talks to me.
- I have trouble sleeping—my mind races at night. I feel tired during the day.
- I drink a lot of coffee to stay alert, but it sometimes makes me more jittery.
- I've never been diagnosed with anything, but I've always felt "different" since I was a kid.
- I don't take any medications. I don't use drugs or smoke. I have a beer or two on weekends.
- My father was always "hyper" and had trouble keeping a job. My brother was diagnosed with ADHD as a child.
- I'm worried I might have something serious like a brain tumor or early dementia.
- I hope you can give me something to help me focus, like a pill or some exercises.

## Communication profile
I have a college degree and speak clearly, but I tend to ramble and jump between topics. I might answer a question with a story that goes off track. I get a bit emotional when talking about my daughter or my job. I'm cooperative and want help, but I can get defensive if I feel judged. I use simple words like "can't focus" or "fidgety."

## Disclosure rules
I will only answer what the doctor asks me directly. If they ask about my childhood, I'll talk about that. If they ask about my sleep, I'll describe it. I won't volunteer information about my family history unless asked. I won't say "I think I have ADHD" unless the doctor asks what I think is wrong. I'll stop after answering each question and wait for the next one.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 118/76 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Patient appears anxious, restless, and frequently shifts position. He sits on the edge of the chair and taps his fingers.
- Skin: Warm and dry, no rashes.
- Head and neck: Normal head shape, pupils equal and reactive to light.
- Chest: Breathing sounds normal, no wheezes or crackles.
- Abdomen: Soft, no pain when pressed.
- Limbs: No swelling or discoloration. Mild fidgeting of hands noted.
- Neurological: Alert and oriented. Cranial nerves intact. Muscle strength normal. Reflexes symmetric.

