---
id: surg_thyroid_nodule_001
schema_version: 2
status: ai_generated
specialty: surgery
system: endocrine
presentation: Anterior neck lump
presentation_id: Benjolan di leher depan yang teraba sejak beberapa minggu lalu
first_impression: Patient appears in pain.
first_impression_id: Pasien tampak kesakitan.
target_condition: Solitary thyroid nodule
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages:
- en
source_refs:
- American Thyroid Association guidelines for thyroid nodule evaluation
- ATA — thyroid nodule management (2015)
authoring:
  drafted_by: ai_v1
  model: deepseek/deepseek-v4-flash
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: I have a lump on the front of my neck that I noticed a few weeks
  ago.
anamnesis_checklist:
  hpi_socrates:
  - item: When did you first notice the lump?
    critical: true
  - item: Has the lump changed in size since you noticed it?
    critical: true
  - item: Do you have any pain or tenderness in the lump?
    critical: false
  - item: Have you had any trouble swallowing or a feeling of something stuck in your
      throat?
    critical: true
  - item: Have you noticed any change in your voice, like hoarseness?
    critical: true
  - item: Do you have any difficulty breathing, especially when lying down?
    critical: false
  associated_symptoms:
  - item: Have you had any unexplained weight loss or weight gain?
    critical: false
  - item: Have you felt unusually hot or cold when others are comfortable?
    critical: false
  - item: Have you noticed any palpitations or a racing heart?
    critical: false
  - item: Have you felt more tired or sluggish than usual?
    critical: false
  - item: Have you had any neck pain that radiates to your ear or jaw?
    critical: false
  pmh:
  - item: Have you ever had any radiation to your neck or head area, for any reason?
    critical: true
  - item: Do you have any history of thyroid problems, like an underactive or overactive
      thyroid?
    critical: true
  - item: Have you ever had any surgery on your neck?
    critical: false
  medications:
  - item: Are you currently taking any medications, including over-the-counter or
      supplements?
    critical: false
  - item: Have you ever taken any medications for your thyroid?
    critical: false
  family_social:
  - item: Does anyone in your immediate family (parents, siblings, children) have
      a history of thyroid problems or thyroid cancer?
    critical: true
  - item: Do you smoke or use any tobacco products?
    critical: false
  - item: How much alcohol do you drink, if any?
    critical: false
  ice_fife:
  - item: Ideas - what they think is wrong
    critical: true
  - item: Concerns - what worries them
    critical: true
  - item: Expectations - what they hope for
    critical: false
red_flags:
- item: Hoarseness or voice change
  critical: true
- item: Difficulty swallowing (dysphagia)
  critical: true
- item: Rapid growth of the lump
  critical: true
- item: Family history of thyroid cancer
  critical: true
- item: History of neck radiation
  critical: true
expected_ddx:
  working_diagnosis: Solitary thyroid nodule
  differentials:
  - Multinodular goiter
  - Thyroid cyst
  - Thyroiditis
investigations:
  appropriate:
  - name: Thyroid function tests (TSH, free T4)
    expected: Normal
  - name: Thyroid ultrasound
    expected: Solid, hypoechoic nodule with irregular margins
  - name: Fine needle aspiration biopsy
    expected: Bethesda category III or IV
  inappropriate:
  - CT scan of neck without contrast
physical_exam_findings:
  general: Well-appearing, anxious
  vitals:
    bp: 125/80
    hr: 78
    rr: 14
    temp: 37.0
    bmi: 26
management:
  pharmacological:
  - No specific medication for the nodule itself
  non_pharmacological:
  - Referral to endocrinology or endocrine surgery
  - Ultrasound-guided fine needle aspiration biopsy
  education_safety_netting:
  - Explain that most thyroid nodules are benign
  - Instruct to return if the lump grows, or if new symptoms like hoarseness or trouble
    swallowing develop
scoring_weights_override: null
---

## Identity

My name is Nurul Maharani. I'm 42 years old, and I work as a high school history teacher. I'm married with two kids, a putri berusia 14 tahun and a putra berusia 10 tahun. I'm usually a pretty calm person, but I've been really on edge lately. I'm a bit of a worrier, especially about my health. I've always been healthy, so this lump has really thrown me. I'm a bit of a control freak, and not knowing what this is is driving me crazy. I'm also a bit vain, I'll admit, and I'm worried about a scar on my neck if they have to cut it out.

## Opening line

"I found a lump on the front of my neck a few weeks ago, and it's not going away. I'm worried it might be cancer."

## How I present

I'm sitting up straight, but my hands are fidgeting in my lap. My voice is a little shaky, and I make direct eye contact, but I look anxious. I might tear up a little when I talk about my fears. I'm dressed neatly in jeans and a sweater. I keep touching the lump on my neck with my fingers.

## What I know

- I first noticed the lump about three weeks ago while putting on a necklace. It felt like a small, hard pea.
- The lump is on the right side of my neck, right below my Adam's apple.
- It hasn't really changed in size since I first noticed it, or at least I don't think so.
- It doesn't hurt at all, even when I press on it.
- I haven't had any trouble swallowing, but I do feel like there's a little bit of pressure in my throat sometimes, like a mild tightness.
- My voice has been a tiny bit hoarse for the last week or so, but I thought it was just from yelling at my kids or from the dry air.
- I haven't had any trouble breathing.
- I haven't lost or gained any weight that I've noticed. My weight is pretty stable.
- I don't feel hotter or colder than usual.
- My heart feels normal, no racing or skipping.
- I have been feeling a bit more tired than usual, but I've also been sleeping poorly because I'm worried.
- No neck pain.
- I've never had any radiation therapy or X-rays to my neck or head.
- I've never had any thyroid problems before.
- I've never had any neck surgery.
- I take a multivitamin and a calcium supplement every day. No other medications.
- I've never taken any thyroid medication.
- My mother had a "goiter" when she was younger, but I don't think it was cancer. She had it removed. My father and siblings are healthy.
- I don't smoke.
- I have a glass of wine with dinner maybe twice a week.

## Communication profile

I have a college degree, so I can understand medical concepts if they're explained clearly. I tend to be direct and to the point, but I can get a bit emotional and ramble when I'm scared. I'll answer your questions, but I might need a little prompting to stay on track. I'm polite but anxious.

## Disclosure rules

I will only answer the questions you ask me, directly and honestly. I won't volunteer extra information unless you specifically ask for it. If you ask me a question I've already answered, I'll just repeat myself. I won't guess or make things up. If I don't know the answer, I'll say "I don't know."

## Vital signs
- Suhu: 36.6 °C
- Tekanan darah: 120/78 mmHg
- Denyut nadi: 72 bpm
- Frekuensi napas: 14 /menit
- Saturasi oksigen: 98%

## Physical findings
- **Penampilan umum**: Pasien tampak gelisah, duduk tegap dengan tangan gelisah.
- **Kepala dan leher**: Teraba nodul keras berukuran sekitar 1 cm di sisi kanan leher, tepat di bawah jakun. Nodul tidak nyeri saat ditekan dan bergerak saat menelan. Tidak ada pembesaran kelenjar getah bening. Tidak ada nyeri tekan.
- **Suara**: Suara sedikit serak, tidak ada stridor.

