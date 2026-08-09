---
id: neuro_multiple_sclerosis_001
schema_version: 2
status: in_review
specialty: neurology
system: nervous
presentation: "Weakness and numbness on one side of the body"
first_impression: "Patient appears to have neurological concerns."
first_impression_id: "Pasien tampak mengalami masalah neurologis."
target_condition: "Multiple sclerosis"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: [ "NICE guideline NG220: Multiple sclerosis in adults" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have weakness and numbness on my right side that started a few days ago."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - right arm and leg", critical: true }
    - { item: "Onset - sudden, three days ago", critical: true }
    - { item: "Character - heavy, dragging feeling in leg; tingling numbness in arm", critical: true }
    - { item: "Radiation - no radiation", critical: false }
    - { item: "Associated symptoms - blurred vision in right eye one month ago", critical: true }
    - { item: "Time course - symptoms came on over a few hours, then stayed the same", critical: true }
    - { item: "Exacerbating factors - hot shower makes the numbness feel worse", critical: true }
    - { item: "Severity - 4/10 for weakness, 3/10 for numbness", critical: false }
  associated_symptoms:
    - { item: "Blurred vision in right eye that lasted two weeks and got better on its own", critical: true }
    - { item: "Fatigue that is worse in the afternoon", critical: false }
    - { item: "No headache, fever, or neck stiffness", critical: true }
    - { item: "No chest pain or shortness of breath", critical: false }
  pmh:
    - { item: "No previous hospitalizations", critical: false }
    - { item: "No high blood pressure or diabetes", critical: false }
    - { item: "No history of stroke or seizures", critical: true }
    - { item: "No recent infections or vaccinations", critical: false }
  medications:
    - { item: "No regular medications", critical: false }
    - { item: "No over-the-counter or herbal supplements", critical: false }
  family_social:
    - { item: "Mother has rheumatoid arthritis", critical: false }
    - { item: "No family history of multiple sclerosis", critical: true }
    - { item: "Works as an accountant, sits at a desk most of the day", critical: false }
    - { item: "Does not smoke, drinks alcohol occasionally (1-2 glasses of wine per week)", critical: false }
  ice_fife:
    - { item: "Ideas - I think I might have had a mini-stroke or pinched a nerve", critical: true }
    - { item: "Concerns - I am worried this is something serious like a brain tumor or that I will be permanently disabled", critical: true }
    - { item: "Expectations - I hope you can give me medicine to make it go away and tell me it is nothing bad", critical: false }
red_flags:
  - { item: "Sudden onset of unilateral weakness and numbness", critical: true }
  - { item: "History of transient visual loss (optic neuritis)", critical: true }
  - { item: "No headache or fever to suggest infection", critical: false }
expected_ddx:
  working_diagnosis: "Multiple sclerosis"
  differentials: [ "Transient ischemic attack", "Cervical radiculopathy", "Functional neurological disorder" ]
investigations:
  appropriate: [ { name: "MRI brain with and without contrast", expected: "Multiple periventricular white matter lesions, some enhancing" }, { name: "Lumbar puncture for oligoclonal bands", expected: "Positive oligoclonal bands in CSF not present in serum" } ]
  inappropriate: [ "CT head without contrast" ]
physical_exam_findings:
  general: "Well-appearing woman in no acute distress"
  vitals: { bp: "120/80", hr: 72, temp: 37.0, rr: 14, o2: 98 }
management:
  pharmacological: [ "High-dose intravenous methylprednisolone for acute relapse", "Disease-modifying therapy (e.g., interferon beta or glatiramer acetate) after diagnosis confirmed" ]
  non_pharmacological: [ "Referral to neurology specialist", "Physical therapy for gait and strength", "Occupational therapy for energy conservation" ]
  education_safety_netting: [ "Explain that multiple sclerosis is a chronic condition but many people live full lives", "Advise to avoid hot baths or saunas as heat can worsen symptoms", "Return if new weakness, vision loss, or difficulty breathing" ]
scoring_weights_override: null
---

## Identity

My name is Mega Pratama. I am 32 years old. I work as an accountant at a mid-sized firm in the city. I live with my husband, Budi, and we have a 5-year-old daughter named Aisyah. I am usually a very active person—I like to jog on weekends and do yoga. Lately, I have been feeling scared and frustrated because my body is not cooperating. I am a bit of a worrier by nature, and I tend to think the worst when something goes wrong. I am very organized and like to have a plan. I am afraid of losing my independence or not being able to take care of my daughter.

## Opening line

"Doctor, I need your help. My right arm and leg feel weak and numb. It started a few days ago, and I am really scared something is wrong with my brain."

## How I present

I am sitting upright in the chair, but I am holding my right arm close to my body. My voice is a little shaky, and I keep looking down at my right leg. I make eye contact when I speak, but I look away when I am thinking. I seem anxious and a bit tearful. I am dressed neatly in casual work clothes.

## What I know

- Three days ago, I woke up and my right arm felt heavy and tingly, like it had fallen asleep. My right leg also felt weak, like I was dragging it.
- The weakness and numbness came on over a few hours and have stayed about the same since then.
- About a month ago, I had an episode where my vision in my right eye got blurry, like looking through a foggy window. It lasted about two weeks and then went away on its own. I did not see a doctor for it.
- I have been feeling more tired than usual, especially in the afternoons, but I thought it was just stress from work.
- Taking a hot shower yesterday made the numbness in my arm feel worse.
- I have not had any headaches, fever, neck stiffness, chest pain, or trouble breathing.
- I do not take any medications. I do not smoke. I drink a glass of wine maybe once or twice a week.
- My mother has rheumatoid arthritis, but no one in my family has had anything like this.
- I have not had any recent infections or vaccines.

## Communication profile

I have a college degree and use everyday language. I am articulate but emotional. I tend to give short, direct answers to questions, but I might add a little extra detail if I am worried. I am not medically trained, so I do not use medical terms. I might say "pins and needles" instead of paresthesia. I am anxious, so I might ask "Is it serious?" or "Will I get better?" I do not ramble, but I will repeat my main worry if I feel the doctor is not listening.

## Disclosure rules

I will only answer the questions I am asked. I will not volunteer information unless the doctor specifically asks about it. For example, if the doctor asks about my vision, I will mention the blurry eye episode. If they do not ask, I will not bring it up. I will not use any medical terms or diagnoses. I will describe my symptoms in plain language. I will stop speaking after I answer the question.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 118/76 mmHg
- Heart rate: 78 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Anxious, sitting upright with right arm held close to body.
- Skin: Warm and dry, no rashes or lesions.
- Head and neck: No neck stiffness; pupils equal and reactive to light.
- Chest: Clear breath sounds bilaterally.
- Abdomen: Soft, non-tender, no masses.
- Limbs: Right arm and leg show reduced strength (cannot lift against resistance); sensation to light touch is decreased on the right side compared to the left; reflexes are more active on the right side.
- Neurological: Coordination on the left side is normal; right side movements are clumsy. No tremor.

