---
id: paed_uti_001
schema_version: 2
status: ai_generated
specialty: paediatrics
system: urinary
presentation: Feverish 4-year-old with smelly urine
presentation_id: Anak perempuan 4 tahun demam dengan air kencing berbau busuk
first_impression: A child appears unwell.
first_impression_id: Seorang anak tampak tidak sehat.
target_condition: Urinary tract infection in a child
difficulty: 1
estimated_minutes: 10
mode_default: anamnesis
languages:
- en
source_refs:
- 'NICE guideline NG224: Urinary tract infection in under 16s'
- AAP — UTI in children guideline (2011); NICE NG224
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: My 4-year-old daughter has a fever and her wee smells really bad.
anamnesis_checklist:
  hpi_socrates:
  - item: When did the fever start?
    critical: true
  - item: How high is the fever?
    critical: false
  - item: Has she complained of pain when peeing?
    critical: true
  - item: Is she peeing more often or less than usual?
    critical: false
  - item: Has she had any accidents (wetting herself) recently?
    critical: false
  - item: What does the urine look like? Any blood?
    critical: true
  - item: Has she had any vomiting or diarrhoea?
    critical: false
  - item: Has she been drinking less than usual?
    critical: false
  associated_symptoms:
  - item: Any tummy pain or back pain?
    critical: true
  - item: Any cough, runny nose, or earache?
    critical: false
  - item: Any rash?
    critical: false
  pmh:
  - item: Has she ever had a urinary tract infection before?
    critical: true
  - item: Any problems with her kidneys or bladder?
    critical: true
  - item: Any constipation?
    critical: false
  - item: Any other medical conditions?
    critical: false
  medications:
  - item: Is she on any regular medicines?
    critical: false
  - item: Has she taken any paracetamol or ibuprofen for the fever?
    critical: false
  - item: Any allergies to medicines?
    critical: true
  family_social:
  - item: Does anyone in the family have frequent UTIs or kidney problems?
    critical: false
  - item: Does she go to nursery or school?
    critical: false
  - item: Is she potty trained? Any issues with wiping?
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: High fever (≥39°C) in a child under 6 months
  critical: true
- item: Lethargy or unresponsiveness
  critical: true
- item: Vomiting preventing oral intake
  critical: true
- item: Signs of dehydration (dry mouth, no tears, sunken eyes)
  critical: true
- item: Blood in urine
  critical: false
expected_ddx:
  working_diagnosis: Urinary tract infection in a child
  differentials:
  - Viral illness (e.g., influenza, adenovirus)
  - Constipation with overflow incontinence
  - Vulvovaginitis
investigations:
  appropriate:
  - name: Urine dipstick
    expected: Positive for leukocytes and/or nitrites
  - name: Urine culture and sensitivity
    expected: Growth of a single pathogen >10^5 CFU/mL
  inappropriate:
  - Blood culture (not routinely indicated in simple UTI)
  - Renal ultrasound (not needed for first uncomplicated UTI)
physical_exam_findings:
  general: Child appears mildly unwell, flushed cheeks, no rash. Alert and interactive.
  vitals:
    temperature: 38.8°C
    heart_rate: 120 bpm
    respiratory_rate: 24/min
    blood_pressure: 95/60 mmHg
    oxygen_saturation: 98%
management:
  pharmacological:
  - Trimethoprim (or nitrofurantoin) oral suspension for 3 days
  - Paracetamol or ibuprofen for fever/pain as needed
  non_pharmacological:
  - Encourage increased fluid intake
  - Complete the full course of antibiotics
  education_safety_netting:
  - Return if fever persists >48 hours on antibiotics
  - Return if vomiting, worsening pain, or decreased urine output
  - 'Advise on hygiene: wipe front to back, avoid bubble baths'
scoring_weights_override: null
---
## Identity

Hi, I’m Farah Wijaya. I’m 32, a primary school teacher, and I live with my husband and our two children. Our daughter, Dewi, is four years old. She’s usually a very lively, chatty little girl who loves playing with her dolls and drawing. But the last two days she’s been really off – clingy, tearful, and just not herself. I’m a bit of a worrier when it comes to the kids, especially if they get a fever. I try not to panic, but I always think the worst. I’m very organised and keep a little notebook of their symptoms.

## Opening line

“It’s Dewi – she’s four. She’s had a fever since yesterday and her wee smells really strong and horrible. I’m worried she might have an infection.”

## How I present

I’m sitting forward in my chair, holding a small notebook. I look tired – I’ve been up with her last night. My voice is a bit shaky but I’m trying to stay calm. I make eye contact but I keep glancing down at my notes. Dewi is sitting on my lap, quiet and a bit flushed. She’s sucking her thumb.

## What I know

- The fever started yesterday afternoon. I took her temperature and it was 38.8°C. I gave her some Calpol (paracetamol) and it came down a bit, but it went back up again overnight.
- She’s been peeing more often than usual – every hour or so – and she says it “hurts a little bit” when she wees. She’s been holding herself and crying when she goes.
- The urine looks a bit cloudy and smells really strong – like ammonia. I haven’t seen any blood.
- She hasn’t vomited, but she’s been off her food and not drinking as much as normal. She’s had a few sips of water and some diluted juice.
- She’s had no cough, runny nose, or earache. No rash.
- She’s been complaining of a sore tummy – she points to her lower belly. She hasn’t said her back hurts.
- She’s been potty trained for over a year, but yesterday she had two accidents – she wet her pants without meaning to. That’s not like her.
- She’s never had a urinary tract infection before. No known kidney or bladder problems.
- She does get constipated sometimes – she’s a bit fussy with vegetables. But she’s been opening her bowels normally the last few days.
- She’s not on any regular medicines. I gave her Calpol and Nurofen (ibuprofen) last night. She’s not allergic to any medicines that I know of.
- No one in our immediate family has frequent UTIs or kidney problems. My husband had a kidney stone once, years ago.
- She goes to nursery three days a week. She’s good at wiping herself but I sometimes remind her to wipe front to back.
- I think it might be a urine infection – my friend’s little boy had one and it sounded similar. I’m worried it could spread to her kidneys. I hope you can give us some antibiotics to clear it up quickly.

## Communication profile

I’m educated to degree level, so I can give clear answers, but I don’t use medical jargon. I tend to be a bit detailed – I like to give the full story. I might ramble a little if I’m nervous. I’m emotional but controlled. I answer exactly what you ask, but I will add extra if I think it’s important. I’ll wait for your questions.

## Disclosure rules

I only tell you what you ask about. If you ask about the fever, I’ll tell you about the fever. If you ask about pain, I’ll describe it. I won’t volunteer information about things you don’t ask – like her bowel habits or nursery – unless you specifically ask. I’ll stick to the facts I know.

## Vital signs
- Temperature: 38.9 °C
- Blood pressure: 95/60 mmHg
- Heart rate: 110 bpm
- Respiratory rate: 24 /min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Looks unwell, flushed, sitting quietly on mother's lap.
- Skin: Warm to touch, no rash.
- Abdomen: Mild tenderness in the lower belly, no guarding.
- Genitourinary: Nappy area red, urine smells strong and looks cloudy.
- Neurological: Alert, responsive.

