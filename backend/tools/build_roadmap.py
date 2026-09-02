"""STEP 4 — Specialty roadmap, presentation families, priority queue, review flags.

Produces the planning outputs (04_SKDI_CATALOG_AND_SPECIALTY_ROADMAP §9): a
human-readable specialty report, a presentation-family→entry mapping, a
generation-priority queue (priority ≠ clinical importance), a nomenclature
review report, and a list of ambiguous entries needing human review.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Qora learning domains (STEP 4 §3) ← SKD 2026 system buckets.
DOMAINS = [
    ("neurology", ["sistem_saraf"]),
    ("psychiatry", ["psikiatri"]),
    ("ophthalmology", ["sistem_indera_mata"]),
    ("ent_head_neck", ["sistem_indera_telinga", "sistem_indera_hidung", "kepala_dan_leher"]),
    ("respiratory", ["sistem_respirasi"]),
    ("cardiology_vascular", ["sistem_kardiovaskuler"]),
    ("gastro_hepato_digestive", ["sistem_gi_hepatobilier_pankreas"]),
    ("nephrology_urology", ["sistem_ginjal_saluran_kemih"]),
    ("obgyn_reproductive", ["sistem_reproduksi"]),
    ("endocrinology_metabolic_nutrition", ["sistem_endokrin_metabolik_nutrisi"]),
    ("hemato_immuno_infectious", ["sistem_hemato_imunologi"]),
    ("musculoskeletal_ortho_rheum", ["sistem_muskuloskeletal"]),
    ("derm_venereology", ["sistem_kulit_integumen"]),
    ("forensic_medicolegal", ["forensik_medikolegal"]),
]
# Pediatrics + Emergency are population/context cross-tags (not exclusive taxonomies).

# High-value presentation families (STEP 4 §8) — keyword matchers over entries.
PRESENTATIONS = [
    ("fever", ["demam", "fever", "hiperpireksia"]),
    ("fever_in_child", ["demam", "febrile", "anak", "infant", "bayi"]),
    ("chest_pain", ["nyeri dada", "chest pain", "angina", "iskemik", "infark", "koroner"]),
    ("dyspnea", ["sesak", "dyspnea", "dispnea", "nafas", "respirasi", "wheezing", "asma"]),
    ("cough", ["batuk", "cough", "bronkitis", "pneumonia"]),
    ("headache", ["nyeri kepala", "headache", "migren", "tension", "cluster"]),
    ("seizure", ["kejang", "seizure", "epilepsi", "status epileptikus"]),
    ("weakness_neurologic_deficit", ["lemah", "paralisis", "hemiplegia", "parese", "stroke", "guillain", "miastenia", "myasthenia"]),
    ("altered_consciousness", ["penurunan kesadaran", "koma", "delirium", "syncope", "sinkop", "stupor", "kesadaran"]),
    ("abdominal_pain", ["nyeri perut", "abdominal", "appendisitis", "kolik", "ulkus", "gastritis", "pankreatitis", "cholecystitis"]),
    ("diarrhea", ["diare", "diarrhea", "disentri", "kolera"]),
    ("vomiting", ["muntah", "vomiting", "emesis", "mual"]),
    ("jaundice", ["ikterus", "jaundice", "hepatitis"]),
    ("urinary_symptoms", ["berkemih", "disuria", "poliuria", "kencing", "hematuria", "inkontinensia", "pielonefritis", "uretritis", "sistitis"]),
    ("edema", ["edema", "bengkak", "anasarka", "ascites", "asites"]),
    ("vaginal_discharge", ["keputihan", "vaginal", "vulvovaginitis", "kandidiasis genital", "sifilis"]),
    ("vaginal_bleeding", ["perdarahan", "pendarahan", "abortus", "metroragia", "polimenorea", "menoragia"]),
    ("pregnancy_related_hypertension", ["kehamilan", "preeklamsia", "eklamsia", "hipertensi dalam kehamilan", "antenatal"]),
    ("rash", ["ruam", "rash", "urtikaria", "eritema", "pitiriasis", "eksantem", "varisela", "campak", "morbili", "skabies", "dermatitis"]),
    ("painful_red_eye", ["mata merah", "konjungtivitis", "keratitis", "episkleritis", "uveitis", "hordeolum"]),
    ("ear_pain", ["nyeri telinga", "otitis", "otalgia", "telinga"]),
    ("sore_throat", ["nyeri tenggorok", "faringitis", "tonsilitis", "sakit tenggorokan"]),
    ("joint_pain", ["nyeri sendi", "artritis", "artralgia", "gout", "rheumatoid", "rematoid", "lupus"]),
]


def _matches(name: str, kws: list[str]) -> bool:
    n = name.lower()
    return any(k in n for k in kws)


def build(entries: list[dict]) -> dict:
    sys_to_entries = {}
    for e in entries:
        sys_to_entries.setdefault(e["system"], []).append(e)

    # 1) specialty report
    specialty_report = []
    for domain, systems in DOMAINS:
        es = [e for e in entries if e["system"] in systems]
        tuntas = sum(1 for e in es if e["category"] == "tuntas")
        initial = sum(1 for e in es if e["category"] == "initial_management_and_referral")
        specialty_report.append({
            "domain": domain, "systems": systems,
            "entry_count": len(es), "tuntas": tuntas,
            "initial_management_and_referral": initial,
        })

    # 2) presentation-family mapping → entry ids (cross-domain reuse of variants)
    presentation_map = []
    seen_ids = set()
    for pname, kws in PRESENTATIONS:
        hits = [e["id"] for e in entries if _matches(e["skd2026_name"], kws)]
        presentation_map.append({"presentation": pname, "entry_ids": hits})
        seen_ids.update(hits)

    # 3) priority queue (generation priority — NOT clinical importance)
    #    bias: high-stakes 'initial_management_and_referral' first, then common
    #    'tuntas' core; scored transparently.
    W = {"initial_management_and_referral": 1.0, "tuntas": 0.6}
    queue = []
    for e in entries:
        # score = category weight + presentation-relevance (+0.2 if it feeds a
        # high-value presentation family)
        in_pres = 1 if e["id"] in seen_ids else 0
        base = W.get(e["category"], 0.5)
        score = round(base + 0.2 * in_pres, 3)
        queue.append({"id": e["id"], "skd2026_name": e["skd2026_name"],
                      "system": e["system"], "category": e["category"],
                      "priority_score": score,
                      "in_presentation_family": bool(in_pres)})
    queue.sort(key=lambda x: -x["priority_score"])

    # 4) nomenclature-review flags (draft heuristic — human review required)
    nomenclature = []
    for e in entries:
        flags = []
        if re.search(r"(?i)\b(infirm|retard|mongol|feeb|dwarf unknown)\b", e["skd2026_name"]):
            flags.append("potentially outdated terminology")
        nomenclature.append({"id": e["id"], "skd2026_name": e["skd2026_name"],
                             "flags": flags, "reviewed": False})

    # 5) ambiguous entries (source-inherent duplicate names within same system+cat)
    dup = {}
    for e in entries:
        key = (e["system"], e["category"], e["current_display_name"].strip().lower())
        dup.setdefault(key, []).append(e["id"])
    ambiguous = [ids for ids in dup.values() if len(ids) > 1]

    return {"specialty_report": specialty_report,
            "presentation_families": presentation_map,
            "priority_queue": queue,
            "nomenclature_review": nomenclature,
            "ambiguous_entries": ambiguous}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="content/v3/catalog/skd2026_master_catalog.json")
    ap.add_argument("--out", default="content/v3/catalog/roadmap.json")
    a = ap.parse_args()
    entries = json.loads(Path(a.src).read_text(encoding="utf-8"))
    plan = build(entries)
    op = Path(a.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Roadmap {len(entries)} entries → {a.out}")
    print("Specialties:", len(plan["specialty_report"]),
          "| Presentations:", len(plan["presentation_families"]),
          "| Ambiguous:", len(plan["ambiguous_entries"]))
    print("Top-5 priority:", [(q["skd2026_name"], q["priority_score"]) for q in plan["priority_queue"][:5]])