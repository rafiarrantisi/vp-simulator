"""P1 answer-restraint / leakage gate (BUILD_PLAN §2 P1, §5.2).

These are STRUCTURAL assertions (no LLM needed): the patient prompt is built
from Part B (body) only, the judge ground truth from Part A (frontmatter) only.
A behavioural LLM check stays in `qa/restraint_qa.py` (skips under StubLLM).
"""
from pathlib import Path

from app.rag.prompt_v2 import build_judge_ground_truth, build_patient_prompt
from pipeline.case_v2 import parse_case_v2

_EXEMPLAR = Path(__file__).resolve().parents[2] / "content" / "cases" / "oph_dry_eye_001.md"

# Clinical red-flag jargon a lay patient must never utter unprompted.
_RED_FLAG_JARGON = [
    "keratitis", "uveitis", "angle closure", "photophobia", "microbial",
    "purulent", "vision loss", "high-velocity",
]


def _case():
    return parse_case_v2(_EXEMPLAR)


def test_patient_prompt_excludes_working_diagnosis():
    prompt = build_patient_prompt(_case()).lower()
    assert "dry eye disease" not in prompt  # the hidden working diagnosis
    assert _case().working_diagnosis().lower() not in prompt


def test_patient_prompt_excludes_red_flag_labels():
    c = _case()
    prompt = build_patient_prompt(c).lower()
    # Full clinical red-flag labels are never verbatim in the persona prompt.
    for rf in c.red_flag_items():
        assert rf["item"].lower() not in prompt, f"red-flag label leaked: {rf['item']}"
    # The patient's volunteer-able content (spontaneous presentation + known
    # facts) must not pre-load red-flag findings. NB: disclosure-rules text MAY
    # name a red flag as something to deny when asked — that is correct persona
    # design, verified by behaviour QA (qa/restraint_qa.py), not this structural test.
    volunteerable = (
        c.find_section("how i present") + "\n" + c.find_section("what i know")
    ).lower()
    for jargon in _RED_FLAG_JARGON:
        assert jargon not in volunteerable, f"red-flag jargon pre-loaded as volunteer-able: {jargon}"


def test_patient_prompt_excludes_frontmatter_structure():
    prompt = build_patient_prompt(_case()).lower()
    for token in ("anamnesis_checklist", "expected_ddx", "red_flags",
                  "investigations", "scoring_weights", "schema_version"):
        assert token not in prompt


def test_patient_prompt_includes_persona_and_restraint():
    # Positive control: the persona body and restraint scaffold ARE present.
    prompt = build_patient_prompt(_case())
    assert "really uncomfortable lately" in prompt  # opening line from Part B
    assert "ANSWER RESTRAINT" in prompt
    assert "never invent" in prompt.lower()


def test_first_turn_injection_is_additive():
    base = build_patient_prompt(_case(), is_first_turn=False)
    first = build_patient_prompt(_case(), is_first_turn=True)
    assert "FIRST TURN" in first and "FIRST TURN" not in base
    assert len(first) > len(base)


def test_judge_ground_truth_excludes_persona_body():
    c = _case()
    gt = build_judge_ground_truth(c)
    blob = str(gt).lower()
    # Judge sees scoring ground truth...
    assert gt["red_flags"] and gt["expected_ddx"]
    assert "dry eye disease" in str(gt["expected_ddx"]).lower()
    # ...but never the persona's verbatim opening line / lay narration.
    assert "really uncomfortable lately" not in blob
    assert "maya tan" not in blob


def test_no_un_elicited_red_flag_in_generic_opener_context():
    """The persona body (what the patient may say) must not pre-load red-flag
    findings as volunteered facts. Structural proxy for 'patient won't leak'."""
    c = _case()
    what_i_present = c.find_section("how i present").lower()
    for jargon in _RED_FLAG_JARGON:
        assert jargon not in what_i_present
