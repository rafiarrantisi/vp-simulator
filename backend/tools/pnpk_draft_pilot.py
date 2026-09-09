"""Generate Phase-3 pilot DRAFT authoring JSON (brief Phase 3).

All claims use REAL verified PDF locators from the downloaded PNPK artifacts.
Every claim/mapping/template is review_status=draft with NO approval record:
the compiler MUST reject publish; draft-check reports approval gaps only.
No clinical approval is claimed. Reviewer: clinician (pending).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "content" / "evidence"


def _norm(text: str) -> str:
    return " ".join(text.split())


def _span(sv: str, heading: str, p0: int, p1: int, locator: str, excerpt: str) -> dict:
    return {
        "source_version_id": sv,
        "section_path": [],
        "heading": heading,
        "pdf_page_start": p0,
        "pdf_page_end": p1,
        "printed_page_label": str(p0),
        "locator": locator + " (printed label = PDF page per observed -N- markers; reviewer to confirm)",
        "excerpt_hash": hashlib.sha256(_norm(excerpt).encode()).hexdigest(),
        "excerpt": _norm(excerpt),
    }


UTI_SV = ("PNPK-UTI-2025@sha256:"
          "a7b5bad4c160027425bc22ca02319ff4628e984fc6d471d41af85bb1d040a2ba")
DENGUE_SV = ("PNPK-DENGUE-ADULT-2020@sha256:"
             "6ad741ee6a1b9c095bec7271004a8e831033ea3161c3d9c5078343324aef698b")


def _claim(cid, statement, category, spans, applicability, conds):
    return {
        "claim_id": cid, "claim_revision": 1, "statement": statement,
        "category": category, "support_kind": "direct_guideline",
        "applicability": dict({"condition_codes": conds}, **applicability),
        "evidence_spans": spans, "review_status": "draft",
        "reviewer": "", "reviewed_at": "", "approval_record_id": "",
    }


def build() -> None:
    claims, mappings, templates = [], [], []

    # ---------------- UTI adult ----------------
    claims.append(_claim(
        "UTI-DX-001",
        "Pada wanita tidak hamil, pola disuria disertai frekuensi berkemih "
        "yang meningkat merupakan pola gejala sistitis yang paling spesifik.",
        "diagnosis",
        [_span(UTI_SV, "Sistitis", 87, 87, "paragraf pola gejala spesifik",
               "pengobatan empiris dapat dipertimbangkan jika terdapat disuria "
               "dan frekuensi kencing meningkat dibandingkan sebelumnya, yang "
               "merupakan pola gejala paling spesifik pada wanita tidak hamil")],
        {"pregnancy": "no", "sex": "female", "min_age_years": 18}, ["uti", "cystitis"]))
    claims.append(_claim(
        "UTI-INV-001",
        "Pemeriksaan mikroskopik urin menunjang urinalisis; piuria (leukosit "
        ">5-10/LPB) mengarah pada infeksi.",
        "investigation",
        [_span(UTI_SV, "Pemeriksaan mikroskopik urine", 26, 26, "paragraf piuria",
               "Peningkatan leukosit di urin (piuria), mengarah pada adanya "
               "infeksi bila leukosit >5-10/lapang pandang besar (LPB)")],
        {"pregnancy": "any"}, ["uti"]))
    claims.append(_claim(
        "UTI-INV-002",
        "Kultur urin mengonfirmasi diagnosis dan memandu terapi ISK.",
        "investigation",
        [_span(UTI_SV, "Biakan Urin", 27, 27, "paragraf indikasi kultur",
               "Untuk diagnosis definitif dan kepentingan terapi ISK, dibutuhkan "
               "konfirmasi mikrobiologi dengan melakukan pemeriksaan kultur urin")],
        {"pregnancy": "any"}, ["uti"]))
    claims.append(_claim(
        "UTI-INV-003",
        "Bila dipstick tidak menunjukkan LE, nitrit, atau protein dan "
        "mikroskopis negatif, tidak diperlukan pemeriksaan lanjutan.",
        "investigation",
        [_span(UTI_SV, "Urinalisis dipstick", 107, 107, "paragraf rule-out",
               "Apabila melakukan pemeriksaan urinalisis dipstik dan didapatkan "
               "tidak ada LE, nitrit, protein, atau tidak ditemukan pemeriksaan "
               "mikroskopis maka tidak diperlukan pemeriksaan lanjutan")],
        {"pregnancy": "any"}, ["uti"]))
    claims.append(_claim(
        "UTI-TX-001",
        "Golongan fluorokuinolon tidak sesuai sebagai terapi empiris ISK "
        "komplikata karena resistensi, terutama pasca-siprofloksasin 6 bulan.",
        "management",
        [_span(UTI_SV, "Terapi empiris", 69, 69, "paragraf fluorokuinolon",
               "Golongan fluroquinolones tidak sesuai digunakan sebagai terapi "
               "empiris ISK komplikata akibat resistensi yang terjadi, terutama "
               "pada pasien yang telah menggunakan ciprofloxacin selama enam "
               "bulan terakhir")],
        {"pregnancy": "any", "severity": "complicated"}, ["uti"]))
    claims.append(_claim(
        "UTI-TX-002",
        "Terapi disesuaikan setelah 72 jam berdasarkan kultur dan sensitivitas; "
        "ganti bila intermediet/resisten terhadap empiris awal.",
        "management",
        [_span(UTI_SV, "Penyesuaian terapi", 74, 74, "paragraf 72 jam",
               "setelah pemberian antibiotika selama 72 jam berdasarkan hasil "
               "sensitivitas dari kultur urine; dan bila uropatogen penyebab ISK "
               "menunjukkan sensitivitas intermediet atau resisten terhadap "
               "antibiotik empirik awal")],
        {"pregnancy": "any"}, ["uti"]))
    claims.append(_claim(
        "UTI-RF-001",
        "Pielonefritis membutuhkan antibiotik empiris berpenetrasi ginjal dan "
        "disesuaikan dengan kultur-sensitivitas urin.",
        "red_flag",
        [_span(UTI_SV, "Penatalaksanaan pielonefritis", 95, 95, "paragraf penetrasi",
               "Pada pielonefritis terapi antibiotik empiris harus memiliki "
               "penetrasi pada ginjal yang memadai dan ditargetkan terhadap "
               "patogen yang paling mungkin terjadi. Terapi antibiotik harus "
               "disesuaikan sesuai kebutuhan berdasarkan kultur dan sensitivitas "
               "urin")],
        {"pregnancy": "any"}, ["uti", "pyelonephritis"]))
    claims.append(_claim(
        "UTI-PREG-001",
        "Sistitis pada ibu hamil diterapi antibiotik 5-7 hari.",
        "management",
        [_span(UTI_SV, "Sistitis ibu hamil", 88, 88, "paragraf durasi hamil",
               "Setelah diagnosis sistitis akut ditegakkan, pengobatan dilakukan "
               "pada ibu hamil harus dimulai dengan antibiotik selama 5-7 hari")],
        {"pregnancy": "yes"}, ["uti"]))
    # NOTE: UTI-PREG-001 is intentionally NOT mapped to uti_adult_002
    # (non-pregnant adult female) — demonstrates applicability exclusion.

    # ---------------- Dengue adult ----------------
    claims.append(_claim(
        "DENG-RF-001",
        "Tanda kedaruratan (syok, kejang, penurunan kesadaran, perdarahan, "
        "muntah/asupan oral inadekuat, nyeri perut hebat, letargi, oliguria, "
        "komorbid) mewajibkan rujukan/segera ditangani.",
        "red_flag",
        [_span(DENGUE_SV, "Tanda kedaruratan", 38, 38, "paragraf triase",
               "Bila ada tanda kedaruratan berupa syok, kejang, kesadaran "
               "menurun, perdarahan, muntah dan atau asupan oral inadekuat, "
               "nyeri perut hebat, letargi dan atau gelisah, lemas, akral "
               "pucat, dingin dan basah, oliguria")],
        {"pregnancy": "any", "min_age_years": 18}, ["dengue"]))
    claims.append(_claim(
        "DENG-MG-001",
        "Pasien rawat jalan perlu istirahat cukup dan cairan oral adekuat "
        "berglukosa-elektrolit (bukan air putih biasa): susu, jus buah, "
        "larutan isotonik oral, oralit, air tajin.",
        "management",
        [_span(DENGUE_SV, "Edukasi rawat jalan", 39, 39, "butir cairan oral",
               "Asupan cairan yang adekuat. WHO menganjurkan agar cairan oral "
               "yang diberikan jangan air putih biasa tetapi minuman yang "
               "mengandung glukosa dan elektrolit seperti susu, jus buah, "
               "larutan isotonik oral, oralit, dan air tajin")],
        {"pregnancy": "any", "min_age_years": 18}, ["dengue"]))
    claims.append(_claim(
        "DENG-MG-002",
        "Demam >39 C diberi parasetamol 10 mg/kg/dosis (maks 4 g/hari dewasa), "
        "hindari berlebihan serta hindari aspirin dan NSAID.",
        "management",
        [_span(DENGUE_SV, "Penatalaksanaan demam", 39, 39, "butir parasetamol",
               "Jika suhu tubuh melebihi 39 C, penderita diberikan parasetamol. "
               "Dosis yang dianjurkan adalah 10 mg/kg/dosis. Dosis maksimum "
               "untuk orang dewasa adalah 4 gram/hari. Hindari penggunaan "
               "parasetamol berlebihan dan aspirin dan NSAID")],
        {"pregnancy": "any", "min_age_years": 18}, ["dengue"]))
    claims.append(_claim(
        "DENG-INV-001",
        "Antigen NS1 tinggi sampai hari ke-3 demam dan menurun hari ke-4-7.",
        "investigation",
        [_span(DENGUE_SV, "Deteksi NS1", 28, 28, "paragraf kinetika NS1",
               "tinggi sampai 3 hari setelah demam, dan menurun pada hari 4-7")],
        {"pregnancy": "any", "min_age_years": 18}, ["dengue"]))
    claims.append(_claim(
        "DENG-INV-002",
        "Trombositopenia dan hemokonsentrasi (hematokrit naik) sering pada DBD, "
        "umumnya saat demam mulai turun (fase defervesens).",
        "investigation",
        [_span(DENGUE_SV, "Temuan laboratorium", 14, 14, "paragraf trombosit",
               "Trombositopenia dan meningkatnya hematokrit (hemokonsentrasi), "
               "merupakan temuan yang sering didapat pada DBD dan umumnya "
               "terjadi sewaktu demam mulai turun")],
        {"pregnancy": "any", "min_age_years": 18}, ["dengue"]))

    def _mapping(mid, target, kind, cids, triggers, tpl, variants, prio=1):
        return {
            "mapping_id": mid, "canonical_target_id": target,
            "target_kind": "per_item", "claim_ids": cids,
            "trigger_statuses": triggers, "template_id": tpl,
            "display_priority": prio, "applicable_variant_ids": variants,
            "review_status": "draft", "approval_record_id": "",
        }

    # NOTE: only hx_* routine asks link to live report rows today (verified
    # matrix in Phase 3 report). inv/mg/dx/safety-derived items have no
    # answer-key counterpart; mapping them would silently never fire, so
    # they are recorded as coverage gaps instead.
    T = "T--evidence-001"
    mappings.append(_mapping("M-UTI-HX-001", "hx_1", "per_item",
                             ["UTI-DX-001"], ["hit", "partial"], T, ["uti_adult_002"]))
    mappings.append(_mapping("M-UTI-HX-002", "hx_2", "per_item",
                             ["UTI-DX-001"], ["hit", "partial"], T, ["uti_adult_002"], 2))
    mappings.append(_mapping("M-UTI-HX-004", "hx_4", "per_item",
                             ["UTI-RF-001"], ["hit"], T, ["uti_adult_002"], 2))
    mappings.append(_mapping("M-DENG-HX-001", "hx_1", "per_item",
                             ["DENG-INV-001"], ["hit"], T, ["dengue_001_mild"]))
    mappings.append(_mapping("M-DENG-HX-008", "hx_8", "per_item",
                             ["DENG-RF-001"], ["hit"], T, ["dengue_001_mild"], 2))
    mappings.append(_mapping("M-DENG-HX-009", "hx_9", "per_item",
                             ["DENG-RF-001"], ["hit"], T, ["dengue_001_mild"], 2))
    mappings.append(_mapping("M-DENG-HX-010", "hx_10", "per_item",
                             ["DENG-RF-001"], ["hit"], T, ["dengue_001_mild"], 2))
    templates.append({
        "template_id": T, "template_revision": 1,
        "statuses": ["hit", "partial", "miss"],
        "text": "Item {label} {status_word} pada penilaian ini. {reason} [{ref}]",
        "placeholders": ["label", "status_word", "reason", "ref"],
        "review_status": "draft", "approval_record_id": "",
    })

    packs = [{
        "pack_id": "PNPK-PILOT-DRAFT-001",
        "pack_revision": 1,
        "clinical_content_version": "v3.0",
        "compatible_scoring_versions": ["qora-score-1.0"],
        "content_release_id": "rel-pnpk-pilot-draft-1",
        "families": ["fam_uti", "fam_dengue"],
        "allowed_conditions": ["uti", "cystitis", "pyelonephritis", "dengue"],
        "supported_modes": ["practice"],
        "supported_stages": ["koas"],
        "review_record": {},
    }]

    for name, items in (("claims", claims), ("mappings", mappings),
                        ("templates", templates), ("packs", packs)):
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "pilot_draft_001.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=1,
                       sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(claims)} claims, {len(mappings)} mappings, "
          f"{len(templates)} templates, {len(packs)} packs")


if __name__ == "__main__":
    build()
