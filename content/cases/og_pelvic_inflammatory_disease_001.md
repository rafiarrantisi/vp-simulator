---
id: og_pelvic_inflammatory_disease_001
schema_version: 2
status: in_review
specialty: obstetrics_gynaecology
system: reproductive
presentation: "Pelvic pain and discharge"
presentation_id: "Nyeri perut bagian bawah dan keputihan yang tidak normal"
first_impression: "Patient appears to have gynecological concerns."
first_impression_id: "Pasien tampak mengalami masalah ginekologi."
target_condition: "Pelvic inflammatory disease"
difficulty: 2
estimated_minutes: 20
mode_default: anamnesis
languages: [en]
source_refs: ["CDC STI Treatment Guidelines, 2021"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "I have this pain in my lower belly and a weird discharge."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Site of pain (lower abdomen)", critical: true }
    - { item: "Onset (gradual over 3 days)", critical: false }
    - { item: "Character (dull ache, cramping)", critical: false }
    - { item: "Radiation (none)", critical: false }
    - { item: "Associated symptoms (fever, chills)", critical: true }
    - { item: "Time course (worsening)", critical: false }
    - { item: "Exacerbating factors (movement, intercourse)", critical: false }
    - { item: "Severity (moderate, 6/10)", critical: false }
  associated_symptoms:
    - { item: "Abnormal vaginal discharge (yellow-green, foul-smelling)", critical: true }
    - { item: "Pain during intercourse", critical: false }
    - { item: "Irregular bleeding between periods", critical: false }
    - { item: "Urinary frequency or burning", critical: false }
  pmh:
    - { item: "History of sexually transmitted infections", critical: true }
    - { item: "Recent intrauterine device insertion", critical: false }
    - { item: "Previous pelvic infections", critical: false }
  medications:
    - { item: "Current antibiotic use", critical: false }
    - { item: "Oral contraceptive pills", critical: false }
  family_social:
    - { item: "Sexual activity (new partner in past 2 months)", critical: true }
    - { item: "Number of sexual partners", critical: false }
    - { item: "Condom use", critical: true }
    - { item: "History of STI in partner", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever >38°C", critical: true }
  - { item: "Severe lower abdominal pain with rebound tenderness", critical: true }
  - { item: "Vomiting or inability to keep fluids down", critical: true }
expected_ddx:
  working_diagnosis: "Pelvic inflammatory disease"
  differentials: ["Acute appendicitis", "Ectopic pregnancy", "Ovarian cyst rupture"]
investigations:
  appropriate:
    - { name: "Nucleic acid amplification test for Chlamydia trachomatis and Neisseria gonorrhoeae", expected: "Positive for Chlamydia trachomatis" }
    - { name: "Pregnancy test (urine or serum)", expected: "Negative" }
    - { name: "Complete blood count", expected: "Elevated white blood cell count" }
  inappropriate: ["CT abdomen and pelvis without contrast"]
physical_exam_findings:
  general: "Patient appears uncomfortable, guarding lower abdomen."
  vitals: { temperature: 38.2, heart_rate: 95, blood_pressure: 115/75, respiratory_rate: 18 }
management:
  pharmacological:
    - "Ceftriaxone 500 mg IM single dose"
    - "Doxycycline 100 mg PO twice daily for 14 days"
    - "Metronidazole 500 mg PO twice daily for 14 days"
  non_pharmacological:
    - "Hospitalization if severe illness or unable to tolerate oral medications"
    - "Partner treatment and STI screening"
  education_safety_netting:
    - "Complete full course of antibiotics even if symptoms improve"
    - "Avoid sexual intercourse until treatment completed and symptoms resolved"
    - "Return if fever worsens, pain increases, or vomiting develops"
scoring_weights_override: null
---

## Identity

My name is Gita Rahayu. I'm 24 years old and work as a receptionist at a dental office. I live with my roommate in a small apartment. I'm usually pretty healthy and active—I like going for runs and hanging out with friends. Lately, I've been feeling really worried because this pain isn't going away. I'm a bit shy about talking about personal stuff, especially down there, but I know I need help. I'm scared it might be something serious.

## Opening line

"Hi, thanks for seeing me. I've had this pain in my lower belly for a few days now, and there's this discharge that's really bothering me."

## How I present

I'm sitting hunched over a bit, holding my lower stomach. I look tired and a little pale. My voice is quiet, and I avoid eye contact when talking about the discharge. I seem anxious but relieved to be here.

## What I know

- The pain started about three days ago. It's a dull ache, like bad period cramps, but it's not going away.
- The pain is in my lower belly, on both sides. It doesn't shoot anywhere else.
- It hurts more when I move around or have sex. It's about a 6 out of 10 in pain.
- I have a yellow-green discharge that smells bad. It's more than usual.
- I've had some chills and felt feverish on and off. I took my temperature last night and it was 100.5°F.
- I've been spotting a little between my periods, which isn't normal for me.
- I have a new boyfriend. We've been together for about two months. We don't always use condoms.
- I had chlamydia once, about two years ago. I took some pills and it went away.
- I'm not on any medications right now, except for birth control pills.
- I haven't had any surgeries.
- I don't smoke or drink much.

## Communication profile

I speak clearly but quietly. I'm not very medical—I use words like "down there" and "private parts." I might get a bit embarrassed and look away when talking about sex or discharge. I answer questions directly but don't offer extra details unless asked. I'm polite and cooperative.

## Disclosure rules

I only answer what is asked. If the doctor asks about the pain, I describe it but don't bring up the discharge unless asked. If they ask about my sexual history, I'll answer honestly but briefly. I don't volunteer my ideas about what's wrong unless they ask. I wait for the doctor to lead the conversation.

## Vital signs
- Temperature: 38.1°C
- Blood pressure: 110/70 mmHg
- Heart rate: 95 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 98% on room air

## Physical findings
- General appearance: The patient appears tired and pale, sitting hunched over holding her lower stomach.
- Abdomen: There is tenderness in the lower abdomen on both sides. Pressing causes pain, and it hurts more when moving.
- Pelvic exam: There is a yellow-green discharge. During the internal exam, moving the opening of the womb causes pain, and there is tenderness on both sides of the womb.

