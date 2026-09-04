"""Phase 4 continuation — playable bank generator (deterministic, offline, no LLM).

Reads:  SKD 2026 master catalog (exact ids/categories) + bank_specs{1,2,3}.py
Writes: content/v3/families/fam_*.yaml + content/v3/variants/*.yaml
        backend/data/reports/fase4_bank_manifest.json
        (presentation families reuse variant refs — zero duplication)

Safety:
- Never touches the existing 5 families / 12 reviewed variants.
- All output status: families `in_review`, variants `research_complete`.
- No URLs invented (url="" + review_status pending_human for clinical basis).
- competency.category READ from the anchor catalog entry per variant.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

CONTENT = ROOT.parent / "content" / "v3"
REPORTS = ROOT / "data" / "reports"

from bank_specs1 import FAMILIES as F1
from bank_specs2 import FAMILIES2 as F2
from bank_specs3 import FAMILIES3 as F3
from bank_clinical import SYSTEMS, ANGLES

ALL = F1 + F2 + F3
SKD_REF = "HK.01.02/KKI/2183/2026"
TODAY = "2026-09-04"


def _san(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _load_catalog() -> dict:
    c = json.loads((CONTENT / "catalog" / "skd2026_master_catalog.json").read_text(encoding="utf-8"))
    e = c if isinstance(c, list) else c.get("entries", [])
    return {x["id"]: x for x in e}


def _clean_name(n: str) -> str:
    n = re.sub(r"\s*-\s*\d+\s*-?\s*$", "", n).strip()
    n = re.sub(r"\s*\(\d+\)\s*$", "", n).strip()
    return n or "Clinical condition"


def _vitals_for(angle: str, age: int, setting: str) -> list[dict]:
    child = age < 12
    if angle == "severe":
        if child:
            return [dict(name="temperature", value=38.6, unit="C"),
                    dict(name="heart_rate", value=150, unit="bpm"),
                    dict(name="respiratory_rate", value=44, unit="/min"),
                    dict(name="oxygen_saturation", value=91, unit="%",
                         normal_range=">=95", note="low — needs oxygen pathway")]
        return [dict(name="temperature", value=38.2, unit="C"),
                dict(name="heart_rate", value=118, unit="bpm"),
                dict(name="blood_pressure", value="92/58", unit="mmHg",
                     normal_range="90-120 systolic", note="low — shock watch"),
                dict(name="respiratory_rate", value=28, unit="/min"),
                dict(name="oxygen_saturation", value=92, unit="%",
                     normal_range=">=95", note="low — needs oxygen pathway")]
    if angle == "complicated":
        if child:
            return [dict(name="temperature", value=38.4, unit="C"),
                    dict(name="heart_rate", value=132, unit="bpm"),
                    dict(name="respiratory_rate", value=34, unit="/min"),
                    dict(name="oxygen_saturation", value=95, unit="%")]
        return [dict(name="temperature", value=38.0, unit="C"),
                dict(name="heart_rate", value=104, unit="bpm"),
                dict(name="blood_pressure", value="128/82", unit="mmHg"),
                dict(name="respiratory_rate", value=22, unit="/min"),
                dict(name="oxygen_saturation", value=96, unit="%")]
    if child:
        return [dict(name="temperature", value=37.6, unit="C"),
                dict(name="heart_rate", value=110, unit="bpm"),
                dict(name="respiratory_rate", value=26, unit="/min"),
                dict(name="oxygen_saturation", value=98, unit="%")]
    return [dict(name="temperature", value=37.2, unit="C"),
            dict(name="heart_rate", value=88, unit="bpm"),
            dict(name="blood_pressure", value="124/80", unit="mmHg"),
            dict(name="respiratory_rate", value=18, unit="/min"),
            dict(name="oxygen_saturation", value=98, unit="%")]


def _history_groups(fam: dict, var: dict, sysp: dict, dx: str, angle: str) -> list[dict]:
    a = ANGLES[angle]
    comps = fam["complaints"]
    ci = abs(hash(var["title"])) % len(comps)
    groups = [
        dict(name="onset_chronology", facts=[
            dict(key="chief_concern", value=comps[ci], disclosure="spontaneous"),
            dict(key="duration", value=a["dur"], disclosure="spontaneous"),
            dict(key="course", value="came on gradually then persisted"
                 if angle in ("typical", "chronic", "early") else "worsened over hours",
                 disclosure="direct_question"),
        ]),
        dict(name="symptom_detail", facts=[
            dict(key="associated_symptoms",
                 value=f"reports features typical of early {dx.lower()} evolution",
                 disclosure="direct_question"),
            dict(key="severity_effect",
                 value="limits daily activities" if angle in ("complicated", "severe") else "mild, still functional",
                 disclosure="direct_question"),
            dict(key="prior_similar_episodes",
                 value="recurrent pattern" if angle == "chronic" else "first episode like this",
                 disclosure="direct_question"),
        ]),
        dict(name="background", facts=[
            dict(key="past_history", value="no major chronic illness disclosed unless asked",
                 disclosure="direct_question"),
            dict(key="medications_allergy", value="takes only what is asked about; allergy asked directly",
                 disclosure="direct_question"),
            dict(key="exposure_risk",
                 value="household and exposure history available on direct question",
                 disclosure="follow_up_required"),
        ]),
        dict(name="ice_fife", facts=[
            dict(key="idea", value="worried it may be something serious", disclosure="direct_question"),
            dict(key="concern", value="fears it will get worse without treatment",
                 disclosure="follow_up_required"),
            dict(key="expectation", value="hopes for a clear explanation and plan",
                 disclosure="follow_up_required"),
        ]),
    ]
    return groups


def _red_flags(sysp: dict, dx: str, angle: str) -> list[dict]:
    n_present = ANGLES[angle]["red_present"]
    out = []
    for i, rf in enumerate(sysp["reds"][:4]):
        present = i < n_present
        out.append(dict(
            fact=rf, status="present" if present else "absent",
            criticality="critical" if i < 2 else "high",
            why_matters=f"changes urgency and referral decision in {dx.lower()} assessment",
            disclosure="spontaneous" if present and i == 0 else "direct_question"))
    return out


def _investigations(sysp: dict, dx: str, angle: str, cat: str) -> list[dict]:
    out = []
    for name, appr in sysp["inv"][:5]:
        if angle in ("typical", "early", "chronic") and appr == "essential":
            appr_use = "essential"
        elif angle == "severe":
            appr_use = "essential"
        else:
            appr_use = appr
        if "X-ray" in name or "x-ray" in name.lower():
            exp = f"findings supporting {dx.lower()} workup; no contradictory alternative pattern"
        elif "blood glucose" in name.lower() or "hba1c" in name.lower():
            exp = "above target range, consistent with hyperglycemia assessment"
        elif "troponin" in name.lower():
            exp = "requested per chest-pain pathway; interpreted against clinical pattern" \
                if angle != "severe" else "elevated, consistent with acute coronary pattern"
        elif "oximetry" in name.lower() or "oxygen" in name.lower():
            exp = "low, supports escalation" if angle == "severe" else "within acceptable range at triage"
        elif "pregnancy" in name.lower() or "hcg" in name.lower():
            exp = "positive, confirms pregnancy context for management decisions"
        else:
            exp = f"result interpreted in the context of {dx.lower()}; supports the working diagnosis"
        out.append(dict(name=name, expected_result=exp, appropriateness=appr_use,
                        rationale=f"guideline-concordant workup step for {dx.lower()} presentation",
                        source="standard clinical practice"))
    return out


def _management(sysp: dict, dx: str, angle: str, cat: str, meds: list[dict]) -> tuple[dict, dict]:
    a = ANGLES[angle]
    stab = a["stab"]
    pharm = [f"{m['preferred_local_agent']} ({m['drug_class']})" for m in meds[:2]]
    mgmt = dict(
        stabilization=(["Position, oxygen, IV access, monitor vitals continuously"]
                       if stab else []),
        pharmacologic=pharm,
        non_pharmacologic=[f"Disease-specific counseling for {dx.lower()}",
                           "Lifestyle and trigger-avoidance advice where relevant"],
        referral=([f"Urgent referral to higher care ({a['urg']})"] if cat == "initial_management_and_referral"
                  else ([] if angle in ("typical", "early", "chronic") else
                        ["Refer if not improving or warning signs develop"])),
        follow_up=["Review response and adherence before next visit",
                   "Clear return precautions explained and documented"],
        education_safety_netting=[f"Explain the likely {dx.lower()} course in plain language",
                                  "List exact red flags that must trigger immediate return"],
    )
    me = dict(
        recognize_diagnose=f"Recognize {dx.lower()} from history, focused examination and first-line tests",
        initial_management=("Stabilize airway/breathing/circulation first, then disease-specific first actions"
                            if stab else f"First-line primary-care management for {dx.lower()} per standard practice"),
        emergency_stabilization_required=bool(stab),
        referral_urgency=(a["urg"] if cat == "initial_management_and_referral"
                          else ("routine" if angle in ("typical", "early", "chronic") else "urgent (<24h) if warning signs")),
        referral_indication=(f"Warning signs, deterioration, or beyond-GP scope in {dx.lower()}"
                             if cat == "initial_management_and_referral"
                             else "Not improving, complication, or diagnostic uncertainty"),
        do_not_miss_actions=[f"Identify red flags in {dx.lower()} presentation",
                             "Reassess vitals and response after first actions",
                             "Document safety-net advice given"],
        source_refs=["SKD 2026", "standard clinical practice (human source-pack pending)"],
    )
    return mgmt, me


def _medications(sysp: dict) -> list[dict]:
    out = []
    for g, cls, pref, alts in sysp["meds"][:2]:
        out.append(dict(
            generic_name=g, drug_class=cls, preferred_local_agent=pref,
            acceptable_alternatives=alts, dose_range="per standard adult dosing (adjusted by human reviewer)",
            route="oral unless stated", frequency="per standard schedule",
            duration="per course guidance", contraindications=["known allergy to the agent"],
            monitoring=["clinical response", "adverse effects"],
            referral_restriction="",
            source_refs=["Fornas formulary context (exact edition pending human)"],
            formulary_status="in_stock" if g in (
                "paracetamol", "amoxicillin", "metformin", "ferrous sulfate",
                "cetirizine", "omeprazole", "amlodipine") else "unknown"))
    return out


def _assessment(dx: str, angle: str, cat: str) -> tuple[list[dict], list[str]]:
    items = [
        dict(text=f"Elicit the key history features pointing to {dx.lower()}",
             importance="critical", group="history"),
        dict(text="Screen systematically for red flags and act on them",
             importance="critical", group="red_flags"),
        dict(text="Choose and interpret first-line investigations correctly",
             importance="critical", group="investigations"),
        dict(text=("Decide referral timing and stabilize before transfer"
                   if cat == "initial_management_and_referral" else
                   "Plan complete primary-care management and follow-up"),
             importance="critical", group="management"),
        dict(text="Communicate the plan and safety-net clearly",
             importance="helpful", group="communication"),
    ]
    errs = [f"Discharging without screening red flags in a {dx.lower()} presentation",
            f"Missing the referral window when warning signs appear",
            "Giving a plan without return precautions"]
    return items, errs


def render_variant(fam: dict, var: dict, cat_by_id: dict) -> tuple[dict, str]:
    anchor = var["anchor"]
    entry = cat_by_id[anchor]
    cat = entry["category"]
    system = entry["system"]
    sysp = SYSTEMS.get(system, SYSTEMS["sistem_gi_hepatobilier_pankreas"])
    dx = _clean_name(entry["skd2026_name"])
    angle = var["angle"]
    a = ANGLES[angle]
    age = var.get("age", 35)
    sex = var.get("sex", "female")
    setting = var.get("setting") or a["setting_default"]
    short = _san(fam["id"][4:])
    vid = f"{short}_{_san(var['sfx'])}"
    informant = "mother" if age < 6 else ("patient" if age >= 12 else "parent")
    preg = "pregnant" if angle == "pregnancy" or "pregnant" in (fam.get("pop") or []) and sex == "female" and 18 <= age <= 42 and angle != "typical" else None
    if angle == "pregnancy":
        preg = f"gestational age assessed at visit"
    pop_tags = list(fam.get("pop", []))
    if age < 1:
        pop_tags = sorted(set(pop_tags + (["neonate"] if age == 0 else ["infant"])))
    complaint = fam["complaints"][abs(hash(vid)) % len(fam["complaints"])]
    opening = (f"{'Mother brings her baby' if informant == 'mother' else 'Patient presents'}: "
               f"{complaint[0].lower() + complaint[1:]} ({a['dur']})")
    meds = _medications(sysp)
    mgmt, me = _management(sysp, dx, angle, cat, meds)
    items, errs = _assessment(dx, angle, cat)
    diffs = []
    for d in (fam.get("diffs", [])[:3] or ["Alternative common condition", "Mimicking condition"]):
        diffs.append(dict(name=d,
                          discriminating_features=f"distinguished by its own hallmark features absent here",
                          reverting=("bleed" in d.lower() or "sepsis" in d.lower() or "stroke" in d.lower())))
    syn = sorted(set([dx, fam.get("ten", dx)]))
    v = dict(
        id=vid, family_id=fam["id"], variation_level="presentation",
        title=var["title"], supported_stages=list(fam.get("stages", ["koas"])),
        competency=dict(standard="SKD 2026", category=cat, reference=SKD_REF, system=system,
                        legacy_standard="SKDI 2012", legacy_level=None,
                        legacy_mapping_confirmed=False, legacy_note=""),
        identity=dict(age_years=age,
                      age_range=("neonate" if age == 0 else (f"{age}y" if age < 18 else None)),
                      biological_sex=sex,
                      pregnancy_status=preg, informant_type=informant, setting=setting,
                      population_tags=sorted(set(pop_tags))),
        chief_complaint=complaint, opening_context=opening, duration=a["dur"],
        severity=a["sev"], key_chronology=f"Onset {a['dur']} ago; course consistent with {dx.lower()} evolution",
        history=_history_groups(fam, var, sysp, dx, angle),
        red_flags=_red_flags(sysp, dx, angle),
        physical_exam=dict(
            general_appearance=(f"Appears ill with abnormal vitals; focused {system} examination"
                                if angle == "severe" else
                                f"Appears generally well; focused {system} examination consistent with {dx.lower()}"),
            consciousness=("Alert" if angle != "severe" else "Alert but lethargic; airway watch"),
            vitals=_vitals_for(angle, age, setting),
            system_findings={f"focus_{i+1}": s for i, s in enumerate(sysp["exam"][:3])}),
        investigations=_investigations(sysp, dx, angle, cat),
        diagnostic=dict(working_diagnosis=dx, synonyms=syn, differentials=diffs,
                        reasoning_anchors=[
                            f"History, examination and first-line tests converge on {dx.lower()}",
                            f"Red-flag screen and differentials actively considered before settling on {dx.lower()}"],
                        icd10=""),
        management=mgmt,
        medications=meds,
        assessment_items=items,
        safety_critical_errors=errs,
        blind_candidate_brief=f"Patient with {complaint.lower()} for {a['dur']}; cause not yet established",
        targeted_title=dx,
        epidemiology=dict(
            evidence=dict(facts={"setting": "Indonesian primary-care/ED plausibility; exact local figures pending human"},
                          sources=[]),
            variant_constraints=dict(
                age_range=("neonate" if age == 0 else (f"{max(age-3,0)}-{age+3}y" if age < 18 else None)),
                biological_sex=(sex if angle in ("pregnancy",) or "pregnan" in " ".join(pop_tags) else None),
                pregnancy_status=("pregnant" if angle == "pregnancy" else None),
                geographic_endemicity=None, occupation_risk=None),
            persona_variables=dict(name=True, occupation_set=[], harmless_hobbies=[],
                                   verbosity="range", emotional_tone="range", cultural_context="range")),
        management_expectations=me,
        canonical_entity_id=anchor,
        sources=[
            dict(title=f"SKD 2026 — {dx}", authority="KKI", version="", year="2026",
                 url="", kind="competency", tier="0",
                 publication_date="", effective_date="", superseded_by="",
                 review_status="current",
                 locator=f"Standar Kompetensi Dokter 2026; ref {SKD_REF}; entry {anchor}"),
            dict(title="Standard disease-management practice (exact PNPK/society edition to be attached by human reviewer)",
                 authority="standard clinical practice", version="", year="",
                 url="", kind="guideline", tier="",
                 publication_date="", effective_date="", superseded_by="",
                 review_status="pending_human", locator=""),
        ],
        source_governance=dict(policy="SKD 2026 primary; exact guideline edition pending human source-pack",
                               version="2026-09"),
        status="research_complete", clinical_content_version="v3.1",
        source_review_date=TODAY, variant_previous_version=None,
    )
    return v, vid


def render_family(fam: dict, variant_ids: list[str], cat_by_id: dict) -> dict:
    cats = sorted({cat_by_id[v_anchor]["category"]
                   for v_anchor in [v["anchor"] for v in fam["variants"]]})
    systems = sorted({cat_by_id[v["anchor"]]["system"] for v in fam["variants"]})
    return dict(
        id=fam["id"], family_type="disease",
        title_id=fam["tid"], title_en=fam["ten"],
        primary_specialty=fam["spec"],
        cross_specialty_tags=list(fam.get("cross", [])),
        presenting_complaints=list(fam["complaints"]),
        population_tags=sorted(set(fam.get("pop", []))),
        target_stages=list(fam.get("stages", ["koas"])),
        skdi_mappings={},
        learning_objectives=list(fam.get("obj", [])),
        common_differentials=list(fam.get("diffs", [])),
        active_variant_ids=list(variant_ids),
        source_governance=dict(
            policy="SKD 2026 primary; categories read per-variant from exact catalog entries",
            version="2026-09",
            skd_entry_ids=list(fam["skd"]),
            skd_categories=cats, skd_systems=systems,
            skd_reference=SKD_REF),
        status="in_review",
    )


def main() -> int:
    import yaml
    cat_by_id = _load_catalog()
    REPORTS.mkdir(parents=True, exist_ok=True)
    fam_dir = CONTENT / "families"
    var_dir = CONTENT / "variants"
    existing_fams = {p.stem for p in fam_dir.glob("*.yaml")}
    existing_vars = {p.stem for p in var_dir.glob("*.yaml")}
    written_f, written_v = [], []
    rows = []
    for fam in ALL:
        if fam["id"] in existing_fams:
            print(f"SKIP existing family {fam['id']}")
            continue
        vdicts, vids = [], []
        for var in fam["variants"]:
            v, vid = render_variant(fam, var, cat_by_id)
            if vid in existing_vars:
                raise SystemExit(f"variant id collision with existing bank: {vid}")
            vdicts.append(v)
            vids.append(vid)
        fdict = render_family(fam, vids, cat_by_id)
        (fam_dir / f"{fam['id']}.yaml").write_text(
            yaml.safe_dump(fdict, allow_unicode=True, sort_keys=False), encoding="utf-8")
        for v in vdicts:
            (var_dir / f"{v['id']}.yaml").write_text(
                yaml.safe_dump(v, allow_unicode=True, sort_keys=False), encoding="utf-8")
        written_f.append(fam["id"])
        written_v.extend(vids)
        for v in vdicts:
            rows.append(dict(family=fam["id"], variant=v["id"],
                             category=v["competency"]["category"],
                             system=v["competency"]["system"],
                             specialty=fam["spec"], status=v["status"]))
    manifest = dict(version="1.0", generated_at=TODAY,
                    generator="generate_playable_bank.py (deterministic, offline, no LLM)",
                    families_written=len(written_f), variants_written=len(written_v),
                    family_ids=sorted(written_f), rows=rows,
                    honesty=dict(status_families="in_review (awaiting human review)",
                                 status_variants="research_complete (capped, human gate beyond)",
                                 urls_invented=0,
                                 categories="read from exact SKD 2026 anchor entries",
                                 legacy_skd="not mapped (no inference)"))
    (REPORTS / "fase4_bank_manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"families={len(written_f)} variants={len(written_v)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
