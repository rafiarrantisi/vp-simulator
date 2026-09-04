"""Phase 7C — deterministic semantic adjudication (plan §14, §19-21).

No literal exact-match scoring. Handles ID↔EN, abbreviations, synonyms,
common typos, paraphrase, and lay phrasing expressing the same clinical
concept. Never relies on unsafe substring containment alone:

- negation guard ("tidak/tanpa/avoid/no/...") blocks false credit;
- single-token containment of a long target is NOT a hit (avoids rewarding
  "dengue" for "severe dengue with shock" as fully adequate — that is a
  family-correct but severity-incomplete partial, plan §19);
- severity/complication tokens are checked explicitly for diagnosis items.

Deterministic and dependency-light: reuses the canonical normalizers from
`pipeline.case_v3.semantic` (diagnosis ID/EN surfaces) and
`pipeline.clinical_contracts.medication` (drug ID/EN/abbr/typo).
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.case_v3.semantic import expand_id, normalize as _dx_normalize
from pipeline.clinical_contracts.medication import match_agent, normalize_medication_text

_NEGATIONS = (
    "tidak",
    "tak ",
    "tanpa",
    "bukan",
    "belum",
    "jangan",
    "hindari",
    "no ",
    "not ",
    "without",
    "avoid",
    "deny",
    "denies",
    "negative",
    "none",
    "never",
)

_SEVERITY_TOKENS = {
    "berat",
    "complicated",
    "critical",
    "dengan syok",
    "derajat",
    "grade",
    "komplikasi",
    "kritis",
    "mild",
    "moderate",
    "ringan",
    "sedang",
    "severe",
    "shock",
    "stadium",
    "stage",
    "syok",
    "tanpa komplikasi",
    "tipe",
    "type",
    "uncomplicated",
    "with shock",
}

_VAGUE_FILLER = {
    "check",
    "drug",
    "education",
    "edukasi",
    "istirahat",
    "medicine",
    "obat",
    "pemeriksaan",
    "pengobatan",
    "periksa",
    "refer",
    "rest",
    "rujuk",
    "terapi",
    "tes",
    "test",
    "tindakan",
    "treatment",
}

_AVOID_MARKERS = (
    "avoid",
    "hindari",
    "jangan",
    "tanpa",
    "do not",
    "don't",
    "dont",
    "stop",
    "hentikan",
    "kontra",
    "never give",
    "jangan berikan",
)

_SEV_HIGH = {
    "berat",
    "complicated",
    "critical",
    "dss",
    "haemorrhagic",
    "hemorrhagic",
    "komplikasi",
    "kritis",
    "severe",
    "shock",
    "syok",
    "warning",
}

_SEV_LOW = {
    "mild",
    "no",
    "ringan",
    "tanpa",
    "tidak",
    "uncomplicated",
    "without",
}

_SEV_PHRASE_CONFLICTS = (
    ("with warning", "without warning"),
    ("dengan tanda bahaya", "tanpa tanda bahaya"),
    ("dengan syok", "tanpa syok"),
    ("with shock", "without shock"),
    ("trombosit turun", "trombosit normal"),
)

_CONCEPTS: tuple[tuple[str, frozenset, frozenset], ...] = (
    ("fever", frozenset({"febrile", "febris", "fever", "pyrexia"}), frozenset({"demam", "panas"})),
    (
        "onset",
        frozenset({"began", "continuous", "duration", "episode", "onset", "pattern", "saddleback", "start"}),
        frozenset({"durasi", "hari", "kapan", "menerus", "mulai", "pola", "sejak", "terus"}),
    ),
    (
        "bleeding",
        frozenset({"bleeding", "epistaxis", "gum", "haemorrhage", "hemorrhage", "manifestations", "petechiae"}),
        frozenset({"berdarah", "bintik", "gusi", "mimisan", "pendarahan", "perdarahan"}),
    ),
    (
        "warning",
        frozenset(
            {"abdominal", "danger", "flag", "lethargy", "red", "severe", "shock", "vomit", "vomiting", "warning"}
        ),
        frozenset({"bahaya", "berat", "lemas", "muntah", "perut", "syok", "tanda", "waspada"}),
    ),
    (
        "fluids_rest",
        frozenset({"fluid", "fluids", "hydration", "oral", "rest"}),
        frozenset({"cairan", "hidrasi", "istirahat", "minum"}),
    ),
    (
        "referral",
        frozenset({"control", "follow", "monitor", "precautions", "refer", "referral", "return"}),
        frozenset({"kembali", "kontrol", "pantau", "rujuk", "waspada"}),
    ),
    (
        "course",
        frozenset(
            {"clearly", "counsel", "counselled", "course", "explain", "explained", "home", "monitor", "monitoring"}
        ),
        frozenset({"dijelaskan", "dipantau", "jelaskan", "pantau", "penjelasan", "perjalanan", "rumah"}),
    ),
    (
        "labs",
        frozenset({"blood", "cbc", "count", "full", "monitor", "monitoring", "platelet", "platelets", "serial"}),
        frozenset({"darah", "hitung", "lab", "trombosit"}),
    ),
    (
        "nsaid",
        frozenset({"anti", "aspirin", "ibuprofen", "nsaid", "nsaids", "nyeri"}),
        frozenset({"antalgin", "asetosal", "ibuprofen", "nsaid"}),
    ),
    (
        "appetite_general",
        frozenset({"activity", "appetite", "condition", "general", "sleep"}),
        frozenset({"aktivitas", "makan", "nafsu", "sehari", "tidur"}),
    ),
)


def _is_avoidance_item(norm_expected: str) -> bool:
    return (
        "avoid" in norm_expected
        or "hindari" in norm_expected
        or "unsafe action" in norm_expected
        or "jangan" in norm_expected
    )


def _has_avoidance_marker(norm_observed: str) -> bool:
    return any(m in norm_observed for m in _AVOID_MARKERS)


def _concept_hit(norm_exp: str, norm_obs: str) -> str:
    """Return matching concept name or '' (either language, either side)."""
    exp_toks = set(norm_exp.split())
    obs_toks = set(norm_obs.split())
    for name, en, id_ in _CONCEPTS:
        surfaces = en | id_
        if exp_toks & surfaces and obs_toks & surfaces:
            return name
    return ""


def _concept_shared(norm_exp: str, norm_obs: str) -> set[str]:
    """Shared concept surface tokens (for negation-window checks)."""
    exp_toks = set(norm_exp.split())
    obs_toks = set(norm_obs.split())
    shared: set[str] = set()
    for _, en, id_ in _CONCEPTS:
        surfaces = en | id_
        if exp_toks & surfaces and obs_toks & surfaces:
            shared |= obs_toks & surfaces
    return shared


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _has_negation(text_norm: str, term_norm: str) -> bool:
    """True when the term appears negated ("tidak ada demam", "no fever")."""
    if not term_norm or term_norm not in text_norm:
        return False
    for neg in _NEGATIONS:
        n = neg.strip()
        if n and f"{n} {term_norm}" in text_norm:
            return True
    return False


_NEG_WINDOW = {
    "avoid",
    "belum",
    "bukan",
    "denies",
    "deny",
    "hindari",
    "jangan",
    "menyangkal",
    "negative",
    "never",
    "no",
    "none",
    "not",
    "sangkal",
    "tak",
    "tanpa",
    "tidak",
    "without",
}


def _window_negated(form: str, matched: str) -> bool:
    """True when a matched token is preceded (≤3 tokens) by a negation
    marker ("tidak ada perdarahan", "denies bleeding"). A summarized
    negative is not positive evidence of eliciting — conservative miss."""
    toks = form.split()
    hit = set(matched.split())
    for i, t in enumerate(toks):
        if t in hit and any(
            toks[max(0, i - 3) : i].count(n) for n in _NEG_WINDOW if n in toks[max(0, i - 3) : i]
        ):
            return True
    return False


def _single_vs_multi(form: str, term: str) -> bool:
    """True when a lone observed token faces a multi-token term — substring
    containment here over-credits ("dengue" for "severe dengue")."""
    return len(form.split()) == 1 and len(term.split()) >= 2 and form != term


def _norm_generic(s: str) -> str:
    t = _dx_normalize(s or "")
    m = normalize_medication_text(s or "")
    forms = [t]
    if m and m != t:
        forms.append(m)
    return " ".join(dict.fromkeys(forms))


def _candidate_forms(s: str) -> list[str]:
    """All normalized surface forms of a learner text (ID/EN/abbr expanded)."""
    base = _norm_generic(s)
    forms = [base]
    for e in expand_id(s or ""):
        n = _norm_generic(e)
        if n and n not in forms:
            forms.append(n)
    return [f for f in forms if f]


def _typo_match(norm_obs: str, norm_exp: str) -> bool:
    """True typo (edit distance 1-2 on a long token). Distance 0 (exact
    shared token) is NOT a typo — it is handled by the containment /
    hierarchy rules so single-token family names are not over-credited."""
    for tok in norm_obs.split():
        for goal in norm_exp.split():
            if len(tok) >= 6 and len(goal) >= 6:
                d = _levenshtein(tok, goal)
                if 1 <= d <= 2:
                    return True
    return False


def _severity_of(norm_text: str) -> set[str]:
    toks = set(norm_text.split())
    out: set[str] = set()
    for sev in _SEVERITY_TOKENS:
        if set(sev.split()) <= toks or sev in norm_text:
            out.add(sev.split()[0])
    return out


@dataclass
class Adjudication:
    """Result of adjudicating ONE rubric item against observed evidence."""

    status: str
    score_0_3: int
    reason: str
    matched_quote: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "score_0_3": self.score_0_3,
            "reason": self.reason,
            "matched_quote": self.matched_quote,
        }


def adjudicate(
    expected: str,
    observed_texts: list[str],
    *,
    synonyms: list[str] | None = None,
    acceptable_alternatives: list[str] | None = None,
    kind: str = "general",
) -> Adjudication:
    """Adjudicate one rubric item deterministically.

    `kind`: general | diagnosis | medication | management | communication.
    Returns miss/0 when there is no supporting evidence (plan §3.4).
    """
    synonyms = synonyms or []
    acceptable_alternatives = acceptable_alternatives or []
    quotes = [q for q in (observed_texts or []) if (q or "").strip()]
    if not (expected or "").strip():
        return Adjudication("miss", 0, "rubric item has no expected text")
    if not quotes:
        return Adjudication("miss", 0, "no supporting evidence → no credit")
    norm_exp = _norm_generic(expected)
    if not norm_exp:
        return Adjudication("miss", 0, "expected text normalizes to empty")
    avoid_item = _is_avoidance_item(norm_exp)

    def _allowed(form: str) -> bool:
        if avoid_item and not _has_avoidance_marker(form):
            return False
        return True

    if kind == "diagnosis":
        exp_toks = set(norm_exp.split())
        for q in quotes:
            for form in _candidate_forms(q):
                obs_toks = set(form.split())
                extra_high = (obs_toks & _SEV_HIGH) - (exp_toks & _SEV_HIGH)
                extra_low = (obs_toks & _SEV_LOW) - (exp_toks & _SEV_LOW)
                phrase_clash = any(hi in form and lo in norm_exp for hi, lo in _SEV_PHRASE_CONFLICTS)
                if (extra_high or extra_low or phrase_clash) and not _has_negation(form, norm_exp):
                    core = [t for t in norm_exp.split() if t not in _severity_of(norm_exp)]
                    if set(core) & obs_toks:
                        return Adjudication(
                            "miss", 0, "contradicts canonical severity/state", matched_quote=""
                        )

    for q in quotes:
        for form in _candidate_forms(q):
            if _has_negation(form, norm_exp) or (not avoid_item and _window_negated(form, norm_exp)):
                continue
            if not _allowed(form):
                continue
            if _single_vs_multi(form, norm_exp) or _single_vs_multi(norm_exp, form):
                continue
            if norm_exp in form or form in norm_exp:
                if len(form.split()) >= 2 or len(norm_exp.split()) <= 2:
                    return Adjudication(
                        "hit", 3, "observed evidence matches expected concept", matched_quote=q.strip()
                    )

    for q in quotes:
        for form in _candidate_forms(q):
            for syn in list(synonyms) + list(acceptable_alternatives):
                n_syn = _norm_generic(syn)
                if not n_syn or _has_negation(form, n_syn):
                    continue
                if not _allowed(form):
                    continue
                if _single_vs_multi(form, n_syn) or _single_vs_multi(n_syn, form):
                    continue
                if n_syn in form or form in n_syn or _typo_match(form, n_syn):
                    alt = "acceptable alternative" if syn in acceptable_alternatives else "synonym"
                    return Adjudication(
                        "hit",
                        3,
                        f"clinically equivalent {alt} matched: '{syn}'",
                        matched_quote=q.strip(),
                    )

    for q in quotes:
        for form in _candidate_forms(q):
            if _has_negation(form, norm_exp) or (not avoid_item and _window_negated(form, norm_exp)):
                continue
            if not _allowed(form):
                continue
            if norm_exp in form or form in norm_exp:
                if kind == "diagnosis" and len(form.split()) == 1 and len(norm_exp.split()) >= 3:
                    return Adjudication(
                        "partial",
                        2,
                        "correct disease family but incomplete severity/state",
                        matched_quote=q.strip(),
                    )
                return Adjudication(
                    "hit", 3, "observed evidence matches expected concept", matched_quote=q.strip()
                )

    if kind == "medication":
        cands = [expected] + list(synonyms) + list(acceptable_alternatives)
        for q in quotes:
            hit = match_agent(q, cands)
            if hit and not _has_negation(_norm_generic(q), _norm_generic(hit)):
                alt = "acceptable alternative" if hit in acceptable_alternatives else "expected agent"
                return Adjudication(
                    "hit", 3, f"medication {alt} matched: '{hit}'", matched_quote=q.strip()
                )

    if kind in ("general", "management", "diagnosis"):
        for q in quotes:
            for form in _candidate_forms(q):
                if not _allowed(form):
                    continue
                concept = _concept_hit(norm_exp, form)
                if not concept or _has_negation(form, norm_exp):
                    continue
                shared = _concept_shared(norm_exp, form)
                if not avoid_item and shared and _window_negated(form, " ".join(sorted(shared))):
                    continue
                if kind == "diagnosis":
                    return Adjudication(
                        "partial",
                        2,
                        f"broad but partially relevant (shared concept '{concept}', not an equivalent diagnosis)",
                        matched_quote=q.strip(),
                    )
                return Adjudication(
                    "hit",
                    3,
                    f"same clinical concept in ID/EN wording: '{concept}'",
                    matched_quote=q.strip(),
                )

    for q in quotes:
        for form in _candidate_forms(q):
            if _typo_match(form, norm_exp) and not _has_negation(form, norm_exp):
                return Adjudication(
                    "hit", 3, "near-miss typo accepted fairly", matched_quote=q.strip()
                )

    if kind == "diagnosis":
        for q in quotes:
            for form in _candidate_forms(q):
                exp_core = [t for t in norm_exp.split() if t not in _severity_of(norm_exp)]
                if exp_core and set(exp_core) & set(form.split()):
                    return Adjudication(
                        "partial",
                        2,
                        "correct disease family but incomplete severity/state",
                        matched_quote=q.strip(),
                    )

    for q in quotes:
        for form in _candidate_forms(q):
            if not _allowed(form):
                continue
            c, g = set(form.split()), set(norm_exp.split())
            shared = (c & g) - _VAGUE_FILLER
            if not avoid_item and _window_negated(form, " ".join(sorted(shared))):
                continue
            if len(shared) >= 2 and len(shared) >= max(1, min(len(c), len(g)) * 0.5):
                return Adjudication(
                    "hit", 3, "paraphrase expresses the same concept", matched_quote=q.strip()
                )

    for q in quotes:
        for form in _candidate_forms(q):
            if set(form.split()) & _VAGUE_FILLER or len(form.split()) <= 2:
                c, g = set(form.split()), set(norm_exp.split())
                if c & g:
                    return Adjudication(
                        "partial",
                        1,
                        "attempted but substantially inadequate (vague/class-level only)",
                        matched_quote=q.strip(),
                    )

    return Adjudication("miss", 0, "no clinically equivalent evidence found")
