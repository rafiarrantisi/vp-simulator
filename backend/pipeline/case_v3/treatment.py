"""FASE 5 — Indonesia-aware treatment normalization & assessment (STANDALONE).

Status: ADVISORY layer only. The LLM judges do NOT depend on this module
(the FASE 5 brief explicitly stops before judge rewiring). It is exercised by
tests + the demo tool, and its verdict taxonomy is the contract a future
judge integration must honor:

  preferred > acceptable > incomplete > inappropriate > unsafe

Principles:
- Generic clinical concepts, never brands, never exact-string matching.
- Bilingual ID/EN, synonyms, class terms, common abbreviations, reasonable typos.
- International alternatives that are clinically correct are `acceptable`,
  never auto-zero; local preference is a separate note, not a penalty.
- Fornas/JKN is formulary CONTEXT (availability hints for UI ordering) and
  NEVER changes a verdict (see governance.py Fornas isolation).
- Learner-stage rules decide which detail is demanded: preclinical = agent
  concept; koas/OSCE management station = agent + dose + route + frequency +
  duration — but ONLY for detail the variant truth actually specifies. Missing
  authoring is never the student's fault.
- Dose numbers below come from standard practice and MUST be verified against
  the attached PNPK/society edition at human source-pack (see provenance).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from pipeline.case_v3 import formulary_id as FID

DOSE_PROVENANCE = (
    "standard-practice dosing starter — verify against the attached "
    "PNPK/society edition at human source-pack; never a prescription"
)

VERDICTS = ("preferred", "acceptable", "incomplete", "inappropriate", "unsafe")
_WORST = {v: i for i, v in enumerate(["preferred", "acceptable", "incomplete",
                                      "inappropriate", "unsafe"])}


# ── data ─────────────────────────────────────────────────────────────
@dataclass
class DoseSpec:
    min_amount: float = 0      # in `unit`
    max_amount: float = 0
    unit: str = ""             # mg | g | mcg | mL | puff | tablet | mg_per_kg
    route: str = ""            # PO | IV | IM | topical | inhaled | PR
    freq_per_day: str = ""     # e.g. "3" (q8h), "1", "prn"
    duration: str = ""         # e.g. "5-7 days"
    note: str = ""


@dataclass
class TreatmentAgent:
    generic: str
    role: str = "preferred"    # preferred | alternative
    dose: DoseSpec = field(default_factory=DoseSpec)
    contraindications: list[str] = field(default_factory=list)
    monitoring: list[str] = field(default_factory=list)
    verified: bool = False     # True when dose/role comes from a verified
                               # scenario overlay or dose override (not thin pool truth)


@dataclass
class TreatmentProfile:
    variant_id: str = ""
    indication: str = ""
    immediate_priority: list[str] = field(default_factory=list)
    stabilization: list[str] = field(default_factory=list)
    definitive: list[str] = field(default_factory=list)
    agents: list[TreatmentAgent] = field(default_factory=list)
    referral: str = ""
    followup: str = ""
    # scenario-level unsafe rules: [{generic|class, reason}]
    unsafe_rules: list[dict] = field(default_factory=list)
    provenance: str = DOSE_PROVENANCE

    def specified_detail(self) -> set[str]:
        """Which detail dimensions the truth actually specifies (dose-gated)."""
        out = {"agent"}
        for a in self.agents:
            d = a.dose
            if d.max_amount > 0:
                out.add("dose")
            if d.route:
                out.add("route")
            if d.freq_per_day:
                out.add("frequency")
            if d.duration:
                out.add("duration")
        return out


@dataclass
class AgentResult:
    generic: str | None
    matched_text: str = ""
    verdict: str = "missed"    # preferred|acceptable|incomplete|inappropriate|unsafe|missed
    detail_missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class TreatmentAssessment:
    overall: str = "incomplete"
    agents: list[AgentResult] = field(default_factory=list)
    unsafe_hits: list[dict] = field(default_factory=list)
    formulary_notes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ── learner-stage detail rules ───────────────────────────────────────
def required_detail(learner_stage: str, station: str, profile: TreatmentProfile) -> set[str]:
    """Detail dimensions demanded. Never demands what truth doesn't specify."""
    specified = profile.specified_detail()
    if learner_stage == "preclinical":
        return {"agent"} & specified
    # koas / OSCE management station: full detail — gated by truth
    if station in ("management", "osce_full"):
        return {"agent", "dose", "route", "frequency", "duration"} & specified
    return {"agent"} & specified


# ── input parsing ────────────────────────────────────────────────────
_SPLIT = re.compile(r"[;,\n]+|\b(?: and | dan | plus |\+)\b", re.I)
_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|g\b|mcg|µg|ml\b|tablet(?:s)?|tab(?:let)?|kaplet|puff(?:s)?|semprot(?:an)?|tetes|drop(?:s)?|mg\s*/\s*kg)", re.I)
_FREQ = re.compile(r"(\d+)\s*[x×]\s*(?:sehari| sehari|daily|a day|per day|perhari|/hari)|q\s*(\d+)\s*h|\b(od|qd|bid|tid|qid|prn)\b|sehari\s*(\d+)\s*[x×]|(satu|dua|tiga|empat|sekali|one|two|three|four|once|twice)\s*(?:kali\s*sehari|[x×]\s*sehari|times?\s*(?:daily|a day|per day|sehari))?|\bsekali sehari\b|\bsehari\b|\bdaily\b|\bonce daily\b", re.I)
_WORD_FREQ = {"satu": "1", "dua": "2", "tiga": "3", "empat": "4", "sekali": "1",
              "one": "1", "two": "2", "three": "3", "four": "4",
              "once": "1", "twice": "2"}
_ROUTE_PATTERNS = [
    (re.compile(r"\biv\b|intravena|infus|injeksi iv", re.I), "IV"),
    (re.compile(r"\bim\b|intramuskular|intramuscular|suntik (?:bokong|paha|lengan)", re.I), "IM"),
    (re.compile(r"\bpo\b|oral|minum|per oral|diminum", re.I), "PO"),
    (re.compile(r"\bpr\b|per rectal|rektal|suppositoria|dubur", re.I), "PR"),
    (re.compile(r"oles|topikal|topical|krim|salep|cream|ointment", re.I), "topical"),
    (re.compile(r"hirup|inhal|nebul|puff|semprot.*(?:mulut|hirup)|mdi|dpi", re.I), "inhaled"),
    (re.compile(r"tetes (?:mata|telinga|hidung)|eye drops?|ear drops?", re.I), "topical"),
]
_DUR = re.compile(r"(?:selama|for|x|×)?\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*(hari|days?|minggu|weeks?|bulan|months?)", re.I)
_BID_MAP = {"od": "1", "qd": "1", "bid": "2", "tid": "3", "qid": "4"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


# local alias index with hyphen-insensitive keys (budesonide-formoterol ==
# budesonide formoterol). Built once from the formulary starter map.
_ALIASES: dict[str, str] = {}
for _a, _g in FID._ALIAS_INDEX.items():
    _ALIASES.setdefault(_a.replace("-", " "), _g)


def _negated(text_low: str, start: int) -> bool:
    return bool(_NEG.search(text_low[max(0, start - 20):start]))
_DURATION_INHERENT = ("single", "once", "ongoing", "long-term", "longterm",
                      "chronic", "lifetime", "stat", "prn")

# negation window for truth-mining (never learn "avoid X" as "give X")
_NEG = re.compile(r"\b(avoid|no |tanpa|jangan|stop|hold|never|bukan|contra|withhold|hindari)\b", re.I)


def parse_segment(seg: str) -> dict:
    """Extract {agents:[generic], class_terms:[], dose_mg, route, freq, duration}."""
    out: dict = {"agents": [], "class_terms": [], "dose": None, "route": None,
                 "freq": None, "duration": None, "raw": seg}
    low = _norm(seg)
    # agents: longest-alias-first scan over tokens/phrases
    found: list[str] = []
    for alias, gen in sorted(_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if len(alias) < 3:
            continue
        if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low):
            if gen not in found:
                found.append(gen)
    # fuzzy fallback per word for long tokens with no exact hit
    if not found:
        for w in set(re.findall(r"[a-z]+", low)):
            g, d = FID.fuzzy_generic(w)
            if g and g not in found:
                found.append(g)
                out.setdefault("fuzzy", []).append({"token": w, "generic": g, "dist": d})
    out["agents"] = found
    for term, cls in FID.CLASS_TERMS.items():
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", low):
            if cls not in out["class_terms"]:
                out["class_terms"].append(cls)
    m = _NUM.search(seg)
    if m:
        val = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        if unit.startswith("g") and not unit.startswith("mg") and len(unit) <= 2 and "mg" not in unit:
            # bare "g" (gram) vs mg — keep as written
            pass
        out["dose"] = {"amount": val, "unit": unit}
    for pat, route in _ROUTE_PATTERNS:
        if pat.search(seg):
            out["route"] = route
            break
    if not out["route"] and out.get("dose"):
        # solid oral formulations imply PO unless stated otherwise
        if re.search(r"(tablet|tab|kaplet|kapsul|capsule|mg|g\b)", seg, re.I):
            out["route"] = "PO-implied"
    f = _FREQ.search(seg)
    if f:
        out["freq"] = (f.group(1) or f.group(4)
                       or _WORD_FREQ.get((f.group(5) or "").lower())
                       or _BID_MAP.get((f.group(3) or "").lower(), f.group(3))
                       or "1")  # bare "sehari/daily" matched with no number = once daily
        if f.group(2):
            out["freq"] = f"q{f.group(2)}h"
    d = _DUR.search(seg)
    if d:
        out["duration"] = d.group(0).strip()
    return out


def _dose_ok(parsed: dict, spec: DoseSpec) -> tuple[bool, str]:
    if spec.max_amount <= 0 or not parsed.get("dose"):
        return True, ""
    amt, unit = parsed["dose"]["amount"], parsed["dose"]["unit"]
    # mg/kg specs compare directly when student wrote mg/kg
    if "kg" in spec.unit and "kg" in unit:
        ok = spec.min_amount <= amt <= spec.max_amount
        return ok, "" if ok else f"dose {amt} outside {spec.min_amount}-{spec.max_amount} {spec.unit}"
    if "kg" in spec.unit or "kg" in unit:
        return True, ""  # cannot compare fairly — do not penalize
    # normalize g->mg
    def to_mg(a: float, u: str) -> float | None:
        u = u.lower()
        if u.startswith("mg"):
            return a
        if u == "g":
            return a * 1000
        return None
    a_mg, lo, hi = to_mg(amt, unit), to_mg(spec.min_amount, spec.unit), to_mg(spec.max_amount, spec.unit)
    if a_mg is None or lo is None or hi is None:
        return True, ""
    ok = (lo * 0.8) <= a_mg <= (hi * 1.25)  # 20-25% tolerance band
    return ok, "" if ok else f"dose {amt}{unit} outside expected {spec.min_amount}-{spec.max_amount}{spec.unit}"


def _route_ok(parsed: dict, spec: DoseSpec) -> tuple[bool, str]:
    if not spec.route or not parsed.get("route"):
        return True, ""
    alias = {"oral": "PO", "minum": "PO"}
    pr = alias.get(parsed["route"].lower(), parsed["route"])
    if pr == "PO-implied" and spec.route == "PO":
        return True, ""  # solid oral formulation implies PO
    ok = pr == spec.route
    return ok, "" if ok else f"route {parsed['route']} vs expected {spec.route}"


def _freq_num(f: str | None) -> float | None:
    if not f:
        return None
    f = str(f).strip().lower()
    if f == "prn":
        return -1.0  # as-needed — never a mismatch, handled by caller
    m = re.match(r"q(\d+)h", f)
    if m:
        return 24.0 / float(m.group(1))
    try:
        return float(f)
    except ValueError:
        return None


def _freq_ok(parsed: dict, spec: DoseSpec) -> tuple[bool, str]:
    if not spec.freq_per_day or not parsed.get("freq"):
        return True, ""
    if str(spec.freq_per_day) == "1" and not parsed.get("freq"):
        return True, ""  # single administration is the default reading
    pf = _freq_num(parsed["freq"])
    if pf is None or pf < 0:
        return True, ""
    lo_hi = str(spec.freq_per_day).split("-")
    try:
        lo, hi = float(lo_hi[0]), float(lo_hi[-1])
    except ValueError:
        return True, ""
    ok = lo <= pf <= hi
    return ok, "" if ok else f"frequency {parsed['freq']} vs expected {spec.freq_per_day}x/day"


# ── universal safety net (conservative, standard) ────────────────────
def _universal_unsafe(generic: str, *, age_years: float | None,
                      pregnant: bool, bleeding_context: bool,
                      dysentery_context: bool) -> str:
    g = (generic or "").lower()
    nsaid = {"ibuprofen", "diclofenac", "aspirin"}
    if g in nsaid and bleeding_context and g != "aspirin":
        return "NSAID in bleeding/dengue context — bleeding risk"
    if g == "aspirin" and bleeding_context:
        return "aspirin in bleeding context (analgesic use) — bleeding risk"
    if g == "aspirin" and age_years is not None and age_years < 12:
        return "aspirin in a child — Reye risk"
    if g == "doxycycline" and (pregnant or (age_years is not None and age_years < 8)):
        return "doxycycline in pregnancy/young child — avoid"
    if g == "ciprofloxacin" and pregnant:
        return "fluoroquinolone in pregnancy — avoid, use beta-lactam pathway"
    return ""


# ── assessment ───────────────────────────────────────────────────────
def assess_treatment(student_text: str, profile: TreatmentProfile, *,
                     learner_stage: str = "koas", station: str = "management",
                     age_years: float | None = None, pregnant: bool = False,
                     bleeding_context: bool = False,
                     dysentery_context: bool = False) -> TreatmentAssessment:
    """Deterministic, LLM-free treatment grading against a profile."""
    res = TreatmentAssessment()
    need = required_detail(learner_stage, station, profile)
    segments = [s for s in _SPLIT.split(student_text or "") if s.strip()]
    parsed = [parse_segment(s) for s in segments]
    mentioned: dict[str, dict] = {}
    for p in parsed:
        for g in p["agents"]:
            mentioned.setdefault(g, p)
    prof_by_gen = {a.generic: a for a in profile.agents}

    for gen, agent in prof_by_gen.items():
        if gen in mentioned:
            p = mentioned[gen]
            missing = [d for d in ("dose", "route", "frequency", "duration") if d in need
                       and ((d == "dose" and agent.dose.max_amount > 0 and not p.get("dose"))
                            or (d == "route" and agent.dose.route and not p.get("route")
                                and p.get("route") != "PO-implied")
                            or (d == "frequency" and agent.dose.freq_per_day
                                and agent.dose.freq_per_day != "1" and not p.get("freq"))
                            or (d == "duration" and agent.dose.duration and not p.get("duration")
                                and not agent.dose.duration.lower().startswith(_DURATION_INHERENT)))]
            notes: list[str] = []
            verdict = "preferred" if agent.role == "preferred" else "acceptable"
            if agent.dose.max_amount > 0 and p.get("dose"):
                ok, why = _dose_ok(p, agent.dose)
                if not ok:
                    verdict, notes = "inappropriate", [why + " — dose error"]
            if verdict in ("preferred", "acceptable") and agent.dose.route and p.get("route"):
                ok, why = _route_ok(p, agent.dose)
                if not ok:
                    # wrong route for a route-critical agent (e.g. IM adrenaline
                    # given IV bolus) is a safety event, not a detail miss
                    if gen == "adrenaline":
                        verdict, notes = "unsafe", [why + " — IV bolus adrenaline risks fatal arrhythmia; IM only"]
                    else:
                        verdict, notes = "inappropriate", [why]
            if verdict in ("preferred", "acceptable") and agent.dose.freq_per_day and p.get("freq"):
                ok, why = _freq_ok(p, agent.dose)
                if not ok:
                    verdict, notes = "incomplete", [why + " — check frequency"]
            if verdict in ("preferred", "acceptable") and missing:
                verdict = "incomplete"
                notes.append("missing detail: " + ", ".join(missing))
            res.agents.append(AgentResult(generic=gen, matched_text=p["raw"][:80],
                                          verdict=verdict, detail_missing=missing, notes=notes))
        else:
            res.agents.append(AgentResult(generic=gen, verdict="missed",
                                          notes=["not mentioned"]))

    # student-mentioned agents outside the profile
    for gen, p in mentioned.items():
        if gen in prof_by_gen:
            continue
        reason = _universal_unsafe(gen, age_years=age_years, pregnant=pregnant,
                                   bleeding_context=bleeding_context,
                                   dysentery_context=dysentery_context)
        rule_hit = next((r for r in profile.unsafe_rules
                         if r.get("generic") == gen or r.get("class") in
                         (FID.GENERICS.get(gen, {}).get("cls", ""),)), None)
        if reason or rule_hit:
            why = reason or rule_hit.get("reason", "contraindicated in this scenario")
            res.agents.append(AgentResult(generic=gen, matched_text=p["raw"][:80],
                                          verdict="unsafe", notes=[why]))
            res.unsafe_hits.append({"generic": gen, "reason": why})
        else:
            # loperamide-type scenario rules via class match
            res.agents.append(AgentResult(generic=gen, matched_text=p["raw"][:80],
                                          verdict="inappropriate",
                                          notes=["not indicated for this scenario per variant truth"]))

    # class-only mentions (right area, no agent)
    if not mentioned:
        for p in parsed:
            for cls in p.get("class_terms", []):
                res.notes.append(f"class-level mention only ({cls}) — agent required: incomplete")

    # formulary context: information only, never affects the verdict
    for gen in mentioned:
        info = FID.GENERICS.get(gen)
        if info:
            res.formulary_notes.append(
                f"{gen}: commonly available generic in Indonesian practice "
                f"(ordering hint: {info.get('hint', 'unknown')}) — availability never changes correctness")

    order = ["preferred", "acceptable", "incomplete", "inappropriate", "unsafe", "missed"]
    rank = {v: i for i, v in enumerate(order)}
    verdicts = [a.verdict for a in res.agents if a.verdict != "missed"]
    if not verdicts:
        verdicts = ["incomplete"] if any(p.get("class_terms") for p in parsed) or (student_text or "").strip() else ["incomplete"]
        if not (student_text or "").strip():
            verdicts = ["incomplete"]
            res.notes.append("no treatment submitted")
    res.overall = sorted(verdicts, key=lambda v: rank.get(v, 2))[-1]
    if res.unsafe_hits:
        res.overall = "unsafe"
    # coverage cap: a submission graded `preferred` that omits ANOTHER
    # verified preferred agent is at most incomplete (e.g. reliever-only
    # in persistent asthma). Thin/unverified pool agents never trigger the
    # cap — missing authoring is not the student's fault.
    # Alternative-only answers keep their `acceptable`.
    if res.overall == "preferred" and any(
            a.verdict == "missed"
            and prof_by_gen[a.generic].role == "preferred"
            and (prof_by_gen[a.generic].verified
                 or prof_by_gen[a.generic].dose.max_amount > 0)
            for a in res.agents):
        res.overall = "incomplete"
        res.notes.append("a preferred agent is missing — regimen incomplete")
    return res


# ── derive a profile from variant truth ──────────────────────────────
def profile_from_variant(v, *, dose_overrides: dict[str, dict] | None = None) -> TreatmentProfile:
    """Build a TreatmentProfile from a ClinicalVariant's canonical truth.

    `dose_overrides`: {generic: {min,max,unit,route,freq,duration,note}} for
    demo/verified scenarios. Without overrides, dose detail is unspecified and
    stage rules will not demand it (honest thin-truth handling).
    """
    dose_overrides = dose_overrides or {}
    mgmt = v.management
    me = v.management_expectations
    agents: list[TreatmentAgent] = []
    for m in (v.medications or []):
        ov = dose_overrides.get(m.generic_name, {})
        agents.append(TreatmentAgent(
            generic=m.generic_name,
            role="preferred",
            dose=DoseSpec(min_amount=ov.get("min", 0), max_amount=ov.get("max", 0),
                          unit=ov.get("unit", ""), route=ov.get("route", ""),
                          freq_per_day=ov.get("freq", ""), duration=ov.get("duration", ""),
                          note=ov.get("note", "")),
            contraindications=list(m.contraindications or []),
            monitoring=list(m.monitoring or []),
            verified=bool(ov)))
        for alt in (m.acceptable_alternatives or []):
            g = FID.lookup_generic(alt) or alt.strip().lower()
            if g and all(a.generic != g for a in agents):
                o2 = dose_overrides.get(g, {})
                agents.append(TreatmentAgent(
                    generic=g, role="alternative",
                    dose=DoseSpec(min_amount=o2.get("min", 0), max_amount=o2.get("max", 0),
                                  unit=o2.get("unit", ""), route=o2.get("route", ""),
                                  freq_per_day=o2.get("freq", ""), duration=o2.get("duration", "")),
                    contraindications=[], monitoring=[]))
    # fallback: mine management free-text for known generics the structured
    # medication list missed (common in pre-FASE-5 variants, e.g. paracetamol
    # written only in a pharmacologic string). Mined agents are preferred by
    # role but carry NO dose truth (stage rules will not demand dose).
    have = {a.generic for a in agents}
    for line in list(mgmt.pharmacologic or []) + list(mgmt.non_pharmacologic or []):
        low_line = _norm(line)
        for alias, gen in sorted(_ALIASES.items(), key=lambda kv: -len(kv[0])):
            if len(alias) < 5 or gen in have:
                continue
            m = re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low_line)
            if m and not _negated(low_line, m.start()):
                agents.append(TreatmentAgent(generic=gen, role="preferred"))
                have.add(gen)
    return TreatmentProfile(
        variant_id=v.id,
        indication=v.diagnostic.working_diagnosis,
        immediate_priority=list(mgmt.stabilization or [])[:3],
        stabilization=list(mgmt.stabilization or []),
        definitive=list(mgmt.pharmacologic or []) + list(mgmt.non_pharmacologic or []),
        agents=agents,
        referral="; ".join(mgmt.referral or [])[:300],
        followup="; ".join(mgmt.follow_up or [])[:300],
        unsafe_rules=_scenario_unsafe_rules(v),
    )


def _scenario_unsafe_rules(v) -> list[dict]:
    """Scenario-derived unsafe rules from the variant's own safety truth."""
    rules: list[dict] = []
    blob = " ".join([v.diagnostic.working_diagnosis] +
                    list(v.safety_critical_errors or []) +
                    [r.fact for r in (v.red_flags or [])]).lower()
    if "dengue" in blob or "bleed" in blob or "berdarah" in blob:
        rules.append({"class": "nsaid",
                      "reason": "NSAID in dengue/bleeding scenario — plasma-leak/bleed risk; use paracetamol"})
    if "dysentery" in blob or "bloody" in blob or "berdarah" in blob and "diarrhea" in blob:
        rules.append({"generic": "loperamide",
                      "reason": "antimotility in dysentery — toxic megacolon risk"})
    return rules
