"""FASE 5 — Indonesian formulary context (starter dataset, HONEST provenance).

This is NOT the Fornas and NOT a guideline. It is a curated starter map of
generic medicines commonly used in Indonesian primary care / JKN practice,
used ONLY for:
  1. normalizing learner free-text (brand/ID-spelling -> generic concept), and
  2. UI suggestion prioritization (show familiar local options first).

Rules:
- `availability_hint` is a UI-ordering heuristic, NEVER a coverage claim and
  NEVER shown to learners as "Fornas-listed". A pharmacist/human must verify
  against the current Fornas/KMK edition before any formulary claim is made.
- Treatment truth (what is CORRECT) comes from disease guidelines via the
  variant's MedicationConcept truth — never from this file.
- Brands are listed ONLY as normalization aliases (learner typed them), never
  as recommendations.
"""
from __future__ import annotations

PROVENANCE = (
    "formulary_id starter v1 — curated common-practice map; "
    "verify against the current Fornas/KMK edition before any formulary claim; "
    "never a disease guideline (see governance.py Fornas isolation)"
)

# generic -> {class, id_aliases (brands/ID spellings/EN synonyms/abbrev),
#             availability_hint: core | common | unknown (ordering only)}
GENERICS: dict[str, dict] = {
"paracetamol": dict(cls="analgesic-antipyretic",
    aliases=["parasetamol", "acetaminophen", "panadol", "sanmol", "pam ol", "paracetamole"],
    hint="core"),
"ibuprofen": dict(cls="nsaid",
    aliases=["proris", "brufen", "ibuprophen", "oa ins", "oains"],
    hint="core"),
"diclofenac": dict(cls="nsaid",
    aliases=["diklofenak", "voltaren", "cataflam"],
    hint="common"),
"amoxicillin": dict(cls="beta-lactam antibiotic",
    aliases=["amoksisilin", "amoxan", "amoxsan", "amoxycillin", "amoxil"],
    hint="core"),
"amoxicillin-clavulanate": dict(cls="beta-lactam antibiotic",
    aliases=["amoksisilin klavulanat", "co-amoxiclav", "coamoxiclav", "clamixin", "augmentin"],
    hint="common"),
"cefadroxil": dict(cls="cephalosporin antibiotic",
    aliases=["sefadroksil", "cefadroxyl", "longacef"],
    hint="common"),
"ceftriaxone": dict(cls="cephalosporin antibiotic",
    aliases=["seftriakson", "ceftriaxon", "broadcef"],
    hint="common"),
"ciprofloxacin": dict(cls="fluoroquinolone antibiotic",
    aliases=["siprofloksasin", "cipro", "ciproxin", "baquinor"],
    hint="common"),
"metronidazole": dict(cls="nitroimidazole antibiotic",
    aliases=["metronidazol", "flagyl", "grafazol"],
    hint="common"),
"doxycycline": dict(cls="tetracycline antibiotic",
    aliases=["doksisiklin", "doxy", "vibramycin"],
    hint="common"),
"azithromycin": dict(cls="macrolide antibiotic",
    aliases=["azitromisin", "zithromax", "zithromax", "azomax"],
    hint="common"),
"co-trimoxazole": dict(cls="sulfonamide antibiotic",
    aliases=["kotrimoksazol", "trimethoprim-sulfamethoxazole", "tmp-smx", "bactrim", "sanprima"],
    hint="common"),
"nystatin": dict(cls="topical antifungal",
    aliases=["nistatin", "mycostatin"],
    hint="common"),
"fluconazole": dict(cls="azole antifungal",
    aliases=["flukonazol", "diflucan"],
    hint="common"),
"terbinafine": dict(cls="allylamine antifungal",
    aliases=["terbinafin", "lamisil"],
    hint="common"),
"permethrin": dict(cls="scabicide",
    aliases=["permetrin", "scabimite"],
    hint="common"),
"mupirocin": dict(cls="topical antibiotic",
    aliases=["mupirosin", "bactroban"],
    hint="common"),
"hydrocortisone": dict(cls="low-potency topical steroid",
    aliases=["hidrokortison", "hydrocortison", "calacort"],
    hint="common"),
"mometasone": dict(cls="topical steroid",
    aliases=["mometason", "elocon", "momeson"],
    hint="common"),
"cetirizine": dict(cls="antihistamine",
    aliases=["setirizin", "cetirizin", "cetiriz", "incidal", "zyrtec"],
    hint="core"),
"loratadine": dict(cls="antihistamine",
    aliases=["loratadin", "claritin", "logan"],
    hint="common"),
"omeprazole": dict(cls="proton-pump inhibitor",
    aliases=["omeprazol", "omeprazol", "lanso", "ppi"],
    hint="core"),
"lansoprazole": dict(cls="proton-pump inhibitor",
    aliases=["lansoprazol", "lanzoprazole", "ppi"],
    hint="common"),
"oral rehydration salts": dict(cls="rehydration",
    aliases=["ors", "oralit", "oral rehydration salt", "rehydration salts", "cairan rehidrasi oral", "cro"],
    hint="core"),
"zinc": dict(cls="micronutrient adjunct",
    aliases=["zink", "seng", "zinc sulfate"],
    hint="core"),
"metformin": dict(cls="biguanide glucose-lowering",
    aliases=["metformine", "glucophage", "hexpham"],
    hint="core"),
"glimepiride": dict(cls="sulfonylurea glucose-lowering",
    aliases=["glimepirid", "amaryl", "glimepirid"],
    hint="common"),
"insulin": dict(cls="insulin",
    aliases=["insuline", "lantus", "novorapid", "levemir", "humulin"],
    hint="common"),
"amlodipine": dict(cls="calcium-channel blocker",
    aliases=["amlodipin", "norvask", "tensivask"],
    hint="core"),
"candesartan": dict(cls="angiotensin-receptor blocker",
    aliases=["candesartan", "arb", "atacand", "blopress"],
    hint="common"),
"bisoprolol": dict(cls="beta blocker",
    aliases=["bisoprolol", "concor", "beta blocker", "beta bloker"],
    hint="common"),
"aspirin": dict(cls="antiplatelet",
    aliases=["asetosal", "aspilet", "aspirine", "acetylsalicylic acid", "mini aspirin"],
    hint="core"),
"clopidogrel": dict(cls="antiplatelet",
    aliases=["klopidogrel", "plavix", "clopidogrel"],
    hint="common"),
"furosemide": dict(cls="loop diuretic",
    aliases=["furosemid", "lasix", "diuretik"],
    hint="common"),
"atorvastatin": dict(cls="statin",
    aliases=["atorvastatin", "lipitor", "statin"],
    hint="common"),
"simvastatin": dict(cls="statin",
    aliases=["simvastatin", "statin"],
    hint="common"),
"salbutamol": dict(cls="short-acting bronchodilator",
    aliases=["ventolin", "salbutamol", "albuterol", " bricanyl", "inhaler biru"],
    hint="core"),
"budesonide-formoterol": dict(cls="ics-laba controller",
    aliases=["symbicort", "budesonid formoterol", "controller inhaler", "inhaler coklat"],
    hint="common"),
"prednisone": dict(cls="systemic corticosteroid",
    aliases=["prednison", "prednisone", "steroid oral"],
    hint="common"),
"dexamethasone": dict(cls="systemic corticosteroid",
    aliases=["deksametason", "dexamethason", "dexametason", "kortikosteroid"],
    hint="common"),
"adrenaline": dict(cls="anaphylaxis first-line",
    aliases=["adrenalin", "epinephrine", "epinefrin", "epipen", "epi"],
    hint="core"),
"diazepam": dict(cls="seizure rescue",
    aliases=["diazepam", "valium", "stresolid"],
    hint="common"),
"sertraline": dict(cls="ssri antidepressant",
    aliases=["sertralin", "zoloft", "ssri", "antidepresan"],
    hint="common"),
"fluoxetine": dict(cls="ssri antidepressant",
    aliases=["fluoksetin", "prozac", "ssri"],
    hint="common"),
"ferrous sulfate": dict(cls="oral iron",
    aliases=["ferosulfat", "ferrous sulphate", "tardyferon", "sangobion", "tambah darah", "tablet tambah darah", "ttd"],
    hint="core"),
"folic acid": dict(cls="hematinic adjunct",
    aliases=["asam folat", "folat", "folavit"],
    hint="common"),
"methyldopa": dict(cls="pregnancy-safe antihypertensive",
    aliases=["metildopa", "aldomet"],
    hint="common"),
"nifedipine": dict(cls="calcium-channel blocker",
    aliases=["nifedipin", "adalat"],
    hint="common"),
"colchicine": dict(cls="gout flare agent",
    aliases=["kolkisin", "colchicin"],
    hint="common"),
"allopurinol": dict(cls="urate-lowering",
    aliases=["alopurinol", "zyloric", "puricemia"],
    hint="common"),
"tramadol": dict(cls="weak opioid",
    aliases=["tramadol", "tramal", "opioid lemah"],
    hint="common"),
"ondansetron": dict(cls="antiemetic",
    aliases=["ondansetron", "zofran", "antimuntah"],
    hint="common"),
"aciclovir": dict(cls="herpes antiviral",
    aliases=["asiklovir", "aciclovir", "acyclovir", "zovirax", "valaciclovir", "valasiklovir"],
    hint="common"),
"artemether-lumefantrine": dict(cls="artemisinin combination therapy",
    aliases=["act", "artemisinin", "artemeter", "coartem", "antimalaria"],
    hint="common"),
"albendazole": dict(cls="anthelmintic",
    aliases=["albendazol", "cacing", "obat cacing", "combantrin", "vermox", "mebendazole", "mebendazol"],
    hint="core"),
"fluticasone nasal spray": dict(cls="intranasal corticosteroid",
    aliases=["flutikasone", "fluticasone", "avamis", "semprot hidung", "nasal spray"],
    hint="common"),
"loperamide": dict(cls="antimotility (avoid in dysentery/children)",
    aliases=["loperamid", "imodium", "diareeen"],
    hint="unknown"),
"ofloxacin ear drops": dict(cls="topical ear antibiotic",
    aliases=["ofloksasin tetes telinga", "ofloxacin", "tetes telinga"],
    hint="common"),
"chloramphenicol eye drops": dict(cls="topical eye antibiotic",
    aliases=["kloramfenikol tetes mata", "chloramphenicol", "tetes mata", "cendo"],
    hint="core"),
"artificial tears": dict(cls="ocular lubricant",
    aliases=["air mata buatan", "tetes mata pelumas", "insto"],
    hint="common"),
}

# class-level terms (ID + EN) -> canonical class (verdict: incomplete, never a hit alone)
CLASS_TERMS: dict[str, str] = {
"antibiotik": "antibiotic", "antibiotic": "antibiotic",
"antihipertensi": "antihypertensive", "antihypertensive": "antihypertensive",
"obat hipertensi": "antihypertensive",
"oa ins": "nsaid", "oains": "nsaid", "nsaid": "nsaid",
"antiinflamasi": "nsaid", "anti-inflammatory": "nsaid",
"antidiabetes": "glucose-lowering", "obat diabetes": "glucose-lowering",
"diuretik": "diuretic", "diuretic": "diuretic",
"statin": "statin",
"ssri": "ssri antidepressant", "antidepresan": "ssri antidepressant", "antidepressant": "ssri antidepressant",
"ppi": "proton-pump inhibitor",
"arb": "angiotensin-receptor blocker",
"ccb": "calcium-channel blocker",
"inhaler": "bronchodilator", "obat hirup": "bronchodilator",
"kortikosteroid": "corticosteroid", "corticosteroid": "corticosteroid", "steroid": "corticosteroid",
"antijamur": "antifungal", "antifungal": "antifungal",
"obat cacing": "anthelmintic", "anthelmintic": "anthelmintic",
"ttd": "oral iron", "tablet tambah darah": "oral iron",
"oralit": "rehydration", "cro": "rehydration",
"antialergi": "antihistamine", "anti-allergy": "antihistamine",
"antinyeri": "analgesic", "painkiller": "analgesic",
"penurun panas": "antipyretic",
}


def _norm_token(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKC", s).lower().strip()
    return re.sub(r"\s+", " ", s)


def build_alias_index() -> dict[str, str]:
    """alias token -> generic name."""
    idx: dict[str, str] = {}
    for gen, info in GENERICS.items():
        idx[_norm_token(gen)] = gen
        for a in info.get("aliases", []):
            t = _norm_token(a)
            if t and t not in idx:
                idx[t] = gen
    return idx


_ALIAS_INDEX = build_alias_index()


def lookup_generic(token: str) -> str | None:
    """Exact alias lookup (generic concept, not brand/exact-string worship)."""
    return _ALIAS_INDEX.get(_norm_token(token))


def fuzzy_generic(token: str, *, max_dist: int = 2) -> tuple[str | None, int]:
    """Typo-tolerant lookup for tokens len>=6. Returns (generic, distance)."""
    from pipeline.case_v3.semantic import _levenshtein
    t = _norm_token(token)
    if len(t) < 6:
        return None, 99
    best, bd = None, 99
    for alias, gen in _ALIAS_INDEX.items():
        if abs(len(alias) - len(t)) > max_dist:
            continue
        d = _levenshtein(t, alias)
        if d < bd:
            best, bd = gen, d
            if d == 0:
                break
    if bd <= max_dist:
        return best, bd
    return None, bd


def lookup_class(token: str) -> str | None:
    return CLASS_TERMS.get(_norm_token(token))
