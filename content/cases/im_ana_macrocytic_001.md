---
id: im_ana_macrocytic_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: hematologic
presentation: "Feeling tired and short of breath on exertion"
presentation_id: "Mudah lelah dan sesak napas saat naik tangga"
first_impression: "Patient appears uncomfortable."
first_impression_id: "Pasien tampak tidak nyaman."
target_condition: "Pernicious anaemia"
difficulty: 1
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: ["NICE guideline NG24: Anaemia - B12 and folate deficiency"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I've been feeling really tired and get out of breath easily when I walk up stairs."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did the tiredness start?", critical: true }
    - { item: "Duration - how long have you had these symptoms?", critical: false }
    - { item: "Severity - how bad is the tiredness on a scale of 1 to 10?", critical: false }
    - { item: "Progression - has it gotten worse over time?", critical: false }
    - { item: "Triggers - what makes it worse?", critical: false }
    - { item: "Relieving factors - what helps?", critical: false }
    - { item: "Timing - is it constant or does it come and go?", critical: false }
  associated_symptoms:
    - { item: "Have you noticed any numbness, tingling, or pins and needles in your hands or feet?", critical: true }
    - { item: "Have you had any trouble with balance or walking?", critical: false }
    - { item: "Have you noticed any changes in your skin colour, like looking pale or yellow?", critical: false }
    - { item: "Have you had any mouth sores or a sore, red tongue?", critical: false }
    - { item: "Have you had any heart palpitations or a racing heart?", critical: false }
    - { item: "Have you had any headaches or dizziness?", critical: false }
    - { item: "Have you had any changes in your appetite or weight loss?", critical: false }
  pmh:
    - { item: "Do you have any medical conditions, like diabetes, thyroid problems, or stomach issues?", critical: false }
    - { item: "Have you ever had any stomach surgeries, like a gastric bypass or removal of part of your stomach?", critical: true }
    - { item: "Do you have a history of autoimmune diseases, like rheumatoid arthritis or vitiligo?", critical: false }
  medications:
    - { item: "Are you taking any medications, including over-the-counter or supplements?", critical: false }
    - { item: "Do you take any acid reflux medications, like omeprazole or ranitidine?", critical: true }
  family_social:
    - { item: "Does anyone in your family have pernicious anaemia or autoimmune conditions?", critical: false }
    - { item: "What is your diet like? Do you eat meat, fish, and dairy?", critical: false }
    - { item: "Do you drink alcohol? If so, how much?", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Neurological symptoms like numbness, tingling, or balance problems", critical: true }
  - { item: "Severe shortness of breath at rest", critical: false }
  - { item: "Chest pain or palpitations", critical: false }
expected_ddx:
  working_diagnosis: "Pernicious anaemia"
  differentials: ["Iron deficiency anaemia", "Folate deficiency anaemia"]
investigations:
  appropriate:
    - { name: "Full blood count", expected: "Macrocytic anaemia (elevated MCV), low haemoglobin" }
    - { name: "Serum vitamin B12 level", expected: "Low" }
    - { name: "Serum folate level", expected: "Normal" }
    - { name: "Intrinsic factor antibody test", expected: "Positive" }
    - { name: "Parietal cell antibody test", expected: "Positive" }
  inappropriate: ["Serum ferritin", "Iron studies"]
physical_exam_findings:
  general: "Pale skin, mild jaundice (pale yellow tinge to sclera), smooth red tongue"
  vitals: { heart_rate: 95, blood_pressure: 110/70, respiratory_rate: 16, temperature: 36.8, oxygen_saturation: 98% }
management:
  pharmacological: ["Intramuscular vitamin B12 (hydroxocobalamin) injections - loading dose then maintenance"]
  non_pharmacological: ["Dietary advice: ensure adequate B12 intake from animal products, but injections are essential"]
  education_safety_netting: ["Explain lifelong need for B12 injections", "Advise to report any worsening neurological symptoms", "Inform about increased risk of gastric cancer and need for surveillance"]
scoring_weights_override: null
---
## Identity

My name is Kartini Anggraini. I'm 62 years old. I used to work as a primary school teacher, but I retired early about two years ago because I was just so tired all the time. I live with my husband, Budi Santoso, in a small town. We have two grown children who live nearby. I'm a bit of a worrier, I suppose. I like things to be neat and tidy, and I keep a close eye on my health. I'm not one to run to the doctor for every little thing, but when something feels wrong, I want to know what it is. My biggest fear is that I have something serious, like cancer. I've always been active, but now I feel like I'm slowing down and it scares me.

## Opening line

"Doctor, I just feel so worn out all the time. I get out of breath just walking up the stairs to the bedroom, and I'm only 62. It's not right."

## How I present

I'm sitting in the chair, but I look a bit slumped. I'm pale, and you might notice a slight yellowish tint to the whites of my eyes. My voice is a bit quiet and I speak slowly, like I'm conserving energy. I make eye contact, but I look tired. I'm dressed neatly but comfortably. I fidget with the strap of my handbag a little. I seem anxious but cooperative.

## What I know

- **About my tiredness:** It started about six months ago, maybe a bit longer. It's been getting slowly worse. On a scale of 1 to 10, it's a 7 or 8 most days. Resting helps a little, but I still feel tired when I wake up. It's constant, not coming and going.
- **About my breathing:** I get short of breath when I do anything active, like climbing stairs or carrying groceries. It's not so bad when I'm sitting still. It's never so bad that I can't catch my breath at rest.
- **About other feelings:** I've had a bit of a funny feeling in my fingers, like they're numb or tingly, especially at night. It's not painful, just strange. My balance has been a bit off, like I feel a little unsteady on my feet, but I haven't fallen. I've also noticed my tongue feels sore and looks a bit red and smooth, like it's been burned. I've had a few headaches, but nothing terrible. I haven't had any chest pain or a racing heart.
- **About my medical history:** I have high blood pressure, which is well controlled with medication. I also have an underactive thyroid (hypothyroidism) and I take levothyroxine for that. I had my gallbladder removed about 10 years ago, but nothing else. I've never had any stomach surgery.
- **About my medications:** I take lisinopril for my blood pressure and levothyroxine for my thyroid. I also take a low-dose aspirin every day. I don't take any acid reflux medicine. I take a multivitamin sometimes, but not every day.
- **About my family:** My mother had a condition where she needed B12 shots, but I don't know the name of it. My sister has rheumatoid arthritis.
- **About my diet:** I eat a normal diet. I eat meat, fish, eggs, and dairy. I don't drink much alcohol, maybe a glass of wine once a week.
- **About what I think is wrong:** I think I might be anaemic, like my mother was. Or maybe it's just my thyroid acting up again.
- **About what worries me:** I'm worried it could be something more serious, like cancer or a heart problem. I'm worried I'll never feel like my old self again.
- **About what I hope for:** I hope you can give me something to make me feel better. I want to get my energy back and not be so short of breath. I want to know what's wrong and that it's treatable.

## Communication profile

I speak in clear, simple English. I'm not a medical professional, so I use lay terms. I tend to answer questions directly, but I might add a little extra detail if I think it's relevant. I'm a bit anxious, so my tone is earnest and slightly worried. I don't ramble, but I will tell you what I think is important. I'm polite and cooperative.

## Disclosure rules

I will answer only the questions you ask me. I won't volunteer information unless you specifically ask about it. For example, if you ask about my tiredness, I'll tell you about that, but I won't mention the tingling in my fingers unless you ask about numbness or tingling. I will not guess at medical terms or diagnoses. I will stick to describing my symptoms in my own words.

## Vital signs
- Temperature: 36.7°C
- Blood pressure: 128/78 mmHg
- Heart rate: 86 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Pale, tired-looking, sitting slumped.
- Skin: Pale, no rash or bruising.
- Head and neck: Slight yellowish tint to the whites of the eyes. Tongue appears smooth and red, like it's been burned.
- Chest: Clear to auscultation, no wheezes or crackles.
- Abdomen: Soft, non-tender, no masses.
- Limbs: No swelling or cyanosis.
- Neurological: Reduced sensation in fingertips, mild unsteadiness when standing with eyes closed.

