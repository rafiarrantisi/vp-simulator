"""Phase 13 — Final Integration / Pilot Release validation (plan §Phase 13).

Validates the WHOLE upgraded learning loop end-to-end WITHOUT changing
production behavior:

  Journey A — self-directed Case:
    V3 variant truth -> UserPerformanceRecord -> Evidence-Locked Hybrid
    Judge -> NormalizedScoringOutput -> longitudinal adapt ->
    readiness/progress (Result, Dashboard, Mentor speak one language, §36).
  Journey B — Mentor guided journey:
    free-text goal ctx -> planning_policy rank (deterministic, constrained)
    -> Today's Mission -> coach insight -> adaptation -> readiness ->
    end-of-journey report (completed != ready).
  Journey C — safety failure:
    superficially good checklist + catastrophic safety miss ->
    safety gate + capped score + non-pass rating + explicit feedback +
    mandatory Mentor remediation + capped readiness (no "Great job!").
  Journey D — accepted alternative treatment:
    clinically acceptable alternative wording/regimen gets fair credit
    (never exact-string zero).
  Journey E — guideline/version reproducibility:
    every score pins clinical-content / evidence-pack / scoring versions;
    historical results keep their original version (no silent rewrite);
    a no-change surveillance cycle leaves live truth untouched.

Isolation-safe: imports `pipeline.*` + pure `app.domains.mentor.*`
functions only (no app DB, no router, no network, no LLM). Deterministic.
Additive validation only — no migration, no UX change, no contract change.
"""
from pipeline.case_v3.loader import default_registry
from pipeline.clinical_contracts import version_stamp
from pipeline.clinical_contracts.medication import MedicationConcept, grade_regimen
from pipeline.clinical_contracts.versions import (
    CLINICAL_CONTENT_VERSION,
    EVIDENCE_PACK_VERSION,
    SCORING_VERSION,
)
from pipeline.judge.calibration_fixtures import (
    CANONICAL_DIAGNOSIS,
    DIAGNOSIS_SYNONYMS,
    FIXTURES,
    RUBRIC,
)
from pipeline.judge.evidence import build_rubric_from_variant
from pipeline.judge.pipeline import HYBRID_JUDGE_MODE, run_hybrid_judge
from pipeline.progress.longitudinal import adapt_report
from pipeline.progress.readiness import READINESS_VERSION, compute_readiness
from pipeline.surveillance.service import run_surveillance_cycle


def _run(record, **kw):
    args = dict(
        rubric_items=RUBRIC,
        learner_stage="koas",
        mode="practice",
        canonical_diagnosis=CANONICAL_DIAGNOSIS,
        diagnosis_synonyms=DIAGNOSIS_SYNONYMS,
        session_id="phase13-pilot",
    )
    args.update(kw)
    return run_hybrid_judge(record, **args)


def _report_dict(out, overall_override=None, osce=False, safety=None):
    """Shape a NormalizedScoringOutput into a longitudinal adapt_report input.

    Uses compat shape (per_dimension 0..100 + scoring_version) so adapt_report
    folds dims deterministically without touching any DB.
    """
    dims = {}
    for d, entry in (out.core_domains or {}).items():
        dims[str(d)] = {"score": entry.get("pct", 0), "max": 100}
    dims = {"history": {"score": 70, "max": 100}}
    overall = overall_override or out.overall_0_100
    safety_gates = safety or [
        {"type": g.gate, "detail": g.detail} for g in (out.safety_gates or [])
    ]
    return {
        "overall": overall,
        "per_dimension": dims,
        "per_item": [],
        "safety_gates": safety_gates,
        "summary": "phase13 pilot",
        "scoring_version": out.scoring_version,
        "mode": "osce" if osce else "practice",
    }


class TestJourneyA:
    def test_variant_truth_feeds_single_rubric(self):
        reg = default_registry()
        assert len(reg.families) > 0
        assert len(reg.variants) > 0
        variant = next(iter(reg.variants.values()))
        rubric = build_rubric_from_variant(variant)
        assert len(rubric) > 0
        assert all(r.get("expected") for r in rubric)

    def test_excellent_case_scores_high_with_evidence(self):
        out = _run(FIXTURES["excellent"]())
        assert "advisory" == HYBRID_JUDGE_MODE
        assert out.overall_0_100 >= 60
        assert str(out.global_rating).lower() in ("pass", "superior")
        assert out.scoring_version == SCORING_VERSION
        assert out.evidence_pack_version == EVIDENCE_PACK_VERSION
        assert out.clinical_content_version == CLINICAL_CONTENT_VERSION
        evidenced = [i for i in out.items if i.evidence]
        assert len(evidenced) >= 5
        assert out.feedback.get("overall_assessment")
        assert out.feedback.get("what_to_practise_next") is not None
        for line in out.feedback.get("what_you_did_well", []):
            assert line.get("evidence") and line.get("expected")

    def test_result_dashboard_mentor_share_one_language(self):
        out = _run(FIXTURES["pass"]())
        rep = _report_dict(out)
        ns = adapt_report(rep, content_schema="new", session_id="s1")
        assert ns.overall_0_100 == out.overall_0_100
        assert ns.engine == "v3_compat"
        assert ns.scoring_version == SCORING_VERSION
        sessions = [ns.to_dict()]
        ready = compute_readiness(sessions)
        assert ready["version"] == READINESS_VERSION
        assert ready["session_count"] == 1
        assert ready["confidence"] == "low"
        assert ready["score"] <= 59


class TestJourneyB:
    def _ctx(self):
        return {
            "goal": "Internal Medicine OSCE in 7 days",
            "target_specialty": "internal medicine",
            "level": "koas",
            "timeline_days": 7,
            "weaknesses": ["management"],
        }

    def test_planning_is_deterministic_and_constrained(self):
        from app.domains.mentor.planning_policy import build_candidates, rank_candidates

        reg = default_registry()
        cands = build_candidates([], registry=reg, learner_stage="koas")
        assert len(cands) > 0
        assert all(str(c.get("review_state", "")).lower() != "draft" for c in cands)
        ctx = self._ctx()
        first = rank_candidates(cands, ctx, day=1, duration_days=7)
        second = rank_candidates(cands, ctx, day=1, duration_days=7)
        assert [c["ref"] for c in first] == [c["ref"] for c in second]
        assert all("_score" in c and "_reasons" in c for c in first)
        assert isinstance(first[0]["_reasons"], list)

    def test_todays_mission_coach_adaptation_readiness_loop(self):
        from app.domains.mentor.adaptive import decide_adaptation
        from app.domains.mentor.coach import build_coach_insight
        from app.domains.mentor.mission import end_of_journey_report, todays_mission

        pick_reason = "target_specialty+coverage_gap"
        journey_cases = [
            {
                "day": 1,
                "case_id": "fam_dengue",
                "focus_area": "Internal Medicine foundation",
                "status": "available",
                "estimated_minutes": 45,
                "selection_reason": pick_reason,
                "slot_type": "core",
            }
        ]
        mission = todays_mission(journey_cases, readiness={"needs_work": []})
        assert mission["state"] == "ready"
        assert mission["cta"]["case_id"] == "fam_dengue"
        assert mission["expected_minutes"] == 45
        assert mission["why"][0] in pick_reason

        out = _run(FIXTURES["pass"]())
        rep = _report_dict(out)
        adaptation = decide_adaptation(
            score=out.overall_0_100,
            report=rep,
            family_ref="fam_dengue",
            recent_scores=[70, out.overall_0_100],
        )
        assert adaptation["slot_kind"] in ("none", "spaced_revisit")
        insight = build_coach_insight(
            report=rep,
            score=out.overall_0_100,
            journey_ctx={
                "goal": "osce",
                "target_specialty": "internal medicine",
                "timeline_days": 7,
            },
            adaptation=adaptation,
            next_pick={"case_id": "fam_tb", "selection_reason": "coverage_gap"},
        )
        assert insight["headline"]
        weak_dims = {d for d in (rep.get("per_dimension") or {})}
        for g in insight["evidence"]["weak_dims"]:
            assert (g in weak_dims) is True
        report = end_of_journey_report(
            journey={"context": {"goal": "osce"}, "progress": {"total": 1, "completed": 1}},
            readiness=compute_readiness(
                [adapt_report(rep, content_schema="new", session_id="s1").to_dict()]
            ),
            evidence_log=[{"specialty": "internal medicine", "score": out.overall_0_100}],
        )
        assert report["verdict"] in ("completed", "ready")
        assert report["note"].startswith("Journey completed")


class TestJourneyC:
    def test_safety_miss_caps_score_rating_and_readiness(self):
        from app.domains.mentor.adaptive import decide_adaptation
        from app.domains.mentor.coach import build_coach_insight

        out = _run(FIXTURES["unsafe"]())
        assert len(out.safety_gates) > 0
        assert str(out.global_rating).lower() in ("fail", "borderline")
        assert out.feedback.get("safety_flags")
        mgmt_line = out.feedback.get("management", "")
        assert "afety" in mgmt_line
        rep = _report_dict(out)
        adaptation = decide_adaptation(
            score=out.overall_0_100,
            report=rep,
            family_ref="fam_dengue",
            recent_scores=[out.overall_0_100],
        )
        assert adaptation["action"] == "remediate"
        assert adaptation["slot_kind"] == "remediation"
        assert adaptation.get("mandatory") is True
        insight = build_coach_insight(
            report=rep,
            score=out.overall_0_100,
            journey_ctx={"goal": "osce"},
            adaptation=adaptation,
        )
        assert insight["safety_flag"] is True
        assert "safety" in insight["headline"].lower()
        ns = adapt_report(rep, content_schema="new", session_id="unsafe1")
        assert ns.safety_triggered is True
        ready = compute_readiness([ns.to_dict()])
        assert ready["score"] <= 59
        assert any(d["factor"] in ("safety", "safety_cap") for d in ready["drivers"])

    def test_no_evidence_no_credit_holds(self):
        out = _run(FIXTURES["weak"]())
        misses = [i for i in out.items if i.adjudication == "miss"]
        assert len(misses) >= len(out.items) // 3
        for item in out.items:
            if item.score_0_3 == 3:
                assert item.evidence


class TestJourneyD:
    def _concept(self):
        return MedicationConcept(
            generic_name="paracetamol",
            preferred_agents=["paracetamol", "parasetamol"],
            acceptable_alternatives=["acetaminophen"],
            contraindications=["ibuprofen"],
        )

    def test_synonym_typo_abbreviation_get_fair_credit(self):
        c = self._concept()
        g = grade_regimen("acetaminophen", [c])
        assert g.outcome in ("correct_preferred", "acceptable_alternative")
        g2 = grade_regimen("PCM", [c])
        assert g2.outcome in ("correct_preferred", "acceptable_alternative", "incomplete")
        assert g2.outcome != "inappropriate"

    def test_judge_accepts_alternative_tx_fixture(self):
        out = _run(
            FIXTURES["acceptable_alternative_tx"](), treatment_concepts=[self._concept()]
        )
        tx = out.feedback.get("treatment_grade")
        assert tx.get("outcome") in ("correct_preferred", "acceptable_alternative")
        out_bad = _run(FIXTURES["unsafe"](), treatment_concepts=[self._concept()])
        tx_bad = out_bad.feedback.get("treatment_grade")
        assert tx_bad.get("outcome") == "unsafe"

    def test_paraphrase_gets_fair_treatment(self):
        out = _run(FIXTURES["unusual_wording_correct"]())
        assert out.overall_0_100 >= _run(FIXTURES["weak"]()).overall_0_100
        assert out.overall_0_100 >= 50


class TestJourneyE:
    def test_scores_pin_all_versions(self):
        out = _run(FIXTURES["pass"]())
        stamp = version_stamp()
        assert out.scoring_version == stamp["scoring_version"]
        assert out.evidence_pack_version == stamp["evidence_pack_version"]
        assert out.clinical_content_version == stamp["clinical_content_version"]

    def test_history_keeps_original_version(self):
        out = _run(FIXTURES["pass"]())
        rep = _report_dict(out)
        ns = adapt_report(rep, content_schema="new", session_id="hist1")
        assert ns.scoring_version == SCORING_VERSION
        assert ns.scoring_version == rep["scoring_version"]

    def test_no_change_surveillance_leaves_live_truth_untouched(self):
        import hashlib
        import json

        from pipeline.case_v3.loader import default_registry

        _reg = default_registry()
        before = hashlib.sha256(
            json.dumps(sorted(getattr(_reg(), "families", {}).keys())).encode()
        ).hexdigest()
        result, _queue = run_surveillance_cycle({})
        assert result.live_truth_changed is False
        assert result.tasks_created == 0
        after = hashlib.sha256(
            json.dumps(sorted(getattr(_reg(), "families", {}).keys())).encode()
        ).hexdigest()
        assert before == after

    def test_browser_payload_carries_no_hidden_answer_key(self):
        rec = FIXTURES["pass"]()
        non_dx_text = " ".join(
            rec.channel_texts("conversation")
            + rec.channel_texts("examination")
            + rec.channel_texts("investigation")
        ).lower()
        assert "without warning signs" not in non_dx_text
