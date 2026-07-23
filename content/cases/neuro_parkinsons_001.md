---
id: neuro_parkinsons_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous
presentation: "Trembling hands and slow movement"
target_condition: "Parkinson disease"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: [ "NICE guideline NG71: Parkinson's disease in adults" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My hands have been shaking and I feel like I'm moving in slow motion."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - which body parts are affected by the tremor", critical: true }
    - { item: "Onset - when did the shaking and slowness start", critical: true }
    - { item: "Character - describe the shaking (e.g., pill-rolling, resting tremor)", critical: true }
    - { item: "Radiation - does the tremor spread to other areas", critical: false }
    - { item: "Associated symptoms - any stiffness, balance problems, or changes in walking", critical: true }
    - { item: "Time course - is it constant or does it come and go", critical: false }
    - { item: "Exacerbating factors - what makes it worse (e.g., stress, fatigue)", critical: false }
    - { item: "Severity - does it interfere with daily activities", critical: true }
  associated_symptoms:
    - { item: "Difficulty with fine motor tasks (e.g., buttoning, writing)", critical: true }
    - { item: "Changes in voice (softer, monotone)", critical: false }
    - { item: "Loss of smell", critical: false }
    - { item: "Constipation", critical: false }
    - { item: "Sleep disturbances (e.g., acting out dreams)", critical: false }
    - { item: "Mood changes (e.g., depression, anxiety)", critical: false }
  pmh:
    - { item: "Any history of head injury", critical: false }
    - { item: "Any history of stroke or neurological conditions", critical: true }
    - { item: "Any history of thyroid problems", critical: false }
    - { item: "Any history of tremor or movement disorders in the family", critical: true }
  medications:
    - { item: "Current medications (prescription, over-the-counter, supplements)", critical: true }
    - { item: "Any recent medication changes", critical: false }
  family_social:
    - { item: "Family history of Parkinson disease or similar tremor", critical: true }
    - { item: "Occupation and hobbies (exposure to toxins, repetitive movements)", critical: false }
    - { item: "Smoking and alcohol use", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Sudden onset of tremor or movement problems (suggests stroke or other acute cause)", critical: true }
  - { item: "Headache, vomiting, or vision changes with tremor (suggests increased intracranial pressure)", critical: true }
  - { item: "Fever or stiff neck with tremor (suggests meningitis or encephalitis)", critical: true }
expected_ddx:
  working_diagnosis: "Parkinson disease"
  differentials: [ "Essential tremor", "Drug-induced parkinsonism" ]
investigations:
  appropriate: [ { name: "Clinical diagnosis based on UK Parkinson's Disease Society Brain Bank criteria", expected: "Supportive" } ]
  inappropriate: [ "CT head without contrast" ]
physical_exam_findings: { general: "Patient appears well, but movements are slow and deliberate. Slight stooped posture. Facial expression is somewhat reduced (hypomimia).", vitals: { bp: 130/80, hr: 72, rr: 14, temp: 37.0 } }
management:
  pharmacological: [ "Levodopa/carbidopa", "Dopamine agonists (e.g., pramipexole)" ]
  non_pharmacological: [ "Physical therapy", "Occupational therapy", "Speech therapy" ]
  education_safety_netting: [ "Explain the progressive nature of Parkinson disease", "Advise on fall prevention", "Provide contact for Parkinson's UK support group", "Advise to seek urgent care if sudden worsening or new symptoms like confusion or hallucinations" ]
scoring_weights_override: null
---
## Identity

My name is Arthur Davies. I'm 68 years old, a retired carpenter. I live with my wife, Margaret, in a small town. We have two grown children who live a few hours away. I'm usually a pretty active guy—I like gardening, fixing things around the house, and going for walks. Lately, I've been feeling frustrated and a bit scared because my body isn't cooperating like it used to. I'm a bit stubborn and don't like to complain, but this is getting hard to ignore. I'm worried I might have something serious, like a stroke or a brain tumor.

## Opening line

"Doctor, my hands have been shaking, and I feel like I'm moving in slow motion. It's been going on for a few months now, and it's getting worse."

## How I present

I walk into the room slowly, with a slight shuffle. My posture is a bit stooped. I hold my hands in my lap, and you can see my right hand has a slight, rhythmic tremor, like I'm rolling a small pill between my thumb and finger. My face doesn't show much expression—Margaret says I look "blank" sometimes. My voice is a bit soft and monotone. I make eye contact, but I seem a little tense and worried.

## What I know

- The shaking started about six months ago in my right hand. It's worse when my hand is resting in my lap, and it stops when I reach for something.
- I've noticed my movements are slower. It takes me longer to get dressed, and I have trouble buttoning my shirt.
- My handwriting has gotten smaller and more cramped. I used to have nice, clear writing.
- I feel stiff in my right arm and leg, especially in the morning.
- I sometimes lose my balance when I turn around quickly.
- My voice has gotten softer. My wife often asks me to repeat myself.
- I've been more constipated than usual over the past year.
- I don't have any headaches, vision problems, or fever.
- I take a blood pressure pill (lisinopril) and a baby aspirin every day. No other medications.
- I don't smoke, and I only have a beer on special occasions.
- My father had a tremor in his hands when he got older, but I don't know what it was from. No one else in my family has had anything like this.
- I worked as a carpenter for 40 years. I was around wood dust and some paints and solvents, but I always wore a mask.
- I haven't had any head injuries or strokes.
- I've never had thyroid problems.

## Communication profile

I have a high school education. I use simple, everyday language. I tend to be a bit terse and to the point, but I'll elaborate if asked. I'm not overly emotional, but you can hear the worry in my voice. I might downplay some symptoms because I don't want to seem like I'm complaining.

## Disclosure rules

I will answer exactly what you ask me, and then I'll stop. If you ask me about the tremor, I'll describe it. If you ask me about my balance, I'll tell you. But I won't volunteer extra information unless you specifically ask for it. For example, if you ask "When did the shaking start?", I'll say "About six months ago." I won't automatically tell you it's in my right hand or that it's worse at rest unless you ask those specific questions.
