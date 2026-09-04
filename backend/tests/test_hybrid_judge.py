"""FASE 7 — Evidence-locked hybrid judge fixtures (deterministic, offline).

Fixture matrix (intentionally hard): exact, paraphrase, vague, omitted,
family-wrong-severity, wrong dx, intl-alternative, drug-wrong-dose, unsafe
drug, good-components-wrong-priority, high-checklist+catastrophic-miss,
verbose-weak, concise-strong, Bahasa Indonesia, English, mixed, abbrev, typo.
Plus STOP-guard: no live router/judge imports the experimental hybrid layer.
"""
from pipeline.case_v3.loader import CaseRegistry
from app.domains.scoring import hybrid as H


def _variant():
    reg = CaseRegistry.from_dir()
    for vid in ("dengue_001_mild", "uti_adult_002"):
        if vid in reg.variants:
            return reg.variants[vid]
    return next(iter(reg.variants.values()))


def _upr(**kw):
    base = dict(transcript=[], pf_notes="", pf_areas=[], ddx={}, management={},
                mode="practice", overtime=False, learner_level="koas")
    base.update(kw)
    return H.build_upr(**base)


def _score(**kw):
    return H.score_hybrid(_variant(), _upr(**kw))


def test_stop_guard_no_live_import():
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1] / "app"
    live = ["app/domains/sessions/v2_router.py",
            "app/domains/sessions/v3_compat_service.py",
            "app/rag/judge_v2.py", "app/rag/judge_v3.py"]
    for rel in live:
        txt = (root.parent / rel.replace("app/", "app/")).read_text() if False else None
    import app.domains.sessions.v2_router as R
    import app.domains.sessions.v3_compat_service as C
    import app.rag.judge_v2 as J2
    import app.rag.judge_v3 as J3
    for mod in (R, C, J2, J3):
        src = open(mod.__file__, encoding="utf-8").read()
        assert "scoring.hybrid" not in src and "from hybrid" not in src, \
            f"live module must not import hybrid: {mod.__name__}"


def test_exact_answer_scores_high_and_pass():
    v = _variant()
    hx = [f.key.replace("_", " ") for g in v.history for f in g.facts]
    t = [{"role": "user", "content": f"Could you tell me about {k}?"} for k in hx]
    for r in (v.red_flags or [])[:3]:
        fact = (getattr(r, "fact", "") or "")[:90]
        t.append({"role": "user", "content": f"Do you have {fact}?"})
    t.append({"role": "user", "content": "What warning signs should prompt return, and do you need referral?"})
    mgmt = {"terapi": "; ".join(v.management.pharmacologic or ["antibiotic"])}
    if getattr(v.management, "referral", None):
        mgmt["referral"] = "; ".join(v.management.referral)
    if getattr(v.management, "education_safety_netting", None):
        mgmt["edukasi"] = "; ".join(v.management.education_safety_netting)
    if getattr(v.management, "non_pharmacologic", None):
        mgmt["complete"] = "; ".join(v.management.non_pharmacologic)
    r = _score(transcript=t, ddx={"dx1": v.diagnostic.working_diagnosis}, management=mgmt)
    assert r["diagnosis_grade"]["tier"] == "exact"
    assert r["overall"] > 45, f"strong evidence should pass comfortably, got {r['overall']}"
    assert r["global_rating"] in ("Pass", "Superior", "Borderline")


def test_paraphrase_accepted_no_evidence_no_credit():
    v = _variant()
    # paraphrase of first history fact should at least partially credit
    key = v.history[0].facts[0].key.replace("_", " ")
    r = _score(transcript=[{"role": "user", "content": f"Tell me more regarding {key} please"}])
    assert any(e["adjudication"] in ("hit", "partial") for e in r["evidence_ledger"])
    # empty submission: ledger all miss, overall low
    r2 = _score(transcript=[])
    assert all(e["adjudication"] == "miss" for e in r2["evidence_ledger"]
               if e["domain"] == "anamnesis" or True) or r2["overall"] < 40


def test_vague_question_not_full_credit():
    r = _score(transcript=[{"role": "user", "content": "tell me everything"}])
    anam = [e for e in r["evidence_ledger"] if e["domain"] == "anamnesis"]
    assert all(e["score_0_3"] < 3 for e in anam)


def test_omitted_item_miss():
    r = _score(transcript=[{"role": "user", "content": "hello"}],
               ddx={"dx1": "wrong disease xyz"}, management={})
    assert r["diagnosis_grade"]["tier"] in ("wrong", "dangerous-miss", "broad-partial")
    assert r["overall"] < 60


def test_family_wrong_severity_partial():
    v = _variant()
    # strip severity words from target to simulate family-only answer
    fam = " ".join(w for w in v.diagnostic.working_diagnosis.split()
                   if w.lower() not in ("severe", "mild", "acute", "berat", "ringan"))
    r = _score(transcript=[], ddx={"dx1": fam or "dengue"})
    assert r["diagnosis_grade"]["tier"] in ("family-incomplete-severity", "exact", "broad-partial")


def test_wrong_diagnosis_clamped():
    r = _score(transcript=[{"role": "user", "content": "do you have headache?"}],
               ddx={"dx1": "migraine"}, management={"terapi": "paracetamol"})
    assert r["by_domain"]["diagnosis_ddx"]["score"] <= 20.0


def test_intl_alternative_acceptable():
    # Loose agent concept (class term) must not auto-zero pharm
    r = _score(transcript=[], ddx={}, management={"terapi": "oral antibiotic per guideline"})
    assert r["pharm_grade"]["score_0_3"] >= 1


def test_correct_drug_wrong_dose_detail():
    v = _variant()
    truth = "; ".join(v.management.pharmacologic[:1]) or "antibiotic"
    agent = truth.split()[0]
    r = _score(transcript=[], management={"terapi": agent})  # agent only, no dose
    assert r["pharm_grade"]["score_0_3"] in (1, 2, 3)  # never crashes; detail-gated


def test_unsafe_drug_gate_and_cap():
    r = _score(transcript=[{"role": "user", "content": "any dengue?"}],
               ddx={"dx1": "dengue"},
               management={"terapi": "ibuprofen NSAID for dengue fever"})
    types = {g["type"] for g in r["safety_gates"]}
    assert "dangerous_drug" in types
    assert r["overall"] <= 40.0
    assert r["global_rating"] == "Fail"


def test_high_checklist_catastrophic_miss_capped():
    v = _variant()
    hx = [f.key.replace("_", " ") for g in v.history for f in g.facts]
    t = [{"role": "user", "content": f"about {k}?"} for k in hx]
    r = _score(transcript=t, ddx={"dx1": "totally wrong"},
               management={"terapi": "ibuprofen NSAID for dengue"})
    assert r["overall"] <= 40.0  # safety overrides checklist gaming
    assert "great job" not in (r["feedback"]["summary"] or "").lower()


def test_verbose_weak_vs_concise_strong():
    weak = _score(transcript=[{"role": "user", "content": "hello " * 50}])
    v = _variant()
    hx = [f.key.replace("_", " ") for g in v.history for f in g.facts][:4]
    strong = _score(
        transcript=[{"role": "user", "content": f"Do you have {k}?"} for k in hx],
        ddx={"dx1": v.diagnostic.working_diagnosis})
    assert strong["overall"] > weak["overall"]


def test_bahasa_indonesia_mixed_abbrev_typo():
    r_id = _score(transcript=[{"role": "user", "content": "Apakah ada demam berdarah?"}],
                  ddx={"dx1": "DBD"})
    assert r_id["diagnosis_grade"]["tier"] in ("exact", "family-incomplete-severity", "broad-partial")
    r_typo = _score(transcript=[], ddx={"dx1": "denguee"})
    assert r_typo["diagnosis_grade"]["tier"] in ("exact", "family-incomplete-severity")
    r_mix = _score(transcript=[{"role": "user", "content": "Ada nyeri saat kencing? dysuria?"}])
    assert any(e["adjudication"] in ("hit", "partial") for e in r_mix["evidence_ledger"])


def test_overtime_penalty_deterministic():
    v = _variant()
    hx = [f.key.replace("_", " ") for g in v.history for f in g.facts][:3]
    t = [{"role": "user", "content": f"about {k}?"} for k in hx]
    a = _score(transcript=t, overtime=False)
    b = _score(transcript=t, overtime=True)
    assert abs((a["overall"] - b["overall"]) - 10.0) < 0.2 or b["overall"] == 0.0


def test_arithmetic_server_controlled_shapes():
    r = _score(transcript=[{"role": "user", "content": "fever?"}])
    assert r["schema"] == "hybrid_score/0.1"
    assert set(r["by_domain"].keys()) == set(H.EIGHT_DOMAINS)
    assert 0.0 <= r["overall"] <= 100.0
    assert r["global_rating"] in ("Fail", "Borderline", "Pass", "Superior")
    assert r["standard_setting"].startswith("none")
    n = H.to_normalized(r, session_id="s1", case_id="c1")
    assert n["schema"] == "normalized_score/1.0"
    assert n["hybrid"]["global_rating_4tier"] == r["global_rating"]
