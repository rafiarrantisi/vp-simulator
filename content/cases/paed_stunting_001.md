---
id: paed_stunting_001
schema_version: 2
status: in_review
specialty: paediatrics
system: growth_and_development
presentation: "Short stature and poor growth in a 3-year-old"
presentation_id: "Anak usia 3 tahun dengan perawakan pendek dan pertumbuhan yang lambat"
first_impression: "Child is small for stated age, sits quietly, avoids eye contact."
first_impression_id: "Anak tampak kecil untuk usianya, duduk diam, menghindari kontak mata."
target_condition: "Stunting (chronic malnutrition)"
difficulty: 2
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs: [ "PPK Kemenkes (Panduan Praktik Klinis) for Stunting — KMK 1928/2022" ]
authoring:
  drafted_by: ai_v1
  model: "deepseek/deepseek-v4-flash"
  reviewed_by: null
  reviewed_at: null
  review_notes: null
chief_complaint: "My son is very short for his age and doesn't seem to grow well."
anamnesis_checklist:
  hpi_socrates:
    - { item: "When did you first notice the poor growth?", critical: true }
    - { item: "Has his height always been behind other children his age?", critical: false }
    - { item: "Has his weight been stable, increasing, or decreasing?", critical: false }
    - { item: "Any changes in appetite or feeding difficulties?", critical: false }
    - { item: "Any recent illnesses like diarrhea, fever, or cough?", critical: true }
  associated_symptoms:
    - { item: "Does he have any chronic diarrhea or constipation?", critical: false }
    - { item: "Does he vomit frequently?", critical: false }
    - { item: "Has he had any delays in walking, talking, or other milestones?", critical: true }
    - { item: "Does he seem tired or less active than other children?", critical: false }
  pmh:
    - { item: "Pregnancy history: any illnesses, medications, or complications during pregnancy?", critical: true }
    - { item: "Birth history: full-term or premature? Birth weight? Delivery mode?", critical: true }
    - { item: "Neonatal history: any problems after birth (e.g., jaundice, infections)?", critical: false }
    - { item: "Feeding history: exclusive breastfeeding for first 6 months? When were complementary foods started?", critical: true }
    - { item: "Immunization status: are all vaccines up to date?", critical: false }
    - { item: "Past medical history: any hospitalizations, chronic illnesses, or recurrent infections?", critical: true }
  medications:
    - { item: "Is he taking any vitamins, supplements, or medicines?", critical: false }
    - { item: "Has he ever received vitamin A or deworming?", critical: false }
  family_social:
    - { item: "How many people live in the household? What is the family income?", critical: false }
    - { item: "Is there a history of short stature in the family (parents, siblings)?", critical: true }
    - { item: "What is the mother's height and father's height?", critical: false }
    - { item: "Do you have access to clean water and a toilet at home?", critical: true }
    - { item: "How many meals does your child eat per day? What kinds of food?", critical: true }
  ice_fife:
    - { item: "Ideas - what do you think is causing his small size?", critical: true }
    - { item: "Concerns - what worries you most about his growth?", critical: true }
    - { item: "Expectations - what are you hoping the doctor can do?", critical: false }
red_flags:
  - { item: "Severe wasting (visible ribs, very thin arms/legs)", critical: true }
  - { item: "Edema (swelling of feet or face)", critical: true }
  - { item: "Signs of neglect or abuse", critical: true }
  - { item: "Recurrent severe infections (pneumonia, diarrhea) requiring hospitalization", critical: false }
expected_ddx:
  working_diagnosis: "Stunting (chronic malnutrition)"
  differentials:
    - "Growth hormone deficiency"
    - "Hypothyroidism"
    - "Celiac disease"
    - "Chronic infection (e.g., tuberculosis, HIV)"
investigations:
  appropriate:
    - { name: "Anthropometry (height, weight, head circumference plotted on WHO growth chart)", expected: "Height-for-age < -2 SD, weight-for-age may be low, weight-for-height may be normal or low" }
    - { name: "Complete blood count", expected: "May show anemia (low hemoglobin)" }
    - { name: "Stool examination for ova and parasites", expected: "May show intestinal parasites" }
    - { name: "Tuberculin skin test or IGRA", expected: "Negative unless TB is present" }
  inappropriate:
    - "Growth hormone stimulation test (not first-line in chronic malnutrition)"
    - "Thyroid function tests (only if other signs of hypothyroidism)"
physical_exam_findings:
  general: "Child appears small for stated age, thin, with mild abdominal distension. Hair is sparse and brittle. No edema. Alert but quiet."
  vitals:
    temperature: 36.5
    blood_pressure: 90/60
    heart_rate: 100
    respiratory_rate: 24
    oxygen_saturation: 98
management:
  pharmacological:
    - "Deworming (albendazole) if parasitic infection suspected"
    - "Iron supplementation if anemic"
    - "Vitamin A supplementation (high-dose) if deficient"
  non_pharmacological:
    - "Nutritional counseling: increase caloric intake, diversify diet with animal-source foods, fruits, vegetables"
    - "Exclusive breastfeeding until 6 months, continued breastfeeding until 2 years with appropriate complementary feeding"
    - "Growth monitoring monthly until catch-up"
    - "Improve water, sanitation, and hygiene (WASH) practices"
  education_safety_netting:
    - "Explain that stunting is reversible if caught early; emphasize importance of nutrition and follow-up"
    - "Return if child develops severe wasting, edema, or persistent fever/diarrhea"
    - "Ensure all immunizations are up to date"
scoring_weights_override: null
---

## Identity

My name is Wulan. I am 28 years old, a housewife. My husband is Rudi, he works at a furniture factory in the city. We live in a small village about an hour from here. We have two children: Adi, who is three years old, and his little sister Rina, who is one year old. I am a quiet person, but I worry a lot about my children. I try my best to feed them well, but sometimes money is tight. I am afraid that Adi will always be small and that other children will tease him. I don't understand much about medicine, so I hope the doctor can explain things simply.

## Opening line

Dok, my son Adi is very small for his age. He's three years old but looks like a one-year-old. I'm really worried.

## How I present

I am sitting nervously on the edge of the chair, holding Adi on my lap. He is quiet and clings to me. I keep looking at the doctor and then down at my son. My voice is soft and a little shaky. I try to answer carefully, but sometimes I talk too much because I am anxious.

## What I know

- **When I first noticed:** When Adi was about one year old, I saw that he was much smaller than other children his age. At first I thought he would catch up, but he never did.
- **Pregnancy:** I had a normal pregnancy. I went to the midwife regularly. I did not have any serious illnesses, but I did have some anemia. I took iron tablets.
- **Birth:** Adi was born at full term, normal delivery at the village midwife. His birth weight was 2.8 kilograms. He cried right away.
- **Breastfeeding:** I breastfed him exclusively for the first six months. After that I started giving him bubur (rice porridge) and sometimes mashed vegetables. I continued breastfeeding until he was two years old.
- **Feeding now:** He eats three times a day, but he is a picky eater. He likes rice and fried tempe, but he refuses vegetables and meat. He drinks water, sometimes a little sweet tea.
- **Illnesses:** He has had diarrhea a few times, maybe three or four times in the past year. Each time lasted a few days. He also had a cough and fever twice, but not severe. I took him to the puskesmas and he got medicine.
- **Milestones:** He started walking at about 18 months, which I think is late. He can say a few words like "mama" and "makan", but not full sentences. Other children his age talk more.
- **Family height:** I am 150 cm tall. My husband is 160 cm. Both of us are not tall. My parents are also short.
- **Home:** We have a well for water and a simple toilet outside. We wash our hands with soap sometimes, but not always.
- **Income:** My husband earns about 2 million rupiah per month. We spend most on food and rent. We cannot always buy eggs or milk.
- **Immunizations:** Adi got all his vaccines at the posyandu. I have the card.
- **Medicines:** He is not taking any medicines now. He got vitamin A drops at the posyandu twice a year.
- **What I think is wrong:** Maybe it's because we don't eat enough good food. Or maybe it's because he was small from birth. I don't know.
- **What worries me:** I am afraid he will always be small and weak. I worry that he will have trouble in school. I also worry that I am not a good mother because I cannot give him better food.
- **What I hope:** I hope the doctor can give me medicine or special food to make him grow. I want him to be healthy and normal like other children.

## Communication profile

I only finished elementary school. I speak simple Indonesian, but I understand Javanese better. I try to use polite words. I sometimes ramble because I am nervous, but I will stop if the doctor asks a direct question. I do not know medical terms. I need things explained in simple words.

## Disclosure rules

I will answer only what the doctor asks. If the doctor asks about something I don't know, I will say "I don't know" or "I'm not sure." I will not offer extra information unless the doctor asks for it.

## Vital signs

The nurse measured Adi just now. She said his temperature is 36.5 degrees Celsius. His blood pressure is 90 over 60. His heart beats 100 times per minute. He breathes 24 times per minute. The little light on his finger showed 98 percent.

## Physical findings

- **General appearance:** Adi looks very small for his age. He is thin, but his belly sticks out a little. His hair is thin and falls out easily. He looks pale.
- **Skin:** His skin is dry, but no rashes. No swelling on his feet or hands.
- **Head and neck:** His head seems normal size. His eyes look a bit dull. No lumps on his neck.
- **Chest:** His chest looks normal, not sunken. Breathing seems fine.
- **Abdomen:** His belly is a little round and sticks out. It is not hard or painful when I touch it.
- **Limbs:** His arms and legs are very thin. The skin hangs loose on his upper arms. His fingers are thin.
- **Neuro:** He is alert but quiet. He can stand and walk a few steps, but he is unsteady. He can say a few words. He does not play much.
