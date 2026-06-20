"""Data-driven scoring, calibrated judge, and answer-key (BUILD_PLAN §6)."""
from pathlib import Path

from app.domains.scoring.rubric_v2 import (
    RUBRICS,
    resolve_weights,
    validate_weights,
)
from app.rag.answer_key import build_answer_key
from app.rag.judge_v2 import _normalize, build_judge_prompt, evaluate_v2
from app.rag.prompt_v2 import build_patient_prompt
from pipeline.case_v2 import parse_case_v2

_EXEMPLAR = Path(__file__).resolve().parents[2] / "content" / "cases" / "oph_dry_eye_001.md"
_APPENDIX = Path(__file__).resolve().parents[2] / "content" / "cases" / "im_gi_appendicitis_001.md"


def _case():
    return parse_case_v2(_EXEMPLAR)


# ── Rubric (weights as data) ──
def test_all_rubrics_sum_to_100():
    for mode, weights in RUBRICS.items():
        assert sum(weights.values()) == 100, f"{mode} must sum to 100"


def test_classic_preset_preserved():
    assert RUBRICS["classic_anamnesis"] == {"coverage": 40, "fife": 20, "red_flags": 20, "communication": 20}


def test_resolve_default_and_override():
    assert resolve_weights(None) == RUBRICS["anamnesis"]
    assert resolve_weights("osce_full") == RUBRICS["osce_full"]
    custom = {"history_coverage": 50, "red_flags": 30, "communication": 20}
    assert resolve_weights("anamnesis", custom) == custom  # valid override wins


def test_invalid_override_falls_back():
    bad = {"history_coverage": 50, "red_flags": 30}  # sums to 80
    assert validate_weights(bad)  # has errors
    assert resolve_weights("anamnesis", bad) == RUBRICS["anamnesis"]  # ignored


# ── Answer key (model answer from Part A) ──
def test_answer_key_complete():
    ak = build_answer_key(_case())
    assert ak["expected_ddx"]["working_diagnosis"].lower().startswith("dry eye")
    assert len(ak["expected_ddx"]["differentials"]) >= 2
    assert ak["red_flags"] and any(r["critical"] for r in ak["red_flags"])
    assert any(g["group"] == "ice_fife" for g in ak["anamnesis_checklist"])
    assert ak["investigations"]["appropriate"]
    assert ak["management"]["non_pharmacological"]


# ── Judge (stub-safe shape + calibration mechanics) ──
def test_evaluate_v2_stub_shape():
    report = evaluate_v2(_case(), [{"role": "user", "content": "hello"}])
    assert report["mode"] == "anamnesis"  # from case mode_default
    assert set(report["per_dimension"].keys()) == set(RUBRICS["anamnesis"].keys())
    for d, w in RUBRICS["anamnesis"].items():
        assert report["per_dimension"][d]["max"] == w
    assert report["overall"] == 0  # stub
    assert "answer_key" in report  # debrief reveal data attached


def test_overall_recomputed_and_clamped():
    weights = RUBRICS["anamnesis"]
    raw = {
        "per_dimension": {
            "history_coverage": {"score": 999, "feedback": "x"},  # over-max -> clamp to 35
            "red_flags": {"score": -5, "feedback": ""},            # negative -> clamp to 0
            "ice_fife": {"score": 10, "feedback": ""},
        },
        "per_item": [{"dimension": "history_coverage", "item": "Onset", "status": "HIT", "evidence": "q"}],
        "overall": 500,  # lying total — must be ignored
        "summary": "ok",
    }
    norm = _normalize(raw, "anamnesis", weights)
    assert norm["per_dimension"]["history_coverage"]["score"] == 35  # clamped to max
    assert norm["per_dimension"]["red_flags"]["score"] == 0          # clamped to 0
    # overall = sum of clamped dimension scores (not the model's 500)
    assert norm["overall"] == 35 + 0 + 10 + 0 + 0
    assert norm["per_item"][0]["status"] == "hit"  # normalised lowercase


def test_osce_full_mode_end_to_end():
    case = parse_case_v2(_APPENDIX)
    report = evaluate_v2(case, [{"role": "user", "content": "hello"}])
    assert report["mode"] == "osce_full"  # from case mode_default
    assert set(report["per_dimension"].keys()) == set(RUBRICS["osce_full"].keys())
    assert report["per_dimension"]["investigations"]["max"] == 15
    assert report["per_dimension"]["management"]["max"] == 10
    ak = report["answer_key"]
    assert ak["investigations"]["appropriate"]
    assert ak["expected_ddx"]["working_diagnosis"] == "Acute appendicitis"


def test_judge_prompt_is_conservative_and_leak_free():
    weights = RUBRICS["anamnesis"]
    system, msgs = build_judge_prompt(_case(), [{"role": "user", "content": "When did it start?"}],
                                      "anamnesis", weights)
    assert "ELICITED" in system and "conservative" in system.lower()
    content = msgs[0]["content"]
    assert "Anorexia" not in content  # (sanity: appendicitis-only token absent)
    # Judge sees ground truth, never the persona's verbatim opening line.
    assert "really uncomfortable lately" not in content.lower()
    assert "really uncomfortable lately" in build_patient_prompt(_case()).lower()  # but the patient does
