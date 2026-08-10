---
id: derm_rosacea_001
schema_version: 2
status: in_review
specialty: dermatology
system: integumentary
presentation: "Facial redness and flushing"
presentation_id: "Wajah merah dan memerah terus, serta muncul bintil yang tidak kunjung hilang"
first_impression: "Patient appears to have skin concerns."
first_impression_id: "Pasien tampak memiliki masalah kulit."
target_condition: "Acne rosacea"
difficulty: 1
estimated_minutes: 15
mode_default: anamnesis
languages: [en]
source_refs:
  - "American Academy of Dermatology guidelines for rosacea"
  - "National Rosacea Society / AAD rosacea guidelines (2017)"

authoring: { drafted_by: ai_v1, model: "deepseek/deepseek-v4-flash", reviewed_by: null, reviewed_at: null, review_notes: null }
chief_complaint: "My face keeps getting red and flushing, and I have bumps that won't go away."
anamnesis_checklist:
  hpi_socrates:
    - { item: "Onset: when did this start?", critical: true }
    - { item: "Triggers: what makes the redness worse (e.g., sun, heat, spicy food, alcohol)?", critical: false }
    - { item: "Location: which parts of the face are affected?", critical: false }
    - { item: "Quality: is the redness constant or does it come and go?", critical: false }
    - { item: "Severity: how bothersome is it on a scale of 1-10?", critical: false }
    - { item: "Timing: does it happen at certain times of day or season?", critical: false }
    - { item: "Context: what were you doing when it first appeared?", critical: false }
    - { item: "Exacerbating factors: anything that makes it worse?", critical: false }
    - { item: "Relieving factors: anything that helps?", critical: false }
  associated_symptoms:
    - { item: "Burning or stinging sensation", critical: false }
    - { item: "Dryness or flaking", critical: false }
    - { item: "Bumps (papules, pustules) - are they present?", critical: true }
    - { item: "Eye irritation (grittiness, redness, blurred vision)", critical: true }
  pmh:
    - { item: "History of acne or other skin conditions", critical: false }
    - { item: "History of sunburns or frequent sun exposure", critical: false }
    - { item: "Known allergies", critical: false }
  medications:
    - { item: "Current skin care products (cleansers, moisturizers, prescription creams)", critical: false }
    - { item: "Any topical steroids or antibiotics used on face", critical: false }
  family_social:
    - { item: "Family history of rosacea or acne", critical: false }
    - { item: "Alcohol consumption", critical: false }
    - { item: "Dietary habits (spicy foods, hot drinks)", critical: false }
  ice_fife:
    - { item: "Ideas - what they think is wrong", critical: true }
    - { item: "Concerns - what worries them", critical: true }
    - { item: "Expectations - what they hope for", critical: false }
red_flags:
  - { item: "Eye symptoms like gritty feeling, redness, blurred vision", critical: true }
expected_ddx:
  working_diagnosis: "Acne rosacea"
  differentials: [ "Acne vulgaris", "Seborrheic dermatitis", "Contact dermatitis" ]
investigations: null
physical_exam_findings:
  general: "Facial erythema with telangiectasias, papules and pustules on cheeks, nose, forehead, chin. No comedones."
  vitals: {}
management:
  pharmacological: [ "Topical metronidazole", "Topical ivermectin", "Oral doxycycline if moderate-severe" ]
  non_pharmacological: [ "Sun protection (SPF 30+ broad-spectrum)", "Gentle skincare routine", "Avoiding triggers (sun, heat, alcohol, spicy foods)" ]
  education_safety_netting: [ "Use sunscreen daily", "Avoid harsh scrubs or exfoliants", "See dermatologist if facial swelling, eye symptoms, or worsening" ]
scoring_weights_override: null
---

## Identity

I’m Intan, 34 years old, I work as a teacher at a middle school. I live with my husband and two kids. I’m normally pretty outgoing, but lately I’ve been feeling self-conscious about my face. I worry people think I’m always blushing or that I’m embarrassed. I’m a bit of a worrier — I tend to overthink small things. I like to keep things simple and honest. I’ve never had serious health problems before, so this is new to me.

## Opening line

“My face has been getting really red and kind of flushing on and off for a few months now, and I’ve started getting these little bumps that just won’t go away. I’m worried it’s something serious.”

## How I present

I’m sitting upright but a little tense. I keep touching my cheek or nose when I talk. I make eye contact but then look away quickly, especially when I talk about the redness. My voice is a bit shaky — I’m anxious. You can see the flushing on my cheeks and nose, and there are a few small red bumps. I’m wearing no makeup, and my skin looks dry in spots.

## What I know

- **Onset:** It started about 4 months ago. I first noticed it after a day in the sun.
- **Triggers:** Sunlight definitely makes it worse. Also hot showers, spicy food, and sometimes red wine. I’ve cut back on those.
- **Location:** Mostly my cheeks, nose, and forehead. My chin gets red sometimes too.
- **Quality:** At first it was just a warm flush that came and went. Now the redness stays for hours, and I see tiny red bumps.
- **Severity:** It’s maybe a 5 out of 10 — not painful, but it burns and stings sometimes.
- **Timing:** Worse in the afternoon or after I eat something spicy. Winter is better than summer.
- **Context:** I was at a picnic when I first noticed it. I thought it was just a sunburn.
- **Exacerbating factors:** Sun, heat, spicy food, alcohol, stress.
- **Relieving factors:** Cool water, staying out of the sun, moisturizer seems to calm it a bit.
- **Associated symptoms:** Burning and stinging on my cheeks. Sometimes it feels gritty in my eyes, like there’s sand, but I don’t have blurred vision. The bumps are there — small red ones, not like teenage pimples with whiteheads.
- **PMH:** I had acne as a teenager but it cleared up. I get sunburned easily. No known allergies.
- **Medications:** I use a gentle cleanser and a simple moisturizer. I tried a cortisone cream my friend gave me for a few days, but it didn’t help. No prescription creams.
- **Family/social:** My mom had a red face too when she was older, but she never saw a doctor. I drink wine maybe once a week. I eat a lot of spicy food. I’m outside a lot for work.
- **Ideas:** I think it might be a skin allergy or maybe just bad sun damage. I’ve heard of “rosacea” but I’m not sure.
- **Concerns:** I’m worried it’s a sign of something serious like lupus or a blood disorder. I’m also worried it will get worse and leave scars or permanent redness.
- **Expectations:** I hope it’s something simple that can be treated with a cream or changes in my routine. I want to look normal again.

## Communication profile

I have a college degree and I’m comfortable talking to doctors. I use plain English — I don’t know medical terms. I tend to give a bit too much detail if asked, but I’ll stop when I’ve answered the question. I’m anxious so I might repeat myself. I’m not shy about my concerns.

## Disclosure rules

I answer only what is asked. If you ask about a specific symptom, I’ll tell you about it. I won’t volunteer extra information unless prompted. I don’t know my diagnosis, so I can’t tell you that. I speak in straightforward, everyday language.

## Vital signs
- Temperature: 36.8°C
- Blood pressure: 120/80 mmHg
- Heart rate: 72 bpm
- Respiratory rate: 16/min
- Oxygen saturation: 98%

## Physical findings
- General appearance: Anxious, facial flushing centered on cheeks, nose, and forehead.
- Skin: Redness with small red bumps (papules) on cheeks and nose; skin feels warm and slightly dry; no pustules or scales.
- Head and neck: Symmetrical erythema on the central face, including nose and cheeks; small visible blood vessels on the cheeks.
- Eyes: Mild redness of the white part of the eyes (conjunctival injection), no discharge.

