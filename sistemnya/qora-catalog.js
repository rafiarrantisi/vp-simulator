// ============================================================
// Qora — clinical catalogues for the post-Assess pickers (§4.8)
// ------------------------------------------------------------
// Comprehensive, specialty-agnostic lists of investigations and
// management options for the "Data Penunjang" (investigations) and
// "Terapi" (therapy) pickers. English (product language). Expand freely.
// Exposed on window for the concatenated bundle scope.
// ============================================================

window.QORA_INVESTIGATIONS = {
  'Haematology': [
    'Full Blood Count (FBC)', 'Blood film', 'Reticulocyte count', 'ESR',
    'Haematinics (ferritin, B12, folate)', 'Iron studies', 'Coagulation screen (PT/APTT/INR)',
    'D-dimer', 'Group & Save', 'Crossmatch', 'HbA1c',
  ],
  'Biochemistry': [
    'Urea & Electrolytes (U&E)', 'Liver Function Tests (LFTs)', 'C-reactive protein (CRP)',
    'Bone profile (Ca, PO4, ALP)', 'Magnesium', 'Amylase / Lipase', 'Troponin', 'BNP',
    'Thyroid Function Tests (TFTs)', 'Fasting glucose', 'Random glucose', 'Lipid profile',
    'Serum urate', 'Creatine kinase (CK)', 'Cortisol', 'Ammonia', 'Arterial blood gas (ABG)',
    'Venous blood gas (VBG)', 'Blood ketones',
  ],
  'Endocrine & Immunology': [
    'Autoantibodies (ANA, ANCA, RF, anti-CCP)', 'Complement (C3/C4)', 'Immunoglobulins',
    'Coeliac serology (anti-tTG)', 'Beta-hCG (serum)', 'Short Synacthen test', 'Dexamethasone suppression test',
  ],
  'Microbiology & Serology': [
    'Blood cultures', 'Urine MC&S', 'Sputum MC&S', 'Stool MC&S', 'Wound swab',
    'CSF analysis (Gram stain & culture)', 'HIV / Hepatitis B / Hepatitis C serology',
    'ASO titre', 'Malaria blood film', 'COVID / Influenza swab', 'Sexual health screen (NAAT)',
    'Throat swab',
  ],
  'Urine & Bedside': [
    'Urinalysis (dipstick)', 'Urine β-hCG (pregnancy test)', 'Capillary blood glucose',
    'Capillary ketones', 'Peak expiratory flow', '12-lead ECG', 'Blood pressure',
    'Otoscopy', 'Fundoscopy',
  ],
  'Radiology & Imaging': [
    'Chest X-ray', 'Abdominal X-ray', 'Limb / joint X-ray', 'CT head', 'CT chest',
    'CT abdomen & pelvis', 'CT pulmonary angiogram (CTPA)', 'MRI brain', 'MRI spine',
    'Ultrasound abdomen', 'Ultrasound pelvis / transvaginal', 'Doppler ultrasound (leg, for DVT)',
    'Echocardiogram', 'Contrast swallow / barium study', 'Mammography', 'DEXA scan', 'V/Q scan',
  ],
  'Cardio-respiratory & Neuro': [
    '24-hour ECG (Holter)', 'Exercise tolerance test', 'Spirometry / pulmonary function tests',
    'EEG', 'Nerve conduction studies / EMG', 'Lumbar puncture',
  ],
  'Endoscopy & Procedures': [
    'Upper GI endoscopy (OGD)', 'Colonoscopy / flexible sigmoidoscopy', 'Bronchoscopy',
    'Cystoscopy', 'Nasendoscopy', 'Skin / tissue biopsy', 'Bone marrow biopsy',
    'Pleural aspiration', 'Ascitic tap',
  ],
  'Specialty-specific': [
    'Slit-lamp examination', 'Tonometry (intra-ocular pressure)', 'Visual field testing',
    'Fluorescein staining', 'Audiometry', 'Tympanometry', 'Skin scraping / Wood’s lamp',
    'Patch testing', 'Dermoscopy', 'Cervical smear', 'CTG (foetal monitoring)',
  ],
};

window.QORA_THERAPIES = {
  'Pharmacological': [
    'Simple analgesia (paracetamol)', 'NSAIDs', 'Opioid analgesia', 'Antibiotics (per local guideline)',
    'Antiemetics', 'IV fluids', 'Supplemental oxygen', 'Bronchodilators (salbutamol)',
    'Corticosteroids', 'Proton pump inhibitor (PPI)', 'Antihistamines', 'Anticoagulation',
    'Antihypertensives', 'Insulin / oral hypoglycaemics', 'Topical treatment', 'Antivirals',
    'Antifungals', 'Diuretics', 'Adrenaline (IM, anaphylaxis)',
  ],
  'Non-pharmacological': [
    'Rest / activity modification', 'Limb elevation', 'Ice / heat therapy', 'Wound care & dressing',
    'Physiotherapy', 'Occupational therapy', 'Dietary modification', 'Smoking cessation support',
    'Weight management', 'Psychological therapy (e.g. CBT)',
  ],
  'Procedures & Referral': [
    'Admit for observation', 'Urgent same-day referral', 'Surgical referral', 'Specialist referral',
    'Incision & drainage', 'Urinary catheterisation', 'Splinting / immobilisation',
    'Nebuliser therapy', 'IV access & monitoring', 'Cardioversion',
  ],
  'Education & Safety-netting': [
    'Explain the diagnosis in plain language', 'Red-flag return advice', 'Safety-netting timeframe',
    'Lifestyle advice', 'Medication counselling', 'Arrange follow-up', 'Provide written information',
    'Address ideas, concerns & expectations',
  ],
};
