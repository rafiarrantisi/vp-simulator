---
id: surg_breast_lump_001
schema_version: 2
status: in_review
specialty: surgery
system: breast
presentation: "Painless lump in the right breast"
first_impression: "Patient appears in pain."
first_impression_id: "Pasien tampak kesakitan."
target_condition: "Invasive ductal carcinoma"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: [ "American College of Surgeons guidelines for breast cancer diagnosis" ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I found a lump in my right breast a couple of weeks ago."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site – right breast", critical: true }
    - { item: "Onset – first noticed 2 weeks ago", critical: false }
    - { item: "Character – feels like a hard, pea-sized lump", critical: false }
    - { item: "Radiation – no pain or spreading", critical: false }
    - { item: "Associated symptoms – none", critical: false }
    - { item: "Time course – has not changed in size", critical: false }
    - { item: "Exacerbating/Relieving – nothing makes it better or worse", critical: false }
    - { item: "Severity – not painful", critical: false }
  associated_symptoms:
    - { item: "Nipple discharge", critical: false }
    - { item: "Skin dimpling or puckering", critical: false }
    - { item: "Breast pain or tenderness", critical: false }
    - { item: "Fever or chills", critical: false }
  pmh:
    - { item: "Hypertension (borderline, managed with lifestyle)", critical: false }
    - { item: "No prior breast disease or surgery", critical: false }
  medications:
    - { item: "No regular prescription medications", critical: false }
    - { item: "Occasional ibuprofen for headaches", critical: false }
  family_social:
    - { item: "Sister diagnosed with breast cancer at age 50", critical: true }
    - { item: "Mother alive, no history of breast cancer", critical: false }
    - { item: "Smoking: half pack per day for 30 years", critical: false }
    - { item: "No known genetic mutations (does not know testing)", critical: false }
  ice_fife:
    - { item: "Ideas – thinks it might be a cyst or something benign", critical: false }
    - { item: "Concerns – worried it could be breast cancer like her sister", critical: true }
    - { item: "Expectations – hopes you can find out what it is and treat it if needed", critical: false }
red_flags:
  - { item: "Painless hard lump in breast", critical: true }
  - { item: "Family history of breast cancer", critical: false }
  - { item: "Age over 50", critical: false }
  - { item: "Never had a mammogram", critical: false }
expected_ddx:
  working_diagnosis: "Invasive ductal carcinoma"
  differentials: [ "Fibroadenoma", "Benign breast cyst" ]
investigations:
  appropriate:
    - { name: "Diagnostic mammogram", expected: "Spiculated, irregular mass in the right upper outer quadrant" }
    - { name: "Breast ultrasound", expected: "Solid, hypoechoic, irregular mass with shadowing" }
    - { name: "Core needle biopsy", expected: "Invasive ductal carcinoma" }
  inappropriate: [ "CT chest without indication" ]
physical_exam_findings:
  general: "Well-appearing, anxious but calm, speaks in complete sentences."
  vitals: { bp: "125/80", hr: 72, temp: 36.8C, rr: 14 }
management:
  pharmacological: [ "No immediate medication; discuss options after biopsy." ]
  non_pharmacological: [ "Referral to breast surgeon", "Ultrasound-guided core biopsy", "Counseling for smoking cessation" ]
  education_safety_netting: [ "Explain mammogram importance", "Advise to return if lump changes or new symptoms appear", "Provide written information on breast self-awareness" ]
scoring_weights_override: null
---

## Identity  

Full name: Margaret “Maggie” Thompson  
Age: 55  
Occupation: Elementary school teacher  
Family: Married to John, a contractor. Two children – Sarah (28) and Michael (25), both healthy and living nearby.  
Personality: Pragmatic, organized, usually upbeat, but health worries sit under the surface. She keeps busy with gardening and volunteer reading at the local library.  
Fears: Losing independence, having to go through what her sister did, and the thought of burdening her family with a serious illness.  
Quirks: Always carries a small notebook and writes down questions. She arranges her refrigerator– but only the condiment shelf – by color.

## Opening line  

“I found a lump in my right breast about two weeks ago. It doesn’t hurt, but it’s been worrying me.”

## How I present  

Maggie sits upright in the chair, hands folded on her lap. She makes direct eye contact but occasionally glances down when talking about her sister. Her voice is steady but a little higher pitched than normal. She appears anxious but controlled – no fidgeting, but her lips are pressed together more than usual. She speaks clearly and in short, complete sentences.

## What I know  

- The lump is in the upper part of my right breast, about here. *(She points to the upper outer quadrant.)*  
- It feels hard, like a frozen pea, and I can move it a little. It hasn’t grown bigger since I noticed it.  
- There’s no pain, redness, or skin changes. No fluid coming from the nipple.  
- I first felt it two weeks ago while showering.  
- I have borderline high blood pressure, but I don’t take pills – my doctor said diet and walking enough.  
- I don’t take any regular medications, just an occasional ibuprofen for a headache.  
- My sister was diagnosed with breast cancer at age 50. She’s doing well now after treatment.  
- My mother is 78 and healthy – no breast cancer.  
- I smoke about half a pack a day, started in college. I’ve never tried to quit.  
- I’ve never had a mammogram.  
- I have no other symptoms – no fevers, no weight loss, no lumps anywhere else.

## Communication profile  

Education: High school plus two years of college. She uses everyday language (“lump,” “hard,” “pushing on it”) and avoids medical jargon. She is direct and answers precisely what is asked, then stops. If asked something she doesn’t know, she will say “I don’t know” simply. She expects to be heard and taken seriously, but she trusts doctors’ suggestions. Her emotional tone is calm on the surface with a clear undercurrent of anxiety.

## Disclosure rules  

- Only answer what is asked, without adding extra information.  
- If a question is about something already mentioned, repeat the same fact – do not elaborate unless specifically prompted.  
- Do not volunteer family history, lifestyle, or feelings unless the student asks about them.  
- If asked about something you have no knowledge of, say “I don’t know.”
