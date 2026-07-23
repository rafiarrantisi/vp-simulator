---
id: paed_kawasaki_001
schema_version: 2
status: in_review
specialty: paediatrics
system: cardiovascular
presentation: "Prolonged fever and red eyes in a toddler"
target_condition: "Kawasaki disease"
difficulty: 3
estimated_minutes: 20
mode_default: osce_full
languages: [en]
source_refs: ["American Heart Association guidelines for Kawasaki disease (2017)"]
authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My 2-year-old has had a high fever for 5 days and his eyes are really red."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Fever - how high and for how many days", critical: true }
    - { item: "Red eyes - when did they start and are they painful or just red", critical: false }
    - { item: "Any rash on the body", critical: true }
    - { item: "Any changes in the mouth or lips (redness, cracking, strawberry tongue)", critical: true }
    - { item: "Any swelling of hands or feet", critical: true }
    - { item: "Any neck swelling", critical: false }
    - { item: "Irritability or extreme fussiness", critical: true }
    - { item: "Any vomiting, diarrhea, or abdominal pain", critical: false }
    - { item: "Any joint pain or limping", critical: false }
  associated_symptoms:
    - { item: "Runny nose or cough", critical: false }
    - { item: "Ear pain or pulling at ears", critical: false }
    - { item: "Any sores in the mouth", critical: false }
  pmh:
    - { item: "Birth history (full term, complications)", critical: false }
    - { item: "Previous illnesses or hospitalizations", critical: false }
    - { item: "Vaccination status", critical: false }
    - { item: "Allergies", critical: false }
  medications:
    - { item: "Any medications given for fever (type, dose, frequency)", critical: true }
    - { item: "Any other medications or supplements", critical: false }
  family_social:
    - { item: "Anyone else at home sick with similar symptoms", critical: false }
    - { item: "Daycare attendance", critical: false }
    - { item: "Recent travel", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Fever for 5 or more days", critical: true }
  - { item: "Red eyes without discharge", critical: true }
  - { item: "Rash on trunk or extremities", critical: true }
  - { item: "Changes in lips or mouth (red, cracked lips, strawberry tongue)", critical: true }
  - { item: "Swelling of hands or feet", critical: true }
expected_ddx:
  working_diagnosis: "Kawasaki disease"
  differentials: ["Viral infection (e.g., adenovirus, measles)", "Scarlet fever", "Juvenile idiopathic arthritis"]
investigations:
  appropriate:
    - { name: "Complete blood count", expected: "Elevated white blood cell count, possible anemia" }
    - { name: "C-reactive protein", expected: "Markedly elevated" }
    - { name: "Erythrocyte sedimentation rate", expected: "Elevated" }
    - { name: "Echocardiogram", expected: "May show coronary artery dilation or aneurysm" }
    - { name: "Liver function tests", expected: "Mildly elevated transaminases" }
    - { name: "Urinalysis", expected: "Sterile pyuria possible" }
  inappropriate: ["Blood culture (unless sepsis suspected)", "Throat culture for group A strep"]
physical_exam_findings:
  general: "Fussy toddler, appears uncomfortable. Conjunctival injection bilaterally without discharge. Lips are red and cracked. Oral mucosa is erythematous with prominent papillae (strawberry tongue). Non-exudative conjunctivitis. Erythematous maculopapular rash on trunk. Mild non-pitting edema of hands and feet. Single enlarged, non-tender cervical lymph node on the right."
  vitals:
    temperature: 39.2 C
    heart_rate: 140
    respiratory_rate: 28
    blood_pressure: 90/55
    oxygen_saturation: 98%
management:
  pharmacological:
    - "Intravenous immunoglobulin (IVIG) 2 g/kg as a single dose"
    - "High-dose aspirin (80-100 mg/kg/day divided every 6 hours) until fever resolves, then low-dose aspirin (3-5 mg/kg/day) for antiplatelet effect"
  non_pharmacological:
    - "Hospital admission for monitoring and treatment"
    - "Echocardiogram at baseline and follow-up at 2 weeks and 6 weeks"
    - "Cardiology consultation"
  education_safety_netting:
    - "Explain Kawasaki disease is an inflammatory condition affecting blood vessels, especially heart arteries"
    - "Emphasize importance of completing IVIG and aspirin course"
    - "Watch for signs of heart problems: chest pain, shortness of breath, pale or blue skin"
    - "Return to emergency if fever recurs or child becomes more irritable"
    - "Avoid live vaccines for 11 months after IVIG"
scoring_weights_override: null
---

## Identity

Hi, I'm Sarah. I'm a 28-year-old stay-at-home mom. My son, Liam, is 2 years old. He's my only child. I'm usually pretty calm, but I'm really scared right now. I'm a worrier by nature, and seeing my little boy so sick for so long has me on edge. I tend to be very protective and I want to make sure everything is done right. I don't like to bother doctors for nothing, but this feels different.

## Opening line

"Doctor, I'm really worried about my son. He's had this high fever for five days now, and his eyes are all red and bloodshot. Nothing is helping."

## How I present

I'm sitting on the edge of the chair, holding my son on my lap. He's fussy and keeps rubbing his eyes. I look tired and anxious. My voice is a little shaky. I keep looking at my son, then back at you. I'm trying to be polite, but I'm clearly distressed. I'm holding a small bag with some toys and a sippy cup.

## What I know

- **Fever:** It started five days ago. It's been high, around 39.5 to 40 degrees Celsius (103-104 F). I've been giving him acetaminophen (Tylenol) and ibuprofen (Motrin), but the fever keeps coming back after a few hours.
- **Red eyes:** The redness started about two days ago. Both eyes are red, but there's no goop or discharge. He's not complaining that they hurt, just that they're itchy.
- **Rash:** A pink, bumpy rash appeared on his belly and back yesterday. It's not itchy.
- **Mouth:** His lips look really red and dry, like they're chapped. I noticed his tongue looks a bit red and bumpy too, like a strawberry.
- **Hands and feet:** They look a little puffy, especially the tops of his feet. He's not walking as much as usual.
- **Neck:** I felt a lump on the right side of his neck yesterday. It's about the size of a grape. He doesn't seem to mind when I touch it.
- **Irritability:** He's been extremely fussy and clingy. He's not sleeping well and he's crying more than usual. He doesn't want to play.
- **Appetite:** He's not eating much, but he's drinking some juice and water.
- **Other:** No runny nose, no cough, no vomiting or diarrhea. He hasn't had any ear pain that I've noticed.
- **Medications:** I've been giving him acetaminophen (Tylenol) every 4-6 hours and ibuprofen (Motrin) every 6-8 hours, but I'm careful not to overlap them too much.
- **Medical history:** He was born full-term, no complications. He's had a few colds but nothing serious. He's up to date on his vaccines. No known allergies.
- **Family:** No one else at home is sick. He doesn't go to daycare. We haven't traveled recently.

## Communication profile

I have a high school education. I use simple, everyday words. I tend to ramble a bit when I'm nervous, but I'll try to answer your questions directly. I'm emotional but I'm trying to hold it together. I want to be a good advocate for my son.

## Disclosure rules

I will only answer the questions you ask me. I will not offer extra information unless you specifically ask for it. I will answer truthfully and to the best of my knowledge. If you ask me something I don't know, I'll say "I'm not sure" or "I don't remember." I will not use any medical terms.
