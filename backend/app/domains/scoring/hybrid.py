"""FASE 7 — Evidence-locked hybrid clinical judge (EXPERIMENTAL, report-only).

Status: DOES NOT replace any live scoring path. `judge_v2.evaluate_v2` and
`judge_v3.evaluate_v3` remain the only live judges; no router imports this
module (pinned by test). This module is the deterministic core a future
calibrated cutover must use: LLM output may propose evidence, but ALL
arithmetic is server-controlled here.

Architecture (per FASE 7 brief):
  User Performance Record (UPR) — one struct combining transcript, PF actions,
    investigations, diagnosis/DDx, management/pharm/referral/education,
    overtime, mode, learner level.
  Evidence Ledger — every rubric item gets {expected, observed evidence,
    source location, adjudication, score 0-3, reason}. Hard rule:
    no evidence → no full credit; clinically-equivalent wording is accepted.
  Semantic adjudication — ID/EN, synonyms, abbreviations, typos, paraphrases,
    broad-vs-specific, alternate management; constrained by the canonical
    rubric, never substring-containment alone.
  Deterministic arithmetic — item 0-3 × criticality × domain × learner weights,
    overtime, safety caps. LLM never computes totals.
  Safety override — missed shock / unsafe discharge / failure to stabilize /
    dangerous drug / missed urgent referral / major contraindication /
    dangerous procedure caps the overall and the global rating.
  Diagnosis hierarchical (exact+severity > family incomplete > broad partial >
    wrong > dangerous miss). Management split (priority/stabilization/
    definitive/medication/monitoring/education/referral). Pharm detail
    (indication/agent/dose/route/frequency/duration/contra/monitoring),
    stage-aware.
  Global rating Fail/Borderline/Pass/Superior — holistic layer AFTER scores,
    never overrides safety. Explicitly NOT borderline-regression (BRM is a
    cohort/station standard-setting technique; needs station + human data).
  Feedback composer — from the ledger only; never claims un-evidenced acts.
  Versioned output — maps into `contracts.NormalizedScore` + hybrid extension.

Domain basis: eight broad domains are the STARTING point
(Anamnesis, Physical Examination, Investigations/Procedures, Diagnosis & DDx,
Non-Pharmacological Management, Pharmacological Management,
Communication/Education, Professional Behavior). They are mapped from the
existing V2 rubric (anamnesis/osce_full/classic) + V3 learner-profile dims +
contracts CORE_OSCE_DOMAINS — see DOMAIN_MAP below. Indonesian OSCE
references were cross-checked as credible-background only; no old document is
claimed as official-current without human verification (that check is a
human calibration step, not a code claim).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Any

HYBRID_VERSION = "0.1-experimental"
HYBRID_SCHEMA = "hybrid_score/0.1"

# ── eight broad domains (starting point, mapped — not a new official claim) ──
EIGHT_DOMAINS = (
    "anamnesis",
    "physical_exam",
    "investigations",
    "diagnosis_ddx",
    "nonpharm_mgmt",
    "pharm_mgmt",
    "communication_education",
    "professional_behavior",
)

# Existing V2 / V3 / contracts dim -> eight-domain mapping (audit matrix).
DOMAIN_MAP = {
    # V2 anamnesis + osce_full
    "history_coverage": "anamnesis",
    "coverage": "anamnesis",
    "red_flags": "anamnesis",
    "ice_fife": "communication_education",
    "questioning_technique": "anamnesis",
    "communication": "communication_education",
    "clinical_safety": "professional_behavior",
    "physical_exam": "physical_exam",
    "investigations": "investigations",
    "diagnostic_reasoning": "diagnosis_ddx",
    "management": "nonpharm_mgmt",  # split further into nonpharm/pharm below
    # V3 learner-profile dims
    "info_gathering": "anamnesis",
    "focus_efficiency": "anamnesis",
    "reasoning_coherence": "diagnosis_ddx",
    "diagnostic_quality": "diagnosis_ddx",
    "investigation_strategy": "investigations",
    "management_safety": "professional_behavior",
    # contracts core
    "history": "anamnesis",
    "diagnosis": "diagnosis_ddx",
    "safety": "professional_behavior",
}

ITEM_SCALE = (0, 1, 2, 3)  # not done/incorrect, attempted-inadequate, partial, adequate
CRITICALITY_WEIGHT = {"routine": 1.0, "important": 1.5, "critical": 2.0, "safety-critical": 3.0}

# Base domain weights per mode (sum 100). Learner-stage multiplies detail
# demand inside pharm/dx grading, not these top-level weights (kept stable so
# calibration compares like-for-like across stages).
DOMAIN_WEIGHTS = {
    "practice": {  # history-focused
        "anamnesis": 30, "physical_exam": 0, "investigations": 0,
        "diagnosis_ddx": 20, "nonpharm_mgmt": 10, "pharm_mgmt": 10,
        "communication_education": 20, "professional_behavior": 10,
    },
    "osce": {  # full arc
        "anamnesis": 20, "physical_exam": 12, "investigations": 12,
        "diagnosis_ddx": 16, "nonpharm_mgmt": 10, "pharm_mgmt": 10,
        "communication_education": 10, "professional_behavior": 10,
    },
}

SAFETY_GATE_TYPES = frozenset({
    "missed_shock", "unsafe_discharge", "failure_to_stabilize", "dangerous_drug",
    "missed_urgent_referral", "major_contraindication", "dangerous_procedure",
    # compat aliases from the live judges (mapped, not duplicated)
    "missed_critical_red_flag", "unsafe_management", "failed_urgent_referral",
    "missed_emergency_red_flag",
})

GLOBAL_RATINGS_4 = ("Fail", "Borderline", "Pass", "Superior")


# ── text normalisation (shared, deterministic) ─────────────────────────────
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_ID_ABBR = {
    "dbd": "dengue", "tb": "tuberculosis", "tbc": "tuberculosis",
    "htn": "hypertension", "dm": "diabetes", "ckd": "kidney",
    "uti": "urinary tract infection", "isk": "urinary tract infection",
    "pne": "pneumonia", "hf": "heart failure", "copd": "copd",
    "mi": "myocardial infarction", "acs": "acute coronary",
    "nsaid": "nsaid", "oralit": "ors",
}
_ID_WORD = {
    "hipertensi": "hypertension", "tekanan darah tinggi": "hypertension",
    "kencing": "urination", "nyeri": "pain", "demam": "fever",
    "batuk": "cough", "sesak": "dyspnea", "mual": "nausea", "muntah": "vomiting",
    "diare": "diarrhea", "dehidrasi": "dehydration",
    "demam berdarah": "dengue", "tipus": "typhoid",
    "gula": "diabetes", "asam urat": "gout",
}


def _expand_forms(s: str) -> list[str]:
    n = _norm(s)
    forms = [n]
    for ab, ex in _ID_ABBR.items():
        if re.search(rf"\b{re.escape(ab)}\b", n):
            forms.append(n.replace(ab, ex))
    for idw, en in _ID_WORD.items():
        if idw in n:
            forms.append(n.replace(idw, en))
    return list(dict.fromkeys(forms))


def _tokens(s: str) -> set[str]:
    return set(_norm(s).split()) - {""}


def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if not la or not lb:
        return max(la, lb)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _concept_match(observed_forms: list[str], expected: str) -> dict:
    """Robust adjudication for one expected concept vs observed text forms.

    Combines exact/containment + token-overlap + synonym/abbrev expansion +
    typo tolerance. Never substring-alone: containment without token overlap
    on a short expected string is downgraded to partial/attemped.
    Returns {verdict: hit|partial|attempted|miss, reason}.
    """
    exp_n = _norm(expected)
    if not exp_n:
        return {"verdict": "miss", "reason": "empty expected"}
    exp_tok = _tokens(expected)
    best = {"verdict": "miss", "reason": "no overlap", "overlap": 0.0}
    for of in observed_forms:
        if not of:
            continue
        # exact / containment (needs token support for short strings)
        if exp_n == of:
            return {"verdict": "hit", "reason": "exact"}
        overlap = len(exp_tok & _tokens(of)) / max(len(exp_tok), 1)
        if exp_n in of or of in exp_n:
            if overlap >= 0.5 or len(exp_n) >= 12:
                return {"verdict": "hit", "reason": "contained+overlap"}
            best = {"verdict": "partial", "reason": "contained-weak-overlap", "overlap": overlap}
            continue
        if overlap >= 0.67:
            return {"verdict": "hit", "reason": f"token-overlap {overlap:.2f}"}
        if overlap >= 0.34:
            if best["verdict"] == "miss":
                best = {"verdict": "partial", "reason": f"token-overlap {overlap:.2f}", "overlap": overlap}
            continue
        # typo tolerance on single-token concepts
        if len(exp_tok) == 1:
            w = next(iter(exp_tok))
            for t in _tokens(of):
                if _lev(w, t) <= max(1, len(w) // 4) and len(w) >= 4:
                    return {"verdict": "partial", "reason": f"near-miss typo {w}~{t}"}
    # broad-vs-specific: observed is a hypernym of expected (e.g. "pneumonia"
    # for "child pneumonia with danger signs") — handled by caller via hierarchy;
    # here a weak overlap is at most attempted.
    if best["verdict"] == "miss" and best.get("overlap", 0) > 0:
        return {"verdict": "attempted", "reason": "weak signal"}
    return best


_NEG = re.compile(r"\b(no|not|without|tidak|tanpa|bukan|negat\w*|denies|denied)\b")


def _negated(sentence: str) -> bool:
    return bool(_NEG.search(_norm(sentence)))


# ── UPR ────────────────────────────────────────────────────────────────────
@dataclass
class UserPerformanceRecord:
    transcript_user_texts: list[dict] = field(default_factory=list)  # {text, turn}
    pf_areas: list[str] = field(default_factory=list)
    pf_notes: str = ""
    investigations: list[str] = field(default_factory=list)
    diagnosis: str = ""
    differentials: list[str] = field(default_factory=list)
    management_text: str = ""
    medications: list[str] = field(default_factory=list)
    referral: str = ""
    education: str = ""
    overtime: bool = False
    mode: str = "practice"  # practice | osce
    learner_level: str = "koas"  # preclinical | koas

    def to_dict(self) -> dict:
        return asdict(self)


def build_upr(*, transcript: list[dict] | None = None, pf_notes: str | None = None,
              pf_areas: list | None = None, ddx: dict | None = None,
              management: dict | None = None, mode: str | None = None,
              overtime: bool = False, learner_level: str | None = None) -> UserPerformanceRecord:
    """Combine every real evidence source into one record.

    Transcript credit uses USER turns only (what the candidate elicited/said) —
    patient text is context, never evidence of candidate performance.
    """
    user_texts = []
    for i, m in enumerate(transcript or []):
        if (m.get("role") or "") != "user":
            continue
        t = str(m.get("content", m.get("text", "")) or "").strip()
        if t:
            user_texts.append({"text": t, "turn": i})
    mgmt = management if isinstance(management, dict) else {}
    inv: list[str] = []
    for k in ("penunjang", "investigations", "tests"):
        v = mgmt.get(k)
        if isinstance(v, str) and v.strip():
            inv.append(v.strip())
        elif isinstance(v, list):
            inv.extend(str(x) for x in v if str(x).strip())
    dx, ddxs = "", []
    if isinstance(ddx, dict):
        for k in ("dx1", "dx2", "dx3", "working", "diagnosis"):
            v = ddx.get(k)
            if isinstance(v, str) and v.strip() and v.strip().lower() not in ("none", "null", "skip"):
                (ddxs if ddxs and k != "dx1" else ddxs).append(v.strip())
        dx = str(ddx.get("dx1") or ddx.get("working") or ddx.get("diagnosis") or "").strip()
        if dx and dx not in ddxs:
            ddxs = [dx] + ddxs
    elif isinstance(ddx, str):
        dx = ddx.strip()
        ddxs = [dx] if dx else []
    meds: list[str] = []
    for k in ("terapi", "medications", "drugs", "obat"):
        v = mgmt.get(k)
        if isinstance(v, str) and v.strip():
            meds.append(v.strip())
        elif isinstance(v, list):
            meds.extend(str(x) for x in v if str(x).strip())
    return UserPerformanceRecord(
        transcript_user_texts=user_texts,
        pf_areas=[str(a) for a in (pf_areas or []) if str(a).strip()],
        pf_notes=str(pf_notes or ""),
        investigations=inv,
        diagnosis=dx, differentials=ddxs,
        management_text=" ".join(str(mgmt.get(k) or "") for k in ("terapi", "complete", "management")),
        medications=meds,
        referral=str(mgmt.get("referral") or mgmt.get("rujukan") or ""),
        education=str(mgmt.get("edukasi") or mgmt.get("education") or ""),
        overtime=bool(overtime),
        mode=(mode or "practice").lower() if (mode or "").lower() in ("practice", "osce") else "practice",
        learner_level=learner_level or "koas",
    )


# ── rubric items from canonical variant ────────────────────────────────────
@dataclass
class RubricItem:
    key: str
    domain: str  # one of EIGHT_DOMAINS
    expected: str
    criticality: str = "routine"  # routine|important|critical|safety-critical
    evidence_kind: str = "transcript"  # transcript|pf|investigations|diagnosis|management|referral|education
    synonyms: list[str] = field(default_factory=list)


def rubric_from_variant(v) -> list[RubricItem]:
    """Derive rubric items from the SAME canonical variant every surface reads."""
    items: list[RubricItem] = []
    try:
        for g in (getattr(v, "history", None) or []):
            for f in (getattr(g, "facts", None) or []):
                key = getattr(f, "key", "") or ""
                val = getattr(f, "value", "")
                items.append(RubricItem(
                    key=f"hx:{key}", domain="anamnesis",
                    expected=f"{key.replace('_', ' ')} {val}".strip(),
                    criticality="important",
                    evidence_kind="transcript",
                    synonyms=[key.replace("_", " ")]))
        for r in (getattr(v, "red_flags", None) or []):
            fact = getattr(r, "fact", "") or str(r)
            crit = str(getattr(getattr(r, "criticality", ""), "value", getattr(r, "criticality", "")) or "")
            items.append(RubricItem(
                key=f"rf:{fact[:40]}", domain="anamnesis",
                expected=fact,
                criticality="safety-critical" if crit == "critical" else "critical",
                evidence_kind="transcript"))
        pe = getattr(v, "physical_exam", None)
        for area in ((getattr(pe, "system_findings", None) or {}).keys() if pe else []):
            items.append(RubricItem(
                key=f"pe:{area}", domain="physical_exam",
                expected=f"examine {str(area).replace('_', ' ')}",
                criticality="important", evidence_kind="pf"))
        for inv in (getattr(v, "investigations", None) or []):
            name = getattr(inv, "name", "") or ""
            ap = getattr(getattr(inv, "appropriateness", None), "value", getattr(inv, "appropriateness", "")) or ""
            items.append(RubricItem(
                key=f"inv:{name}", domain="investigations",
                expected=name,
                criticality="critical" if ap in ("essential",) else "important",
                evidence_kind="investigations",
                synonyms=[getattr(inv, "expected_result", "") or ""]))
        dd = getattr(v, "diagnostic", None)
        if dd is not None and getattr(dd, "working_diagnosis", ""):
            items.append(RubricItem(
                key="dx:working", domain="diagnosis_ddx",
                expected=getattr(dd, "working_diagnosis", ""),
                criticality="critical", evidence_kind="diagnosis",
                synonyms=list(getattr(dd, "synonyms", None) or [])))
            for d in (getattr(dd, "differentials", None) or [])[:3]:
                nm = getattr(d, "name", d) if not isinstance(d, dict) else d.get("name", "")
                items.append(RubricItem(
                    key=f"ddx:{nm}", domain="diagnosis_ddx",
                    expected=str(nm), criticality="routine", evidence_kind="diagnosis"))
        mg = getattr(v, "management", None)
        if mg is not None:
            for bucket, dom in (("stabilization", "nonpharm_mgmt"),
                                ("pharmacologic", "pharm_mgmt"),
                                ("non_pharmacologic", "nonpharm_mgmt"),
                                ("referral", "nonpharm_mgmt"),
                                ("follow_up", "nonpharm_mgmt"),
                                ("education_safety_netting", "communication_education")):
                for entry in (getattr(mg, bucket, None) or []):
                    items.append(RubricItem(
                        key=f"mg:{bucket}:{str(entry)[:30]}", domain=dom,
                        expected=str(entry),
                        criticality="critical" if bucket in ("stabilization", "referral") else "important",
                        evidence_kind="management" if dom != "communication_education" else "education"))
        for a in (getattr(v, "assessment_items", None) or []):
            txt = getattr(a, "text", "") or ""
            imp = str(getattr(getattr(a, "importance", ""), "value", getattr(a, "importance", "")) or "")
            items.append(RubricItem(
                key=f"ass:{txt[:30]}", domain="diagnosis_ddx",
                expected=txt,
                criticality="critical" if imp == "critical" else "important",
                evidence_kind="transcript"))
    except Exception:
        pass
    # Communication/professionalism are transcript-pattern items (always present
    # so the ledger is complete even for thin variants). Synonyms cover the
    # observable phrasings candidates actually use (open questions, empathy
    # markers, return precautions) so equivalent behaviour is not missed on
    # wording alone.
    items.append(RubricItem(key="comm:empathy", domain="communication_education",
                            expected="empathy and lay language", criticality="routine",
                            evidence_kind="transcript",
                            synonyms=["tell me about", "how are you", "sorry to hear",
                                      "i understand", "terima kasih", "maaf",
                                      "could you tell me"]))
    items.append(RubricItem(key="prof:safety-net", domain="professional_behavior",
                            expected="safety netting and urgency", criticality="critical",
                            evidence_kind="transcript",
                            synonyms=["return if", "come back if", "warning signs",
                                      "danger signs", "referral", "rujuk",
                                      "kembali jika", "tanda bahaya"] ))
    return items


# ── evidence ledger ────────────────────────────────────────────────────────
@dataclass
class LedgerEntry:
    key: str
    domain: str
    expected: str
    observed: str = ""
    source: str = ""  # turn:N | pf | investigations | diagnosis | management | referral | education
    adjudication: str = "miss"  # hit|partial|attempted|miss
    score_0_3: int = 0
    reason: str = ""
    criticality: str = "routine"

    def to_dict(self) -> dict:
        return asdict(self)


def _evidence_pool(upr: UserPerformanceRecord, kind: str) -> list[tuple[str, str]]:
    """Candidate-observed texts for one evidence kind as (text, source)."""
    if kind == "transcript":
        return [(t["text"], f"turn:{t['turn']}") for t in upr.transcript_user_texts]
    if kind == "pf":
        pool = [(upr.pf_notes, "pf:notes")] if upr.pf_notes.strip() else []
        pool += [(a.replace("_", " "), f"pf:area:{a}") for a in upr.pf_areas]
        return pool
    if kind == "investigations":
        return [(t, "investigations") for t in upr.investigations]
    if kind == "diagnosis":
        return [(upr.diagnosis, "diagnosis")] + [(d, "ddx") for d in upr.differentials]
    if kind == "management":
        return [(upr.management_text, "management")] + [(m, "management:med") for m in upr.medications]
    if kind == "referral":
        return [(upr.referral, "referral")] if upr.referral.strip() else []
    if kind == "education":
        return [(upr.education, "education")] if upr.education.strip() else []
    return []


def adjudicate_item(item: RubricItem, upr: UserPerformanceRecord) -> LedgerEntry:
    """Adjudicate ONE rubric item against the UPR (deterministic, no LLM)."""
    pool = _evidence_pool(upr, item.evidence_kind)
    forms: list[str] = []
    sources: list[str] = []
    for text, src in pool:
        for f in _expand_forms(text):
            forms.append(f)
            sources.append(src)
    # expected + synonyms as the target set
    targets = [item.expected] + list(item.synonyms or [])
    best_verdict, best_src, best_obs, best_reason = "miss", "", "", "no evidence"
    for tgt in targets:
        if not (tgt or "").strip():
            continue
        r = _concept_match(forms, tgt)
        if r["verdict"] == "hit":
            # negation guard: a negated mention is not elicitation credit
            idx = next((i for i, f in enumerate(forms)
                        if _norm(tgt) in f or len(_tokens(tgt) & _tokens(f)) > 0), None)
            obs = pool[idx][0] if idx is not None and idx < len(pool) else ""
            # sentence-level negation check on the matched observed text
            if obs and _negated(obs) and item.evidence_kind == "transcript":
                best_verdict, best_src, best_obs = "attempted", pool[idx][1], obs
                best_reason = "negated mention — not elicited"
                continue
            return LedgerEntry(key=item.key, domain=item.domain, expected=item.expected,
                               observed=obs, source=pool[idx][1] if idx is not None and idx < len(pool) else "",
                               adjudication="hit", score_0_3=3,
                               reason=r["reason"], criticality=item.criticality)
        elif r["verdict"] in ("partial", "attempted") and best_verdict == "miss":
            idx = 0
            best_verdict = r["verdict"]
            best_reason = r["reason"]
            best_obs = pool[0][0] if pool else ""
            best_src = pool[0][1] if pool else ""
    score = {"hit": 3, "partial": 2, "attempted": 1, "miss": 0}[best_verdict]
    # HARD RULE: no evidence → no full credit (partial max without a source).
    if not pool and score > 0:
        score, best_verdict, best_reason = 0, "miss", "no evidence pool"
    if best_verdict == "partial" and score > 2:
        score = 2
    return LedgerEntry(key=item.key, domain=item.domain, expected=item.expected,
                       observed=best_obs, source=best_src,
                       adjudication=best_verdict, score_0_3=score,
                       reason=best_reason, criticality=item.criticality)


def build_ledger(v, upr: UserPerformanceRecord) -> list[LedgerEntry]:
    return [adjudicate_item(it, upr) for it in rubric_from_variant(v)]


# ── diagnosis hierarchy + pharm detail (deterministic) ─────────────────────
def grade_diagnosis_hierarchical(submitted: str, v) -> dict:
    """exact+severity (3) > family incomplete (2) > broad partial (1) > wrong (0)
    > dangerous miss (0 + gate). Deterministic token/family rules, no LLM."""
    from pipeline.case_v3.semantic import normalize as _sem_norm
    dd = getattr(v, "diagnostic", None)
    target = (getattr(dd, "working_diagnosis", "") or "") if dd else ""
    syns = list(getattr(dd, "synonyms", None) or []) if dd else []
    diffs = []
    if dd:
        for d in (getattr(dd, "differentials", None) or []):
            diffs.append(getattr(d, "name", d) if not isinstance(d, dict) else d.get("name", ""))
    sub = _norm(submitted)
    if not sub:
        return {"tier": "wrong", "score_0_3": 0, "reason": "no diagnosis submitted", "gate": None}
    cand_forms = _expand_forms(submitted)
    cand_all = _norm(" ".join(cand_forms))
    tgt_forms = _expand_forms(target) + [_norm(s) for s in syns for _ in [0]]
    tgt_forms = [t for t in tgt_forms if t]
    # exact: any target form ↔ any candidate form containment (abbrev-expanded).
    # Severity is only demanded when the TARGET itself carries a severity
    # token (mild/moderate/severe/berat/ringan); a variant-level `severity`
    # field that never appears in the diagnosis name must not downgrade exact.
    _SEV = ("mild", "moderate", "severe", "berat", "ringan", "tanpa", "without", "dengan")
    for tf in tgt_forms:
        for cf in cand_forms:
            if tf and cf and (tf in cf or cf in tf):
                tgt_sev = [w for w in _tokens(tf) if w in _SEV]
                if tgt_sev and not any(w in cand_all for w in tgt_sev):
                    return {"tier": "family-incomplete-severity", "score_0_3": 2,
                            "reason": "correct family, severity missing", "gate": None}
                return {"tier": "exact", "score_0_3": 3, "reason": "exact/synonym match", "gate": None}
    # typo tolerance: single-edit near-miss on head terms
    for tf in tgt_forms:
        for wt in _tokens(tf):
            if len(wt) < 5:
                continue
            for cf in cand_forms:
                for wc in _tokens(cf):
                    if _lev(wt, wc) <= max(1, len(wt) // 5):
                        return {"tier": "exact", "score_0_3": 3,
                                "reason": f"near-miss typo {wc}~{wt}", "gate": None}
    # correct family: shares head noun with target (e.g. "pneumonia" vs "child pneumonia")
    tt, st = _tokens(target), _tokens(submitted)
    head_overlap = tt & st
    if len(head_overlap) >= 1 and any(len(w) >= 5 for w in head_overlap):
        # dangerous miss check: submitted is a reverting differential's opposite?
        return {"tier": "family-incomplete-severity", "score_0_3": 2,
                "reason": f"correct family, incomplete ({sorted(head_overlap)[:3]})", "gate": None}
    # broad partially relevant: submitted matches a listed differential
    for d in diffs:
        if _norm(d) and (_norm(d) in _norm(submitted) or _norm(submitted) in _norm(d)):
            return {"tier": "broad-partial", "score_0_3": 1,
                    "reason": f"differential-level only: {d}", "gate": None}
    # dangerous miss: target is safety-critical and nothing close submitted
    crit_rf = [getattr(r, "fact", "") for r in (getattr(v, "red_flags", None) or [])]
    if crit_rf:
        return {"tier": "dangerous-miss", "score_0_3": 0,
                "reason": "wrong diagnosis with critical red flags unaddressed",
                "gate": "missed_urgent_referral"}
    _ = _sem_norm  # keep the shared normalizer referenced (single truth)
    _ = cand_forms
    return {"tier": "wrong", "score_0_3": 0, "reason": "no family match", "gate": None}


def grade_pharm_detail(upr: UserPerformanceRecord, v) -> dict:
    """Stage-aware pharm detail: preclinical wants agent concept; koas/OSCE
    management station wants agent+dose+route+frequency+duration — but ONLY for
    detail the variant truth specifies (missing authoring is never the
    student's fault). Returns {score_0_3, reason, missing[]}.

    NOTE: formulary/Fornas context never changes this verdict (isolation).
    """
    mg = getattr(v, "management", None)
    truth_agents = list(getattr(mg, "pharmacologic", None) or []) if mg else []
    if not truth_agents:
        return {"score_0_3": 3, "reason": "no pharm truth specified", "missing": []}
    obs = " ".join([upr.management_text] + list(upr.medications))
    obs_n = _norm(obs)
    if not obs_n.strip():
        return {"score_0_3": 0, "reason": "no management submitted", "missing": ["agent"]}
    # agent concept: any truth agent headword present (generic, tolerant)
    agent_hit = any(len(_tokens(a) & _tokens(obs)) >= 1 for a in truth_agents)
    if not agent_hit:
        # international acceptable alternative is still acceptable — check class
        # terms loosely (e.g. "antibiotic" for a named antibiotic truth)
        if "antibiot" in obs_n or "antibiotic" in obs_n:
            agent_hit = True
    if not agent_hit:
        return {"score_0_3": 0, "reason": "no agent concept", "missing": ["agent"]}
    if (upr.learner_level or "koas") == "preclinical":
        return {"score_0_3": 3, "reason": "agent concept adequate (preclinical)", "missing": []}
    # koas: demand detail only where truth specifies it (dose-gated)
    truth_joined = _norm(" ".join(truth_agents))
    demands = [d for d in ("mg", "ml", "tablet", "x", "daily", "hour", "day", "iv", "po", "oral")
               if d in truth_joined]
    if not demands:
        return {"score_0_3": 3, "reason": "agent adequate; truth specifies no dose detail", "missing": []}
    detail_hits = sum(1 for d in demands if d in obs_n)
    if detail_hits >= max(1, len(demands) - 1):
        return {"score_0_3": 3, "reason": "agent + detail adequate", "missing": []}
    if detail_hits >= 1:
        return {"score_0_3": 2, "reason": "agent correct, detail incomplete", "missing": ["detail"]}
    return {"score_0_3": 1, "reason": "agent only, detail missing", "missing": ["dose/route/frequency/duration"]}


# ── safety ─────────────────────────────────────────────────────────────────
_UNSAFE_PATTERNS = [
    (re.compile(r"\bnsaid\b.*dengue|dengue.*\bnsaid\b|\bibuprofen\b.*dengue|dengue.*\bibuprofen\b"), "dangerous_drug", "NSAID in dengue"),
    (re.compile(r"\bdischarge\b.*(shock|severe)|pulang.*syok"), "unsafe_discharge", "unsafe discharge"),
    (re.compile(r"\bno\s+referral\b.*(emergency|severe)|tanpa\s+rujuk.*gawat"), "missed_urgent_referral", "missed urgent referral"),
]


def detect_safety_gates(v, upr: UserPerformanceRecord, ledger: list[LedgerEntry]) -> list[dict]:
    """Explicit gates/caps from ledger + management truth (deterministic)."""
    gates: list[dict] = []
    obs_all = " ".join([t["text"] for t in upr.transcript_user_texts] + [upr.management_text] + list(upr.medications))
    obs_n = _norm(obs_all)
    for rx, typ, label in _UNSAFE_PATTERNS:
        if rx.search(obs_n):
            gates.append({"type": typ, "detail": label})
    # failure to stabilize: variant expects stabilization but UPR has none
    mg = getattr(v, "management", None)
    stab = list(getattr(mg, "stabilization", None) or []) if mg else []
    needs_stab = any(_norm(s) not in ("", "none required", "none") for s in stab)
    if needs_stab and not obs_n.strip():
        gates.append({"type": "failure_to_stabilize", "detail": "stabilization expected, none submitted"})
    # missed shock: critical red flags all missed in ledger
    crit = [e for e in ledger if e.criticality == "safety-critical"]
    if crit and all(e.adjudication == "miss" for e in crit):
        gates.append({"type": "missed_shock", "detail": f"{len(crit)} safety-critical items unelicited"})
    # major contraindication: only when the submission both references the
    # error context AND dismisses/escalates unsafely (discharge, no referral,
    # ignore). Mere mention of "warning signs" in a question must never gate.
    _DISMISS = ("discharge", "pulang", "no referral", "tanpa rujuk", "ignore",
                "abaikan", "no need", "tidak perlu")
    if any(d in obs_n for d in _DISMISS):
        for err in (getattr(v, "safety_critical_errors", None) or []):
            en = _norm(err)
            if en and any(w in obs_n for w in _tokens(en) if len(w) >= 6):
                gates.append({"type": "major_contraindication", "detail": err[:120]})
                break
    # de-duplicate by type
    seen, out = set(), []
    for g in gates:
        if g["type"] not in seen:
            seen.add(g["type"])
            out.append(g)
    # map live-judge compat aliases onto the canonical set for consumers
    return out


# ── deterministic aggregation ──────────────────────────────────────────────
def aggregate(ledger: list[LedgerEntry], *, mode: str, overtime: bool,
              safety_gates: list[dict], dx_grade: dict, pharm_grade: dict) -> dict:
    """Item → domain → overall, all server-controlled (LLM never does math).

    per-domain pct = weighted mean of item scores (0-3 → 0-100) with
    criticality weights; overall = domain-weight mean; overtime −10;
    any safety gate caps overall at 40.
    """
    weights = DOMAIN_WEIGHTS.get(mode, DOMAIN_WEIGHTS["practice"])
    by_domain: dict[str, dict] = {}
    for d in EIGHT_DOMAINS:
        items = [e for e in ledger if e.domain == d]
        if not items:
            by_domain[d] = {"score": 0.0, "max": 100.0, "n": 0, "unassessed": True}
            continue
        num = sum(e.score_0_3 / 3.0 * CRITICALITY_WEIGHT.get(e.criticality, 1.0) for e in items)
        den = sum(CRITICALITY_WEIGHT.get(e.criticality, 1.0) for e in items)
        pct = round(100.0 * num / den, 1) if den else 0.0
        by_domain[d] = {"score": pct, "max": 100.0, "n": len(items), "unassessed": False}
    # diagnosis/pharm hierarchical overlays clamp their domains (evidence-locked:
    # a wrong dx cannot be rescued by routine checklist hits).
    if dx_grade["score_0_3"] == 0:
        by_domain["diagnosis_ddx"] = {"score": min(by_domain["diagnosis_ddx"]["score"], 20.0),
                                      "max": 100.0, "n": by_domain["diagnosis_ddx"]["n"],
                                      "unassessed": False, "clamped": "dx-hierarchical"}
    if pharm_grade["score_0_3"] == 0 and not by_domain["pharm_mgmt"].get("unassessed"):
        by_domain["pharm_mgmt"] = {"score": min(by_domain["pharm_mgmt"]["score"], 25.0),
                                   "max": 100.0, "n": by_domain["pharm_mgmt"]["n"],
                                   "unassessed": False, "clamped": "pharm-detail"}
    overall = round(sum(by_domain[d]["score"] * weights.get(d, 0) for d in EIGHT_DOMAINS) / 100.0, 1)
    if overtime:
        overall = max(0.0, round(overall - 10.0, 1))
    capped = False
    if safety_gates:
        if overall > 40.0:
            overall, capped = 40.0, True
    return {"by_domain": by_domain, "overall": overall,
            "overtime_penalty": 10 if overtime else 0, "safety_capped": capped}


def global_rating(overall: float, safety_gates: list[dict],
                  ledger: list[LedgerEntry]) -> str:
    """Examiner-like holistic layer AFTER scores. Never overrides safety:
    any gate caps at Borderline; shock/dangerous-drug caps at Fail."""
    types = {g.get("type") for g in safety_gates}
    if types & {"missed_shock", "dangerous_drug", "unsafe_discharge"}:
        return "Fail"
    if safety_gates:
        return "Borderline" if overall >= 40 else "Fail"
    # coherence: many partials with few hits reads Borderline even at 60+
    hits = sum(1 for e in ledger if e.adjudication == "hit")
    if overall >= 80 and hits >= 5:
        return "Superior"
    if overall >= 60:
        return "Pass"
    if overall >= 45:
        return "Borderline"
    return "Fail"


# ── feedback composer (ledger-only, no hallucination) ──────────────────────
def compose_feedback(ledger: list[LedgerEntry], *, dx_grade: dict, pharm_grade: dict,
                     safety_gates: list[dict], overall: float,
                     learner_level: str, mode: str) -> dict:
    hits = [e for e in ledger if e.adjudication == "hit"][:3]
    misses = [e for e in ledger if e.adjudication == "miss" and e.criticality in ("critical", "safety-critical")][:3]
    if not misses:
        misses = [e for e in ledger if e.adjudication == "miss"][:3]
    well = [f"Evidenced: {e.expected} ({e.source})" for e in hits] or ["No fully-evidenced items yet — ask targeted questions."]
    missed = [f"Missed: {e.expected} — no evidence in {e.evidence_kind if hasattr(e, 'evidence_kind') else 'submission'}" for e in misses]
    reasoning = f"Diagnosis tier: {dx_grade['tier']} — {dx_grade['reason']}."
    mgmt = f"Pharm detail: {pharm_grade['reason']}."
    expectation = ("Examiner expectation (%s/%s): prioritize safety-critical items first, "
                   "then complete the %s arc." % (learner_level, mode, mode))
    nxt = [f"Practise: {e.expected}" for e in misses[:2]] or ["Practise: focused red-flag screening."]
    safety = [f"{g['type']}: {g.get('detail', '')}" for g in safety_gates]
    summary = (f"Overall {overall:.1f}. {well[0]} {missed[0] if missed else ''}".strip())
    return {"summary": summary, "what_you_did_well": well,
            "what_you_missed": missed, "reasoning_review": reasoning,
            "management_review": mgmt, "examiner_expectation": expectation,
            "what_to_practise_next": nxt, "safety": safety}


# ── top-level entry ────────────────────────────────────────────────────────
def score_hybrid(v, upr: UserPerformanceRecord) -> dict:
    """Deterministic evidence-locked score (no I/O, no LLM, no DB)."""
    ledger = build_ledger(v, upr)
    dx_grade = grade_diagnosis_hierarchical(upr.diagnosis, v)
    pharm_grade = grade_pharm_detail(upr, v)
    gates = detect_safety_gates(v, upr, ledger)
    agg = aggregate(ledger, mode=upr.mode, overtime=upr.overtime,
                    safety_gates=gates, dx_grade=dx_grade, pharm_grade=pharm_grade)
    rating = global_rating(agg["overall"], gates, ledger)
    feedback = compose_feedback(ledger, dx_grade=dx_grade, pharm_grade=pharm_grade,
                                safety_gates=gates, overall=agg["overall"],
                                learner_level=upr.learner_level, mode=upr.mode)
    return {"schema": HYBRID_SCHEMA, "hybrid_version": HYBRID_VERSION,
            "mode": upr.mode, "learner_level": upr.learner_level,
            "overall": agg["overall"], "by_domain": agg["by_domain"],
            "overtime_penalty": agg["overtime_penalty"],
            "safety_capped": agg["safety_capped"],
            "safety_gates": gates,
            "diagnosis_grade": dx_grade, "pharm_grade": pharm_grade,
            "global_rating": rating,
            "evidence_ledger": [e.to_dict() for e in ledger],
            "feedback": feedback,
            # NOTE: not borderline-regression — single-session holistic rating only.
            "standard_setting": "none (BRM requires cohort/station + human examiners)"}


def to_normalized(hybrid_result: dict, *, session_id: str = "",
                  case_id: str = "") -> dict:
    """Map hybrid output into the contracts.NormalizedScore shape + extension."""
    from app.domains.scoring.contracts import from_v2_report
    per_dimension = {d: {"score": v.get("score", 0), "max": 100,
                         "feedback": ""} for d, v in (hybrid_result.get("by_domain") or {}).items()}
    pseudo = {"overall": hybrid_result.get("overall", 0),
              "per_dimension": per_dimension,
              "per_item": [{"dimension": e.get("domain", ""), "item": e.get("expected", ""),
                            "status": ("hit" if e.get("adjudication") == "hit"
                                       else "partial" if e.get("adjudication") == "partial" else "miss"),
                            "evidence": e.get("observed", "")}
                           for e in (hybrid_result.get("evidence_ledger") or [])],
              "safety_gates": hybrid_result.get("safety_gates", []),
              "summary": (hybrid_result.get("feedback") or {}).get("summary", ""),
              "mode": hybrid_result.get("mode", "")}
    base = from_v2_report(pseudo, session_id=session_id, case_id=case_id,
                          content_schema="new", mode=hybrid_result.get("mode", ""),
                          rubric_name="hybrid-8domain", engine="hybrid_deterministic")
    d = base.to_dict()
    d["hybrid"] = {"hybrid_version": HYBRID_VERSION,
                   "global_rating_4tier": hybrid_result.get("global_rating"),
                   "diagnosis_grade": hybrid_result.get("diagnosis_grade"),
                   "pharm_grade": hybrid_result.get("pharm_grade"),
                   "safety_capped": hybrid_result.get("safety_capped"),
                   "standard_setting": hybrid_result.get("standard_setting")}
    return d
