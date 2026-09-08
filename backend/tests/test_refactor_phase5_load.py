"""Phase 5 — concurrency, cancellation, failure matrix (brief §10, §12).

Stub-provider application capacity (NOT provider claims): concurrent gated
streams, burst arrivals, mixed judge load, slow reader, early disconnect,
missing/corrupt artifacts, stale frozen revision. Slow fake latency stands
in for provider wait; instant-stub runs measure routing/DB overhead only.
"""
from __future__ import annotations

import threading
import time
import uuid

import pytest
from fastapi.testclient import TestClient


def _auth(h, tag="p5"):
    email = f"{tag}{uuid.uuid4().hex[:8]}@example.com"
    h.post("/api/auth/signup",
           json={"email": email, "password": "secret12", "full_name": "P5"})
    r = h.post("/api/auth/login", json={"email": email, "password": "secret12"})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": "Bearer " + r.json()["data"]["token"]}


def _mk_session(h, case_id="fam_dengue"):
    headers = _auth(h)
    r = h.post("/api/v2/sessions", json={"case_id": case_id, "language": "en"},
               headers=headers)
    assert r.status_code == 200, r.text[:200]
    return r.json()["data"]["sessionId"], headers


def _slow_v3(monkeypatch, delay=0.05, chunks=6):
    import asyncio

    import app.rag.engine_v3 as e3

    async def slow(*a, **k):
        for i in range(chunks):
            await asyncio.sleep(delay)
            yield f"tok{i} "

    def sync_slow(*a, **k):
        async def gen():
            async for c in slow():
                yield c

        return gen()

    monkeypatch.setattr(e3, "astream_respond", sync_slow)


def _run_streams(h, sid, headers, n, text="halo?"):
    results, errors = [], []

    def fire(i):
        try:
            with h.stream("POST", f"/api/v2/sessions/{sid}/turns/stream",
                          json={"text": f"{text} {i}"}, headers=headers) as r:
                body = b"".join(r.iter_bytes())
            results.append((r.status_code, len(body)))
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=fire, args=(i,)) for i in range(n)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.time() - t0, results, errors


def test_concurrent_streams_complete_cleanly(monkeypatch):
    from app.main import app

    _slow_v3(monkeypatch, delay=0.05, chunks=6)
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        dt, results, errors = _run_streams(h, sid, headers, 10)
        assert not errors, errors[:1]
        assert len(results) == 10
        assert all(s == 200 and n > 0 for s, n in results), results
        # admission reusable afterwards (no leaked slots)
        dt2, results2, errors2 = _run_streams(h, sid, headers, 2, text="lagi?")
        assert not errors2 and len(results2) == 2


def test_burst_arrivals_bounded(monkeypatch):
    from app.main import app

    _slow_v3(monkeypatch, delay=0.02, chunks=3)
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        dt, results, errors = _run_streams(h, sid, headers, 25, text="burst?")
        assert not errors, errors[:1]
        assert len(results) == 25
        assert all(s == 200 for s, _ in results)


def test_cancel_midstream_releases_everything(monkeypatch, caplog):
    """Drive the route generator directly: aclose() mid-stream must mark
    cancelled, release the admission slot, and close the upstream stream."""
    import asyncio
    import logging

    import app.rag.engine_v3 as e3
    from app.database import SessionLocal
    from app.domains.sessions.turn_acceptance import accept_turn
    from app.domains.sessions.v3_compat_service import stream_turn
    from app.domains.sessions.models import SessionRow
    from app.main import app
    from fastapi.testclient import TestClient

    _slow_v3(monkeypatch, delay=0.05, chunks=200)
    with TestClient(app) as h:
        sid, headers = _mk_session(h, "fam_dengue")
        db = SessionLocal()
        row = db.get(SessionRow, sid)
        uid = row.user_id
        snap = accept_turn(db, session_id=sid, user_id=uid, text="halo?",
                           input_type="text")
        db.close()

        async def drive():
            agen = await stream_turn(snap, uid, "halo?", "text")
            try:
                first = await agen.__anext__()
                assert first
                await agen.aclose()
            finally:
                pass

        with caplog.at_level(logging.INFO, logger="qora.perf"):
            asyncio.run(drive())
        msgs = [rec.getMessage() for rec in caplog.records
                if rec.name == "qora.perf"]
        assert any("outcome=cancelled" in m for m in msgs), msgs[-3:]
        # slot reusable immediately (no leak)
        from app.shared.admission import conversation_limiter
        import anyio

        async def reacquire():
            with anyio.fail_after(5):
                await conversation_limiter().acquire()
            conversation_limiter().release()

        asyncio.run(reacquire())



def test_missing_variant_fails_closed():
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionRow
    from app.main import app

    with TestClient(app) as h:
        sid, headers = _mk_session(h, "fam_dengue")
        db = SessionLocal()
        try:
            row = db.get(SessionRow, sid)
            row.variant_id = "no_such_variant_xyz"
            db.commit()
        finally:
            db.close()
        r = h.post(f"/api/v2/sessions/{sid}/turns/stream",
                   json={"text": "halo?"}, headers=headers)
        assert r.status_code == 422, (r.status_code, r.text[:200])


def test_stale_frozen_revision_conflicts():
    from app.database import SessionLocal
    from app.domains.sessions.models import SessionRow
    from app.main import app

    with TestClient(app) as h:
        sid, headers = _mk_session(h, "fam_dengue")
        db = SessionLocal()
        try:
            row = db.get(SessionRow, sid)
            row.variant_canonical_hash = "tampered-hash"
            db.commit()
        finally:
            db.close()
        r = h.post(f"/api/v2/sessions/{sid}/turns/stream",
                   json={"text": "halo?"}, headers=headers)
        assert r.status_code == 409, (r.status_code, r.text[:200])


def test_mixed_judge_load_keeps_chat_flowing(monkeypatch):
    from app.main import app

    _slow_v3(monkeypatch, delay=0.05, chunks=4)
    with TestClient(app) as h:
        sid, headers = _mk_session(h)
        sid2, headers2 = _mk_session(h, "em_anaphylaxis_001")
        h.post(f"/api/v2/sessions/{sid2}/turns", json={"text": "halo?"},
               headers=headers2)
        dt, results, errors = _run_streams(h, sid, headers, 5)
        r = h.post(f"/api/v2/sessions/{sid2}/score",
                   json={"ddx": {}, "management": {}}, headers=headers2)
        assert r.status_code == 200, r.text[:200]
        assert not errors
        assert all(s == 200 for s, _ in results)



def test_upstream_closed_on_cancel():
    """Cancellation propagates down the bridge chain to the provider
    stream (no dangling upstream connection)."""
    import asyncio
    from types import SimpleNamespace

    import app.rag.llm as llm_mod
    from app.rag import engine_v3

    closed = []

    class RecStream:
        def __aiter__(self):
            return self._gen()

        async def _gen(self):
            yield "a "

        async def aclose(self):
            closed.append(True)

    class C:
        def astream(self, *a, **k):
            async def gen():
                st = RecStream()
                try:
                    async for c in st:
                        yield c
                finally:
                    await st.aclose()

            return gen()

    llm_mod._async_client = C()
    try:
        from pipeline.case_v3.loader import default_registry

        v = default_registry().variants["dengue_001_mild"]

        async def go():
            it = engine_v3.astream_respond(v, [], "hi?")
            assert (await it.__anext__()) == "a "
            await it.aclose()

        asyncio.run(go())
    finally:
        llm_mod._async_client = None
    assert closed == [True]
