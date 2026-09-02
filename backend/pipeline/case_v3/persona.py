"""STEP 2 — constraint-based persona generation.

The persona is NEVER a source of clinical truth; it renders the variant's
canonical facts inside safe constraints. The generator may randomize only
clinically irrelevant fields (name, non-critical occupation, hobbies,
phrasing, emotional tone) from the allowed pools. Protected clinical fields
are injected straight from canonical truth and are structurally unmodifiable.
"""
from __future__ import annotations

import random

from pipeline.case_v3.models import ClinicalVariant, PersonaConstraints, SessionInstance

# Clinically-relevant persona fields the generator is FORBIDDEN to change.
PROTECTED_FIELDS = {
    "working_diagnosis", "symptom_chronology", "age_category", "epidemiologic_exposure",
    "red_flags", "pregnancy", "comorbidity_affecting_management", "physical_findings",
    "investigations", "treatment_truth", "rubric",
}

# Allowed name pools (age-appropriate; Indonesian-first per pivot).
_NAME_POOLS = {
    "adult_f": ["Siti", "Ratna", "Dewi", "Alya", "Wulan", "Sri", "Rina", "Intan"],
    "adult_m": ["Budi", "Agus", "Bambang", "Dimas", "Rizky", "Eko", "Hendra", "Joko"],
    "child_m": ["Andi", "Raka", "Dimas", "Fajar", "Bima", "Arga"],
    "child_f": ["Alya", "Nisa", "Putri", "Kirana", "Salsa"],
}
_OCCUPATIONS = ["teacher", "office worker", "shopkeeper", "student", "housewife", "farmer", "driver"]
_HOBBIES = ["watching television", "gardening", "listening to music", "light reading", "taking walks"]
_TONES = ["anxious", "calm", "matter-of-fact", "slightly worried"]
_VERBOSITY = ["short", "medium", "detailed"]

# Which of the allowed pools a variant's identity maps to.
def _age_pool(v: ClinicalVariant) -> str:
    a = v.identity.age_years
    sex = (v.identity.biological_sex or "").lower()
    if a is not None and a < 18:
        return "child_f" if sex.startswith("f") else "child_m"
    return "adult_f" if sex.startswith("f") else "adult_m"


class PersonaGenerator:
    def __init__(self, constraints: PersonaConstraints, seed: int):
        self.c = constraints
        self.rng = random.Random(seed)

    def generate(self, v: ClinicalVariant) -> dict:
        """Produce a persona rendering. PROTECTED fields come from `v` verbatim,
        never invented."""
        protected = v.protected_fields_canonical()

        persona = {
            # randomizable (only if allowed / clinically non-critical)
            "name": self._pick_name(v) if self.c.allow_name_generation else "",
            "occupation": self._pick(self.c.occupation_set or _OCCUPATIONS),
            "hobby": self._pick(_HOBBIES),
            "emotional_tone": self._pick(_TONES) if self.c.anxiety_level == "range" else "neutral",
            "verbosity": self._pick(_VERBOSITY) if self.c.verbosity == "range" else self.c.verbosity,
            "language_style": self.c.language_style,
            "health_literacy": self.c.education_health_literacy,
            "relationship": self.c.relationship,
            # protected clinical facts — forced from canonical truth
            "working_diagnosis": protected["working_diagnosis"],
            "chief_complaint": protected["chief_complaint"],
            "red_flags": protected["red_flags"],
            "vitals": protected["vitals"],
            "identity": {
                "age_years": v.identity.age_years, "age_range": v.identity.age_range,
                "biological_sex": v.identity.biological_sex,
                "pregnancy_status": v.identity.pregnancy_status,
                "informant_type": v.identity.informant_type, "setting": v.identity.setting,
                "population_tags": v.identity.population_tags,
            },
        }
        return persona

    def _pick(self, pool) -> str:
        return self.rng.choice(pool) if pool else ""

    def _pick_name(self, v: ClinicalVariant) -> str:
        pool = _age_pool(v)
        return self.rng.choice(_NAME_POOLS[pool])


def persona_from_constraints(v: ClinicalVariant, constraints: PersonaConstraints, seed: int) -> dict:
    return PersonaGenerator(constraints, seed).generate(v)


# Ensure run reproducibility at the instance level.
def build_session_instance(v: ClinicalVariant, *, persona_seed: int, language: str = "id",
                           learner_stage: str = "koas", mode: str = "blind",
                           entry_point: str | None = None) -> SessionInstance:
    """Create a reproducible runtime instance from a variant."""
    return SessionInstance(
        family_id=v.family_id, variant_id=v.id, persona_seed=persona_seed,
        session_facts={"variant_canonical_hash": v.canonical_hash()},
        language=language, learner_stage=_stage_or(learner_stage), mode=mode,
        entry_point=entry_point, hidden_labels=_default_hidden(mode),
    )


def _stage_or(s: str):
    from pipeline.case_v3.vocab import LearnerStage
    try:
        return LearnerStage(s)
    except ValueError:
        return LearnerStage.KOAS


def _default_hidden(mode: str) -> dict:
    return {
        "show_diagnosis": mode == "targeted",
        "show_chronicle": True,
        "show_red_flags_in_debrief": True,
    }


__all__ = ["PersonaGenerator", "persona_from_constraints", "build_session_instance",
           "PROTECTED_FIELDS", "PROTECTED_FIELDS"]