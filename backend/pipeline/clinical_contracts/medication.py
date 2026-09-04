"""Phase 2 Task C — medication normalization contract (plan §9, Phase 5 A-D).

A clinical medication concept layer that separates *clinical correctness*
from *local (Fornas) preference*, plus deterministic ID/EN/abbreviation/typo
normalization for learner answers. Treatment entry stays low-friction:
concepts are matched against free text, never a forced catalog pick.

Grading outcomes (plan Phase 5D):
  correct_preferred | acceptable_alternative | incomplete |
  inappropriate | unsafe

Fornas context (KMK HK.01.07/MENKES/1199/2025, effective 2026-04-01) is
recorded as formulary context only — never as disease-management truth.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

OUTCOMES = ('correct_preferred', 'acceptable_alternative', 'incomplete', 'inappropriate', 'unsafe')

FORNAS_REFERENCE = 'KMK HK.01.07/MENKES/1199/2025'
FORNAS_EFFECTIVE_DATE = '2026-04-01'


@dataclass
class MedicationConcept:
    """One prescribable concept for a variant's management truth."""

    generic_name: str
    med_class: str = ''
    preferred_agents: list[str] = field(default_factory=list)
    acceptable_alternatives: list[str] = field(default_factory=list)
    indication: str = ''
    dose_range: str = ''
    route: str = ''
    frequency: str = ''
    duration: str = ''
    contraindications: list[str] = field(default_factory=list)
    monitoring: list[str] = field(default_factory=list)
    in_fornas: bool | None = None
    fornas_note: str = ''
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'MedicationConcept':
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (d or {}).items() if k in known})

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not (self.generic_name or '').strip():
            errors.append('generic_name empty (generic naming is primary)')
        if not self.preferred_agents and not self.acceptable_alternatives:
            errors.append(f"'{self.generic_name}': no preferred or alternative agents listed")
        return errors


_ID_EN_DRUGS = {
    'parasetamol': 'paracetamol',
    'asetaminofen': 'paracetamol',
    'acetaminofen': 'paracetamol',
    'amoksisilin': 'amoxicillin',
    'siprofloksasin': 'ciprofloxacin',
    'nitrofurantoin': 'nitrofurantoin',
    'sefiksim': 'cefixime',
    'seftriakson': 'ceftriaxone',
    'antasida': 'antacid',
    'oralit': 'ors',
    'rifampisin': 'rifampicin',
    'rifampin': 'rifampicin',
    'isoniazid': 'isoniazid',
    'inh': 'isoniazid',
    'pirazinamid': 'pyrazinamide',
    'pirasinamid': 'pyrazinamide',
    'etambutol': 'ethambutol',
    'etamburol': 'ethambutol',
    'oat': 'anti tuberculosis',
    'fdc': 'fixed dose combination',
    'azitromisin': 'azithromycin',
    'azitromycin': 'azithromycin',
    'levofloksasin': 'levofloxacin',
    'levofloksacin': 'levofloxacin',
    'doksisiklin': 'doxycycline',
    'kloramfenikol': 'chloramphenicol',
    'kotrimoksazol': 'co-trimoxazole',
    'salbutamol': 'salbutamol',
    'budesonid': 'budesonide',
    'beclometason': 'beclometasone',
    'beklometason': 'beclometasone',
    'prednison': 'prednisone',
    'prednisolon': 'prednisolone',
    'prednisolone': 'prednisolone',
    'deksametason': 'dexamethasone',
    'oksigen': 'oxygen',
    'metformin': 'metformin',
    'gliklazid': 'gliclazide',
    'glibenklamid': 'glibenclamide',
    'glimepirid': 'glimepiride',
    'dapagliflozin': 'dapagliflozin',
    'empagliflozin': 'empagliflozin',
    'asetosal': 'aspirin',
    'aspirin': 'aspirin',
    'aspilet': 'aspirin',
    'klopidogrel': 'clopidogrel',
    'tikagrelor': 'ticagrelor',
    'atorvastatin': 'atorvastatin',
    'simvastatin': 'simvastatin',
    'enoksaparin': 'enoxaparin',
    'enoxaparin': 'enoxaparin',
    'amlodipin': 'amlodipine',
    'lisinopril': 'lisinopril',
    'losartan': 'losartan',
    'hidroklorotiazid': 'hydrochlorothiazide',
    'hct': 'hydrochlorothiazide',
    'nitrogliserin': 'nitroglycerin',
    'ibuprofen': 'ibuprofen',
    'antalgin': 'metamizole',
    'metamizol': 'metamizole',
    'ors': 'ors',
    'ondansetron': 'ondansetron',
    'omeprazol': 'omeprazole',
}

_ABBR_DRUGS = {
    'pcm': 'paracetamol',
    'amox': 'amoxicillin',
    'cipro': 'ciprofloxacin',
    'nitro': 'nitrofurantoin',
    'rif': 'rifampicin',
    'oat': 'anti tuberculosis',
    'fdc': 'fixed dose combination',
    'dapt': 'dual antiplatelet',
    'ace-i': 'ace inhibitor',
    'acei': 'ace inhibitor',
    'arb': 'angiotensin receptor blocker',
    'ccb': 'calcium channel blocker',
    'saba': 'short acting beta agonist',
    'ics': 'inhaled corticosteroid',
    'ocs': 'oral corticosteroid',
    'asa': 'aspirin',
    'inr': 'inr',
}

_CLASS_ALIASES = {
    'penghambat ace': 'ace inhibitor',
    'ace inhibitor': 'ace inhibitor',
    'acei': 'ace inhibitor',
    'penghambat kalsium': 'calcium channel blocker',
    'antihipertensi': 'antihypertensive',
    'antibiotik': 'antibiotic',
    'antibiotika': 'antibiotic',
    'obat anti tb': 'anti tuberculosis',
    'obat anti tuberkulosis': 'anti tuberculosis',
    'antiplatelet ganda': 'dual antiplatelet',
    'kortikosteroid inhalasi': 'inhaled corticosteroid',
    'kortikosteroid oral': 'oral corticosteroid',
    'beta agonis': 'short acting beta agonist',
    'antidiabetik oral': 'oral hypoglycaemic',
    'obat gula': 'oral hypoglycaemic',
}


def normalize_medication_text(s: str) -> str:
    """Normalize one learner medication token to a generic key."""
    t = unicodedata.normalize('NFKC', s or '').lower()
    t = re.sub('[^a-z0-9\\s]', ' ', t)
    t = re.sub('\\s+', ' ', t).strip()
    if t in _ABBR_DRUGS:
        return _ABBR_DRUGS[t]
    if t in _ID_EN_DRUGS:
        return _ID_EN_DRUGS[t]
    if t in _CLASS_ALIASES:
        return _CLASS_ALIASES[t]
    out = [_ID_EN_DRUGS.get(tok) or _ABBR_DRUGS.get(tok) or tok for tok in t.split()]
    joined = ' '.join(out)
    for alias, canon in _CLASS_ALIASES.items():
        if alias in joined:
            joined = joined.replace(alias, canon)
    return joined


def normalize_class_text(s: str) -> str:
    """Normalize a class phrase to its canonical class key (ID/EN/abbrev)."""
    t = normalize_medication_text(s)
    return _CLASS_ALIASES.get(t, t)


def class_matches(answer_norm: str, med_class: str) -> bool:
    """True when the learner named the expected class in any supported form."""
    cls = normalize_class_text(med_class or '')
    if not cls:
        return False
    if cls in answer_norm:
        return True
    cls_toks = set(cls.split())
    ans_toks = set(answer_norm.split())
    return len(cls_toks) >= 2 and len(cls_toks & ans_toks) >= 2


_DOSE_RE = re.compile(r'\b\d+(?:[.,]\d+)?\s?(?:mg|g|mcg|µg|iu|unit|tablet|tab|kapsul|capsule|ml)\b')
_ROUTE_RE = re.compile(r'\b(oral|po|iv|intravena|intravenous|im\b|intramuskular|subkutan|subcutaneous|inhalasi|inhaled|nebul|topikal|topical|diminum|disuntik|infus|sl\b|sublingual)\b')
_FREQ_RE = re.compile(r'\b(\d+\s?[x×]\s?\d*|sekali sehari|dua kali sehari|once daily|twice daily|three times|tiw|bid|tid|qid|daily|harian|per hari|/hari|tiap \d+ jam|every \d+h)\b')
_DURATION_RE = re.compile(r'\b(selama \d+ hari|\d+\s?hari|\d+\s?minggu|\d+\s?bulan|\d+\s?months?|\d+\s?weeks?|\d+\s?days?|full course|sampai habis)\b')


def extract_dose_signals(answer: str) -> dict:
    """Advisory detail signals (plan §21): dose/route/frequency/duration.

    These enrich feedback detail; they NEVER fail an answer by themselves —
    the station task / learner level decides what detail is required
    (judge calibration, Phase 7). Absence of a signal is informational.
    """
    t = normalize_medication_text(answer)
    return {
        'has_dose': bool(_DOSE_RE.search(t)),
        'has_route': bool(_ROUTE_RE.search(t)),
        'has_frequency': bool(_FREQ_RE.search(t)),
        'has_duration': bool(_DURATION_RE.search(t)),
    }


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def match_agent(answer: str, candidates: list[str]) -> str:
    """Return the matched candidate or '' (exact → synonym → near-miss typo)."""
    norm = normalize_medication_text(answer)
    norm_cands = {normalize_medication_text(c): c for c in candidates}
    for key, orig in norm_cands.items():
        if key and (key in norm or norm in key):
            return orig
    for key, orig in norm_cands.items():
        if not key:
            continue
        for tok in norm.split():
            if len(tok) >= 6 and _levenshtein(tok, key.split()[0]) <= 2:
                return orig
    return ''


@dataclass
class MedicationGrade:
    outcome: str
    matched_agent: str = ''
    detail: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


def grade_medication_answer(answer: str, concept: MedicationConcept) -> MedicationGrade:
    """Deterministic grading of one free-text answer against one concept."""
    text = normalize_medication_text(answer)
    if not text:
        return MedicationGrade('incomplete', detail='no medication submitted')
    for c in concept.contraindications or []:
        if normalize_medication_text(c) and normalize_medication_text(c) in text:
            return MedicationGrade('unsafe', matched_agent=c, detail=f'contraindicated: {c}')
    hit = match_agent(answer, concept.preferred_agents or [])
    if hit:
        return MedicationGrade(
            'correct_preferred',
            matched_agent=hit,
            detail=_with_detail_signals(f'locally preferred: {hit}', answer, concept),
        )
    hit = match_agent(answer, concept.acceptable_alternatives or [])
    if hit:
        return MedicationGrade(
            'acceptable_alternative',
            matched_agent=hit,
            detail=_with_detail_signals(f'clinically acceptable alternative: {hit}', answer, concept),
        )
    if class_matches(text, concept.med_class or ''):
        return MedicationGrade('incomplete', detail='correct class, agent unspecified')
    if normalize_medication_text(concept.generic_name) in text:
        return MedicationGrade(
            'incomplete',
            detail=_with_detail_signals('correct agent, detail missing', answer, concept),
        )
    return MedicationGrade('inappropriate', detail='no match to expected concept')


def _with_detail_signals(base: str, answer: str, concept: MedicationConcept) -> str:
    """Append advisory dose/route/frequency/duration coverage to the detail.

    Advisory only: missing detail never changes the outcome here (the judge,
    Phase 7, decides what detail a station/level requires).
    """
    sig = extract_dose_signals(answer)
    missing: list = []
    if (concept.dose_range or '').strip() and not sig['has_dose']:
        missing.append(f'expected dose context: {concept.dose_range}')
    if (concept.duration or '').strip() and not sig['has_duration']:
        missing.append(f'expected duration context: {concept.duration}')
    if (concept.route or '').strip() and not sig['has_route']:
        missing.append(f'expected route context: {concept.route}')
    if not missing:
        return base
    return base + '; detail absent (advisory): ' + '; '.join(missing)


@dataclass
class RegimenGrade:
    """Grading of one free-text answer against a variant's full concept list."""

    outcome: str
    per_concept: list[dict] = field(default_factory=list)
    detail: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


def grade_regimen(answer: str, concepts: list[MedicationConcept]) -> RegimenGrade:
    """Grade a full treatment answer against several concepts (one variant).

    Outcome precedence (plan Phase 5D):
      unsafe (any concept unsafe) > incomplete (partial coverage) >
      acceptable_alternative (all covered, ≥1 alternative) >
      correct_preferred (all covered, all preferred) ;
      inappropriate only when nothing matches anything.
    Empty answer is `incomplete` (no credit — never a pass by default).
    """
    concepts = list(concepts or [])
    if not (answer or '').strip():
        return RegimenGrade('incomplete', per_concept=[], detail='no medication submitted')
    if not concepts:
        return RegimenGrade('incomplete', per_concept=[], detail='no expected concepts defined')
    per: list = []
    for c in concepts:
        g = grade_medication_answer(answer, c)
        per.append(
            {
                'generic_name': c.generic_name,
                'outcome': g.outcome,
                'matched_agent': g.matched_agent,
                'detail': g.detail,
            }
        )
    outcomes = [p['outcome'] for p in per]
    if any(o == 'unsafe' for o in outcomes):
        bad = next(p for p in per if p['outcome'] == 'unsafe')
        return RegimenGrade('unsafe', per_concept=per, detail=f"unsafe: {bad['detail']}")
    covered = [o for o in outcomes if o in ('correct_preferred', 'acceptable_alternative')]
    if not covered:
        if any(o == 'incomplete' for o in outcomes):
            return RegimenGrade('incomplete', per_concept=per, detail='partial match only (class/agent without full concept)')
        return RegimenGrade('inappropriate', per_concept=per, detail='no match to any expected concept')
    if len(covered) < len(concepts):
        return RegimenGrade(
            'incomplete', per_concept=per, detail=f'{len(covered)}/{len(concepts)} concepts covered'
        )
    if all(o == 'correct_preferred' for o in outcomes):
        return RegimenGrade('correct_preferred', per_concept=per, detail='all concepts locally preferred')
    return RegimenGrade(
        'acceptable_alternative', per_concept=per, detail='all concepts covered with ≥1 acceptable alternative'
    )
