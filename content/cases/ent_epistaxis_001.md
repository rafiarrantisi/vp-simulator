---
id: ent_epistaxis_001
schema_version: 2
status: in_review
specialty: ent
system: ent
presentation: "Nosebleed"
first_impression: "Patient appears to have ear, nose, or throat discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan telinga, hidung, atau tenggorokan."
target_condition: "Epistaxis"
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages: [en]
source_refs: [ "AAO-HNS Clinical Practice Guideline: Epistaxis" ]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "I have a nosebleed that won't stop."
anamnesis_checklist:
  hpi_socrates:
    - { item: "When did the nosebleed start?", critical: true }
    - { item: "Which nostril is bleeding?", critical: false }
    - { item: "How long did the bleeding last?", critical: true }
    - { item: "How much blood did you lose?", critical: false }
    - { item: "What were you doing when it started?", critical: false }
    - { item: "Did you have any trauma to the nose?", critical: true }
    - { item: "Have you had nosebleeds before?", critical: false }
  associated_symptoms:
    - { item: "Do you have any pain?", critical: false }
    - { item: "Do you feel lightheaded or dizzy?", critical: true }
    - { item: "Do you have any headache?", critical: false }
    - { item: "Do you have any difficulty breathing?", critical: false }
  pmh:
    - { item: "Do you have high blood pressure or liver disease?", critical: false }
    - { item: "Do you have a bleeding disorder?", critical: true }
    - { item: "Have you ever had surgery on your nose?", critical: false }
  medications:
    - { item: "Are you taking any blood thinners like aspirin or warfarin?", critical: true }
    - { item: "Are you taking any other medications?", critical: false }
  family_social:
    - { item: "Does anyone in your family have a bleeding disorder?", critical: false }
    - { item: "Do you smoke or drink alcohol?", critical: false }
  ice_fife:
    - { item: "Ideas – what do you think is causing this?", critical: true }
    - { item: "Concerns – what worries you about this nosebleed?", critical: true }
    - { item: "Expectations – what do you hope I can do for you today?", critical: false }
    - { item: "Feelings – how does this make you feel?", critical: false }
    - { item: "Impact – how has this affected your daily life?", critical: false }
red_flags:
  - { item: "Are you taking blood thinners?", critical: true }
  - { item: "Have you had a recent head injury?", critical: false }
  - { item: "Do you have a history of easy bruising or bleeding?", critical: true }
  - { item: "Do you feel faint or lightheaded?", critical: true }
expected_ddx:
  working_diagnosis: "Epistaxis"
  differentials: [ "Trauma", "Coagulopathy" ]
investigations:
  appropriate: []
  inappropriate: []
physical_exam_findings:
  general: "Not applicable for anamnesis mode"
  vitals: {}
management:
  pharmacological: []
  non_pharmacological: []
  education_safety_netting: []
scoring_weights_override: null
---
## Identity
My name is Sarah Johnson. I’m 32 years old, and I work as an elementary school teacher. I’m married to Mark, and we have two kids—a boy and a girl. I’m usually a pretty calm person, but when it comes to my health, I can get a bit nervous. I tend to overthink things, and I’m scared that even a small symptom might be something serious. I’m a bit of a worrier, and I always carry tissues in my purse because I hate messes.

## Opening line
I woke up this morning with a nosebleed that just won’t stop, and I’m really worried.

## How I present
I’m sitting upright on the exam chair, pressing a tissue against my left nostril. My voice sounds a bit nasally because I’m trying to keep my head tilted forward. I’m making eye contact, but my eyes are wide and I look tense. I’m fidgeting with the tissue in my hand. I speak quickly, clearly anxious.

## What I know
- The nosebleed started about 30 minutes ago, right after I woke up. I was still lying in bed.
- It’s coming from my left nostril. The bleeding is steady but not gushing and hasn’t stopped yet.
- I’ve lost a few teaspoons of blood, maybe a little more. It’s not a huge amount, but it’s a lot for me.
- I was sleeping when it started. I didn’t bump my nose or pick it.
- I’ve had occasional nosebleeds before, especially in dry weather, but they always stopped after a few minutes. This one is different.
- I don’t have any pain, not even in my nose. I don’t feel dizzy or lightheaded.
- I don’t take any blood thinners. My only medication is birth control pills.
- I don’t have any medical conditions like high blood pressure or liver problems. I’ve never been told I have a bleeding disorder.
- No one in my family has a bleeding disorder. I don’t smoke, and I only drink alcohol on rare occasions.
- I think this might be a sign of something serious, like a brain tumor. I heard that can cause nosebleeds.
- I’m worried it won’t stop, and I’m scared it could be a sign of a bigger problem.
- I just want the bleeding to stop, and I want to know what’s wrong so I can stop worrying.

## Communication profile
I have a high school education and use simple, everyday words. I tend to talk in short sentences and get straight to the point. I’m a bit anxious, so I might repeat myself or sound a little dramatic. I’m not shy—I’ll tell you exactly what I’m feeling.

## Disclosure rules
I will answer only the question you ask me, and then I’ll stop. I won’t volunteer extra information unless you specifically ask for it.
