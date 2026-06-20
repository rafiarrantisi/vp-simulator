"""Schema-v2 parser + structural A/B separation (BUILD_PLAN §5.1)."""
from pathlib import Path

from pipeline.case_v2 import CaseV2, parse_case_v2

_EXEMPLAR = Path(__file__).resolve().parents[2] / "content" / "cases" / "oph_dry_eye_001.md"


def _load() -> CaseV2:
    return parse_case_v2(_EXEMPLAR)


def test_parses_frontmatter_and_body():
    c = _load()
    assert c.frontmatter_ok is True
    assert c.id == "oph_dry_eye_001"
    assert c.frontmatter["specialty"] == "ophthalmology"
    assert c.frontmatter["schema_version"] == 2
    assert c.body.startswith("# Patient persona")


def test_structural_ab_separation():
    # Part A is the frontmatter dict; Part B is the body string; they don't bleed.
    c = _load()
    assert isinstance(c.part_a, dict) and isinstance(c.part_b, str)
    # A scoring artefact present in Part A must NOT be in Part B.
    assert "anamnesis_checklist" in c.part_a
    assert "anamnesis_checklist" not in c.part_b.lower()


def test_checklist_flatten_and_critical():
    c = _load()
    items = c.checklist_items()
    assert len(items) >= 8
    assert any(i["critical"] for i in items)
    # ice_fife group present in the flattened items
    assert any(i["group"] == "ice_fife" for i in items)


def test_red_flags_and_working_diagnosis():
    c = _load()
    rf = c.red_flag_items()
    assert rf and any(i["critical"] for i in rf)
    assert c.working_diagnosis().lower().startswith("dry eye disease")


def test_find_section():
    c = _load()
    assert c.find_section("opening line")
    assert c.find_section("disclosure rules")
    assert c.find_section("communication")
    assert c.find_section("nonexistent-section") == ""


def test_missing_frontmatter_is_tolerated():
    # Parser must not crash on a non-frontmatter file (linter reports it).
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# just a body\nno frontmatter here\n")
        name = f.name
    c = parse_case_v2(name)
    assert c.frontmatter_ok is False
    assert c.frontmatter == {}
