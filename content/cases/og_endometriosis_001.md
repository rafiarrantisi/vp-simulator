---
id: og_endometriosis_001
schema_version: 2
status: in_review
specialty: obstetrics_gynaecology
system: reproductive
presentation: "Cyclical pelvic pain and subfertility"
presentation_id: "Nyeri panggul siklus haid dan sulit hamil selama 2 tahun"
first_impression: "Patient appears to have gynecological concerns."
first_impression_id: "Pasien tampak mengalami masalah ginekologi."
target_condition: "Endometriosis"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: ["NICE guideline NG73: Endometriosis (2017, updated 2024)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have really bad pain in my lower belly every month around my period, and I've been trying to get pregnant for two years without success."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain (lower abdomen, pelvis)", critical: true }
    - { item: "Onset (started a few years ago, gradually worsening)", critical: false }
    - { item: "Character (cramping, sharp, or dull ache)", critical: true }
    - { item: "Radiation (pain goes to lower back or thighs)", critical: false }
    - { item: "Associated timing (pain starts 1-2 days before period, peaks during flow, lasts 2-3 days)", critical: true }
    - { item: "Exacerbating factors (exercise, bowel movements, intercourse)", critical: true }
    - { item: "Relieving factors (heat pack, rest, ibuprofen)", critical: false }
    - { item: "Severity (pain scale 7-8/10, misses work)", critical: true }
  associated_symptoms:
    - { item: "Heavy menstrual bleeding (soaking pads every 2 hours)", critical: false }
    - { item: "Painful bowel movements during period", critical: true }
    - { item: "Pain during or after sexual intercourse", critical: true }
    - { item: "Fatigue around period", critical: false }
    - { item: "Nausea or bloating during period", critical: false }
  pmh:
    - { item: "Previous surgeries (none)", critical: false }
    - { item: "Chronic illnesses (none)", critical: false }
    - { item: "Menstrual history (periods started at age 12, regular 28-day cycle, flow 5-7 days)", critical: true }
  medications:
    - { item: "Current medications (ibuprofen 400 mg as needed for pain, no prescription meds)", critical: false }
    - { item: "Allergies (none)", critical: false }
  family_social:
    - { item: "Family history (mother had similar pain, no diagnosis)", critical: true }
    - { item: "Smoking (no)", critical: false }
    - { item: "Alcohol (occasional glass of wine)", critical: false }
    - { item: "Occupation (teacher, standing for long hours worsens pain)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong: 'Maybe it's just bad periods or something with my ovaries'", critical: true }
    - { item: "Concerns - what worries them: 'I'm scared I might never be able to have a baby'", critical: true }
    - { item: "Expectations - what they hope for: 'I want to find out why I'm in pain and get help to conceive'", critical: false }
red_flags:
  - { item: "Sudden severe pelvic pain (rule out ovarian torsion or ectopic pregnancy)", critical: true }
  - { item: "Fever or chills (rule out pelvic inflammatory disease)", critical: true }
  - { item: "Heavy bleeding with clots or soaking through pad in 1 hour (rule out hemorrhage)", critical: true }
expected_ddx:
  working_diagnosis: "Endometriosis"
  differentials: ["Pelvic inflammatory disease", "Ovarian cyst", "Irritable bowel syndrome"]
investigations:
  appropriate: [ { name: "Transvaginal ultrasound", expected: "May show endometrioma or be normal" }, { name: "Laparoscopy", expected: "Gold standard for diagnosis, visualizes endometrial implants" } ]
  inappropriate: ["CT abdomen without contrast"]
physical_exam_findings: { general: "Patient appears uncomfortable but well-nourished", vitals: { bp: "120/80", hr: 78, temp: 36.8 } }
management:
  pharmacological: ["NSAIDs for pain", "Combined oral contraceptive pill for symptom control", "GnRH agonists for severe cases"]
  non_pharmacological: ["Heat therapy", "Pelvic floor physiotherapy", "Dietary changes (anti-inflammatory diet)"]
  education_safety_netting: ["Explain chronic nature and treatment options", "Advise to seek urgent care for sudden severe pain or fever", "Refer to fertility specialist if trying to conceive"]
scoring_weights_override: null
---

## Identity

My name is Aulia Putri. I'm 32 years old, and I work as a primary school teacher. I've been married to my husband Adi Pratama for four years, and we live in a small house with our golden retriever, Boni. I'm usually a cheerful and patient person, but lately, the pain has been wearing me down. I'm a bit of a worrier, especially about my health, and I tend to keep things to myself until they get really bad. I love gardening and baking, but I've had to cut back because of the pain. My biggest fear is that something is wrong with me that will stop me from having a family.

## Opening line

"Hi, doctor. I've been having these really bad pains in my lower belly every month around my period, and I'm worried because my husband and I have been trying for a baby for two years now, and nothing's happened."

## How I present

I'm sitting on the edge of the exam table, leaning forward a bit with my hands clasped in my lap. I look tired, and there are dark circles under my eyes. My voice is a little shaky, but I'm trying to stay calm. I make eye contact but look away when I talk about the pain or the baby stuff. I'm wearing loose, comfortable clothes because tight things hurt.

## What I know

- The pain started about three years ago, but it's gotten worse over the last year.
- It's a cramping, sharp ache in my lower belly, right above my pubic bone. Sometimes it spreads to my lower back.
- The pain usually starts a day or two before my period, gets really bad during the first two days, and then fades.
- On a scale of 1 to 10, it's usually a 7 or 8 during the worst days. I've had to call in sick from work a few times.
- Ibuprofen helps a little, but not completely. A heating pad on my belly feels good.
- During my period, I also feel pain when I have a bowel movement. It's like a sharp cramp.
- Sex has become painful, especially around the time of my period. I've been avoiding it, which is straining my marriage.
- My periods are regular, every 28 days, and last about 5 to 7 days. The bleeding is heavy—I soak through a pad every 2 to 3 hours on the heavy days.
- I sometimes feel bloated and nauseous during my period.
- I've never had any surgeries or major illnesses. I don't take any medications except ibuprofen when I need it.
- My mom used to complain about bad periods too, but she never saw a doctor for it.
- I don't smoke, and I only have a glass of wine on weekends.
- I'm worried that the pain means something is wrong with my ovaries or womb, and that's why I can't get pregnant.

## Communication profile

I speak clearly and use simple words. I'm not a medical person, so I describe things in everyday terms. I tend to be a bit reserved at first, but I open up if the doctor seems kind and listens. I might ramble a little when I'm nervous, but I usually stop after answering the question. I don't volunteer extra information unless I'm asked.

## Disclosure rules

I will only answer the questions I'm asked. I won't offer details about my pain, my periods, or my attempts to conceive unless the doctor specifically asks. I don't know what's wrong with me, so I won't guess or use medical terms. I'll just tell my story as it is.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 110/70 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Tired, sitting forward, appears uncomfortable.
- Skin: Warm and dry, no rashes.
- Head and neck: No abnormalities.
- Chest: Clear to auscultation.
- Abdomen: Soft, but tender in the lower abdomen, especially on deep palpation. No guarding or rebound tenderness.
- Limbs: Normal.
- Neurological: Normal.

