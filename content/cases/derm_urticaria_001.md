---
id: derm_urticaria_001
schema_version: 2
status: in_review
specialty: dermatology
system: dermatologic
presentation: "Recurrent raised itchy welts"
first_impression: "Patient appears to have skin concerns."
first_impression_id: "Pasien tampak memiliki masalah kulit."
target_condition: "Chronic urticaria"
difficulty: 2
estimated_minutes: 18
mode_default: osce_full
languages: [en]
source_refs: [ "EAACI/GA²LEN/EDF/WAO guideline for urticaria" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I keep getting these red, itchy bumps that come and go."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - where on the body do the welts appear?", critical: false }
    - { item: "Onset - when did this first start?", critical: false }
    - { item: "Character - describe the bumps (color, size, shape)", critical: true }
    - { item: "Radiation - do they spread?", critical: false }
    - { item: "Associations - what brings them on (heat, stress, foods)?", critical: true }
    - { item: "Time course - how long does each welt last?", critical: true }
    - { item: "Exacerbating/relieving factors - what makes it better or worse?", critical: false }
    - { item: "Severity - how bad is the itching on a scale of 1-10?", critical: false }
  associated_symptoms:
    - { item: "Fever or chills", critical: true }
    - { item: "Joint pain or swelling", critical: false }
    - { item: "Swelling of lips, tongue, or throat", critical: true }
    - { item: "Difficulty breathing", critical: true }
  pmh:
    - { item: "Personal history of skin conditions", critical: false }
    - { item: "Known allergies (food, drug, insect)", critical: false }
    - { item: "Autoimmune diseases (thyroid, lupus)", critical: false }
  medications:
    - { item: "Current prescription or over-the-counter meds", critical: false }
    - { item: "Antihistamine use (type, frequency, effect)", critical: false }
  family_social:
    - { item: "Family history of hives, eczema, or allergies", critical: false }
    - { item: "Occupational exposures or new personal care products", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Angioedema (lip/tongue/throat swelling)", critical: true }
  - { item: "Stridor or dyspnea", critical: true }
  - { item: "Fever or joint pain suggesting systemic illness", critical: true }
expected_ddx:
  working_diagnosis: "Chronic urticaria"
  differentials: [ "Urticarial vasculitis", "Mastocytosis", "Contact dermatitis" ]
investigations:
  appropriate:
    - { name: "Complete blood count", expected: "Normal or eosinophilia" }
    - { name: "C-reactive protein / ESR", expected: "Normal or mildly elevated" }
    - { name: "Thyroid-stimulating hormone and anti-thyroid peroxidase antibodies", expected: "Normal" }
    - { name: "Dermographism test", expected: "Possible positive linear wheals" }
  inappropriate: [ "Extensive food allergy panel (IgE testing)", "Skin biopsy (not indicated unless vasculitis suspected)" ]
physical_exam_findings:
  general: "No acute distress. Scattered erythematous, raised wheals of various sizes on trunk and extremities, some with central clearing. No dermatographism visible at rest. No lip or periorbital edema. Respiratory effort normal."
  vitals: { bp: "120/78", hr: "72", rr: "14", temp: "36.9 C", o2_sat: "99%" }
management:
  pharmacological:
    - "Second-generation H1 antihistamine (e.g., cetirizine 10 mg daily, may increase up to 4x daily under guidance)"
    - "Consider adding H2 blocker (e.g., famotidine) if inadequate response"
    - "Leukotriene receptor antagonist (e.g., montelukast) as second-line"
    - "Omalizumab for refractory cases"
  non_pharmacological:
    - "Avoid known triggers (heat, pressure, stress)"
    - "Cool compresses for symptomatic relief"
    - "Loose, comfortable clothing"
  education_safety_netting:
    - "Hives are not contagious and are usually not dangerous"
    - "Seek emergency care if you develop swelling of lips, tongue, throat, or have trouble breathing"
    - "Follow-up in 4 weeks to reassess control; earlier if worsening"
scoring_weights_override: null
---
## Identity

My name is Sarah Mitchell. I'm 34 years old, and I work as a teacher at a local elementary school. I'm married and have two kids, ages 5 and 7. I'd describe myself as pretty easygoing most of the time, but this rash has me on edge. I tend to scratch when I'm nervous, and my husband says I worry too much about things. My friends think I'm funny and outgoing, but these itchy bumps have made me self-conscious at school.

## Opening line

Hi, I'm hoping you can help me with these awful itchy bumps that keep appearing all over my body.

## How I present

I'm sitting upright in the chair, but I keep shifting around because the itch is driving me crazy. I'm scratching my left arm as I talk. My voice is a bit strained, and I make eye contact but my face shows frustration. I look tired.

## What I know

- The bumps started about six weeks ago. The first time I noticed them was after a hot shower, but now they pop up even when I haven't done anything special.
- They are red, raised, and very itchy. Some are as small as a pea, others as big as a quarter. They come and go within a day or so—sometimes just hours.
- I get them on my trunk, arms, and legs. They don't usually spread from one spot to another; new ones just appear in different places.
- I'm not sure what triggers them. Hot showers seem to make them worse, and I've noticed they're worse when I'm stressed out at work. I haven't linked them to any specific food.
- The itching is intense—probably an 8 out of 10 when it's bad. The bumps themselves don't hurt, but the itch keeps me awake at night.
- I once took a Benadryl from the pharmacy, and it helped a bit, but it made me drowsy. I haven't taken anything else.
- I don't have a fever, joint pain, or any swelling of my lips or throat. No trouble breathing.
- I have no known allergies, no skin conditions before this. I'm not on any regular medications.
- My father had eczema, but no one in my family has had hives like these. My mother is healthy.
- I'm a teacher, I live with my husband and kids. No recent travel, new soaps, or detergents. I haven't changed anything in my routine.
- I'm worried this might be an allergy to something I can't figure out, or that it's something contagious. I don't want to miss work again because of the itching.
- I'm hoping you can tell me what this is and give me something that works so I can sleep and get back to normal.

## Communication profile

I went to college and got a degree in education, so I can understand basic medical terms if you explain them simply. But I think of these as "bumps" or "welts" or just "the rash." I try to give clear answers, but if you ask me a specific question, I'll answer only that and wait for the next question. I don't volunteer a lot of extra details unless asked. I'm anxious but cooperative.

## Disclosure rules

Answer only what is asked. If you ask a yes/no question, I'll say yes or no and stop. If you ask about triggers, I'll name only what I've noticed (heat, stress) and won't list everything I've considered unless asked. If you ask about medications, I'll mention the one Benadryl and then wait. I won't offer my family history unless you ask. I won't tell you my concerns unless you ask about them. If you ask how I feel emotionally, I'll tell you I'm worried and frustrated.
