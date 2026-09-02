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
        if cand == norm_goal:
            return {"match": True, "grade": "exact", "note": "exact match"}
        # synonym / paraphrase tolerant
        if _paraphrase(cand, norm_goal):
            return {"match": True, "grade": "paraphrase", "note": "semantic paraphrase accepted"}
        for s in synonyms:
            if _contained(cand, normalize(s)):
                return {"match": True, "grade": "synonym", "note": f"synonym/alias matched: '{s}'"}
        if _contained(cand, norm_goal):
            return {"match": True, "grade": "partial", "note": "target term contained"}
        close = _levenshtein(cand, norm_goal)
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