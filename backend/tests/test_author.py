"""Authoring pipeline (BUILD_PLAN §5.3) — prompt, id, extraction, lint loop."""
import pytest

from pipeline import author
from pipeline.case_v2 import make_case_id, parse_string


def test_make_case_id():
    assert make_case_id("internal_medicine", "appendicitis", 1) == "im_appendicitis_001"
    assert make_case_id("ophthalmology", "Dry Eye", 2) == "oph_dry_eye_002"
    assert make_case_id("emergency", "acute coronary syndrome") == "em_acute_coronary_syndrome_001"


def test_author_prompt_enforces_schema_and_restraint():
    system, msgs = author.build_author_prompt(
        "im_gout_001", "internal_medicine", "Acute joint pain", "Gout", 2, "anamnesis"
    )
    content = msgs[0]["content"]
    assert "schema_version: 2" in content
    assert "anamnesis_checklist" in content and "red_flags" in content
    assert "ice_fife" in content
    assert "Lay language only" in content
    assert "leakage" in content.lower()
    assert "Disclosure rules" in content
    assert "im_gout_001" in content  # the id is pinned


def test_validate_inputs():
    assert author.validate_inputs("wizardry", "anamnesis")  # bad specialty
    assert author.validate_inputs("internal_medicine", "telepathy")  # bad mode
    assert author.validate_inputs("internal_medicine", "anamnesis") == []


def test_extract_strips_code_fence():
    wrapped = "```markdown\n---\nid: x\n---\n## Body\nhi\n```"
    out = author.extract_case_markdown(wrapped)
    assert out.startswith("---")
    assert "```" not in out


def test_extract_trims_leading_commentary():
    raw = "Here is your case:\n---\nid: x\n---\n## Body\nhi"
    assert author.extract_case_markdown(raw).startswith("---")


def test_lint_markdown_roundtrips():
    md = (
        "---\nid: im_test_001\nschema_version: 2\nstatus: in_review\n"
        "specialty: internal_medicine\npresentation: T\ntarget_condition: T\n"
        "difficulty: 2\nmode_default: anamnesis\nchief_complaint: pain\n"
        "anamnesis_checklist:\n  hpi_socrates:\n    - {item: Onset, critical: true}\n"
        "  ice_fife:\n    - {item: Ideas, critical: true}\n"
        "red_flags:\n  - {item: Shock, critical: true}\n"
        "expected_ddx:\n  working_diagnosis: Zzz\n  differentials: [A, B]\n---\n"
        "## Opening line\nhi\n\n## Disclosure rules\nanswer only what is asked\n\n"
        "## Communication profile\ncalm\n"
    )
    case, res = author.lint_markdown(md)
    assert case.id == "im_test_001"
    assert res.ok, res.errors


def test_draft_case_requires_real_model(monkeypatch):
    # Under StubLLM, authoring must REFUSE, not fabricate clinical content.
    monkeypatch.setattr(author, "is_stub", lambda: True)
    with pytest.raises(RuntimeError, match="AUTHOR_MODEL|key required"):
        author.draft_case("im_x_001", "internal_medicine", "P", "C", 2, "anamnesis")
