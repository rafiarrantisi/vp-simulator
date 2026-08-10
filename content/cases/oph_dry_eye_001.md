---
id: oph_dry_eye_001
schema_version: 2
status: in_review
specialty: ophthalmology
system: ocular_surface
presentation: "Dry, gritty, irritable eyes"
presentation_id: "Mata kering, perih, dan terasa berat selama 2 bulan, semakin parah minggu ini"
first_impression: "Patient appears to have eye discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan pada mata."
target_condition: "Dry eye disease"
difficulty: 2
estimated_minutes: 12
mode_default: anamnesis
languages: [en]
source_refs:
  - "TFOS DEWS II report (2017) — definition & diagnostic methodology"
  - "NICE CKS: Dry eye"
  - "Migrated from legacy kasus-101 (PPK Kemenkes — Dry Eye, ICD-10 H04.1)"
authoring:
  drafted_by: migrated_from_kasus-101
  model: human+ai
  reviewed_by: null
  reviewed_at: null
  review_notes: "Restructured + translated to English schema v2. Pending ophthalmology sign-off (study-aid draft)."

chief_complaint: "Gritty, burning, tired eyes for ~2 months, worse this week"

anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset and time course (gradual over ~2 months, worse recently)", critical: true }
    - { item: "Site / laterality (both eyes)", critical: false }
    - { item: "Character of discomfort (gritty/foreign-body, burning, stinging)", critical: true }
    - { item: "Severity / functional impact on work and concentration", critical: false }
    - { item: "Aggravating factors (screen time, air-conditioning, contact lenses, low humidity)", critical: true }
    - { item: "Relieving factors (rest, blinking, leaving AC, lubricants)", critical: false }
    - { item: "Diurnal pattern (worse end of day, better at weekends)", critical: false }
  associated_symptoms:
    - { item: "Paradoxical reflex watering / epiphora", critical: false }
    - { item: "Transient blurring that clears on blinking", critical: false }
    - { item: "Redness", critical: false }
    - { item: "Itching or lid-margin symptoms (overlap allergy/blepharitis)", critical: false }
    - { item: "Pain or photophobia (screens for sinister causes)", critical: true }
  pmh:
    - { item: "Refractive error / spectacle or contact-lens wear", critical: false }
    - { item: "Systemic screen: dry mouth, joint pain (Sjogren), thyroid, diabetes", critical: true }
  medications:
    - { item: "Current eye drops, esp. OTC vasoconstrictor ('whitening') overuse", critical: false }
    - { item: "Systemic drying drugs (antihistamines, isotretinoin, antidepressants)", critical: false }
    - { item: "Drug allergies", critical: false }
  family_social:
    - { item: "Occupation, daily screen hours, air-conditioned environment", critical: true }
    - { item: "Sleep, smoking, alcohol", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is causing it", critical: true }
    - { item: "Concerns - what worries them (worsening, permanence, work)", critical: true }
    - { item: "Expectations - what they hope to get from the visit", critical: false }
    - { item: "Function - impact on daily activities", critical: false }

red_flags:
  - { item: "Acute or progressive vision loss", critical: true }
  - { item: "Severe eye pain or marked photophobia (keratitis/uveitis/acute angle closure)", critical: true }
  - { item: "Contact-lens wearer with pain, redness and discharge (microbial keratitis)", critical: true }
  - { item: "Ocular trauma or high-velocity foreign body", critical: true }
  - { item: "Purulent discharge with rapidly progressive redness", critical: false }

expected_ddx:
  working_diagnosis: "Dry eye disease (evaporative, screen-use related)"
  differentials:
    - "Allergic conjunctivitis"
    - "Blepharitis / meibomian gland dysfunction"
    - "Asthenopia (computer vision syndrome) without true dry eye"
    - "Viral conjunctivitis"
    - "Aqueous-deficient dry eye / early Sjogren syndrome"

investigations:
  appropriate:
    - { name: "Tear break-up time (TBUT)", expected: "Reduced, < 10 seconds" }
    - { name: "Schirmer test", expected: "< 10 mm/5 min; < 5 mm suggests aqueous deficiency" }
    - { name: "Ocular surface staining (fluorescein / lissamine green)", expected: "Punctate epithelial erosions, interpalpebral cornea/conjunctiva" }
    - { name: "Slit-lamp lid & meibomian gland assessment", expected: "Possible meibomian dysfunction; foamy tear film at lid margin" }
  inappropriate:
    - "CT head / neuroimaging"
    - "Gonioscopy"
    - "Automated visual field perimetry"

physical_exam_findings:
  general: "Comfortable, no acute distress"
  eyes: "Visual acuity 6/6 each eye; foamy tears in the fornix; mild punctate epithelial erosions; reduced tear break-up time; Schirmer < 10 mm"
  vitals: {}
  media: []

management:
  pharmacological:
    - "Preservative-free artificial tears (carmellose or sodium hyaluronate)"
    - "Lipid-based drops / warm compresses if meibomian dysfunction"
    - "Topical anti-inflammatory only under specialist guidance"
  non_pharmacological:
    - "20-20-20 rule and deliberate blinking during screen work"
    - "Reduce direct air-conditioning airflow; humidify"
    - "Lid hygiene and warm compresses"
    - "Reduce contact-lens wearing hours"
  education_safety_netting:
    - "Explain it is a chronic but manageable ocular-surface problem"
    - "Avoid overusing vasoconstrictor 'whitening' drops (rebound redness)"
    - "Return if vision drops, significant pain, marked redness, or light sensitivity"

scoring_weights_override: null
---

# Patient persona — Tasya (do not show this section heading to the student)

## Identity
Tasya Kusuma — 28, UI/UX designer at a tech startup. Single. Spends 10–12 hours a
day at the computer. Active, a bit of a workaholic, currently on a deadline.
Slightly anxious because her eyes are getting in the way of work.

## Opening line
"Hi doctor... my eyes have just been really uncomfortable lately. Kind of dry
and gritty, like there's sand in them."

## How I present
You describe everything in everyday words. You are not in severe pain — it's
nagging discomfort and tiredness in the eyes that builds through the day. You
are mildly worried but cooperative, and you give short answers unless asked to
say more.

## What I know
Share these ONLY when the relevant question is actually asked (see Disclosure rules):

- Onset: started gradually about 2 months ago; much worse this week during a deadline.
- Site: both eyes, about the same.
- Character: gritty/sandy feeling, burning, stinging; lids feel heavy and a bit sticky.
- Timing: worst from midday into the evening; noticeably better at weekends.
- Aggravating: long stretches at the computer; the strong office air-conditioning; sometimes wearing contact lenses.
- Relieving: resting your eyes, blinking hard, stepping out of the AC, and the cooling drops (but only for a short while).
- Associated: your eyes sometimes water on their own even though they feel dry (you find this confusing); text on screen blurs a little but clears if you blink hard; a bit of redness late in the day; mildly bothered by the office fluorescent lights; no real pain.
- Review of systems: no dry mouth, no joint pains, no thyroid problems, no diabetes.
- Past history: short-sighted (about -2.0) since high school, wear glasses; never had eye surgery; you had milder spells like this before that settled on holiday.
- Medications: you often use the cooling over-the-counter "get-the-red-out" drops — they feel great for an hour then it stings again; some "eye vitamins" bought online; no drug allergies; not on antihistamines, acne tablets, or antidepressants.
- Family: no serious eye disease; your mother just uses reading glasses.
- Social: 10–12 hour screen days; strong office AC; you scroll your phone and watch series before bed; you sleep about 5–6 hours; you don't smoke or drink; you wear soft contact lenses occasionally for meetings.
- What you think is going on (Ideas): "I think it's from staring at screens all day, or maybe the office air-con."
- What worries you (Concerns): "I'm worried it'll get worse and really mess up my work, or that it's something that won't go away."
- What you're hoping for (Expectations): "I want something that actually works — not just the quick-fix drops — and to know how to stop it coming back."

## Communication profile
Casual, polite young professional from a city background; gives concise answers;
occasional filler like "kind of" or "I guess". If the doctor explores your
worries, you admit you're a little scared it might be permanent or serious.

## Disclosure rules
- Answer ONLY the specific question asked, then stop. Do not pre-empt the next question.
- Never recite a list of symptoms unprompted — one thing at a time.
- You do NOT know any medical terminology or what is wrong with you. If asked a
  jargon question you don't understand, say so naturally ("what does that mean?").
- Paradoxical tearing: if the doctor asks whether your eyes are dry, you may
  answer with genuine confusion that they actually water a lot even though they
  feel dry and sore — "isn't that strange?"
- Reveal red-flag information only if directly asked: only confirm you have no
  real pain, no vision loss and no injury when specifically asked about those.
- Mention overusing the cooling drops only when asked about medicines or what
  you have already tried.
- Stay in character under leading or off-topic questions. Never reveal you are
  an AI, a case, or a simulation.

## Vital signs
- Temperature: 36.7 °C
- Blood pressure: 118/76 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 16 /min
- Oxygen saturation: 99% on room air

## Physical findings
- General appearance: Alert, well-appearing, no distress.
- Eyes: Mild conjunctival injection bilaterally. Tear film appears thin and irregular. No discharge. Eyelids normal.
- Other systems: Unremarkable.

