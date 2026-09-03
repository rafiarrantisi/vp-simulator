"""FASE 2 — normalized scoring output contract tests (pure adapters, no LLM).

The live judges are untouched: adapters translate STORED reports into the
single versioned shape at read/export time. Stored history is never rewritten.
"""
import copy

from app.domains.scoring.contracts import (
    CONTRACT_VERSION,
    CORE_OSCE_DOMAINS,
    NormalizedScore,
    from_v2_report,
    from_v3_native,
)


def _v2_report():
    return {
        "mode": "anamnesis",
        "weights": {"history_coverage": 25, "red_flags": 15, "ice_fife": 8,
                    "questioning_technique": 15, "communication": 10,
                    "diagnostic_reasoning": 15, "clinical_safety": 12},
        "per_dimension": {
            "history_coverage": {"score": 20, "max": 25, "feedback": "Good coverage"},
            "red_flags": {"score": 10, "max": 15, "feedback": ""},
            "ice_fife": {"score": 8, "max": 8, "feedback": ""},
            "questioning_technique": {"score": 9, "max": 15, "feedback": ""},
            "communication": {"score": 7, "max": 10, "feedback": ""},
            "diagnostic_reasoning": {"score": 12, "max": 15, "feedback": ""},
            "clinical_safety": {"score": 12, "max": 12, "feedback": ""},
        },
        "per_item": [
            {"dimension": "history_coverage", "item": "Onset", "status": "hit",
             "evidence": "patient said ..."},
            {"dimension": "red_flags", "item": "Fever", "status": "miss", "evidence": ""},
        ],
        "overall": 78,
        "summary": "Solid history, screen red flags.",
        "safety_gates": [{"type": "missed_critical_red_flag", "detail": "Fever not asked"}],
        "answer_key": {"checklist": []},
    }


def test_from_v2_report_core_mapping_and_missing_is_none():
    rep = _v2_report()
    snapshot = copy.deepcopy(rep)
    n = from_v2_report(rep, session_id="s1", case_id="c1", mode="anamnesis",
                       rubric_name="anamnesis", engine="llm_judge_v2",
                       clinical_content_version="v3.0")
    assert rep == snapshot  # adapters never mutate stored history
    assert n.validate() == []
    assert n.overall_0_100 == 78
    assert n.core_osce_domains["history"] == {"score": 20, "max": 25}
    assert n.core_osce_domains["safety"] == {"score": 12, "max": 12}
    # Unassessed in anamnesis mode is None — never silent 0.
    assert n.core_osce_domains["physical_exam"] is None
    assert n.core_osce_domains["investigations"] is None
    assert n.answer_key_present is True
    assert n.scoring["contract_version"] == CONTRACT_VERSION
    assert n.sources["clinical_content_version"] == "v3.0"
    assert len(n.rubric_items) == 2
    assert n.safety_gates == [{"type": "missed_critical_red_flag", "detail": "Fever not asked"}]


def test_from_v2_report_tolerates_empty_stub_shape():
    from app.domains.scoring.rubric_v2 import RUBRICS
    from app.rag.judge_v2 import _empty_report  # real code shape, zero LLM
    n = from_v2_report(_empty_report("anamnesis", RUBRICS["anamnesis"], "stub"),
                       session_id="s", case_id="c")
    assert n.validate() == []
    assert n.overall_0_100 == 0
    assert all(n.core_osce_domains[d] is None or n.core_osce_domains[d]["score"] == 0
               for d in CORE_OSCE_DOMAINS)


def test_from_v3_native_ratio_scale():
    payload = {"total": 0.8, "max": 1.0,
               "by_dimension": {
                   "info_gathering": {"score": 1.0, "notes": "3/3"},
                   "diagnostic_quality": {"score": 0.2, "notes": "weak"},
                   "focus_efficiency": {"score": 0.5, "notes": "placeholder"},
               },
               "safety_flags": [{"gate": "missed_emergency_red_flag", "critical": True}]}
    n = from_v3_native(payload, session_id="s3", case_id="fam_x",
                       clinical_content_version="v3.0")
    assert n.validate() == []
    assert n.content_schema == "new"
    assert n.overall_0_100 == 80.0
    assert n.core_osce_domains["history"] == {"score": 100.0, "max": 100}
    assert n.core_osce_domains["diagnosis"] == {"score": 20.0, "max": 100}
    assert n.safety_gates[0]["type"] == "missed_emergency_red_flag"


def test_contract_version_pinned():
    n = NormalizedScore(session_id="s", case_id="c",
                        core_osce_domains={d: None for d in CORE_OSCE_DOMAINS})
    assert n.validate() == []
    n.contract_version = "9.9"
    assert any("contract_version" in e for e in n.validate())
    n.contract_version = CONTRACT_VERSION
    n.overall_0_100 = 101
    assert any("overall_0_100" in e for e in n.validate())


def test_bad_item_status_rejected():
    n = NormalizedScore(session_id="s", case_id="c",
                        core_osce_domains={d: None for d in CORE_OSCE_DOMAINS},
                        rubric_items=[{"dimension": "x", "item": "y",
                                       "status": "maybe", "evidence": ""}])
    assert any("hit|partial|miss" in e for e in n.validate())
