"""STEP-6 rule 7 — pluggable, grounded semantic grading.

The current scorer is deliberately a lightweight normalizing containment scorer
(NOT a clinically robust judge). This module:
  * exposes an Evaluator protocol so a grounded/normal permissive semantic
    evaluator can be plugged in later (STEP 8 QA / human validation);
  * never fails a learner purely for exact-string mismatch (normalises case,
    strips articles/punctuation, matches synonyms/paraphrases);
  * labels unresolved semantic quality as `grading_limit` so the frontend never
    over-claims clinical robustness.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Pluggable evaluator interface.
class DiagnosisEvaluator:
    """Checks whether a learner's free-text diagnosis matches the target
    semantics. Subclass/override to plug in a real grounded semantic judge."""

    def name(self) -> str:
        return "normalizing_containment"

    def confidence(self) -> str:
        return "advisory"   # not clinical-grade (rule 7)

    def matches(self, submitted: str, target: str, *, synonyms: list[str]) -> dict:
        """Return decision + grading limit note (advisory, pluggable)."""
        norm_goal = normalize(target)
        cand = normalize(submitted)
        if not cand:
            return {"match": False, "grade": "no_candidate", "note": "No diagnosis submitted"}
        # STEP 8: expand Indonesian/English/abbreviation surfaces of the candidate
        # (e.g. 'DBD' → 'dengue', 'hipertensi' → 'hypertension') and re-normalise.
        expanded = [normalize(e) for e in expand_id(submitted)]
        cand_forms = list(dict.fromkeys([cand] + expanded))
        if norm_goal in cand or cand in norm_goal:
            return {"match": True, "grade": "partial", "note": "target term contained"}
        for cf in cand_forms:
            if norm_goal in cf or cf in norm_goal:
                return {"match": True, "grade": "synonym", "note": "ID/EN/abbreviation surface matched"}
        if _paraphrase(cand, norm_goal):
            return {"match": True, "grade": "paraphrase", "note": "semantic paraphrase accepted"}
        for s in synonyms:
            sn = normalize(s)
            if any(sn in cf or cf in sn for cf in cand_forms):
                return {"match": True, "grade": "synonym", "note": f"synonym/alias matched: '{s}'"}
        close = min(_levenshtein(cf, norm_goal) for cf in cand_forms)
        if close <= max(3, len(norm_goal) // 3):
            return {"match": True, "grade": "near_miss",
                    "note": f"near-miss (typo, sd={close}) — accepted, flag for human review",
                    "grading_limit": True}
        return {"match": False, "grade": "mismatch",
                "note": "No clinical-grade claim (advisory grader)"}


# ── normalisation helpers ──────────────────────────────────────────────────
_STOP = {"the", "a", "an", "with", "in", "of", "and", "or", "for",
         "acute", "presentation", "syndrome", "disease", "case"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = [w for w in s.split() if w not in _STOP]
    return " ".join(tokens)


# Indonesian → English clinical synonyms + widely-used abbreviations (STEP 8:
# candidate often writes 'DBD', 'hipertensi', 'DM tipe 2', lowercase/typos).
_ID_EN = {
    # abbreviations → expanded Indonesian + English clinical term
    "dbd": "demam berdarah dengue dengue",
    "tb": "tuberkulosis tuberculosis tb",
    "htn": "hipertensi hypertension",
    "dm": "diabetes mellitus diabetes dm",
    "ckd": "penyakit ginjal kronik chronic kidney disease ckd",
    "uti": "infeksi saluran kemih urinary tract infection uti",
    "isk": "infeksi saluran kemih urinary tract infection isk",
    "pne": "pneumonia pneumonia",
    "agn": "glomerulonefritis akut acute glomerulonephritis agn",
}
# non-abbreviated Indonesian ↔ English disease names treated as equal pairs.
_ID_SYN = {
    "demam berdarah dengue": "dengue",
    "dengue berdarah": "dengue",
    "demam berdarah dengue berat": "severe dengue",
    "dengue syok": "dengue shock",
    "syok dengue": "dengue shock",
    "hipertensi": "hypertension",
    "tekanan darah tinggi": "hypertension",
    "tensi tinggi": "hypertension",
    "darah tinggi": "hypertension",
    "diabetes melitus": "diabetes",
    "diabetes": "diabetes mellitus",
    "kencing manis": "diabetes mellitus",
    "asma": "asthma",
    "pneumonia": "pneumonia",
    "infeksi saluran kemih": "urinary tract infection",
    "gagal ginjal": "renal failure",
    "penyakit ginjal kronik": "chronic kidney disease",
}


def expand_id(s: str) -> list[str]:
    """Return candidate surface forms (ID/EN/abbrev) for a semantic term."""
    out = [s, str(s).lower()]
    lo = str(s).lower().strip()
    if lo in _ID_EN:
        for e in _ID_EN[lo].split():
            out.append(e)
    # token-level abbreviation substitution (e.g. 'DBD berdarah' → 'dengue berdarah')
    tokens = lo.split()
    substituted = []
    for tok in tokens:
        substituted.append(_ID_EN.get(tok, tok) if _ID_EN.get(tok) else tok)
    if substituted != tokens:
        out.append(" ".join(substituted))
    for id_k, en_v in _ID_SYN.items():
        if id_k in lo:
            out.append(en_v)
        if en_v in lo:
            out.append(id_k)
    return list(dict.fromkeys([t for t in out if t]))


def _contained(cand: str, goal: str) -> bool:
    return bool(goal) and (goal in cand or cand in goal)


def _paraphrase(cand: str, goal: str) -> bool:
    """Heuristic paraphrase: candidate is 'dengue' vs goal 'severe dengue with
    shock': overlapping diagnostic core term counts, otherwise not invented."""
    c = set(cand.split())
    g = set(goal.split())
    if not c or not g:
        return False
    overlap = c & g
    return len(overlap) >= 1 and len(overlap) >= min(len(c), len(g)) * 0.5


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


# Convenience for the scorer/HTTP layer.
def diagnose_match(submitted: str, target: str, synonyms: list[str] | None = None,
                   evaluator: DiagnosisEvaluator | None = None) -> dict:
    return (evaluator or DiagnosisEvaluator()).matches(
        submitted, target, synonyms=synonyms or [])