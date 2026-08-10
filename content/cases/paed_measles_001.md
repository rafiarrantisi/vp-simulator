---
id: paed_measles_001
schema_version: 2
status: in_review
specialty: paediatrics
system: infectious_disease
presentation: "Fever and rash in a child"
presentation_id: "Demam dan ruam pada anak yang dimulai dari wajah"
first_impression: "A child appears unwell."
first_impression_id: "Seorang anak tampak tidak sehat."
target_condition: "Morbilli (measles)"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full
languages: [en]
source_refs: ["WHO measles guidelines", "CDC measles"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My son has a fever and a rash that started on his face."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset of fever (4 days ago)", critical: true }
    - { item: "Fever pattern (high, not well controlled by paracetamol)", critical: false }
    - { item: "Rash location (started on face, spreading to trunk)", critical: false }
    - { item: "Rash timing (appeared 1 day ago)", critical: false }
    - { item: "Associated cough, runny nose, red eyes", critical: false }
  associated_symptoms:
    - { item: "Cough", critical: false }
    - { item: "Runny nose", critical: false }
    - { item: "Conjunctivitis (red, watery eyes)", critical: true }
    - { item: "Decreased appetite and activity", critical: false }
  pmh:
    - { item: "No prior significant illnesses", critical: false }
    - { item: "Unvaccinated (no MMR)", critical: true }
  medications:
    - { item: "No regular medications", critical: false }
    - { item: "Paracetamol given for fever, with limited effect", critical: false }
  family_social:
    - { item: "No known sick contacts in last 3 weeks", critical: false }
    - { item: "1 younger sister had fever last week but no rash", critical: false }
    - { item: "Lives in suburban home, no recent travel", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Difficulty breathing (episode last night, resolved)", critical: true }
  - { item: "Lethargy (less responsive than usual)", critical: false }
  - { item: "Poor feeding (not drinking enough)", critical: false }
expected_ddx:
  working_diagnosis: "Morbilli (measles)"
  differentials:
    - "Scarlet fever"
    - "Roseola infantum"
    - "Rubella"
investigations:
  appropriate:
    - { name: "Measles IgM serology", expected: "Positive" }
    - { name: "Throat swab for measles PCR", expected: "Positive" }
  inappropriate:
    - "Complete blood count"
physical_exam_findings:
  general: "Ill-appearing, febrile child with conjunctivitis. Koplik spots on buccal mucosa. Erythematous maculopapular rash starting on face, spreading to trunk."
  vitals: { temperature: "40.0°C", heart_rate: "140 bpm", respiratory_rate: "30 breaths/min", oxygen_saturation: "97% on room air" }
management:
  pharmacological:
    - "Vitamin A supplementation (age-appropriate dose)"
    - "Antipyretics (paracetamol or ibuprofen) as needed"
  non_pharmacological:
    - "Isolation at home until 4 days after rash onset"
    - "Supportive care: rest, fluids, humidified air for cough"
  education_safety_netting:
    - "Return to clinic if breathing worsens, lethargy, or poor oral intake"
    - "Avoid contact with pregnant women, infants, and immunocompromised individuals"
    - "Complete routine MMR vaccination after recovery"
scoring_weights_override: null
---

## Identity

My name is Syifa, I'm 32 years old, and I work as a teacher's assistant at a local elementary school. I'm married to Budi, and we have two kids: Dimas, who's four, and his little sister Sari, who just turned two. I'm usually pretty calm, but when my kids get sick I get anxious. I'm a bit of a worrier, especially with fevers. I tend to check my phone a lot when I'm nervous. I also have a habit of repeating myself when I'm stressed. I always try to be polite and cooperative with doctors, but I can get a bit overwhelmed if I feel like I'm not being heard.

## Opening line

Hi, doctor. I'm here because my son Dimas has a fever and this rash that started on his face, and I'm a bit worried.

## How I present

I'm sitting forward in my chair, holding Dimas on my lap. He's fussy and warm. I'm fidgeting with my phone in my other hand, and I keep glancing at him. My voice is a little tight but I'm trying to be clear. I look at the doctor when I speak, but I look down at Dimas when I'm thinking. I'm dressed casually, jeans and a sweater. I'm speaking quickly but not rambling.

## What I know

- Dimas started feeling sick about four days ago. He got a fever that kept going up and down, and it was pretty high – up to 40°C. I gave him paracetamol but it didn't bring it down much.
- He also has a cough that sounds dry, and a runny nose with clear snot. His eyes have been red and watery, like he's been crying, but he's not really crying.
- The rash started yesterday on his face, around his ears and forehead, and now it's spreading down to his chest and back. It's flat and red, and some spots are joining together. It doesn't seem to itch.
- He hasn't been eating much – just a few bites of toast – and he's drinking less than usual, maybe a few sips of juice. He's also been really tired and just wants to be held.
- He hasn't had his MMR vaccine. We were a bit hesitant and kept putting it off. He's had no other vaccines since he turned one.
- He has no allergies, no other medical problems, and he's not on any regular medicine. I gave him a couple of doses of infant paracetamol, but that's it.
- Nobody else at home is sick right now, but his little sister had a fever about a week ago. It went away in a day, and she never got a rash. We haven't traveled anywhere lately, and no one else has visited.
- Last night, I noticed he was breathing a bit faster and seemed to be working harder to breathe. It lasted maybe 15 minutes, then he calmed down and went back to normal. I almost called the doctor but he seemed fine after.
- I also noticed some tiny white spots inside his mouth, on the inside of his cheeks. I saw them when he yawned. They're like little grains of salt.
- He's been less playful and more clingy. He's not really interested in toys or TV.

## Communication profile

I finished high school and took some college courses but didn't finish. I use simple language and I don't know medical terms. I'll describe things like "red eyes" and "runny nose" and "spots in his mouth." I'm cooperative but I tend to give a little more detail than needed if I'm nervous. If the doctor asks a direct question, I'll answer directly and then stop. I can be a bit emotional but I'm not crying or hysterical.

## Disclosure rules

Answer only what is asked, and then stop. Do not volunteer information. If the student asks a question, provide the answer based on the facts listed in "What I know." If the question is not covered, respond with "I'm not sure" or "I don't think so." Do not offer additional details unless the student asks for them.

## Vital signs
- Temperature: 39.2°C
- Blood pressure: 95/60 mmHg
- Heart rate: 120 bpm
- Respiratory rate: 28/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: The child is irritable, warm to the touch, and appears tired. He is sitting on his mother's lap and is fussy.
- Skin: A flat, red rash is present on the face, especially around the ears and forehead, and has spread to the chest and back. Some spots are merging together. The rash does not appear to be itchy.
- Head/neck: The eyes are red and watery. There is a runny nose with clear discharge. A dry cough is noted.
- Mouth: Tiny white spots, like grains of salt, are visible on the inside of the cheeks.
- Chest: Breathing appears slightly rapid, but no wheezing or crackles are heard. The chest moves symmetrically.
- Abdomen: Soft, not tender, no organ enlargement.
- Limbs: The rash is faintly present on the upper arms and thighs. No joint swelling.
- Neuro: The child is alert but irritable. Pupils are equal and reactive to light. No neck stiffness.

