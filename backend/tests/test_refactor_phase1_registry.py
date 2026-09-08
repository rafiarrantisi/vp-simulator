"""Phase 1 — registry hotfix parity/lifecycle tests (brief §6.3).

Proves the memoized `cached_registry()` hotfix is behavior-identical to
per-call `CaseRegistry.from_dir()` and structurally safe:

- full-corpus prompt equality (all 264 variants, not one sample);
- canonical_hash determinism across independent loads;
- no cross-request mutation (shared objects, stable outputs);
- concurrent cold misses build exactly once, no poisoned cache;
- hot path performs ZERO full-registry rebuilds;
- QORA_REGISTRY_CACHE=0 rollback path restores legacy behavior;
- retained memory within documented budget.
"""
from __future__ import annotations

import os
import resource
import threading

import pytest

from pipeline.case_v3.loader import CaseRegistry


@pytest.fixture(autouse=True)
def _clean_event_loop():
    """asyncio.run() leaves a closed current loop behind, breaking legacy
    get_event_loop() users in later tests. Ensure an open loop instead."""
    import asyncio

    yield
    try:
        closed = asyncio.get_event_loop().is_closed()
    except RuntimeError:
        closed = True
    if closed:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
        except Exception:
            pass



@pytest.fixture()
def fresh_counter(monkeypatch):
    calls = {"n": 0}
    orig = CaseRegistry.from_dir.__func__

    @classmethod
    def counting(cls, root=None):
        calls["n"] += 1
        return orig(cls, root)

    monkeypatch.setattr(CaseRegistry, "from_dir", counting)
    import app.domains.sessions.progress_adapter as pa

    pa._registry_cache.pop("reg", None)
    monkeypatch.setenv("QORA_REGISTRY_CACHE", "1")
    return calls


def _rss_mib() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def test_hot_path_zero_rebuilds(fresh_counter):
    from types import SimpleNamespace

    from app.domains.sessions import v3_compat_service as v3c
    from app.domains.sessions.progress_adapter import cached_registry

    reg = cached_registry()
    assert fresh_counter["n"] == 1
    h = reg.variants["dengue_001_mild"].canonical_hash()
    row = SimpleNamespace(variant_id="dengue_001_mild",
                          variant_canonical_hash=h, persona=None)
    for _ in range(3):
        _, v = v3c._frozen_variant(None, row)
        assert v.id == "dengue_001_mild"
    v3c.library_cards(learner_stage="koas")
    assert fresh_counter["n"] == 1, "hot path must not rebuild registry"


def test_full_corpus_prompt_parity(fresh_counter):
    from app.domains.sessions.progress_adapter import cached_registry
    from app.rag.engine_v3 import v3_patient_prompt

    cached = cached_registry()
    assert fresh_counter["n"] == 1
    fresh = CaseRegistry.from_dir.__func__(CaseRegistry)
    assert fresh_counter["n"] == 2
    assert len(fresh.variants) == len(cached.variants) > 200
    for vid, fv in fresh.variants.items():
        cv = cached.variants[vid]
        assert fv.canonical_hash() == cv.canonical_hash(), vid
        assert (v3_patient_prompt(fv, language="id")
                == v3_patient_prompt(cv, language="id")), vid
        assert (v3_patient_prompt(fv, language="en")
                == v3_patient_prompt(cv, language="en")), vid


def test_shared_objects_stable_across_resolves(fresh_counter):
    from app.domains.sessions.progress_adapter import cached_registry
    from app.rag.engine_v3 import v3_patient_prompt

    a = cached_registry()
    b = cached_registry()
    assert a is b
    v1 = a.variants["dengue_002_warning"]
    p1 = v3_patient_prompt(v1, language="id")
    v2 = b.variants["dengue_002_warning"]
    assert v1 is v2
    assert v3_patient_prompt(v2, language="id") == p1


def test_concurrent_cold_miss_builds_once(fresh_counter):
    import app.domains.sessions.progress_adapter as pa

    pa._registry_cache.pop("reg", None)
    regs: list = []
    errs: list = []

    def worker():
        try:
            regs.append(pa.cached_registry())
        except Exception as e:  # noqa: BLE001
            errs.append(e)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errs
    assert fresh_counter["n"] == 1, f"stampede: {fresh_counter['n']} builds"
    assert all(r is regs[0] for r in regs)


def test_rollback_switch_restores_legacy(fresh_counter, monkeypatch):
    from app.domains.sessions.progress_adapter import cached_registry

    monkeypatch.setenv("QORA_REGISTRY_CACHE", "0")
    a = cached_registry()
    b = cached_registry()
    assert a is not b
    assert fresh_counter["n"] == 2
    assert (a.variants["dengue_001_mild"].canonical_hash()
            == b.variants["dengue_001_mild"].canonical_hash())


def test_retained_memory_within_budget(fresh_counter):
    import gc

    from app.domains.sessions.progress_adapter import cached_registry

    gc.collect()
    before = _rss_mib()
    reg = cached_registry()
    assert len(reg.variants) > 200
    gc.collect()
    retained = _rss_mib() - before
    # Budget §6.1g patient 8 MiB guiding; smoke-guard catches 10x blowups.
    # ru_maxrss is peak-based: recorded as evidence, asserted loosely.
    assert retained < 96, f"registry retained {retained:.1f} MiB peak-delta"
