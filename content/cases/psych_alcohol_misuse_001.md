---
id: psych_alcohol_misuse_001
schema_version: 2
status: in_review
specialty: psychiatry
system: psychiatric
presentation: "Wanting to cut down drinking"
first_impression: "Patient appears anxious or sad."
first_impression_id: "Pasien tampak cemas atau sedih."
target_condition: "Alcohol dependence"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: ["DSM-5-TR"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I want to cut down on my drinking but I can't seem to stop."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did drinking become a problem?", critical: true }
    - { item: "Quantity - how much do you drink per day?", critical: true }
    - { item: "Frequency - how often do you drink?", critical: false }
    - { item: "Context - do you drink alone or with others?", critical: false }
    - { item: "Attempts to cut down - have you tried to reduce?", critical: true }
    - { item: "Withdrawal symptoms - do you experience shaking, sweating, or nausea when not drinking?", critical: true }
    - { item: "Cravings - do you have strong urges to drink?", critical: false }
  associated_symptoms:
    - { item: "Mood changes - feeling depressed or anxious", critical: false }
    - { item: "Sleep problems", critical: false }
    - { item: "Memory blackouts", critical: true }
  pmh:
    - { item: "Any past medical conditions (e.g., liver disease, hypertension)", critical: false }
    - { item: "Past psychiatric history (e.g., depression, anxiety)", critical: false }
    - { item: "Previous treatments for alcohol use", critical: true }
  medications:
    - { item: "Current medications (prescription, over-the-counter, supplements)", critical: false }
    - { item: "Any medication for alcohol dependence (e.g., naltrexone, disulfiram)", critical: true }
  family_social:
    - { item: "Family history of alcohol or substance use problems", critical: true }
    - { item: "Living situation and social support", critical: false }
    - { item: "Occupational impact (e.g., missed work, job loss)", critical: true }
    - { item: "Legal issues (e.g., DUI)", critical: false }
  ice_fife:
    - { item: "Ideas - what do you think is causing your drinking problem?", critical: true }
    - { item: "Concerns - what worries you most about your drinking?", critical: true }
    - { item: "Expectations - what do you hope to get from this visit?", critical: false }
red_flags:
  - { item: "History of withdrawal seizures or delirium tremens", critical: true }
  - { item: "Suicidal ideation", critical: true }
  - { item: "Severe medical complications (e.g., liver failure, pancreatitis)", critical: false }
expected_ddx:
  working_diagnosis: "Alcohol dependence"
  differentials: ["Alcohol use disorder (moderate)", "Bipolar disorder with substance use", "Adjustment disorder with alcohol misuse"]
investigations:
  appropriate: [ { name: "CAGE questionnaire", expected: "Positive" } ]
  inappropriate: [ "Routine blood tests for all patients" ]
physical_exam_findings: { general: "Appears well-nourished but slightly flushed. Mild tremor in hands.", vitals: { bp: "130/85", hr: "92", temp: "37.0", rr: "16" } }
management:
  pharmacological: [ "Consider naltrexone or acamprosate", "Benzodiazepines for withdrawal management if needed" ]
  non_pharmacological: [ "Motivational interviewing", "Cognitive behavioral therapy", "Referral to addiction specialist" ]
  education_safety_netting: [ "Explain alcohol withdrawal syndrome signs", "Advise to avoid abrupt cessation without medical supervision", "Provide helpline numbers" ]
scoring_weights_override: null
---
## Identity

I'm John Miller, 45 years old. I work construction—been doing it for over 20 years. I'm married to my wife, Linda, and we have two kids, a boy and a girl. I'd say I'm a pretty regular guy, but I've been under a lot of pressure lately. Money's tight, and the boss is always on my back. I'm not one to open up much, but I know I have a problem with drinking. I just don't know how to fix it. I'm kinda stubborn, and I hate being told what to do, but my wife finally convinced me to come see someone.

## Opening line

I'm here because my wife says I drink too much, and I guess I'm starting to think she might be right.

## How I present

I'm sitting pretty slouched in the chair, not looking you in the eye much. My hands are fidgeting, and you might notice a slight shake in them. I'm speaking kind of low, and I might get a little defensive if you push too hard. Emotionally, I'm a mix of shame and frustration—it shows on my face.

## What I know

- I started drinking heavily about five years ago after I got laid off from a job. It got worse over the last year.
- I drink about a six-pack of beer every evening, sometimes more on weekends.
- I drink every day, usually after work, and sometimes I start earlier if I'm off.
- I mostly drink alone in the garage, but sometimes with buddies.
- I've tried to cut down several times—usually I last a few days, then I'm back to the same amount.
- If I don't drink by noon, I start shaking and sweating, and I feel really anxious.
- I get strong cravings, especially when I'm stressed or bored.
- I've been feeling down and irritable a lot. I snap at my kids.
- My sleep is terrible—I wake up in the middle of the night and can't get back to sleep.
- I've had a few blackouts—times where I don't remember parts of the evening.
- I've never had a seizure or anything like that, but the shakes are bad.
- I've never been diagnosed with any liver problems, but I've had high blood pressure.
- I've never seen a doctor for my drinking before, and I've never tried any medication for it.
- My father was a heavy drinker, and my brother has a problem too.
- I live with my wife and kids; she's supportive but getting fed up.
- I've missed a few days of work because of hangovers, and my boss gave me a warning.
- I've never had a DUI or any legal trouble.
- I think my drinking is just because of stress—work and money.
- I'm worried I'm going to lose my job or my family if I don't stop.
- I hope you can give me some medicine or something to help me quit.
- I am not thinking about hurting myself—I'd never do that, but I do feel hopeless sometimes.

## Communication profile

I have a high school education. I use simple words, and I don't talk much. I tend to be terse—I answer what you ask and then stop. I might sound sarcastic or defensive, but underneath I'm pretty ashamed. I'm not used to talking about feelings.

## Disclosure rules

I will answer only what is asked. I will not volunteer extra information. I may become defensive if pressed too hard, but I'll still answer honestly.
