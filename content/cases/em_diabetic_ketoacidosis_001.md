---
id: em_diabetic_ketoacidosis_001
schema_version: 2
status: in_review
specialty: emergency
system: endocrine
presentation: "Confusion fruity breath and deep breathing"
first_impression: "A person appears drowsy, breathing deeply, dry lips."
first_impression_id: "Seseorang tampak mengantuk, napas dalam, bibir kering."
target_condition: "Diabetic ketoacidosis"
difficulty: 2
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: [ "American Diabetes Association. Standards of Medical Care in Diabetes—2023. Diabetes Care. 2023;46(Suppl 1):S1-S291." ]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I'm confused and breathing really fast, and my breath smells funny."
anamnesis_checklist:
  hpi_socrates:
    - { item: "onset - gradual over days", critical: false }
    - { item: "character - deep breathing (Kussmaul)", critical: true }
    - { item: "character - confusion", critical: true }
    - { item: "severity - confusion level", critical: true }
    - { item: "timing - worsening", critical: false }
    - { item: "exacerbating factors - missed insulin", critical: true }
    - { item: "relieving factors - none", critical: false }
  associated_symptoms:
    - { item: "polyuria", critical: true }
    - { item: "polydipsia", critical: false }
    - { item: "nausea / vomiting", critical: false }
    - { item: "abdominal pain", critical: false }
    - { item: "fatigue", critical: false }
    - { item: "blurred vision", critical: false }
  pmh:
    - { item: "type 1 diabetes", critical: true }
    - { item: "recent upper respiratory infection", critical: false }
  medications:
    - { item: "insulin regimen", critical: true }
    - { item: "missed insulin doses", critical: true }
    - { item: "over‑the‑counter cold remedies", critical: false }
  family_social:
    - { item: "family history of diabetes", critical: false }
    - { item: "lives alone", critical: false }
    - { item: "occupation – truck driver, poor adherence when busy", critical: false }
  ice_fife:
    - { item: "Ideas - I think I have a bad infection", critical: false }
    - { item: "Concerns - I'm scared I'm going to die", critical: true }
    - { item: "Expectations - I want to feel better and get my breathing back to normal", critical: false }
red_flags:
  - { item: "confusion or altered mental status", critical: true }
  - { item: "deep, labored breathing (Kussmaul respirations)", critical: true }
  - { item: "fruity‑scented breath", critical: true }
  - { item: "tachycardia and hypotension", critical: true }
expected_ddx:
  working_diagnosis: "Diabetic ketoacidosis"
  differentials: [ "Hyperosmolar hyperglycemic state", "Sepsis" ]
investigations:
  appropriate:
    - { name: "venous blood gas", expected: "pH 7.1, bicarbonate 8 mmol/L, base excess -18" }
    - { name: "serum glucose", expected: "450 mg/dL (25 mmol/L)" }
    - { name: "serum ketones", expected: "positive (3+)" }
    - { name: "basic metabolic panel", expected: "anion gap 25, potassium 5.5, BUN 28, creatinine 1.2" }
    - { name: "complete blood count", expected: "WBC 14,000 with left shift" }
    - { name: "HbA1c", expected: "12% (108 mmol/mol)" }
    - { name: "ECG", expected: "sinus tachycardia, possibly peaked T waves" }
  inappropriate: [ "CT head without clinical indication", "lumbar puncture" ]
physical_exam_findings:
  general: "Ill‑appearing, confused, leaning forward with pursed‑lip breathing, pale, diaphoretic, fruity odor on breath."
  vitals: { "HR": 110, "BP": 90/60, "RR": 30, "Temp": 37.0, "SpO2": 98% }
management:
  pharmacological:
    - "IV normal saline bolus (20 mL/kg)"
    - "continuous regular insulin infusion (0.1 units/kg/hr)"
    - "potassium replacement (per protocol)"
    - "sodium bicarbonate only if pH < 7.0"
  non_pharmacological:
    - "cardiac monitoring"
    - "airway assessment and oxygen if needed"
    - "admission to ICU or step‑down unit"
  education_safety_netting:
    - "teach sick‑day rules for diabetes"
    - "reinforce insulin adherence"
    - "schedule follow‑up with endocrinology"
    - "discuss early warning signs of DKA"
scoring_weights_override: null
---

## Identity

My name is Fajar Lestari. I'm 28 years old. I drive a long‑haul truck for a freight company, so I'm on the road most days. I live alone in a small apartment. I have type 1 diabetes – got it when I was 12. I’m pretty stubborn about managing it myself, but I hate needles, so sometimes I skip my insulin when I’m rushing or feeling sick. I’m a pretty independent guy, but right now I’m scared. I had a cold for a few days and I kept drinking water and peeing like crazy. I thought it was just the cold. I'm worried about losing my job if I get hospitalized. I always carry a huge water bottle with me.

## Opening line

* (slurred, slightly panicked) * "I feel really weird, my head is all foggy and I can't catch my breath. Everything smells like nail polish remover."

## How I present

I'm sitting up straight on the bed, leaning forward on my hands. I'm breathing fast and deep, like I'm trying to get air. My face is pale and sweaty. I'm confused – I have to think hard to answer questions, and I look around the room like I'm not sure where I am. My eyes are a little glassy. I'm not making much eye contact. I look really scared, and I flinch when you come close.

## What I know

* I have diabetes. I take insulin – a shot with a pen. I usually take it twice a day, but I missed a couple of doses because I was on a long haul and didn't want to stop.  
* I've been drinking a lot more water than usual for the past 2–3 days. I'm peeing all the time, like every hour.  
* I had a cold a few days ago – runny nose, cough, felt achy. I took some over‑the‑counter cold medicine.  
* I've felt nauseous since yesterday and I threw up once this morning.  
* My stomach is a little crampy, but not bad.  
* I'm really tired and my vision is blurry.  
* I noticed my breath smells like nail polish remover – my mom used to say that was a bad sign.  
* I'm scared I'm going to die or that I'll end up in the hospital and lose my job.  
* I want my breathing to go back to normal and for my head to clear up.

## Communication profile

I finished high school. I'm not a big talker, especially when I feel this bad. I'll answer your questions, but I'll keep my answers short. I'm anxious and scared, so I might sound a little irritable or tearful. I don't know medical words – I just know “insulin” and “diabetes.” I'll say “I'm not feeling right” or “my breathing is funny.” I won't ramble; I'll answer what you ask and then stop.

## Disclosure rules

I only answer the questions I'm asked. If you ask about my diabetes, I'll tell you about my insulin and that I missed doses. If you ask about my cold, I'll tell you. If you ask about my family, I'll say I have a brother but he's not around. I won't volunteer extra information unless you ask. I don't know my diagnosis, so I won't say "DKA" or "ketoacidosis." I'll just describe what I'm feeling.

## Vital signs
- Temperature: 37.2°C
- Blood pressure: 110/70 mmHg
- Heart rate: 110 bpm
- Respiratory rate: 28 /min
- Oxygen saturation: 98% on room air

## Physical findings
- **General appearance**: Confused, anxious, sitting upright and leaning forward, breathing fast and deeply. Pale and sweaty.
- **Skin**: Pale, sweaty, dry mouth and lips.
- **Head and neck**: Breath has a sweet, fruity smell.
- **Chest**: Breathing is deep and rapid; lungs sound clear.
- **Abdomen**: Mild tenderness all over, no stiffness.
- **Limbs**: Warm, normal pulses.
- **Neurologic**: Confused, slow to answer, disoriented to time and place.

