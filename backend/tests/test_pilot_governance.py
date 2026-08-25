"""Governance/worker-audit of the pre-pilot review workflow (master plan §6/§11/§13).

Validates the review-state machine introduced alongside the schema-v2 pipeline:
  - release states require a named clinical reviewer
  - variant_family/variant_id must be set together
  - catalogue summary exposes workflow metadata but never leaks Part A
  - is_released() gating is conservative
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/
from pipeline.case_v2 import (
    RELEASE_STATES,
    CaseV2,
    lint,
    parse_string,
)
from app.domains.cases.v2_catalog import summary


def _mk(id="test_case", status="ai_generated", **extra):
    fm = {
        "id": str(id),
        "schema_version": 2,
        "status": status,
        "specialty": "internal_medicine",
        "system": "renal",
        "presentation": "test",
        "target_condition": "test",
        "difficulty": 2,
        "mode_default": "anamnesis",
        "chief_complaint": "test",
        "username": None,  # safety: arbitrary extra key must not crash
        "source_refs": ["PNPK Kemenkes: X (KMK 1/2000) — https://jdih.kemkes.go.id"],
        "anamnesis_checklist": {"ice_fife": [{"item": "Ideas", "critical": True}]},
        "red_flags": [{"item": "Fever", "critical": True}],
        "expected_ddx": {
            "working_diagnosis": "Test disease",
            "differentials": ["A", "B"],
        },
    }
    fm.update(extra)
    body = """## Identity

I'm a test patient.

## Opening line

Doctor, I feel unwell.

## How I present

I sit here calmly.

## What I know

I have a fever and ideas about it. (disclosure wording only; no diagnosis token)

## Communication profile

Simple and direct.

## Disclosure rules

I answer only what is asked.
"""
    return parse_string("---\n" + yaml.safe_dump(fm, sort_keys=False) + "\n---\n" + body)


def test_release_state_without_reviewer_is_error():
    c = _mk(status="clinically_reviewed")
    res = lint(c)
    assert not res.ok
    assert any("reviewed_by" in e for e in res.errors)


def test_reviewed_clinical_state_passes_release_gate():
    c = _mk(status="clinically_reviewed",
            authoring={"drafted_by": "ai_v1", "reviewed_by": "dr. Test", "reviewed_at": "2026-08-25"})
    res = lint(c)
    assert not any("reviewed_by" in e for e in res.errors)
    assert res.ok  # 'Test disease' must NOT be in body (we wrote it out) — and no other errors


def test_published_requires_reviewer_too():
    assert lint(_mk(status="published")).errors
    c = _mk(status="published", authoring={"reviewed_by": "dr. X", "reviewed_at": "2026-08-01"})
    assert not any("reviewed_by" in e for e in lint(c).errors)


def test_ai_generated_and_in_review_do_not_require_reviewer():
    assert lint(_mk(status="ai_generated")).ok
    assert lint(_mk(status="in_review")).ok
    assert lint(_mk(status="in_review", pilot_candidate=True)).ok


def test_variant_requires_both_fields():
    assert any("variant_family` and `variant_id" in e
               for e in lint(_mk(variant_family="fever")).errors)
    assert any("variant_family` and `variant_id" in e
               for e in lint(_mk(variant_id="x")).errors)
    assert not any("variant_family` and `variant_id" in e
                   for e in lint(_mk(variant_family="fever", variant_id="x")).errors)


def test_competency_requires_standard_authority_version():
    assert not any("competency" in e for e in lint(_mk(competency={
        "standard": "SKDI", "authority": "KKI", "version": "2012", "level": None})).errors)
    assert any("competency.standard" in e for e in lint(_mk(competency={"authority": "KKI"})).errors)


def test_summary_exposes_workflow_not_part_a():
    c = _mk(status="pilot_verified", pilot_candidate=True,
            competency={"standard": "SKDI", "authority": "KKI", "version": "2012", "level": "P"},
            variant_family="fever", variant_id="v1",
            authoring={"reviewed_by": "dr. X", "reviewed_at": "2026-08-01"})
    s = summary(c)
    assert s["pilot_candidate"] is True
    assert s["status"] == "pilot_verified"
    assert s["variant_family"] == "fever" and s["variant_id"] == "v1"
    assert s["competency"]["level"] == "P"
    # Part A scoring truth must never surface in the catalogue:
    for key in ("anamnesis_checklist", "red_flags", "expected_ddx",
                "working_diagnosis", "investigations", "physical_exam_findings"):
        assert key not in s, key


def test_is_released_is_conservative():
    assert not _mk(status="ai_generated").is_released()
    assert not _mk(status="in_review").is_released()
    assert not _mk(status="clinically_reviewed").is_released()  # no reviewer yet
    assert _mk(status="published").is_released()
    assert _mk(status="retired").is_released()
    assert _mk(status="clinically_reviewed",
               authoring={"reviewed_by": "dr. X"}).is_released()
    assert _mk(status="pilot_verified",
               authoring={"reviewed_by": "dr. X"}).is_released()


def test_release_state_set_contains_terminal_states():
    assert "published" in RELEASE_STATES and "retired" in RELEASE_STATES