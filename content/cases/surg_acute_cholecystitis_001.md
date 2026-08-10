---
id: surg_acute_cholecystitis_001
schema_version: 2
status: in_review
specialty: surgery
system: gastrointestinal
presentation: "Right upper quadrant pain"
presentation_id: "Nyeri tajam di perut kanan atas sejak semalam"
first_impression: "Patient appears in pain."
first_impression_id: "Pasien tampak kesakitan."
target_condition: "Acute cholecystitis"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["SAGES guidelines for acute cholecystitis"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have a sharp pain under my right ribs that started last night and won't go away."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain (right upper quadrant)", critical: true }
    - { item: "Onset (sudden, after a heavy meal)", critical: true }
    - { item: "Character (sharp, cramping, or dull)", critical: true }
    - { item: "Radiation (to right shoulder or back)", critical: true }
    - { item: "Associated nausea or vomiting", critical: true }
    - { item: "Aggravating factors (eating fatty foods)", critical: false }
    - { item: "Relieving factors (nothing helps)", critical: false }
    - { item: "Timing (constant, not intermittent)", critical: false }
    - { item: "Exacerbations (worse after meals)", critical: false }
    - { item: "Severity (7/10, bad enough to come to ER)", critical: true }
  associated_symptoms:
    - { item: "Fever or chills", critical: true }
    - { item: "Nausea and vomiting", critical: true }
    - { item: "Loss of appetite", critical: false }
    - { item: "Jaundice or yellowing of skin/eyes", critical: true }
    - { item: "Dark urine or pale stools", critical: false }
  pmh:
    - { item: "Previous gallbladder attacks or gallstones", critical: true }
    - { item: "History of diabetes, hypertension, or obesity", critical: false }
    - { item: "Previous abdominal surgeries", critical: false }
  medications:
    - { item: "Current medications (including over-the-counter)", critical: false }
    - { item: "Allergies to medications", critical: false }
  family_social:
    - { item: "Family history of gallbladder disease", critical: false }
    - { item: "Dietary habits (high-fat diet)", critical: false }
    - { item: "Alcohol use", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever and chills (signs of infection)", critical: true }
  - { item: "Jaundice (possible common bile duct obstruction)", critical: true }
  - { item: "Severe constant pain (possible perforation)", critical: true }
expected_ddx:
  working_diagnosis: "Acute cholecystitis"
  differentials: ["Acute pancreatitis", "Perforated peptic ulcer"]
investigations:
  appropriate:
    - { name: "Abdominal ultrasound", expected: "Thickened gallbladder wall, pericholecystic fluid, gallstones" }
    - { name: "Complete blood count", expected: "Elevated white blood cell count" }
    - { name: "Liver function tests", expected: "Elevated alkaline phosphatase, bilirubin may be normal or mildly elevated" }
    - { name: "Amylase/lipase", expected: "Normal (to rule out pancreatitis)" }
  inappropriate: ["CT abdomen without contrast", "Upper GI series"]
physical_exam_findings:
  general: "Patient appears uncomfortable, holding right upper quadrant, mild distress."
  vitals: { temp: "38.2°C", bp: "130/85", hr: "95", rr: "18", o2_sat: "98%" }
management:
  pharmacological:
    - "IV fluids (normal saline)"
    - "IV antibiotics (e.g., ceftriaxone + metronidazole)"
    - "Analgesics (e.g., morphine or ketorolac)"
  non_pharmacological:
    - "NPO (nothing by mouth) pending surgery"
    - "Laparoscopic cholecystectomy within 24-48 hours"
  education_safety_netting:
    - "Explain need for surgery to remove gallbladder"
    - "Advise to return to ER if pain worsens, fever spikes, or jaundice develops"
    - "Post-operative dietary changes (low-fat diet initially)"
scoring_weights_override: null
---

## Identity

I'm Rina Nugroho, 45 years old. I work as a high school history teacher, and I live with my suami and two remaja in a small town. I'm usually pretty active and healthy, but I've had a few episodes of indigestion after big meals over the past year. I'm a bit anxious about hospitals—I don't like being poked and prodded. I'm a worrier, especially about missing work and letting my students down. I tend to be polite but can get a little short when I'm in pain.

## Opening line

"Doctor, I've got this sharp pain under my right ribs that started last night after a big dinner, and it's not going away. It's really bad."

## How I present

I'm sitting hunched forward in the chair, holding my right side with my hand. My face is pale and sweaty, and I'm breathing shallowly. I make eye contact but look tense and uncomfortable. My voice is strained, and I speak in short sentences because it hurts to take a deep breath.

## What I know

- The pain started suddenly around 9 PM last night, about an hour after I ate a heavy meal of fried chicken and mashed potatoes with gravy.
- It's a sharp, cramping pain right under my right ribs, and it sometimes spreads to my right shoulder blade.
- The pain is constant, about a 7 out of 10, and nothing I do makes it better—not lying down, not sitting up, not taking antacids.
- I've felt nauseous and threw up twice last night. I haven't been able to eat anything since.
- I feel a little feverish and had the chills last night.
- I've had similar but milder pains a few times in the past year after eating fatty foods, but they always went away after a few hours. This one is different—it's not stopping.
- I don't have any yellowing of my skin or eyes, and my urine is normal color.
- I take a daily multivitamin and ibuprofen sometimes for headaches. No other medications.
- I'm allergic to penicillin—it gives me a rash.
- I've never had surgery before, and I don't have diabetes or high blood pressure.
- My mother had her gallbladder removed when she was about my age.
- I drink maybe one glass of wine a week, no smoking.

## Communication profile

I have a college education and speak clearly, but I'm not a medical person. I'll use everyday words like "stomach" for abdomen and "ribs" for the area. I tend to be direct and answer questions honestly, but I can get a little rambly when describing the pain. I'm anxious and want to be taken seriously, so I might repeat myself. I'll stop talking after answering a question, waiting for the next one.

## Disclosure rules

I only answer what I'm asked. If the doctor asks about the pain, I describe it. If they ask about fever, I tell them. I don't volunteer extra information unless prompted. I don't know what's wrong with me—I just know I'm in a lot of pain and need help.

## Vital signs
- Temperature: 38.2 °C
- Blood pressure: 130/85 mmHg
- Heart rate: 98 bpm
- Respiratory rate: 20 /min
- Oxygen saturation: 97%

## Physical findings
- **General appearance**: Anxious, uncomfortable, pale and clammy skin, sitting hunched forward holding right upper abdomen.
- **Skin**: No jaundice, no rash.
- **Head and neck**: Mucous membranes moist, no scleral icterus.
- **Chest**: Lungs clear to auscultation bilaterally, no adventitious sounds.
- **Abdomen**: Tenderness in the right upper quadrant with guarding; positive Murphy's sign (patient stops breathing on deep palpation of right upper quadrant). No rebound tenderness. Bowel sounds normal.
- **Limbs**: No peripheral edema.
- **Neurologic**: Alert and oriented, normal cranial nerves.

