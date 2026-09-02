"""STEP 2 — vocabularies for the canonical clinical schema (case_v3)."""
from __future__ import annotations

from enum import Enum

# ═══ COMPETENCY BASELINE (STEP 4 pivot) ═══════════════════════════════════
# SKD 2026 (HK.01.02/KKI/2183/2026) is the SINGLE PRIMARY competency authority
# for the new case bank. Each Spektrum Penyakit entry is classified as either
# 'tuntas' (managed independently) or 'initial_management_and_referral'
# (stabilise + refer). We use these OFFICIAL 2026 terms — we do NOT auto-map
# them onto SKDI 2012 levels.
SKD2026_STANDARD = "SKD 2026"
SKD2026_REFERENCE = "HK.01.02/KKI/2183/2026"
SKD2026_CATEGORY_TUNTAS = "tuntas"
SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL = "initial_management_and_referral"
SKD2026_CATEGORIES = frozenset({
    SKD2026_CATEGORY_TUNTAS, SKD2026_CATEGORY_INITIAL_MGMT_REFERRAL,
})

# SKD 2026 Spektrum Penyakit — the 16 system buckets (Tab. 4).
SKD2026_SYSTEMS = frozenset({
    "sistem_saraf", "psikiatri", "sistem_indera_mata", "sistem_indera_ear",
    "sistem_indera_hidung", "kepala_dan_leher", "sistem_respirasi",
    "sistem_kardiovaskuler", "sistem_gi_hepato_pankreatik", "sistem_ginjal_kemih",
    "sistem_reproduksi", "sistem_endokrin_metabolik_nutrisi",
    "sistem_hemato_imunologi", "sistem_muskuloskeletal",
    "sistem_kulit_integumen", "forensik_medikolegal",
})

# ── SKDI 2012 — LEGACY competency crosswalk ONLY (not primary authority). ──
# Kept for historical/curriculum/student compatibility (3A/3B/4A terms are
# still used widely). A legacy level may ONLY be set when the same disease is
# actually found & verified in SKDI 2012 — never inferred from the SKD 2026
# category.
SKDI_LEGACY_STANDARD = "SKDI 2012"
SKDI_LEVELS_KNOWN = frozenset({"1", "2", "3A", "3B", "4A"})
SKDI_LEVELS_ALLOWED_PRIMARY = frozenset({"3A", "3B", "4A"})  # legacy crosswalk scope


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


class SourceStatusKind(str, Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    UNCLEAR = "unclear"


class SourceTier(str, Enum):
    TIER0 = "0"          # regulatory / competency (KKI, Kemenkes)
    TIER1 = "1"          # current Indonesian national clinical guidance (PNPK, program)
    TIER2 = "2"          # Indonesian specialty/professional org (PAPDI, PERKI, IDAI, ...)
    TIER3 = "3"          # high-authority international guideline (WHO, NICE, ESC, ACC/AHA...)
    TIER4 = "4"          # standard educational reference


class SourceKind(str, Enum):
    COMPETENCY = "competency"
    DIAGNOSIS = "diagnosis"
    MANAGEMENT = "management"
    EPIDEMIOLOGY = "epidemiology"
    FORMULARY = "formulary"
    OSCE_RUBRIC = "osce_rubric"


class ReviewState(str, Enum):
    DRAFT = "draft"
    AI_GENERATED = "ai_generated"
    RESEARCH_COMPLETE = "research_complete"
    IN_CLINICAL_REVIEW = "in_clinical_review"
    CLINICALLY_REVIEWED = "clinically_reviewed"
    PILOT_VERIFIED = "pilot_verified"
    PUBLISHED = "published"
    NEEDS_UPDATE = "needs_update"
    SUPERSEDED = "superseded"


# States that can ONLY be reached via a human clinical review — never by an
# AI self-attesting on the strength of passing automated tests.
HUMAN_REVIEWED_STATES = frozenset({
    ReviewState.CLINICALLY_REVIEWED, ReviewState.PILOT_VERIFIED,
    ReviewState.PUBLISHED,
})