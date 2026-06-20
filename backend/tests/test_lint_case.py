"""Case linter unit tests (BUILD_PLAN §5.5)."""
from pathlib import Path

from pipeline.case_v2 import CaseV2, lint, parse_case_v2

_EXEMPLAR = Path(__file__).resolve().parents[2] / "content" / "cases" / "oph_dry_eye_001.md"


def test_exemplar_lints_clean():
    res = lint(parse_case_v2(_EXEMPLAR))
    assert res.ok, f"exemplar should have no errors, got: {res.errors}"


def _good_frontmatter() -> dict:
    return {
        "id": "im_test_001", "schema_version": 2, "status": "in_review",
        "specialty": "internal_medicine", "presentation": "Test",
        "target_condition": "Testitis", "difficulty": 2, "mode_default": "anamnesis",
        "chief_complaint": "test pain",
        "anamnesis_checklist": {
            "hpi_socrates": [{"item": "Onset", "critical": True}],
            "ice_fife": [{"item": "Ideas", "critical": True}],
        },
        "red_flags": [{"item": "Shock", "critical": True}],
        "expected_ddx": {"working_diagnosis": "Testitis", "differentials": ["A", "B"]},
    }


def _case(fm: dict, body: str = "") -> CaseV2:
    default_body = (
        "## Opening line\nhello\n\n## Disclosure rules\nanswer only what is asked\n\n"
        "## Communication profile\ncalm\n"
    )
    return CaseV2(id=fm.get("id", "x"), frontmatter=fm, body=body or default_body,
                  body_sections=_sections(body or default_body), path="mem")


def _sections(body: str) -> dict:
    from pipeline.case_v2 import _split_md_sections
    return _split_md_sections(body)


def test_minimal_valid_case_passes():
    assert lint(_case(_good_frontmatter())).ok


def test_missing_red_flags_fails():
    fm = _good_frontmatter()
    fm["red_flags"] = []
    res = lint(_case(fm))
    assert not res.ok
    assert any("red_flags" in e for e in res.errors)


def test_red_flags_without_critical_fails():
    fm = _good_frontmatter()
    fm["red_flags"] = [{"item": "minor", "critical": False}]
    res = lint(_case(fm))
    assert any("critical" in e for e in res.errors)


def test_checklist_without_ice_fife_fails():
    fm = _good_frontmatter()
    fm["anamnesis_checklist"] = {"hpi_socrates": [{"item": "Onset", "critical": True}]}
    res = lint(_case(fm))
    assert any("ice_fife" in e for e in res.errors)


def test_ddx_needs_two_differentials():
    fm = _good_frontmatter()
    fm["expected_ddx"] = {"working_diagnosis": "X", "differentials": ["only-one"]}
    res = lint(_case(fm))
    assert any("differentials" in e for e in res.errors)


def test_bad_specialty_fails():
    fm = _good_frontmatter()
    fm["specialty"] = "wizardry"
    res = lint(_case(fm))
    assert any("specialty" in e for e in res.errors)


def test_osce_full_requires_investigations():
    fm = _good_frontmatter()
    fm["mode_default"] = "osce_full"
    res = lint(_case(fm))
    assert any("investigations" in e for e in res.errors)


def test_body_leakage_detected():
    fm = _good_frontmatter()
    leaky_body = (
        "## Opening line\nhi\n\n## Disclosure rules\nok\n\n## Communication profile\n"
        "calm\n\n## What I know\nworking_diagnosis: Testitis\n"
    )
    res = lint(_case(fm, leaky_body))
    assert any("leakage" in e for e in res.errors)


def test_missing_persona_section_fails():
    fm = _good_frontmatter()
    body = "## Opening line\nhi\n\n## Communication profile\ncalm\n"  # no disclosure rules
    res = lint(_case(fm, body))
    assert any("disclosure rules" in e for e in res.errors)
