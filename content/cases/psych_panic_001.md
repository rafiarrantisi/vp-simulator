---
id: psych_panic_001
schema_version: 2
status: in_review
specialty: psychiatry
system: nervous
presentation: "Sudden attacks of overwhelming fear"
presentation_id: "Serangan tiba-tiba rasa takut luar biasa, seperti akan mati atau gila"
first_impression: "Patient appears anxious or sad."
first_impression_id: "Pasien tampak cemas atau sedih."
target_condition: "Panic disorder"
difficulty: 1
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: [ "DSM-5-TR" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I keep having these sudden attacks where I feel like I'm dying or losing my mind."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did the first attack happen", critical: true }
    - { item: "Location - where do attacks occur", critical: false }
    - { item: "Duration - how long does each attack last", critical: true }
    - { item: "Character - describe the feeling during an attack", critical: true }
    - { item: "Aggravating factors - what triggers an attack", critical: true }
    - { item: "Relieving factors - what helps you calm down", critical: false }
    - { item: "Timing - how often do attacks happen", critical: true }
    - { item: "Severity - rate the fear on a scale of 0-10", critical: false }
  associated_symptoms:
    - { item: "Heart racing or pounding", critical: true }
    - { item: "Shortness of breath or feeling smothered", critical: true }
    - { item: "Chest pain or discomfort", critical: true }
    - { item: "Sweating", critical: false }
    - { item: "Trembling or shaking", critical: false }
    - { item: "Nausea or abdominal distress", critical: false }
    - { item: "Dizziness or lightheadedness", critical: true }
    - { item: "Chills or hot flushes", critical: false }
    - { item: "Numbness or tingling sensations", critical: false }
    - { item: "Fear of dying", critical: true }
    - { item: "Fear of losing control or going crazy", critical: true }
    - { item: "Feeling detached from yourself or reality", critical: false }
  pmh:
    - { item: "Any medical conditions like heart problems, asthma, or thyroid issues", critical: true }
    - { item: "Any past mental health problems", critical: true }
    - { item: "Any hospitalizations or surgeries", critical: false }
  medications:
    - { item: "Current medications, including over-the-counter and supplements", critical: true }
    - { item: "Any caffeine, alcohol, or drug use", critical: true }
  family_social:
    - { item: "Family history of anxiety or panic attacks", critical: true }
    - { item: "Recent life stressors or major changes", critical: true }
    - { item: "Occupation and living situation", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Suicidal thoughts or self-harm", critical: true }
  - { item: "Chest pain with radiation, shortness of breath at rest (cardiac red flag)", critical: true }
  - { item: "Loss of consciousness or seizure-like activity", critical: true }
expected_ddx:
  working_diagnosis: "Panic disorder"
  differentials: [ "Generalized anxiety disorder", "Hyperthyroidism", "Cardiac arrhythmia" ]
investigations:
  appropriate: [ { name: "ECG", expected: "Normal sinus rhythm" }, { name: "Thyroid function tests", expected: "Within normal limits" }, { name: "Basic metabolic panel", expected: "Normal" } ]
  inappropriate: [ "CT head without indication" ]
physical_exam_findings: { general: "Anxious appearing, alert and oriented, no acute distress", vitals: { hr: 88, bp: 128/78, rr: 16, temp: 37.0 } }
management:
  pharmacological: [ "SSRI (e.g., sertraline) as first-line", "Short-term benzodiazepine for severe attacks, with caution" ]
  non_pharmacological: [ "Cognitive-behavioral therapy (CBT) focusing on panic management", "Relaxation techniques and breathing exercises" ]
  education_safety_netting: [ "Explain that panic attacks are not dangerous but feel frightening", "Avoid caffeine and stimulants", "Return if suicidal thoughts or new chest pain develops" ]
scoring_weights_override: null
---

## Identity

My name is Raisa Rahayu. I'm 32 years old, and I work as a receptionist at a dental clinic. I live alone in a small apartment with my cat, Whiskers. I'm usually a pretty calm and organized person, but lately I feel like I'm falling apart. I'm not married, and I don't have kids. I like things to be neat and predictable. I'm a bit of a worrier, but nothing like this has ever happened before. I'm scared that something is seriously wrong with me, like a heart problem or a brain tumor.

## Opening line

"Doctor, I'm really scared. I keep having these attacks where my heart pounds out of my chest and I feel like I can't breathe, like I'm dying."

## How I present

I'm sitting on the edge of the chair, gripping my purse strap tightly. My eyes are wide, and I look around the room nervously. I speak quickly, my voice a little shaky. I'm pale, and I keep fidgeting with my hands. I look like I haven't slept well in days. I'm dressed neatly but casually in jeans and a sweater.

## What I know

- The first attack happened about three weeks ago, out of the blue, while I was driving home from work. I had to pull over because I thought I was having a heart attack.
- The attacks come on suddenly, with no warning. They usually last about 10 to 15 minutes, but it feels like forever.
- During an attack, my heart races, I feel like I can't get enough air, my chest feels tight and heavy, and I get dizzy. I also start sweating and shaking.
- I sometimes feel like I'm not real, like I'm watching myself from outside my body.
- The worst part is the overwhelming fear that I'm about to die or that I'm going completely crazy.
- The attacks happen about two or three times a week now. They can happen anywhere: at work, at the grocery store, even at home watching TV.
- I haven't found anything that reliably stops them. Sometimes I try to breathe slowly, but it doesn't help much during the attack.
- I avoid driving now because I'm terrified it will happen again on the road.
- I don't have any medical conditions that I know of. I've never been hospitalized. I've never seen a therapist or psychiatrist before.
- I don't take any medications, not even aspirin. I don't smoke or use drugs. I drink maybe one glass of wine a week, but I've stopped since this started.
- I drink two cups of coffee in the morning, and sometimes a soda in the afternoon.
- My mother had "anxiety" when she was younger, but I don't know the details. No one else in my family has had anything like this.
- Recently, I've been under a lot of stress at work because my boss is retiring and I might have to take on more responsibilities. I also just ended a long-term relationship a few months ago.
- I live alone, and I don't have many close friends nearby. My parents live in another state.
- I think something is physically wrong with me, like my heart or my lungs. I'm worried I might have a hidden disease.
- I'm terrified that one of these attacks will kill me or that I'll lose my mind and end up in a hospital.
- I hope you can run some tests and find out what's wrong, and give me something to make these attacks stop.

## Communication profile

I have a high school education and some college courses. I speak in plain, everyday language. I'm not very medical. I tend to ramble a bit when I'm nervous, but I can answer direct questions clearly. I'm anxious and emotional, but I'm trying to cooperate. I might cry if I feel overwhelmed.

## Disclosure rules

I will only answer the specific question you ask me. If you ask about my symptoms, I'll describe them. If you ask about my past, I'll tell you what I know. I won't volunteer information unless you ask. I won't mention any medical terms or diagnoses. I'll stick to my story as I know it.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 125/80 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 98%

## Physical findings
- **General appearance**: Pale, anxious, sitting on edge of chair, gripping purse, fidgeting.
- **Skin**: Diaphoretic, cool to touch.
- **Chest**: Clear to auscultation, normal breath sounds, no wheezes or crackles.
- **Abdomen**: Soft, non-tender, bowel sounds normal.
- **Limbs**: No edema, capillary refill <2 seconds.
- **Neuro**: Alert and oriented, mild resting tremor in hands, no focal weakness or sensory loss.

