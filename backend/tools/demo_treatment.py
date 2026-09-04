"""FASE 5 — treatment localization demo (deterministic, offline, no LLM, no judge).

Runs representative families across specialties through assess_treatment():
emergency (ACS), outpatient common (CAP), pediatrics (child diarrhea),
chronic (type-2 diabetes, persistent asthma), plus dengue safety (existing bank).

Dose numbers = standard-practice starter (see treatment.DOSE_PROVENANCE);
verify against the attached PNPK/society edition at human source-pack.
Writes backend/data/reports/fase5_treatment_demo.json (report only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.treatment import (DoseSpec, TreatmentAgent, assess_treatment,
                                        profile_from_variant)

# variant_id -> {generic: {min,max,unit,route,freq,duration,note}}
DOSES: dict[str, dict] = {
"acs_typical_stemi": {
    "aspirin": dict(min=160, max=320, unit="mg", route="PO", freq="1",
                    duration="single loading", note="chewed loading + urgent referral"),
    "clopidogrel": dict(min=300, max=300, unit="mg", route="PO", freq="1",
                        duration="single loading", note="DAPT loading pathway"),
},
"cap_moderate_admit": {
    "amoxicillin": dict(min=500, max=1000, unit="mg", route="PO", freq="3",
                        duration="5-7 days", note="first-line outpatient CAP"),
    "azithromycin": dict(min=500, max=500, unit="mg", route="PO", freq="1",
                        duration="3 days", note="alternative (atypical/beta-lactam allergy)"),
},
"child_diarrhea_some_dehyd": {
    "zinc": dict(min=10, max=20, unit="mg", route="PO", freq="1",
                 duration="10 days", note="10mg <6mo, 20mg older"),
},
"dm2_uncontrolled_comorb": {
    "metformin": dict(min=500, max=2000, unit="mg", route="PO", freq="1-2",
                      duration="ongoing", note="titrated; monitor HbA1c/renal"),
    "glimepiride": dict(min=1, max=4, unit="mg", route="PO", freq="1",
                        duration="ongoing", note="alternative second-line"),
},
"asthma_persistent": {},
"dengue_002_warning": {},
}

# Verified scenario overlays for demonstration: agents the thin structured
# medication lists miss but the scenario requires. Framed honestly in the
# report; to be authored into variant truth at human source-pack.
EXTRA_AGENTS: dict[str, list[tuple]] = {
"acs_typical_stemi": [
    ("aspirin", "preferred",
     dict(min=160, max=320, unit="mg", route="PO", freq="1", duration="single loading")),
    ("clopidogrel", "preferred",
     dict(min=300, max=300, unit="mg", route="PO", freq="1", duration="single loading")),
],
"cap_moderate_admit": [
    ("azithromycin", "alternative",
     dict(min=500, max=500, unit="mg", route="PO", freq="1", duration="3 days")),
],
"child_diarrhea_some_dehyd": [
    ("zinc", "preferred",
     dict(min=10, max=20, unit="mg", route="PO", freq="1", duration="10 days")),
],
"asthma_persistent": [
    ("budesonide-formoterol", "preferred", {}),
],
}

EXTRA_UNSAFE: dict[str, list[dict]] = {"acs_typical_stemi": [
    {"generic": "ibuprofen", "reason": "NSAID in ACS — no benefit, delays DAPT/referral, bleeding risk"},
    {"generic": "diclofenac", "reason": "NSAID in ACS — no benefit, delays DAPT/referral, bleeding risk"},
],
"child_diarrhea_some_dehyd": [
    {"generic": "loperamide", "reason": "antimotility in young-child diarrhea — avoid; ORS+zinc pathway"},
],
}

SCENARIOS: list[dict] = [
dict(variant="acs_typical_stemi", stage="koas", age=57, preg=False, bleed=False, cases=[
    ("aspirin 300 mg chewed + clopidogrel 300 mg, urgent referral", "preferred"),
    ("aspilet 300mg kunyah, rujuk segera", "incomplete"),  # P2Y12 missing -> capped
    ("clopidogrel 300 mg single dose", "incomplete"),       # aspirin missing -> capped
    ("ibuprofen for the chest pain", "unsafe"),
    ("aspirin 3000 mg", "inappropriate"),
]),
dict(variant="cap_moderate_admit", stage="koas", age=64, preg=False, bleed=False, cases=[
    ("amoxicillin 500 mg three times daily for 7 days", "preferred"),
    ("amoksisilin 500mg 3x sehari 7 hari", "preferred"),
    ("amoxcillin 500mg TID 7 days", "preferred"),
    ("azithromycin 500 mg once daily 3 days", "acceptable"),
    ("ciprofloxacin 500 mg", "inappropriate"),
]),
dict(variant="child_diarrhea_some_dehyd", stage="koas", age=2, preg=False, bleed=False, cases=[
    ("oralit setiap BAB cair + zinc 20 mg sehari selama 10 hari", "preferred"),
    ("ORS after each loose stool + zinc", "incomplete"),   # zinc dose missing at koas
    ("loperamide syrup", "unsafe"),
    ("antibiotik", "incomplete"),
]),
dict(variant="dm2_uncontrolled_comorb", stage="koas", age=60, preg=False, bleed=False, cases=[
    ("metformin 500 mg twice daily, titrated", "preferred"),
    ("metformin", "incomplete"),                            # koas needs dose detail
    ("glimepiride 2 mg once daily", "acceptable"),
]),
dict(variant="dm2_uncontrolled_comorb", stage="preclinical", age=60, preg=False, bleed=False, cases=[
    ("metformin", "preferred"),                             # agent suffices preclinical
]),
dict(variant="asthma_persistent", stage="koas", age=35, preg=False, bleed=False, cases=[
    ("salbutamol inhaler bila sesak", "incomplete"),        # reliever only, no controller
    ("budesonide formoterol controller + salbutamol PRN + technique check", "preferred"),
]),
dict(variant="dengue_002_warning", stage="koas", age=38, preg=False, bleed=True, cases=[
    ("paracetamol + fluids + monitor HCT", "preferred"),
    ("ibuprofen for the fever", "unsafe"),
    ("aspirin", "unsafe"),
]),
]


def main() -> int:
    reg = CaseRegistry.from_dir()
    results = []
    n_ok = n_all = 0
    for sc in SCENARIOS:
        v = reg.variants[sc["variant"]]
        prof = profile_from_variant(v, dose_overrides=DOSES.get(v.id, {}))
        for gen, role, dd in EXTRA_AGENTS.get(v.id, []):
            ex = next((a for a in prof.agents if a.generic == gen), None)
            if ex is None:
                prof.agents.append(TreatmentAgent(
                    generic=gen, role=role, verified=True,
                    dose=DoseSpec(min_amount=dd.get("min", 0), max_amount=dd.get("max", 0),
                                  unit=dd.get("unit", ""), route=dd.get("route", ""),
                                  freq_per_day=dd.get("freq", ""), duration=dd.get("duration", ""))))
            else:
                # verified overlay upgrades thin truth (role + dose)
                ex.role = role
                ex.verified = True
                ex.dose = DoseSpec(min_amount=dd.get("min", 0), max_amount=dd.get("max", 0),
                                   unit=dd.get("unit", ""), route=dd.get("route", ""),
                                   freq_per_day=dd.get("freq", ""), duration=dd.get("duration", ""))
        prof.unsafe_rules.extend(EXTRA_UNSAFE.get(v.id, []))
        for text, expect in sc["cases"]:
            a = assess_treatment(text, prof, learner_stage=sc["stage"],
                                 age_years=sc["age"], pregnant=sc["preg"],
                                 bleeding_context=sc["bleed"])
            ok = a.overall == expect
            n_all += 1
            n_ok += ok
            results.append({"variant": v.id, "stage": sc["stage"], "input": text,
                            "expect": expect, "got": a.overall, "ok": ok,
                            "notes": [n for ag in a.agents for n in ag.notes][:3]})
            print(f"[{'OK' if ok else 'FAIL'}] {v.id} | {text[:55]:55s} -> {a.overall} (expect {expect})")
    out = {"version": "1.0", "passed": n_ok, "total": n_all,
           "judge_dependency": "none — standalone advisory layer (FASE 5 stops here)",
           "results": results}
    Path(ROOT, "data", "reports", "fase5_treatment_demo.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"demo: {n_ok}/{n_all}")
    return 0 if n_ok == n_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
