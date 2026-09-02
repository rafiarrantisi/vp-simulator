"""STEP 2 — vocabularies for the canonical clinical schema (case_v3)."""
from __future__ import annotations

from enum import Enum

# SKDI competency levels (competency mapping source, NOT a treatment source).
# Primary new bank scope is 3A / 3B / 4A (01_READ_ME_FIRST §4).
SKDI_LEVELS_ALLOWED_PRIMARY = frozenset({"3A", "3B", "4A"})
SKDI_LEVELS_KNOWN = frozenset({"1", "2", "3A", "3B", "4A"})


class FamilyType(str, Enum):
    DISEASE = "disease"            # diagnosis-centric, e.g. "Malaria"
    PRESENTATION = "presentation"  # complaint-centric, e.g. "Fever in a child"


class DisclosureMode(str, Enum):
    SPONTANEOUS = "spontaneous"                # volunteered in opening
    DIRECT_QUESTION = "direct_question"        # reveal only when asked
    FOLLOW_UP_REQUIRED = "follow_up_required"  # after specific follow-up
    PATIENT_DOES_NOT_KNOW = "patient_does_not_know"
    REQUIRES_EXAM = "requires_exam"
    REQUIRES_INVESTIGATION = "requires_investigation"
    NEVER_REVEAL_TO_PATIENT = "never_reveal_to_patient"


class FactStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class RedFlagCriticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class Appropriateness(str, Enum):
    ESSENTIAL = "essential"
    APPROPRIATE = "appropriate"
    OPTIONAL = "optional"
    UNNECESSARY = "unnecessary"
    HARMFUL = "harmful"


class ItemImportance(str, Enum):
    CRITICAL = "critical"
    HELPFUL = "helpful"
    OPTIONAL = "optional"


class VariationLevel(str, Enum):
    PERSONA = "persona"              # L1: same variant, different safe persona
    PRESENTATION = "presentation"    # L2: same diagnosis, meaningful clinical change
    COMPLEXITY = "complexity"        # L3: comorbidity/severity/complication/atypical


class LearnerStage(str, Enum):
    PRECLINICAL = "preclinical"  # structure/completeness/basic communication
    KOAS = "koas"                # relevance/reasoning/diagnosis/investigation/management/safety


class ClinicalVitalUnits(str, Enum):
    NONE = ""
    CELSIUS = "C"
    BPM = "bpm"
    MMHG = "mmHg"
    PER_MIN = "/min"
    PERCENT = "%"
    KG = "kg"
    CM = "cm"
    SECONDS = "sec"
    LITER_PER_HR = "L/hr"
    ML_PER_KG_HR = "mL/kg/hr"
    MG_DL = "mg/dL"
    MMOL_L = "mmol/L"


class ClinicalSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"