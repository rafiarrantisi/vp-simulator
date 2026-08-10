---
id: em_status_asthmaticus_001
schema_version: 2
status: in_review
specialty: emergency
system: respiratory
presentation: "Worsening shortness of breath unresponsive to inhalers"
presentation_id: "Sesak napas yang semakin berat dan tidak membaik meski sudah menggunakan inhaler"
first_impression: "A person appears severely breathless, unable to speak in full sentences, wheezing."
first_impression_id: "Seseorang tampak sesak berat, tidak bisa bicara kalimat utuh, napas berbunyi."
target_condition: "Acute severe asthma"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["GINA 2024 guidelines for acute asthma"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I can't catch my breath even after using my puffer."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset – when did it start?", critical: true }
    - { item: "Location – where is the discomfort?", critical: false }
    - { item: "Quality – what does it feel like?", critical: false }
    - { item: "Severity – how bad is it on a scale of 0–10?", critical: true }
    - { item: "Timing – constant or comes and goes?", critical: false }
    - { item: "Context – what were you doing when it started?", critical: false }
    - { item: "Alleviating factors – anything that makes it better?", critical: true }
    - { item: "Associated symptoms – do you have cough, wheeze, chest tightness?", critical: false }
  associated_symptoms:
    - { item: "Cough – dry or productive?", critical: false }
    - { item: "Wheezing – audible or only when you breathe out?", critical: false }
    - { item: "Difficulty speaking – can you finish a sentence?", critical: true }
    - { item: "Chest tightness – feeling of pressure?", critical: false }
    - { item: "Anxiety or fear – feeling panicked?", critical: false }
  pmh:
    - { item: "Asthma history – when diagnosed, how controlled?", critical: true }
    - { item: "Previous hospitalizations for breathing problems?", critical: true }
    - { item: "Other chronic conditions (e.g., allergies, heart disease, diabetes)?", critical: false }
  medications:
    - { item: "Current asthma medications (inhalers, pills)?", critical: true }
    - { item: "How often do you use your rescue inhaler?", critical: false }
    - { item: "Any other prescription or over-the-counter medicines?", critical: false }
  family_social:
    - { item: "Family history of asthma or allergies?", critical: false }
    - { item: "Smoking history (yourself or others at home)?", critical: true }
    - { item: "Occupation and living situation?", critical: false }
    - { item: "Recent exposure to triggers (dust, pets, cold, exercise)?", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Unable to speak in full sentences", critical: true }
  - { item: "Using neck muscles to breathe (accessory muscles)", critical: true }
  - { item: "Sweating and heart racing", critical: false }
  - { item: "Cyanosis (blue lips or fingers)", critical: true }
expected_ddx:
  working_diagnosis: "Acute severe asthma"
  differentials: ["Acute exacerbation of COPD", "Anaphylaxis", "Foreign body aspiration"]
investigations:
  appropriate:
    - { name: "Peak expiratory flow (PEF) measurement", expected: "PEF < 50% of predicted" }
    - { name: "Chest X-ray", expected: "Hyperinflation, no infiltrate, no pneumothorax" }
    - { name: "Arterial blood gas (ABG)", expected: "Respiratory alkalosis, mild hypoxemia (PaO2 60-80 mmHg), possible hypercapnia if severe" }
  inappropriate: ["CT chest", "Spirometry (cannot be performed in acute setting)"]
physical_exam_findings:
  general: "Anxious, sitting upright in tripod position, using accessory muscles (sternocleidomastoid, intercostals), diaphoretic. Nasal flaring. Unable to speak full sentences."
  vitals:
    RR: 32
    HR: 120
    BP: 130/80
    SpO2: 88% (room air)
    Temp: 37.0°C
management:
  pharmacological:
    - "Oxygen via nasal cannula or mask to target SpO2 94-98%"
    - "Nebulized salbutamol (5 mg) with oxygen"
    - "Nebulized ipratropium bromide (0.5 mg)"
    - "Systemic corticosteroids: prednisone 40-50 mg PO or IV methylprednisolone 40-80 mg"
    - "Consider IV magnesium sulfate (2 g over 20 min) if poor response"
  non_pharmacological:
    - "Position upright, reassure and calm patient"
    - "Continuous monitoring of SpO2, heart rate, respiratory rate"
    - "Prepare for possible intubation if deteriorating"
  education_safety_netting:
    - "Instruct to use inhaler with spacer at home"
    - "Seek emergency care if symptoms worsen despite treatment"
    - "Follow up with asthma specialist or GP within 48 hours"
    - "Review inhaler technique and daily controller medication adherence"
scoring_weights_override: null
---

## Identity

I'm Tiara Kusuma, 34 years old. I'm a primary school teacher, married to Agus, and we have two young kids – Bunga, 5, and Adi, 7. I'm usually pretty calm and organised, but when my chest gets tight I get scared easily. I've had asthma since I was twelve, but I've been busy lately and haven't been great at taking my brown puffer every day. I don't smoke, and we don't have pets. I try to keep the house clean, but sometimes dust sets me off.

## Opening line

"I can't catch my breath. I've used my blue puffer three times but it's not helping, and I'm really scared."

## How I present

I'm sitting straight up on the edge of the bed, leaning forward with my hands on my knees. My breathing is fast and shallow, and I'm using the muscles in my neck and between my ribs to get air in. I'm sweating, my face is pale, and I can only get out a few words at a time. My eyes are wide open and I look panicked. I keep shaking my head and saying "I can't breathe."

## What I know

- **Onset:** This started about two hours ago, all of a sudden. I was cleaning the living room and dust flew up.
- **Location:** It's all in my chest – feels like a tight band around my ribs.
- **Quality:** Like an elephant sitting on my chest, and I can hear a whistling sound when I breathe out.
- **Severity:** I'd say it's a 9 out of 10. I've never felt this bad before.
- **Timing:** It's been constant since it started, and it's getting worse.
- **Context:** I was dusting the bookshelves – that sometimes triggers my asthma.
- **Alleviating factors:** Nothing helps. I used my blue puffer (albuterol) three times – once when it started, then again after 20 minutes, then a third time. It didn't make any difference.
- **Associated symptoms:** I'm coughing a little, but it's dry. My chest feels tight. I can't finish a sentence – I have to stop after 3 or 4 words. I'm also really anxious and feel like I'm going to die.
- **Cough:** Dry, no phlegm.
- **Wheezing:** I can hear it when I breathe out, and my husband says he can hear it from across the room.
- **Difficulty speaking:** Yes, I can only get out a few words at a time.
- **Chest tightness:** It feels like a heavy weight on my chest.
- **Anxiety:** I'm terrified – I've never had an attack like this.
- **Asthma history:** I was diagnosed at age 12. Usually my asthma is mild, but I've been in hospital twice before – once when I was 16 and once about 5 years ago. Both times I needed oxygen and steroids.
- **Other conditions:** No other health problems.
- **Current medications:** I use a blue puffer (salbutamol) as needed, and a brown puffer (beclomethasone) that I'm supposed to use every day, but I've been forgetting lately. I don't take any other medicines.
- **How often rescue inhaler:** Usually only once or twice a week, but this week I've used it almost every day.
- **Family history:** My mum has asthma.
- **Smoking:** I've never smoked, and no one in my house smokes.
- **Occupation:** I'm a teacher, so I'm around kids all day. I live with my husband and two children.
- **Recent triggers:** Dust from cleaning, and maybe the cold air this morning.
- **Ideas (what I think is wrong):** I think it's a really bad asthma attack – worse than usual.
- **Concerns (what worries me):** I'm scared I'm going to stop breathing altogether. I'm worried about leaving my kids without a mum.
- **Expectations (what I hope for):** I want something that will open up my lungs quickly – maybe oxygen or a strong breathing treatment. I hope I don't need to be put on a machine.

## Communication profile

I have a college degree and speak in complete sentences normally, but right now I'm breathless and can only manage short phrases. I'm very emotional – crying and scared. I tend to answer exactly what's asked and then stop, because talking makes me more breathless. I don't use medical terms – I call my inhaler "the blue puffer" or "the brown puffer". I don't know the diagnosis, just that I have asthma.

## Disclosure rules

I only answer the questions I'm asked, and I keep my answers short. I don't volunteer extra information. If you ask me about my chest tightness, I'll describe it. If you don't ask about my home situation, I won't mention it. I wait for you to prompt me.

## Vital signs
- Temperature: 37.0°C
- Blood pressure: 130/80 mmHg
- Heart rate: 125 bpm
- Respiratory rate: 32 /min
- Oxygen saturation: 88% on room air

## Physical findings
- General appearance: Sitting upright, leaning forward with hands on knees, using neck and rib muscles to breathe, appears very distressed and panicked, pale and sweaty, can only speak a few words at a time.
- Skin: Pale and clammy.
- Head/neck: Neck muscles are tight and pulling with each breath.
- Chest: Breathing is fast and shallow; a whistling sound is heard when breathing out; breathing out takes longer than normal; chest feels tight to the patient; ribs are pulling in between breaths.
- Limbs: Lips and fingertips appear slightly blue.
- Neuro: Alert but extremely anxious, eyes wide open.

