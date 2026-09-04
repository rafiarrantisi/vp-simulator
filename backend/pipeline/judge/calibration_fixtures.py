"""Phase 7G — calibration dataset: representative golden encounters.

Plan §7G + §40-41. Ten archetypes (excellent, pass, borderline, weak,
unsafe, verbose-but-poor, correct-unusual-wording, acceptable-alternative
treatment, incomplete diagnosis, contradiction) grounded on the real
canonical variant `dengue_001_mild` (Dengue fever without warning signs).

Each fixture is a full UserPerformanceRecord + rubric + canonical truth so
`run_hybrid_judge` scores it deterministically TODAY (no LLM, no DB), and
a qualified human reviewer can independently score the SAME fixture on the
review sheet (`HUMAN_REVIEW_SHEET_MD`). `compare_with_human` then reports
Qora-vs-human agreement (per-domain diff, pass/fail agreement, safety
agreement, evidence agreement, false-positive credit, false-negative miss).

Status: fixtures are machine-scored; HUMAN SCORES ARE PENDING (no reviewer
has scored them yet — never claim calibration agreement until that
happens, plan §3.5/§41).
"""
from __future__ import annotations

from pipeline.judge.evidence import UserPerformanceRecord

VARIANT_ID = "dengue_001_mild"

CANONICAL_DIAGNOSIS = "Dengue fever without warning signs"

DIAGNOSIS_SYNONYMS = list(("Dengue", "Dengue fever", "Demam berdarah dengue", "DBD"))

RUBRIC: list[dict] = [
    {
        "item_id": "hx_onset",
        "domain": "history",
        "expected": "Ask about fever onset and pattern",
        "kind": "history",
        "criticality": "critical",
    },
    {
        "item_id": "hx_bleeding",
        "domain": "history",
        "expected": "Ask about bleeding manifestations",
        "kind": "history",
        "criticality": "critical",
    },
    {
        "item_id": "rf_warning",
        "domain": "history",
        "expected": "Screen red flag: warning signs of severe dengue",
        "kind": "safety",
        "criticality": "safety-critical",
    },
    {
        "item_id": "dx_1",
        "domain": "diagnosis_ddx",
        "expected": CANONICAL_DIAGNOSIS,
        "kind": "diagnosis",
        "criticality": "critical",
        "synonyms": DIAGNOSIS_SYNONYMS,
    },
    {
        "item_id": "inv_1",
        "domain": "investigations",
        "expected": "Order full blood count with platelet monitoring",
        "kind": "investigation",
        "criticality": "important",
    },
    {
        "item_id": "mg_fluid",
        "domain": "management_non_pharma",
        "expected": "Advise adequate oral fluids and rest",
        "kind": "management",
        "criticality": "important",
    },
    {
        "item_id": "mg_drug",
        "domain": "management_pharma",
        "expected": "Give paracetamol for fever",
        "kind": "medication",
        "criticality": "important",
        "synonyms": ["paracetamol", "parasetamol"],
    },
    {
        "item_id": "mg_avoid",
        "domain": "management_non_pharma",
        "expected": "Avoid unsafe action: NSAIDs worsen bleeding risk",
        "kind": "safety",
        "criticality": "safety-critical",
    },
    {
        "item_id": "mg_refer",
        "domain": "management_non_pharma",
        "expected": "Explain referral and return precautions",
        "kind": "management",
        "criticality": "critical",
    },
    {
        "item_id": "comm_1",
        "domain": "communication_education",
        "expected": "Explain dengue course and home monitoring clearly",
        "kind": "communication",
        "criticality": "routine",
    },
]

ARCHETYPES = (
    "excellent",
    "pass",
    "borderline",
    "weak",
    "unsafe",
    "verbose_but_poor",
    "unusual_wording_correct",
    "acceptable_alternative_tx",
    "incomplete_diagnosis",
    "contradiction",
)


def _rec(**kw) -> UserPerformanceRecord:
    base = dict(
        conversation_turns=[],
        exam_actions=[],
        investigations=[],
        diagnosis_primary="",
        diagnosis_ddx=[],
        management_lines=[],
        medication_text="",
        referral_text="",
        education_text="",
        overtime=False,
        interaction_mode="practice",
        learner_level="koas",
    )
    base.update(kw)
    return UserPerformanceRecord(**base)


def _u(*texts) -> list[dict]:
    return [{"role": "user", "content": t} for t in texts]


def fixture_excellent() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u(
            "Kapan demam mulai? Apakah terus-menerus atau naik-turun?",
            "Apakah ada mimisan, gusi berdarah, atau bintik merah di kulit?",
            "Apakah ada nyeri perut hebat, muntah terus, atau lemas berat? Itu tanda bahaya dengue yang harus segera ke IGD.",
            "Hindari NSAID seperti ibuprofen karena meningkatkan risiko perdarahan; untuk demam cukup parasetamol.",
            "Saya jelaskan perjalanan dengue dan apa yang dipantau di rumah.",
        ),
        investigations=["full blood count with platelet monitoring"],
        diagnosis_primary="Dengue fever without warning signs",
        diagnosis_ddx=["Viral fever", "Typhoid"],
        management_lines=[] + [
            "Advise adequate oral fluids and rest",
            "Avoid NSAIDs — paracetamol only for fever",
            "Explain referral and return precautions",
        ],
        medication_text="paracetamol; avoid NSAIDs such as ibuprofen",
        referral_text="Explain referral and return precautions",
        education_text="Explain dengue course and home monitoring clearly",
    )


def fixture_pass() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u(
            "Kapan demamnya mulai?",
            "Ada perdarahan seperti mimisan atau gusi berdarah?",
            "Ada nyeri perut hebat atau muntah terus? Itu tanda bahaya.",
            "Hindari obat anti-nyeri NSAID; parasetamol saja untuk demam.",
            "Minum cairan yang cukup dan istirahat ya.",
        ),
        investigations=["full blood count"],
        diagnosis_primary="Dengue",
        diagnosis_ddx=["Typhoid fever"],
        management_lines=[
            "Advise adequate oral fluids and rest",
            "Avoid NSAIDs",
        ],
        medication_text="parasetamol; hindari NSAID",
        education_text="Explain dengue course and home monitoring clearly",
    )


def fixture_borderline() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u(
            "Sudah berapa hari demam?",
            "Ada tanda bahaya seperti nyeri perut atau muntah terus?",
            "Ada keluhan lain?",
        ),
        diagnosis_primary="Viral fever",
        management_lines=["Advise adequate oral fluids and rest"],
        medication_text="paracetamol",
    )


def fixture_weak() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u("Apa keluhannya?", "Sudah minum obat?"),
        diagnosis_primary="Common cold",
    )


def fixture_unsafe() -> UserPerformanceRecord:
    """High checklist chatter + catastrophic safety miss (plan Journey C)."""
    return _rec(
        conversation_turns=_u(
            "Kapan demam mulai? Polanya bagaimana?",
            "Ada mimisan atau gusi berdarah?",
            "Bagaimana nafsu makan dan tidur Anda? Ceritakan aktivitas harian.",
            "Apakah keluarga sehat semua? Bagaimana pekerjaan Anda?",
            "Pulang saja, istirahat di rumah, tidak perlu kontrol atau rujuk.",
        ),
        investigations=["full blood count with platelet monitoring"],
        diagnosis_primary="Dengue fever without warning signs",
        management_lines=["Pulang saja, istirahat di rumah, tidak perlu kontrol atau rujuk"],
        medication_text="ibuprofen",
        education_text="Explain dengue course and home monitoring clearly",
    )


def fixture_verbose_but_poor() -> UserPerformanceRecord:
    long_chat = [] + [
        "Ceritakan semua dari awal sampai akhir secara detail ya.",
        "Bagaimana masa kecil Anda? Riwayat keluarga lengkap?",
        "Apa makanan favorit? Bagaimana pola tidur setahun terakhir?",
        "Apakah stres kerja? Ceritakan suasana kantor dan perjalanan.",
        "Baik, jadi demam ya. Sudah berapa lama kira-kira?",
    ]
    return _rec(
        conversation_turns=_u(*long_chat),
        diagnosis_primary="Fever",
        management_lines=["Advise adequate oral fluids and rest"],
    )


def fixture_unusual_wording_correct() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u(
            "Onset of febrile episode? Continuous or saddleback pattern?",
            "Any haemorrhagic manifestations — epistaxis, gum bleed, petechiae?",
            "Screened for warning signs of severe dengue; counselled on prompt return if abdominal pain, persistent vomiting, lethargy.",
            "Avoid NSAIDs such as ibuprofen — bleeding risk; PCM only.",
        ),
        investigations=["CBC with serial platelet monitoring"],
        diagnosis_primary="DBD",
        diagnosis_ddx=["typhoid fever"],
        management_lines=[] + [
            "Maintain adequate oral fluid intake and rest",
            "Avoid NSAIDs",
            "Explain referral and return precautions",
        ],
        medication_text="PCM; avoid NSAIDs",
        referral_text="Explain referral and return precautions",
        education_text="Counselled on dengue course and home monitoring",
    )


def fixture_acceptable_alternative_tx() -> UserPerformanceRecord:
    r = fixture_pass()
    r.medication_text = "acetaminophen"
    return r


def fixture_incomplete_diagnosis() -> UserPerformanceRecord:
    r = fixture_pass()
    r.diagnosis_primary = "Suspek demam virus"
    r.diagnosis_ddx = []
    return r


def fixture_contradiction() -> UserPerformanceRecord:
    return _rec(
        conversation_turns=_u(
            "Kapan demam mulai?",
            "Tidak ada perdarahan sama sekali, pasien menyangkal mimisan.",
        ),
        investigations=["full blood count with platelet monitoring"],
        diagnosis_primary="Severe dengue with shock",
        diagnosis_ddx=["Dengue fever without warning signs"],
        management_lines=["Advise adequate oral fluids and rest"],
        medication_text="paracetamol",
    )


FIXTURES = {
    "excellent": fixture_excellent,
    "pass": fixture_pass,
    "borderline": fixture_borderline,
    "weak": fixture_weak,
    "unsafe": fixture_unsafe,
    "verbose_but_poor": fixture_verbose_but_poor,
    "unusual_wording_correct": fixture_unusual_wording_correct,
    "acceptable_alternative_tx": fixture_acceptable_alternative_tx,
    "incomplete_diagnosis": fixture_incomplete_diagnosis,
    "contradiction": fixture_contradiction,
}


def score_all(runner) -> dict:
    """Score every archetype with `runner(record) -> NormalizedScoringOutput`."""
    return {name: runner(f()) for name, f in FIXTURES.items()}


def compare_with_human(hybrid_outputs: dict, human_scores: dict) -> dict:
    """Compare hybrid outputs vs independent human reviewer scores.

    `hybrid_outputs`: {archetype: NormalizedScoringOutput}
    `human_scores`: {archetype: {overall, global_rating, safety_triggered,
      item_status: {item_id: hit|partial|miss}}}
    Returns agreement metrics (plan §41: per-domain diff, pass/fail
    agreement, safety agreement, evidence agreement, FP credit, FN miss).
    """

    def _pass(r: str) -> bool:
        return r in ("Pass", "Superior")

    per_domain_diff: list = []
    pass_fail_agree = 0
    pass_fail_total = 0
    safety_agree = 0
    safety_total = 0
    ev_agree = 0
    ev_total = 0
    false_positive_credit = 0
    false_negative_miss = 0
    for name, out in (hybrid_outputs or {}).items():
        human = (human_scores or {}).get(name)
        if not human:
            continue
        for d, entry in (out.core_domains or {}).items():
            hv = ((human.get("core_domains") or {}).get(d) or {}).get("pct")
            if hv is None:
                continue
            try:
                per_domain_diff.append(abs(float((entry or {}).get("pct", 0)) - float(hv)))
            except (TypeError, ValueError):
                continue
        pass_fail_total += 1
        if _pass(str(out.global_rating or "")) == _pass(str(human.get("global_rating") or "")):
            pass_fail_agree += 1
        safety_total += 1
        if bool(out.safety_gates) == bool(human.get("safety_triggered")):
            safety_agree += 1
        h_items = human.get("item_status") or {}
        for it in out.items or []:
            if it.item_id not in h_items:
                continue
            ev_total += 1
            mine = (it.adjudication or "") == "hit"
            theirs = str(h_items.get(it.item_id)) == "hit"
            if mine == theirs:
                ev_agree += 1
            elif mine and not theirs:
                false_positive_credit += 1
            else:
                false_negative_miss += 1
    n = max(1, pass_fail_total)
    return {
        "per_domain_mean_abs_diff": (
            round(sum(per_domain_diff) / len(per_domain_diff), 2) if per_domain_diff else None
        ),
        "pass_fail_agreement": round(pass_fail_agree / n, 3),
        "safety_gate_agreement": round(safety_agree / max(1, safety_total), 3),
        "evidence_agreement": round(ev_agree / max(1, ev_total), 3),
        "false_positive_credit": false_positive_credit,
        "false_negative_miss": false_negative_miss,
        "n_compared": pass_fail_total,
    }


HUMAN_REVIEW_SHEET_MD = """# Phase 7 — Human Calibration Review Sheet (PENDING)

Instructions for the qualified reviewer (doctor / clinical educator):

1. For EACH archetype below (10 golden encounters on variant
   `dengue_001_mild` — Dengue fever without warning signs), read the
   learner record (transcript turns, investigations, diagnosis, management,
   medication) in `backend/pipeline/judge/calibration_fixtures.py`.
2. Score INDEPENDENTLY (do not look at Qora output first):
   - per-item status per rubric item in RUBRIC (hit | partial | miss);
   - per-domain pct for the 8 core domains;
   - overall 0-100; global rating (Fail | Borderline | Pass | Superior);
   - safety_triggered (yes/no + which gate type).
3. Record as JSON: `{archetype: {overall, global_rating, safety_triggered,
   core_domains: {domain: {pct}}, item_status: {item_id: status}}}`.
4. Return to engineering for `compare_with_human`. Disagreements tune
   rubric wording / semantic equivalence / weights / thresholds / safety
   rules (plan §41). Do NOT overfit to one reviewer's preference.

Archetypes: excellent, pass, borderline, weak, unsafe, verbose_but_poor,
unusual_wording_correct, acceptable_alternative_tx, incomplete_diagnosis,
contradiction.

STATUS: no human scores recorded yet — agreement metrics are TBD.
"""
