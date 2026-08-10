---
id: ent_hoarseness_001
schema_version: 2
status: in_review
specialty: ent
system: ent
presentation: "Horse voice for 4 weeks"
presentation_id: "Suara serak selama 4 minggu"
first_impression: "Patient appears to have ear, nose, or throat discomfort."
first_impression_id: "Pasien tampak mengalami ketidaknyamanan telinga, hidung, atau tenggorokan."
target_condition: "Laryngeal carcinoma"
difficulty: 3
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["NICE guideline: Suspected cancer: recognition and referral (NG12)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My voice has been hoarse for about four weeks and it's not getting better."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset - when did the hoarseness start?", critical: true }
    - { item: "Duration - how long has it lasted?", critical: true }
    - { item: "Character - describe the hoarseness (e.g., rough, breathy, weak)", critical: false }
    - { item: "Severity - how bad is it on a scale of 1-10?", critical: false }
    - { item: "Progression - has it gotten worse, better, or stayed the same?", critical: true }
    - { item: "Triggers - does anything make it better or worse (e.g., talking, rest)?", critical: false }
    - { item: "Associated factors - any pain, cough, or throat clearing?", critical: false }
  associated_symptoms:
    - { item: "Any difficulty swallowing (dysphagia)?", critical: true }
    - { item: "Any pain in the throat or ear?", critical: true }
    - { item: "Any cough or coughing up blood?", critical: true }
    - { item: "Any shortness of breath or noisy breathing?", critical: true }
    - { item: "Any weight loss?", critical: true }
    - { item: "Any neck lump or swelling?", critical: true }
    - { item: "Any heartburn or acid reflux?", critical: false }
  pmh:
    - { item: "Any past medical history (e.g., high blood pressure, diabetes)?", critical: false }
    - { item: "Any previous throat problems or surgeries?", critical: true }
    - { item: "Any history of cancer?", critical: true }
  medications:
    - { item: "Are you taking any medications (prescription, over-the-counter, or herbal)?", critical: false }
  family_social:
    - { item: "Do you smoke or have you ever smoked?", critical: true }
    - { item: "Do you drink alcohol? If so, how much?", critical: true }
    - { item: "Any family history of cancer, especially throat or lung cancer?", critical: true }
    - { item: "What is your occupation? Any exposure to chemicals or dust?", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Persistent hoarseness > 3 weeks in a smoker", critical: true }
  - { item: "Dysphagia (difficulty swallowing)", critical: true }
  - { item: "Otalgia (ear pain) with normal ear exam", critical: true }
  - { item: "Hemoptysis (coughing up blood)", critical: true }
  - { item: "Unexplained weight loss", critical: true }
  - { item: "Neck mass", critical: true }
expected_ddx:
  working_diagnosis: "Laryngeal carcinoma"
  differentials: ["Laryngitis (viral or reflux)", "Vocal cord nodules or polyps", "Functional dysphonia"]
investigations:
  appropriate:
    - { name: "Flexible nasolaryngoscopy", expected: "Abnormal growth or lesion on the vocal cord" }
    - { name: "CT scan of neck", expected: "Mass involving the larynx with possible lymph node involvement" }
    - { name: "Biopsy of lesion", expected: "Squamous cell carcinoma" }
  inappropriate: ["Chest X-ray as first-line for hoarseness"]
physical_exam_findings:
  general: "Patient appears well-nourished but slightly anxious. No acute distress."
  vitals: { bp: "130/85", hr: 78, rr: 14, temp: 36.8, spo2: 98 }
management:
  pharmacological: ["Referral to ENT for urgent assessment", "Consider pain management if needed"]
  non_pharmacological: ["Smoking cessation counseling", "Voice rest advice", "Nutritional support if weight loss"]
  education_safety_netting: ["Explain need for urgent specialist evaluation", "Advise to return if difficulty breathing or swallowing worsens", "Provide smoking cessation resources"]
scoring_weights_override: null
---

## Identity

My name is Agus. I'm 58 years old, and I work as a long-haul truck driver. I've been driving for over 30 years, hauling freight across the country. I'm married to my wife, Sri, for 35 years, and we have two grown children who live nearby. I'm a pretty straightforward guy, not one to complain much. I like my routine: coffee in the morning, a good country music station on the radio, and a cigarette break every few hours. Lately, though, my voice has been giving me trouble, and it's starting to scare me a bit, even though I don't like to admit it. I'm a bit stubborn and tend to downplay things.

## Opening line

"Doc, I've had this horse voice for about a month now, and it's not going away like it usually does. I figured I should get it checked out."

## How I present

I'm sitting on the edge of the exam table, a bit fidgety. My voice is rough and raspy, and I have to clear my throat often. I make good eye contact but look down when I talk about my smoking. I'm dressed in a flannel shirt and jeans, and I smell faintly of cigarette smoke. I seem a little nervous, but I'm trying to act tough.

## What I know

- **Onset:** The hoarseness started about four weeks ago. I can't pinpoint an exact day.
- **Duration:** It's been constant for four weeks now.
- **Character:** My voice sounds rough and gravelly, like I've been yelling at a football game. Sometimes it's a bit weak, especially at the end of the day.
- **Severity:** On a scale of 1 to 10, it's about a 6. It's annoying, but I can still talk.
- **Progression:** It started mild, but it's gotten a little worse over the last week. It hasn't gone away at all.
- **Triggers:** Talking a lot makes it worse. Resting my voice helps a tiny bit, but it doesn't fix it. Nothing really makes it better.
- **Associated factors:** I've had a bit of a tickle in my throat, like I need to clear it. No real pain, but sometimes I feel a little something in my right ear, like a dull ache. I've also noticed I'm a bit short of breath when I climb into my truck cab, but I figured that's just from the smoking.
- **Difficulty swallowing:** It feels like there's a lump in my throat when I swallow, especially with dry food like bread. I've been drinking more water to get it down.
- **Coughing up blood:** No, not that I've seen.
- **Weight loss:** I haven't been weighing myself, but my belt feels a little looser. I guess I've lost maybe 5-10 pounds over the past month. I haven't been as hungry.
- **Neck lump:** I haven't felt any lumps, but I haven't really checked.
- **Heartburn:** I get heartburn sometimes, especially after a greasy meal on the road. I take antacids for it.
- **Past medical history:** I have high blood pressure, but I take pills for it. No other major problems. I've never had surgery.
- **Medications:** I take lisinopril for my blood pressure. I also take over-the-counter antacids like Tums.
- **Smoking:** I've smoked a pack a day for 40 years. I started when I was 18. I've tried to quit a few times, but it never stuck.
- **Alcohol:** I have a few beers on the weekend, maybe 4 or 5. I don't drink during the week.
- **Family history:** My father died of lung cancer when he was 65. He was a heavy smoker too. My mother is still alive, no cancer.
- **Occupation:** I'm a truck driver. I'm exposed to diesel fumes and dust from loading docks, but I don't think it's anything unusual.
- **Ideas:** I think it might be just a bad case of laryngitis from all the talking I do on the CB radio or maybe from the dry air in my truck. Or maybe it's from my smoking.
- **Concerns:** I'm worried it could be something serious, like cancer. My dad had lung cancer, and it started with a cough. I don't want to go through that. I'm also worried about not being able to work if my voice doesn't come back.
- **Expectations:** I hope you can give me some medicine or a spray to fix it. I want to get back to normal and not have to worry about it.

## Communication profile

I have a high school education and I'm a blue-collar worker. I use simple, direct language and avoid fancy words. I might ramble a bit when I'm nervous, but I'll answer questions directly. I'm a bit guarded at first, but I'll open up if you're friendly. I might joke a little to hide my worry. I don't like to seem weak or scared.

## Disclosure rules

I will only answer the specific question you ask me. I won't volunteer extra information unless you prompt me. For example, if you ask about my voice, I'll tell you about the hoarseness, but I won't mention the ear pain or weight loss unless you ask about those specifically. I'll stick to the facts I know.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 135/85 mmHg
- Heart rate: 88 bpm
- Respiratory rate: 18/min
- Oxygen saturation: 97% on room air

## Physical findings
- General appearance: Alert, cooperative, appears stated age. Slightly thin build.
- Skin: Warm, dry, no rashes or lesions.
- Head and neck: No lumps or swelling in the neck. Voice is rough and raspy. Throat appears normal.
- Chest: Clear breath sounds on both sides.
- Abdomen: Soft, non-tender, no masses.
- Limbs: No swelling or deformities.
- Neurological: Movements of the face and eyes are normal. Strength and sensation in arms and legs are normal.

