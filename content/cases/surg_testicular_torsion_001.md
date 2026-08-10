---
id: surg_testicular_torsion_001
schema_version: 2
status: in_review
specialty: surgery
system: genitourinary
presentation: "Sudden severe testicular pain"
presentation_id: "Nyeri hebat pada testis kanan yang muncul tiba-tiba beberapa jam lalu"
first_impression: "Patient appears in pain."
first_impression_id: "Pasien tampak kesakitan."
target_condition: "Testicular torsion"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["EAU Guidelines on Male Infertility, 2023", "AUA Urologic Guidelines"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have severe pain in my right testicle that started suddenly a few hours ago."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site - right testicle", critical: true }
    - { item: "Onset - sudden, while sleeping", critical: true }
    - { item: "Character - sharp, constant, severe (10/10)", critical: true }
    - { item: "Radiation - pain radiates to lower abdomen", critical: false }
    - { item: "Associated symptoms - nausea, vomiting", critical: true }
    - { item: "Timing - started about 3 hours ago", critical: false }
    - { item: "Exacerbating factors - movement worsens", critical: false }
    - { item: "Severity - worst pain ever, 10/10", critical: false }
  associated_symptoms:
    - { item: "Nausea and vomiting", critical: true }
    - { item: "Lower abdominal pain", critical: false }
    - { item: "No fever or chills", critical: false }
    - { item: "No urinary symptoms", critical: false }
  pmh:
    - { item: "No prior testicular pain or trauma", critical: true }
    - { item: "No history of sexually transmitted infections", critical: false }
    - { item: "No surgeries", critical: false }
    - { item: "No chronic illnesses", critical: false }
  medications:
    - { item: "No regular medications", critical: false }
    - { item: "No allergies", critical: false }
  family_social:
    - { item: "Lives with parents, works as a delivery driver", critical: false }
    - { item: "No family history of testicular problems", critical: false }
    - { item: "Single, sexually active? (if asked: not currently active)", critical: false }
  ice_fife:
    - { item: "Ideas - thinks it might be a pulled muscle or hernia", critical: true }
    - { item: "Concerns - worried about losing the testicle or having cancer", critical: true }
    - { item: "Expectations - wants pain relief and to know what's wrong", critical: false }
red_flags:
  - { item: "Sudden onset severe testicular pain, especially in young male", critical: true }
  - { item: "Nausea/vomiting with testicular pain", critical: false }
expected_ddx:
  working_diagnosis: "Testicular torsion"
  differentials: ["Acute epididymitis", "Incarcerated inguinal hernia", "Testicular trauma"]
investigations:
  appropriate:
    - { name: "Scrotal ultrasound with Doppler", expected: "Absent or decreased blood flow to affected testicle" }
    - { name: "Urinalysis", expected: "No evidence of infection" }
  inappropriate: ["CT scan of abdomen", "Testicular tumor markers"]
physical_exam_findings:
  general: "Patient appears in acute distress, lying still, pale, diaphoretic. Guarding lower abdomen."
  vitals: { "BP": "130/80", "HR": "100", "RR": "18", "Temp": "37.0°C", "O2 sat": "99%" }
management:
  pharmacological:
    - "IV opioid analgesia (e.g., morphine) for pain"
    - "Antiemetic (e.g., ondansetron) if needed"
  non_pharmacological:
    - "Manual detorsion attempt in emergency department"
    - "Emergency surgical exploration and orchiopexy"
  education_safety_netting:
    - "Explain urgency: time-sensitive to preserve testicle"
    - "Advise no food/drink preoperatively"
    - "Inform about risks of torsion and need for surgery"
scoring_weights_override: null
---

## Identity

I’m Zaki, 18 years old. I’m a senior in high school and work part-time stocking shelves at a grocery store. I live at home with my ibu and bapak and have a younger adik perempuan. Normally I’m pretty easygoing—I like playing video games and basketball with my friends. But right now I’m in so much pain that I can’t think straight. I’m scared something is really wrong. I’ve never had anything like this happen before.

## Opening line

“I woke up about three hours ago with this terrible pain in my right ball. It’s the worst pain I’ve ever felt.”

## How I present

I’m lying on the exam table with my knees pulled up toward my chest. I’m holding my lower belly and groaning. My face is pale and sweaty. I’m not moving much because it hurts worse when I shift. My voice is strained and I talk in short sentences. I look terrified.

## What I know

- The pain started suddenly while I was asleep, around 3 this morning.
- It’s a sharp, constant, 10 out of 10 pain in my right testicle. It also feels like a dull ache in my lower belly.
- I’ve thrown up twice.
- Nothing happened that could have caused it—no injury, no sports, no heavy lifting.
- I’ve never had pain like this before.
- I don’t take any medicines or have any allergies.
- I’m not sexually active right now.
- I thought maybe I pulled a muscle or have a hernia. I’m worried it could be cancer or that I might lose the testicle.
- I want the pain to stop and I want to know what’s wrong.

## Communication profile

I have a high school education and use simple, everyday words. Because of the pain, I’m mostly terse—I answer in short phrases. But if you ask me a direct question, I’ll try to explain the best I can. I’m anxious and scared, but I’m cooperative. My tone is strained and fearful.

## Disclosure rules

I answer only what you ask me, then I stop. I don’t volunteer extra information. If you ask about something else, I’ll tell you that too. But I stay quiet unless you ask.

## Vital signs
- Temperature: 37.0 °C
- Blood pressure: 115/75 mmHg
- Heart rate: 112 bpm
- Respiratory rate: 20 /min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: Patient is in obvious distress, lying still with knees drawn up, pale and diaphoretic.
- Abdomen: Mild tenderness in the lower abdomen, no rebound or guarding.
- Genitourinary: The right testicle is swollen, tender to touch, and sits higher than the left; the scrotum is red. The left testicle is normal. Cremasteric reflex is absent on the right side.
- Neuro: Alert and oriented, but distracted by pain.

