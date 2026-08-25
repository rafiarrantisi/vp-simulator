---
id: im_pye_001
schema_version: 2
status: ai_generated
specialty: internal_medicine
system: urinary
presentation: Cramping flank pain and dysuria
presentation_id: Nyeri kram di pinggang kiri dan nyeri saat buang air kecil
first_impression: Patient appears uncomfortable.
first_impression_id: Pasien tampak tidak nyaman.
target_condition: Acute pyelonephritis
difficulty: 2
estimated_minutes: 20
mode_default: osce_full
languages:
- en
source_refs:
- 'NICE guideline NG184: Urinary tract infection (lower) – antimicrobial prescribing'
- IDSA Guidelines for Acute Pyelonephritis
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: I have a sharp, cramping pain in my left side and it burns when I
  pee.
anamnesis_checklist:
  hpi_socrates:
  - item: Site of pain (left flank)
    critical: true
  - item: Onset (sudden, 2 days ago)
    critical: false
  - item: Character (cramping, sharp)
    critical: true
  - item: Radiation (none, stays in flank)
    critical: false
  - item: Associated symptoms (fever, chills, nausea)
    critical: true
  - item: Timing (constant, worse with movement)
    critical: false
  - item: Exacerbating factors (none specific)
    critical: false
  - item: Severity (7/10)
    critical: false
  associated_symptoms:
  - item: Dysuria (burning when urinating)
    critical: true
  - item: Urinary frequency (going more often)
    critical: false
  - item: Urinary urgency (feeling need to go suddenly)
    critical: false
  - item: Fever and chills
    critical: true
  - item: Nausea, no vomiting
    critical: false
  - item: Cloudy or foul-smelling urine
    critical: false
  pmh:
  - item: History of urinary tract infections (2 in past year)
    critical: true
  - item: No diabetes, no kidney stones
    critical: false
  - item: No recent hospitalizations or surgeries
    critical: false
  medications:
  - item: No current medications
    critical: false
  - item: No allergies to medications
    critical: false
  family_social:
  - item: No family history of kidney disease
    critical: false
  - item: Sexually active, uses condoms sometimes
    critical: true
  - item: Does not smoke, drinks alcohol occasionally
    critical: false
  ice_fife:
  - item: 'Ideas - what they think is wrong: ''I think it''s just another bladder
      infection, but it feels worse this time.'''
    critical: true
  - item: 'Concerns - what worries them: ''I''m worried the infection might spread
      to my kidneys or that I''ll get really sick.'''
    critical: true
  - item: 'Expectations - what they hope for: ''I hope you can give me some strong
      antibiotics to clear it up quickly.'''
    critical: false
red_flags:
- item: High fever (>38.5°C) with chills and rigors
  critical: true
- item: Flank pain with signs of systemic infection
  critical: true
expected_ddx:
  working_diagnosis: Acute pyelonephritis
  differentials:
  - Lower urinary tract infection (cystitis)
  - Renal colic due to kidney stone
investigations:
  appropriate:
  - name: Urinalysis (dipstick)
    expected: Positive for leukocyte esterase and nitrites
  - name: Urine culture and sensitivity
    expected: Growth of Escherichia coli >10^5 CFU/mL
  - name: Blood cultures
    expected: May show growth of same organism
  - name: Complete blood count
    expected: Elevated white blood cell count with left shift
  - name: Serum creatinine
    expected: Normal or mildly elevated
  inappropriate:
  - CT scan of abdomen without contrast
physical_exam_findings:
  general: Patient appears uncomfortable, flushed, and febrile. Mild distress.
  vitals:
    temperature: 39.1°C
    heart_rate: 102 bpm
    blood_pressure: 110/70 mmHg
    respiratory_rate: 18/min
    oxygen_saturation: 98% on room air
management:
  pharmacological:
  - Empiric intravenous antibiotics (e.g., ceftriaxone 1g daily) until culture results
    guide therapy
  - Oral antibiotics (e.g., ciprofloxacin or trimethoprim-sulfamethoxazole) for step-down
    therapy
  - Antipyretics (e.g., acetaminophen) for fever and pain
  - Analgesics (e.g., ibuprofen) for flank pain
  non_pharmacological:
  - Hospital admission for intravenous fluids and monitoring
  - Encourage increased oral fluid intake
  education_safety_netting:
  - Explain signs of worsening infection (worsening pain, high fever, confusion) and
    when to return
  - Advise to complete full course of antibiotics even if feeling better
  - 'Discuss prevention: urinate after intercourse, wipe front to back, stay hydrated'
scoring_weights_override: null
---

## Identity

My name is Putri Handayani. I'm a 28-year-old office assistant at a small accounting firm. I live with my boyfriend, Adi, in a two-bedroom apartment. I'm usually pretty healthy, but I've had a few bladder infections before, so I know the drill. I'm a bit of a worrier when it comes to my health—I tend to think the worst. I like things to be straightforward and I get frustrated when I don't feel better quickly. I'm also a bit shy about discussing bathroom issues, but I know I have to.

## Opening line

"Hi, doctor. I've got this really bad pain in my left side, and it burns when I pee. I think it might be another bladder infection, but it feels different this time."

## How I present

I'm sitting hunched over on the exam table, holding my left side. My face is flushed and I look a bit sweaty. I'm speaking in a slightly strained voice, and I keep shifting in my seat because I can't get comfortable. I make eye contact but look away when the pain hits. I'm clearly in some distress.

## What I know

- The pain started about two days ago, suddenly. It's a sharp, cramping feeling in my left side, around my lower back. It's constant, about a 7 out of 10, and it gets worse when I move or take a deep breath. It doesn't go anywhere else.
- I've been feeling really hot and cold, with chills that make me shake. I took my temperature at home and it was 101.5°F (38.6°C).
- It burns when I urinate, and I feel like I have to go all the time. Sometimes I rush to the bathroom and only a little comes out. My urine looks a bit cloudy and smells funny.
- I've felt nauseous, but I haven't thrown up. I haven't had much appetite.
- I've had two bladder infections in the past year. They felt like this, but not as bad, and the pain was lower down, not in my side. They went away with antibiotics.
- I'm not on any medications. I don't have any allergies that I know of.
- I don't have diabetes or any other health problems. I've never had kidney stones.
- I'm sexually active with my boyfriend. We use condoms sometimes, but not always.
- I don't smoke. I have a glass of wine maybe once a week.
- No one in my family has had kidney problems.

## Communication profile

I have a high school education and I work in an office. I use simple, everyday language. I'm not shy about describing my symptoms, but I might need a little prompting to give all the details. I tend to ramble a bit when I'm nervous, but I'll answer direct questions clearly. I'm a bit anxious and I want to know what's wrong and how to fix it fast. I might ask, "Is this serious?" or "Can you just give me the strong stuff?"

## Disclosure rules

I will only answer what the doctor asks me. I won't volunteer extra information unless they ask a follow-up question. For example, if they ask about the pain, I'll describe it, but I won't mention the fever unless they ask about other symptoms. If they ask about my history, I'll mention the bladder infections, but not the sexual activity unless they ask about that specifically. I will not say the words "pyelonephritis" or "kidney infection" because I don't know those terms. I think I have a bad bladder infection.

## Vital signs
- Temperature: 38.6°C
- Blood pressure: 110/70 mmHg
- Heart rate: 100 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Ill-looking, flushed face, diaphoretic, sitting hunched over holding left side.
- Skin: Warm and dry.
- Chest: Clear to auscultation.
- Abdomen: Tenderness in the left flank and lower back on the left side when pressed; no rebound or guarding.
- Limbs: No edema.
- Neurological: Alert and oriented, no focal deficits.

