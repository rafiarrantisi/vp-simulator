"""Case schema v2 — parser + linter (BUILD_PLAN_pivot_v4 §5.1/§5.5).

Specialty-agnostic case format: YAML frontmatter (Part A, hidden scoring
ground truth) + Markdown body (Part B, patient persona). The split is
STRUCTURAL — Part A is the frontmatter dict, Part B is the body string — so
leakage prevention (moat P1) is a property of the parser, not a prompt hope.

Pure module: depends only on PyYAML + stdlib. Runtime prompt assembly lives in
`app/rag/prompt_v2.py`; this module never builds prompts, only parses/validates.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ── Controlled vocabularies (BUILD_PLAN §5.1/§5.4) ──────────────────────────
SPECIALTIES = frozenset({
    "internal_medicine", "surgery", "paediatrics", "obstetrics_gynaecology",
    "psychiatry", "neurology", "ent", "dermatology", "ophthalmology", "emergency",
})
STATUSES = frozenset({
    "draft", "ai_generated", "in_review", "clinically_reviewed",
    "pilot_verified", "needs_update", "published", "retired", "legacy",
})
MODES = frozenset({"anamnesis", "osce_full"})

# Schema versions understood by this codebase. v2 = legacy prototype bank
# (88/92 in content/cases are v2); v3 = the rebuilt, clinically governed bank
# (STEP 2+). `schema_origin()` maps a case to its cohort.
CURRENT_SCHEMA_VERSION = 3
LEGACY_SCHEMA_VERSIONS = frozenset({2})
# Statuses that describe verified/signed-off content (safe for pilot/public).
VERIFIED_STATUSES = frozenset({
    "clinically_reviewed", "pilot_verified", "published",
})
# Statuses that explicitly mark a case as legacy-era / not part of the new bank.
LEGACY_STATUSES = frozenset({
    "legacy", "ai_generated", "in_review", "draft", "needs_update", "retired", "requires_review",
})

# Clinical review workflow (§11 of master plan). `status` doubles as the
# review state; "published"/"retired" are terminal catalog states.
RELEASE_STATES = frozenset({
    "clinically_reviewed", "pilot_verified", "needs_update",
    "published", "retired",
})
# Statuses that must NOT appear while requiring review (blocked transitions).
PILOT_CANDIDATE_STATES = frozenset({"ai_generated", "in_review", "clinically_reviewed"})

# Specialty -> id abbreviation (BUILD_PLAN §5.1 ID convention).
SPECIALTY_ABBREV: dict[str, str] = {
    "internal_medicine": "im", "surgery": "surg", "paediatrics": "paed",
    "obstetrics_gynaecology": "og", "psychiatry": "psych", "neurology": "neuro",
    "ent": "ent", "dermatology": "derm", "ophthalmology": "oph", "emergency": "em",
}


def make_case_id(specialty: str, slug: str, n: int = 1) -> str:
    """Build a stable case id like `im_appendicitis_001`."""
    abbrev = SPECIALTY_ABBREV.get(specialty, specialty[:4])
    clean = re.sub(r"[^a-z0-9]+", "_", slug.lower()).strip("_")
    return f"{abbrev}_{clean}_{n:03d}"

REQUIRED_KEYS = (
    "id", "schema_version", "status", "specialty", "presentation",
    "target_condition", "difficulty", "mode_default", "chief_complaint",
    "anamnesis_checklist", "red_flags", "expected_ddx",
)

# Required persona-body sections (matched as case-insensitive header substrings).
REQUIRED_BODY_SECTIONS = ("opening line", "disclosure rules", "communication")

# Part-A artefacts that must NOT appear in the persona body (structural leakage
# guard). Lay patients don't speak in scoring/diagnosis tokens. "red-flag" is
# deliberately NOT here — disclosure-rules instruction text may reference it.
BANNED_BODY_TOKENS = (
    "anamnesis_checklist", "working_diagnosis", "expected_ddx",
    "scoring_weights_override", "schema_version", "differential",
    "icd-10", "icd10",
)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")


@dataclass(frozen=True)
class CaseV2:
    """Parsed schema-v2 case. `frontmatter` = Part A; `body` = Part B."""

    id: str
    frontmatter: dict
    body: str
    body_sections: dict[str, str]  # lowercased H2 header -> section text
    path: str
    frontmatter_ok: bool = True  # False if frontmatter missing/unparseable

    # ---- Part A accessors (scoring ground truth) ----
    @property
    def part_a(self) -> dict:
        return self.frontmatter

    @property
    def part_b(self) -> str:
        return self.body

    def checklist_items(self) -> list[dict]:
        """Flatten anamnesis_checklist (dict of lists) into [{item,critical,group}]."""
        out: list[dict] = []
        cl = self.frontmatter.get("anamnesis_checklist") or {}
        if isinstance(cl, dict):
            for group, items in cl.items():
                for it in items or []:
                    out.append(_norm_item(it, group))
        return out

    def red_flag_items(self) -> list[dict]:
        return [_norm_item(it, "red_flag")
                for it in (self.frontmatter.get("red_flags") or [])]

    def working_diagnosis(self) -> str:
        ddx = self.frontmatter.get("expected_ddx") or {}
        return str(ddx.get("working_diagnosis", "")).strip()

    def find_section(self, needle: str) -> str:
        """Body section whose header contains `needle` (case-insensitive)."""
        low = needle.lower()
        for header, text in self.body_sections.items():
            if low in header:
                return text
        return ""

    # ---- Review workflow (§11) ----
    @property
    def review_state(self) -> str:
        return str(self.frontmatter.get("status") or "draft")

    @property
    def pilot_candidate(self) -> bool:
        return bool(self.frontmatter.get("pilot_candidate", False))

    def reviewed_by(self) -> str:
        au = self.frontmatter.get("authoring") or {}
        return (au.get("reviewed_by") or "").strip()

    def is_released(self) -> bool:
        """True once the case is safe to surface to learners (§11)."""
        st = self.review_state
        if st == "requires_review":  # defensive
            return False
        # published/retired are always surfaced; else require clinical sign-off.
        if st in ("published", "retired"):
            return True
        return st in ("clinically_reviewed", "pilot_verified") and bool(self.reviewed_by())

    # ---- Legacy cohort / backward-compat boundary (STEP 1 rebuild) ----
    def schema_origin(self) -> str:
        """Cohort tag: 'v2-legacy' | 'v3' | 'unknown'. Runtime must know which
        schema it is processing (no silent interpretation of missing fields)."""
        sv = self.frontmatter.get("schema_version")
        try:
            n = int(sv)
        except (TypeError, ValueError):
            return "unknown" if sv is not None else "v2-legacy"
        return "v3" if n >= CURRENT_SCHEMA_VERSION else "v2-legacy"

    def is_legacy(self) -> bool:
        """True when a case belongs to the legacy/prototype cohort and is NOT
        part of the rebuilt, clinically governed bank. Conversely a case is
        non-legacy when it is formally released (published) or carries a
        verified status WITH a clinical sign-off, or opts out via
        frontmatter `legacy: false`."""
        # Explicit override: a maintained case may opt out of the legacy cohort.
        # `legacy: true` → legacy; `legacy: false` → maintained. Absent = fall through.
        if "legacy" in self.frontmatter:
            return bool(self.frontmatter.get("legacy", False))
        # `published` is the terminal released state — never part of legacy.
        if self.review_state == "published":
            return False
        # Verified status WITH sign-off = maintained content, not legacy.
        if self.review_state in VERIFIED_STATUSES and bool(self.reviewed_by()):
            return False
        return True

    # ---- Versioning (STEP 1 §6) ----
    def clinical_content_version(self) -> str:
        return str(self.frontmatter.get("clinical_content_version") or "").strip()

    def source_review_date(self) -> str:
        return str(self.frontmatter.get("source_review_date") or "").strip()

    def superseded_by(self) -> str:
        return str(self.frontmatter.get("superseded_by") or "").strip()

    def previous_version(self) -> str:
        return str(self.frontmatter.get("previous_version") or "").strip()

    # ---- Source / grounding (plan §11 Tier hierarchy) ----
    def source_refs(self) -> list:
        """Normalise source_refs to list of dicts (accepts string or dict entries)."""
        raw = self.frontmatter.get("source_refs") or []
        if isinstance(raw, str):
            raw = [raw]
        out = []
        for r in raw:
            if isinstance(r, dict):
                out.append({
                    "title": str(r.get("title") or r.get("name") or "").strip(),
                    "authority": str(r.get("authority") or "").strip(),
                    "version": str(r.get("version") or "").strip(),
                    "year": str(r.get("year") or "").strip(),
                    "url": str(r.get("url") or "").strip(),
                    "effective_date": str(r.get("effective_date") or "").strip(),
                })
            else:
                out.append({"title": str(r).strip(), "authority": "", "version": "",
                            "year": "", "url": "", "effective_date": ""})
        return out

    def has_indonesian_grounding(self) -> bool:
        """True if any source looks Indonesian official (PNPK/KMK/PerMenKes/JDIH)."""
        _prefixes = ("pnpk", "perm", "kmk", "kepmen", "jdih.kemkes", "e-fornas",
                     "formularium", "kemenkes", "kki", "skdi")
        for s in self.source_refs():
            hay = " ".join(v for v in s.values() if v).lower()
            if any(p in hay for p in _prefixes):
                return True
        return False

    # ---- Competency mapping (§3.1 / §6.1) ----
    def competency(self) -> dict:
        return self.frontmatter.get("competency") or {}

    # ---- Variant family (§13) ----
    @property
    def variant_family(self) -> str:
        return str(self.frontmatter.get("variant_family") or "").strip()

    @property
    def variant_id(self) -> str:
        return str(self.frontmatter.get("variant_id") or "").strip()


def _norm_item(it, group: str) -> dict:
    """Accept {item,critical} dicts or bare strings; normalise."""
    if isinstance(it, dict):
        return {"item": str(it.get("item", "")).strip(),
                "critical": bool(it.get("critical", False)),
                "group": group}
    return {"item": str(it).strip(), "critical": False, "group": group}


def _split_md_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        m = _H2_RE.match(line)
        if m:
            if cur is not None:
                sections[cur] = "\n".join(buf).strip()
            cur = m.group(1).strip().lower()
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        sections[cur] = "\n".join(buf).strip()
    return sections


def parse_string(text: str, *, fallback_id: str = "draft", path: str = "<string>") -> CaseV2:
    """Parse schema-v2 case text (used by the authoring pipeline before a file is
    written). Tolerant of missing frontmatter so the linter can report it cleanly."""
    m = _FRONTMATTER_RE.match(text)
    frontmatter_ok = True
    data: dict = {}
    body = text
    if m:
        body = text[m.end():]
        try:
            loaded = yaml.safe_load(m.group(1))
            data = loaded if isinstance(loaded, dict) else {}
            if not isinstance(loaded, dict):
                frontmatter_ok = False
        except yaml.YAMLError:
            frontmatter_ok = False
    else:
        frontmatter_ok = False
    cid = str(data.get("id") or fallback_id)
    return CaseV2(
        id=cid,
        frontmatter=data,
        body=body.strip(),
        body_sections=_split_md_sections(body),
        path=path,
        frontmatter_ok=frontmatter_ok,
    )


def parse_case_v2(path: str | Path) -> CaseV2:
    """Parse a schema-v2 file. Tolerant of missing frontmatter (linter reports it)."""
    p = Path(path)
    return parse_string(p.read_text(encoding="utf-8"), fallback_id=p.stem, path=str(p))


@dataclass(frozen=True)
class LintResult:
    case_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def lint(case: CaseV2) -> LintResult:
    """Validate a schema-v2 case (BUILD_PLAN §5.5). ERRORS are a hard gate;
    WARNINGS surface review items but do not fail CI."""
    errors: list[str] = []
    warnings: list[str] = []
    fm = case.frontmatter

    if not case.frontmatter_ok or not fm:
        return LintResult(case.id, ["Frontmatter missing or unparseable (expected `---` YAML block at top)"])

    # Required keys
    for k in REQUIRED_KEYS:
        if k not in fm or fm[k] in (None, "", [], {}):
            errors.append(f"Missing/empty required key: `{k}`")

    # Controlled vocab
    if fm.get("schema_version") != 2:
        errors.append("`schema_version` must be 2")
    if fm.get("specialty") and fm["specialty"] not in SPECIALTIES:
        errors.append(f"`specialty` not in controlled vocab: {fm['specialty']}")
    if fm.get("status") and fm["status"] not in STATUSES:
        errors.append(f"`status` not in {sorted(STATUSES)}: {fm['status']}")
    mode = fm.get("mode_default")
    if mode and mode not in MODES:
        errors.append(f"`mode_default` not in {sorted(MODES)}: {mode}")
    diff = fm.get("difficulty")
    if diff is not None and (not isinstance(diff, int) or not 1 <= diff <= 5):
        errors.append("`difficulty` must be an integer 1..5")

    # anamnesis_checklist
    items = case.checklist_items()
    if not items:
        errors.append("`anamnesis_checklist` is empty")
    elif not any(i["critical"] for i in items):
        errors.append("`anamnesis_checklist` has no `critical: true` item")
    cl = fm.get("anamnesis_checklist") or {}
    if not (isinstance(cl, dict) and cl.get("ice_fife")):
        errors.append("`anamnesis_checklist.ice_fife` is required and non-empty")

    # red_flags
    rf = case.red_flag_items()
    if not rf:
        errors.append("`red_flags` is empty")
    elif not any(i["critical"] for i in rf):
        errors.append("`red_flags` has no `critical: true` item")

    # expected_ddx
    ddx = fm.get("expected_ddx") or {}
    if not isinstance(ddx, dict) or not str(ddx.get("working_diagnosis", "")).strip():
        errors.append("`expected_ddx.working_diagnosis` is missing")
    if len(ddx.get("differentials") or []) < 2:
        errors.append("`expected_ddx.differentials` needs >=2 entries")

    # investigations (required for osce_full)
    inv = fm.get("investigations") or {}
    appropriate = inv.get("appropriate") or []
    if mode == "osce_full":
        if not appropriate:
            errors.append("`investigations.appropriate` required for osce_full mode")
        for entry in appropriate:
            if not (isinstance(entry, dict) and str(entry.get("expected", "")).strip()):
                errors.append(f"investigation missing `expected`: {entry}")

    # Persona body sections
    for needle in REQUIRED_BODY_SECTIONS:
        if not case.find_section(needle):
            errors.append(f"Persona body missing a `## {needle}...` section")

    # Leakage guard (Part-A artefacts in body)
    low_body = case.body.lower()
    leaked = [t for t in BANNED_BODY_TOKENS if t in low_body]
    if leaked:
        errors.append(f"Part-A leakage: persona body contains {leaked}")
    wd = case.working_diagnosis().lower()
    if wd and wd in low_body:
        errors.append(f"Part-A leakage: working diagnosis '{case.working_diagnosis()}' appears in persona body")

    # ── Warnings (review items, non-fatal) ──
    if not fm.get("source_refs"):
        warnings.append("no `source_refs` (recommended for traceability)")
    if not fm.get("estimated_minutes"):
        warnings.append("no `estimated_minutes`")
    if fm.get("status") == "draft":
        warnings.append("status=draft (not yet publishable)")

    # ── Review workflow (§1/§11) ──
    br = case.reviewed_by()
    if fm.get("status") in RELEASE_STATES and not br:
        errors.append(
            "`status` in %s requires `authoring.reviewed_by` (clinical sign-off) "
            "— see master plan §11" % sorted(RELEASE_STATES)
        )
    if case.pilot_candidate and fm.get("status") == "draft":
        warnings.append("pilot_candidate but status=draft (not ready for a pilot set)")
    # released cases are exempt from the "released-but-no-reviewer" drift check below.

    # Indonesian PNPK/KMK grounding (plan §11 Tier 0/1) — informational.
    if not case.has_indonesian_grounding():
        warnings.append("no Indonesian official grounding (PNPK/KMK/JDIH) in `source_refs` — "
                        "internasional-only or none")

    # ── Competency mapping (§3.1 / §6.1) ──
    comp = case.competency()
    if comp:
        for k in ("standard", "authority", "version"):
            if not str(comp.get(k) or "").strip():
                errors.append(f"`competency.{k}` missing (wajib untuk version-aware mapping)")

    # ── Variant family (§13) ──
    if (case.variant_family or case.variant_id) and not (case.variant_family and case.variant_id):
        errors.append("`variant_family` and `variant_id` must be set together")

    # Heuristic persona-consistency: critical checklist items should have some
    # apparent grounding in the body (true check is LLM-assisted, Phase 2).
    what_i_know = (
        case.find_section("what i know") + "\n"
        + case.find_section("how i present") + "\n"
        + case.find_section("communication")
    ).lower()
    if what_i_know.strip():
        for i in items:
            if i["critical"] and not _loosely_present(i["item"], what_i_know):
                warnings.append(f"consistency: critical item may lack persona grounding: '{i['item']}'")

    return LintResult(case.id, errors, warnings)


_STOPWORDS = frozenset({
    "of", "the", "a", "an", "to", "and", "or", "in", "on", "for", "with",
    "what", "they", "their", "is", "are", "be", "any", "site", "onset",
})


def _loosely_present(item: str, haystack: str) -> bool:
    """True if a meaningful keyword from the checklist item appears in the body."""
    words = re.findall(r"[a-z]{4,}", item.lower())
    keys = [w for w in words if w not in _STOPWORDS]
    return any(k in haystack for k in keys) if keys else True
