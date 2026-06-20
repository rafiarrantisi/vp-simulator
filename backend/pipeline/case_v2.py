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
STATUSES = frozenset({"draft", "in_review", "published", "retired"})
MODES = frozenset({"anamnesis", "osce_full"})

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


def parse_case_v2(path: str | Path) -> CaseV2:
    """Parse a schema-v2 file. Tolerant of missing frontmatter (linter reports
    it) so the linter can give a clean message instead of crashing."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    frontmatter_ok = True
    data: dict = {}
    if m:
        body = text[m.end():]
        try:
            loaded = yaml.safe_load(m.group(1))
            data = loaded if isinstance(loaded, dict) else {}
            if not isinstance(loaded, dict):
                frontmatter_ok = False
        except yaml.YAMLError:
            frontmatter_ok = False
            body = text[m.end():]
    else:
        frontmatter_ok = False
        body = text
    cid = str(data.get("id") or p.stem)
    return CaseV2(
        id=cid,
        frontmatter=data,
        body=body.strip(),
        body_sections=_split_md_sections(body),
        path=str(p),
        frontmatter_ok=frontmatter_ok,
    )


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
