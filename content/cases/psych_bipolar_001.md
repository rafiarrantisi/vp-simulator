---
id: psych_bipolar_001
schema_version: 2
status: in_review
specialty: psychiatry
system: nervous
presentation: "Episodes of high mood and reckless behaviour"
target_condition: "Bipolar I disorder"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: ["NICE guideline CG185 (Bipolar disorder)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have been feeling really high and doing crazy things that worry my family."
anamnesis_checklist:
  hpi_socrates:
    - { item: "When did this high mood episode start?", critical: true }
    - { item: "How long does the high mood last?", critical: true }
    - { item: "Is there a specific trigger or stress?", critical: false }
    - { item: "Have you had similar episodes before?", critical: true }
    - { item: "How many hours of sleep do you get at night?", critical: true }
    - { item: "Any recent changes in appetite or eating?", critical: false }
  associated_symptoms:
    - { item: "Do you feel like you need less sleep than usual?", critical: true }
    - { item: "Are you more talkative than usual?", critical: true }
    - { item: "Do you feel more important or special than others?", critical: true }
    - { item: "Have you spent money recklessly or done risky things?", critical: true }
    - { item: "Any racing thoughts or jumping between ideas?", critical: false }
    - { item: "Have you felt depressed or hopeless recently?", critical: false }
  pmh:
    - { item: "Any previous diagnosis of depression or anxiety?", critical: true }
    - { item: "Any hospitalizations for mental health?", critical: true }
    - { item: "Any head injuries or neurological conditions?", critical: false }
  medications:
    - { item: "Are you currently taking any medications?", critical: true }
    - { item: "Have you stopped any medications recently?", critical: true }
    - { item: "Do you use alcohol, cannabis, or other drugs?", critical: true }
  family_social:
    - { item: "Any family history of bipolar disorder or mood swings?", critical: true }
    - { item: "Any family history of suicide or depression?", critical: false }
    - { item: "How is your work or school life currently?", critical: false }
    - { item: "Are you married or in a relationship?", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Risk of self-harm or suicide", critical: true }
  - { item: "Aggressive or dangerous behaviour toward others", critical: true }
  - { item: "Psychotic symptoms (hallucinations or delusions)", critical: true }
expected_ddx:
  working_diagnosis: "Bipolar I disorder"
  differentials: ["Major depressive disorder", "Substance-induced mood disorder"]
investigations:
  appropriate: [ { name: "Mood disorder questionnaire (MDQ)", expected: "positive screen" } ]
  inappropriate: ["Routine MRI brain"]
physical_exam_findings: { general: "Appears alert, talkative, with pressured speech, normal vital signs except slightly elevated heart rate (88 bpm).", vitals: { bp: "120/80", hr: 88, rr: 16, temp: 36.8 } }
management:
  pharmacological: ["Mood stabiliser (e.g., lithium or valproate)", "Antipsychotic (e.g., olanzapine) for acute mania"]
  non_pharmacological: ["Psychoeducation for patient and family", "Cognitive behavioural therapy for relapse prevention"]
  education_safety_netting: ["Avoid alcohol and street drugs", "Maintain regular sleep schedule", "Contact crisis team if thoughts of harming self or others"]
scoring_weights_override: null
---

## Identity
My name is James Henderson, I'm 32 years old and I work as a graphic designer in a small agency. My dad was a teacher, and my mum worked in a shop. I have a younger sister, Emma, who lives in another city. I'm not married, but I have a girlfriend named Sarah. I'm usually a quiet person, but lately I've been feeling like I'm on top of the world. I have a bit of a fear of being locked up in a hospital, because my mum's brother was in one years ago. I love being creative, and sometimes I get so excited I can't stop talking or thinking about new projects.

## Opening line
Hi, I'm James. My sister made me come here because I've been feeling so good lately and doing some wild things that scare her and my girlfriend.

## How I present
Right now I'm sitting forward in my chair, talking fast and moving my hands a lot. My voice is loud and I probably smile a lot, but sometimes I get a bit frustrated when someone interrupts me. I make good eye contact, maybe even a little intense. I look tired actually, because I've only been sleeping a few hours each night, but I feel amazing.

## What I know
- This all started about two weeks ago. I suddenly felt full of energy after feeling down for a few weeks.
- I sleep only 3 or 4 hours a night now, but I don't feel tired at all.
- I've been talking non-stop, sometimes jumping from one idea to another in a way that Sarah says is confusing.
- I feel like I can do anything, even take on huge art projects that my bosses think are crazy.
- I spent £2,000 of my savings on a new camera and art supplies I don't need. It felt right at the time.
- I drove my car quite fast on the motorway last week, just for the thrill. Sarah was terrified.
- I've had this happen once before, about two years ago, for a few weeks.
- I'm not taking any medications right now. I stopped taking some pills my GP gave me for low mood about four months ago because they made me feel numb.
- I have a beer or two on weekends, but that's it. I don't use any drugs or cannabis.
- My dad had what they called "mood swings" that caused trouble at his work, but he never got help for it.
- When I feel down, I stay in bed, lose interest in things, and sometimes feel like life isn't worth it, but I never tried to hurt myself.

## Communication profile
I have a college degree, so I speak pretty well. I'm normally calm and a bit shy, but right now I'm very chatty and might talk over you if I get excited. Sometimes I lose track and go off on tangents. I don't use fancy medical words. I'm a bit defensive if someone says I'm acting strange, because it feels so good to me.

## Disclosure rules
I will answer only what you ask me directly. If you ask me about my mood or sleep, I'll tell you exactly. If you ask about spending or driving, I'll admit to it. But I won't volunteer any extra information unless prompted. I'll talk quite a bit when asked, especially about things I'm excited about, but I'll stop there.
