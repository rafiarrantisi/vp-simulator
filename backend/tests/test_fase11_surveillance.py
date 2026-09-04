"""FASE 11 — Guideline Watcher / Clinical Surveillance acceptance mirror.

Isolation-safe: imports `pipeline.*` only (no app/DB). No network, no LLM.
All observations are injected fixtures; the watcher has no built-in fetcher.

STOP matrix (plan §30–31, Phase 11 A–F): registry tiers/classes, scheduled
checks, metadata-first comparison, impact mapping, reviewer queue + human
gate, required simulations (Fornas/PNPK/divergence/minor/safety), and the
live-truth guarantee (flag/review only — never auto-publish).
"""
from types import SimpleNamespace

import pytest

from pipeline.surveillance import (
    ReviewerQueue,
    approve_task,
    build_task,
    check_target,
    classify_severity,
    default_surveillance_registry,
    detect_change,
    diff_claims,
    get_target,
    map_impact,
    reject_task,
    run_surveillance_cycle,
    validate_registry,
)
from pipeline.surveillance.check import ObservedSnapshot, SurveillanceFinding
from pipeline.surveillance.diff import ClaimDiff
from pipeline.surveillance.queue import ReviewTask


def _target(**kw):
    d = dict(target_id="t_x", title="Test Guideline", organization="Kemenkes",
             tier="1", kind="guideline", current_version="2021",
             revision_hash="hash-1", publication_date="2021-01-01",
             effective_date="2021-01-01",
             watched_families=["fam_dengue"], claim_areas=["management"])
    d.update(kw)
    from pipeline.surveillance.registry import SurveillanceTarget
    return SurveillanceTarget(**d)


def _stub_registry():
    """Minimal case-registry stub (no YAML I/O)."""
    v1 = SimpleNamespace(id="dengue_001_mild",
                         safety_critical_errors=["missed shock"],
                         assessment_items=[SimpleNamespace(name="history")])
    v2 = SimpleNamespace(id="dengue_002_warning",
                         safety_critical_errors=["missed shock", "no referral"],
                         assessment_items=[SimpleNamespace(name="management")])
    return SimpleNamespace(families={"fam_dengue": object()},
                           variants_for_family=lambda fid: [v1, v2] if fid == "fam_dengue" else [])


def _safety_task():
    finding = SurveillanceFinding(target_id="pnpk_dengue", change_kind="focused_update",
                                  checked_at="2026-09-01",
                                  observed={"observed_version": "2021"})
    diff = ClaimDiff(old_claim="cairan rumatan",
                     new_claim="kontraindikasi cairan — risiko syok",
                     claim_area="management", severity="safety_critical",
                     reasons=["safety signal(s): kontraindikasi"],
                     safety_signals=["kontraindikasi"])
    impacts = [SimpleNamespace(to_dict=lambda: {"family_id": "fam_dengue"})]
    return build_task("pnpk_dengue", finding, diff, impacts,
                      source_metadata={"title": "PNPK DBD"}, created_at="2026-09-01")


def _cycle(targets, observations, claims, **kw):
    def claim_provider(target, finding):
        return claims.get(target.target_id, ("", "", (target.claim_areas or ["x"])[0]))
    params = dict(targets=targets, observations=observations,
                  claim_provider=claim_provider, checked_at="2026-09-03",
                  case_registry=_stub_registry(), treatment_maps={})
    params.update(kw)
    return run_surveillance_cycle(**params)


class TestSourceRegistry:
    def test_default_registry_validates_clean(self):
        errors, _ = validate_registry(default_surveillance_registry())
        assert errors == []

    def test_covers_all_tiers_and_source_classes(self):
        targets = default_surveillance_registry()
        assert {"0", "1", "2", "3"} <= {t.tier for t in targets}
        orgs = " ".join(t.organization for t in targets)
        for org in ("KKI", "Kemenkes", "PAPDI", "IDAI", "PERKI", "WHO", "NICE", "GINA"):
            assert org in orgs, "missing source class " + org
        assert {"formulary", "guideline", "competency", "international", "society"} <= {t.kind for t in targets}
        fornas = next(t for t in targets if t.target_id == "fornas_farmalkes")
        assert fornas is not None and fornas.kind == "formulary"
        assert "management" not in fornas.claim_areas

    def test_duplicate_target_id_is_error(self):
        targets = default_surveillance_registry()
        dup = list(targets) + [targets[0]]
        errors, _ = validate_registry(dup)
        assert any("duplicate" in e for e in errors)

    def test_empty_registry_is_error(self):
        errors, _ = validate_registry([])
        assert errors


class TestChangeDetection:
    def test_no_observation_is_no_change(self):
        f = detect_change(_target(), None)
        assert f.change_kind == "no_change" and not f.has_change

    def test_version_bump_is_new_version(self):
        f = detect_change(_target(), {"observed_version": "2026", "checked_at": "2026-09-01"})
        assert f.change_kind == "new_version"

    def test_same_version_new_hash_is_focused_update(self):
        f = detect_change(_target(), {"observed_version": "2021", "revision_hash": "hash-2",
                                      "checked_at": "2026-09-01"})
        assert f.change_kind == "focused_update"

    def test_superseded_date_is_superseded(self):
        f = detect_change(_target(), {"observed_version": "2021", "revision_hash": "hash-1",
                                      "superseded_date": "2026-08-01", "checked_at": "2026-09-01"})
        assert f.change_kind == "superseded"

    def test_effective_date_only_change(self):
        f = detect_change(_target(), {"observed_version": "2021", "revision_hash": "hash-1",
                                      "publication_date": "2021-01-01",
                                      "effective_date": "2026-10-01", "checked_at": "2026-09-01"})
        assert f.change_kind == "effective_date_change"

    def test_identical_metadata_is_no_change(self):
        f = detect_change(_target(), {"observed_version": "2021", "revision_hash": "hash-1",
                                      "publication_date": "2021-01-01",
                                      "effective_date": "2021-01-01", "checked_at": "2026-09-01"})
        assert f.change_kind == "no_change"

    def test_semantic_fn_skipped_when_metadata_decides_no_change(self):
        calls = []
        f = check_target(_target(),
                         {"observed_version": "2021", "revision_hash": "hash-1",
                          "publication_date": "2021-01-01", "effective_date": "2021-01-01",
                          "checked_at": "2026-09-01"},
                         semantic_fn=lambda: calls.append(1))
        assert f.change_kind == "no_change" and f.decided_by_metadata
        assert calls == []

    def test_fetch_fn_supplies_observation(self):
        f = check_target(_target(), None,
                         fetch_fn=lambda t: {"observed_version": "2026", "checked_at": "2026-09-01"})
        assert f.change_kind == "new_version"


class TestSeverity:
    def test_safety_signal_is_safety_critical(self):
        d = classify_severity("beri cairan rumatan",
                              "JANGAN berikan cairan intravena — kontraindikasi pada syok dengue dengan gagal napas; rujuk segera ",
                              claim_area="management")
        assert d.severity == "safety_critical"
        assert d.safety_signals

    def test_wording_only_is_informational(self):
        d = classify_severity("Berikan edukasi tentang tanda bahaya demam berdarah",
                              "Berikan edukasi mengenai tanda bahaya demam berdarah.",
                              claim_area="management")
        assert d.severity == "informational"

    def test_formulary_change_capped_at_minor(self):
        d = classify_severity("amoksisilin kapsul 500 mg tersedia",
                              "amoksisilin sirup 250 mg/5 mL ditambahkan ke Fornas; ketersediaan diperbarui",
                              claim_area="medications", is_formulary_source=True)
        assert d.severity == "minor"

    def test_formulary_cannot_claim_management_truth(self):
        d = classify_severity("parasetamol tersedia",
                              "parasetamol menjadi lini pertama tatalaksana demam (klaim formularium)",
                              claim_area="medications", is_formulary_source=True)
        assert d.severity in ("minor", "safety_critical")

    def test_international_divergence_flagged(self):
        d = classify_severity("tatalaksana sesuai PNPK: observasi",
                              "NICE recommends routine chest CT for all suspected cases",
                              claim_area="investigations", is_international_source=True)
        assert d.differs_from_local_guidance
        assert "Tier 1" in " ".join(d.reasons)

    def test_superseded_escalates_one_level(self):
        d = classify_severity("sediakan leaflet edukasi v2021",
                              "sediakan leaflet edukasi revisi v2021.1",
                              claim_area="management", change_kind="superseded")
        assert d.severity in ("minor", "clinically_meaningful", "safety_critical")

    def test_semantic_pass_cannot_clear_safety(self):
        d = diff_claims("cairan rumatan", "kontraindikasi cairan — risiko syok",
                        claim_area="management",
                        semantic_fn=lambda o, n: {"proposed_severity": "informational",
                                                  "note": "looks minor"})
        assert d.severity == "safety_critical"


class TestImpactMapping:
    def test_pnpk_dengue_maps_to_variants_and_areas(self):
        t = _target(target_id="pnpk_dengue", claim_areas=["management", "safety"])
        entries, warnings = map_impact(t, "new_version", registry=_stub_registry(),
                                       treatment_maps={})
        assert warnings == []
        vids = {e.variant_id for e in entries}
        assert {"dengue_001_mild", "dengue_002_warning"} <= vids
        areas = {e.area for e in entries}
        assert [e.area for e in entries if e.area == "safety"]
        assert all(e.safety_rule is None for e in entries)

    def test_fornas_isolation_medications_only(self):
        t = _target(target_id="fornas_farmalkes", kind="formulary",
                    title="Formularium Nasional (e-Fornas)",
                    claim_areas=["medications", "management"])
        entries, warnings = map_impact(t, "new_version", registry=_stub_registry(),
                                       treatment_maps={})
        assert {e.area for e in entries} == {"medications"}
        assert len([e for e in entries if e.area == "management"]) == 0

    def test_unknown_family_warns_not_crashes(self):
        t = _target(watched_families=["fam_does_not_exist"])
        entries, warnings = map_impact(t, "new_version", registry=_stub_registry(),
                                       treatment_maps={}, known_family_ids={"fam_dengue"})
        assert any("fam_does_not_exist" in w for w in warnings)
        assert all(e.family_id != "fam_does_not_exist" for e in entries)

    def test_international_entries_carry_divergence_note(self):
        t = _target(target_id="who_dengue", tier="3", kind="international",
                    title="WHO Guideline for Dengue")
        entries, warnings = map_impact(t, "new_version", registry=_stub_registry(),
                                       treatment_maps={})
        assert all("differs_from_local_guidance" in e.reason for e in entries)
        assert len([e for e in entries if e.safety_rule is not None]) == 0


class TestReviewerQueue:
    def test_safety_task_proposes_needs_update(self):
        task = _safety_task()
        assert task.severity == "safety_critical"
        assert task.proposed_content_flag == "needs_update"
        assert task.old_claim and task.new_claim
        assert task.affected_content
        assert task.status == "pending"

    def test_anonymous_approval_rejected(self):
        with pytest.raises(match="named human"):
            approve_task(_safety_task(), "  ", None, None)

    def test_safety_approval_requires_clinical_role(self):
        with pytest.raises(match="clinical"):
            approve_task(_safety_task(), "Budi", "product manager", None)
        task = approve_task(_safety_task(), "dr. Sari", "Dokter Spesialis Anak",
                            "sesuai PNPK 2026")
        assert task.status == "approved"
        assert task.reviewed_by == "dr. Sari"
        assert task.proposed_clinical_content_version == "v3.1"

    def test_rejection_keeps_old_truth(self):
        task = reject_task(_safety_task(), "dr. Sari", "clinician", "belum verifikasi teks")
        assert task.status == "rejected"
        assert task.proposed_clinical_content_version == ""
        assert task.proposed_content_flag == ""

    def test_double_decision_rejected(self):
        task = approve_task(_safety_task(), "dr. Sari", "clinician")
        with pytest.raises(match="already approved"):
            approve_task(task, "dr. Sari", "clinician", None)

    def test_queue_export_refuses_content_tree(self):
        q = ReviewerQueue()
        q.add(_safety_task())
        with pytest.raises(match="content/"):
            q.export_jsonl("content/v3/tasks.jsonl")

    def test_queue_export_jsonl_roundtrip(self, tmp_path):
        q = ReviewerQueue()
        q.add(_safety_task())
        n = q.export_jsonl(tmp_path / "review_tasks.jsonl")
        assert n == 1
        assert (tmp_path / "review_tasks.jsonl").exists()


class TestRequiredSimulations:
    def test_sim1_new_fornas_version(self):
        targets = [_target(target_id="fornas_farmalkes", kind="formulary",
                           title="Formularium Nasional (e-Fornas)", tier="2",
                           current_version="KMK HK.01.07/MENKES/1199/2025",
                           claim_areas=["medications"])]
        result, queue = _cycle(
            targets,
            {"fornas_farmalkes": {"observed_version": "KMK HK.01.07/MENKES/XXXX/2026",
                                  "effective_date": "2026-07-01", "checked_at": "2026-09-03"}},
            {"fornas_farmalkes": ("amoksisilin kapsul tersedia",
                                  "amoksisilin sirup ditambahkan; ketersediaan diperbarui",
                                  "medications")})
        assert result.tasks_created == 1
        task = queue.all()[0]
        assert task.severity in ("informational", "minor")
        assert all(e.area == "medications" for e in task.affected_content)
        assert result.live_truth_changed is False

    def test_sim2_new_pnpk(self):
        targets = [_target(target_id="pnpk_dengue", title="PNPK Tata Laksana DBD",
                           claim_areas=["management", "safety"])]
        result, queue = _cycle(
            targets,
            {"pnpk_dengue": {"observed_version": "2026", "revision_hash": "pnpk-dbd-2026",
                             "checked_at": "2026-09-03",
                             "note": "PNPK DBD edisi 2026 terbit"}},
            {"pnpk_dengue": ("pemberian cairan kristaloid 20 ml/kg bolus",
                             "pemberian cairan kristaloid 10 ml/kg bolus dengan re-evaluasi ketat dan kriteria rujuk diperbarui",
                             "management")})
        assert result.tasks_created == 1
        task = queue.all()[0]
        assert task.severity == "clinically_meaningful"
        vids = {v.variant_id for v in task.affected_content}
        assert {"dengue_001_mild", "dengue_002_warning"} <= vids
        assert result.live_truth_changed is False

    def test_sim3_international_differs_from_local(self):
        targets = [_target(target_id="nice_uti", tier="3", kind="international",
                           title="NICE Guideline: UTI", watched_families=["fam_dengue"],
                           claim_areas=["management"])]
        result, queue = _cycle(
            targets,
            {"nice_uti": {"observed_version": "NG109-rev", "checked_at": "2026-09-03"}},
            {"nice_uti": ("tatalaksana sesuai PNPK",
                          "NICE recommends a management pathway not present in PNPK",
                          "management")})
        assert result.tasks_created == 1
        task = queue.all()[0]
        assert task.differs_from_local_guidance is True
        assert any("Tier 1" in r for r in task.diff_reasons)
        assert result.live_truth_changed is False

    def test_sim4_minor_wording_change(self):
        targets = [_target(claim_areas=["management"])]
        result, queue = _cycle(
            targets,
            {"t_x": {"observed_version": "2021", "revision_hash": "hash-9",
                     "checked_at": "2026-09-03"}},
            {"t_x": ("Berikan edukasi tanda bahaya",
                     "Berikan edukasi mengenai tanda bahaya.", "management")})
        assert result.tasks_created == 1
        assert queue.all()[0].severity == "informational"
        assert result.live_truth_changed is False

    def test_sim5_safety_critical_change(self):
        targets = [_target(target_id="pnpk_dengue", title="PNPK Tata Laksana DBD",
                           claim_areas=["management", "safety"])]
        result, queue = _cycle(
            targets,
            {"pnpk_dengue": {"observed_version": "2021", "revision_hash": "hash-emergency",
                             "checked_at": "2026-09-03",
                             "note": "focused update: kontraindikasi"}},
            {"pnpk_dengue": ("cairan kristaloid rumatan",
                             "KONTRAINDIKASI cairan agresif pada syok dengue dengan gagal napas — stabilisasi oksigen dan rujuk segera ke ICU",
                             "management")})
        assert result.tasks_created == 1
        task = queue.all()[0]
        assert task.severity == "safety_critical"
        assert task.proposed_content_flag == "needs_update"
        assert task.status == "pending"
        assert result.live_truth_changed is False

    def test_no_change_produces_no_task(self):
        targets = [_target()]
        result, queue = _cycle(
            targets,
            {"t_x": {"observed_version": "2021", "revision_hash": "hash-1",
                     "publication_date": "2021-01-01", "effective_date": "2021-01-01",
                     "checked_at": "2026-09-03"}},
            {})
        assert result.tasks_created == 0
        assert len(queue.all()) == 0


class TestLiveTruthUnchanged:
    def test_full_cycle_leaves_content_v3_byte_identical(self):
        import hashlib
        from pathlib import Path

        from pipeline.case_v3.loader import default_registry as load_cases
        root = Path(__file__).resolve().parents[1].parent / "content" / "v3"
        before = {}
        for f in sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.json")):
            before[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
        assert before, "content/v3 not found — test setup broken"
        reg = load_cases()
        targets = default_surveillance_registry()
        observations = {t.target_id: {"observed_version": t.current_version + "-rev",
                                      "checked_at": "2026-09-03"} for t in targets}
        result, queue = run_surveillance_cycle(targets=targets, observations=observations,
                                               checked_at="2026-09-03", case_registry=reg)
        assert result.tasks_created == len(queue.all())
        after = {}
        for f in sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.json")):
            after[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
        assert before == after
        assert result.live_truth_changed is False
