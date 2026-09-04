"""FASE 12 — release-hardening acceptance mirror (plan §PHASE12).

Additive; isolated sqlite (conftest), stub LLM, no migration, no UX change.
Covers: request-id propagation + version-correlation headers, ops version/
readiness shapes without secrets, client-error intake gates + bounds,
rate-limiter eviction + start/pf coverage, flag snapshot safety, exception
envelope hygiene, and metadata-only log helpers.
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.shared import feature_flags, ratelimit

client = TestClient(app)


def _auth():
    email = f"ops12_{uuid.uuid4().hex[:8]}@t.co"
    client.post("/api/auth/signup", json={"email": email, "password": "secret12",
                                          "full_name": "Ops"})
    tok = client.post("/api/auth/login", json={"email": email, "password": "secret12"}
                      ).json()["data"]["token"]
    return {"Authorization": f"Bearer {tok}"}


def test_request_id_generated_and_version_headers_present():
    from pipeline.clinical_contracts.versions import (
        CLINICAL_CONTENT_VERSION,
        EVIDENCE_PACK_VERSION,
        SCORING_VERSION,
    )
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID")
    assert r.headers.get("X-Qora-Scoring-Version") == SCORING_VERSION
    assert r.headers.get("X-Qora-Evidence-Pack") == EVIDENCE_PACK_VERSION
    assert r.headers.get("X-Qora-Content-Version") == CLINICAL_CONTENT_VERSION


def test_request_id_propagated_when_client_supplied():
    r = client.get("/health", headers={"X-Request-ID": "ci-probe-123"})
    assert r.headers.get("X-Request-ID") == "ci-probe-123"


def test_version_headers_on_error_responses():
    from pipeline.clinical_contracts.versions import SCORING_VERSION
    r = client.get("/api/users/me")
    assert r.status_code == 401
    assert r.headers.get("X-Request-ID")
    assert r.headers.get("X-Qora-Scoring-Version") == SCORING_VERSION


def test_ops_version_shape_and_no_secrets():
    import json
    r = client.get("/api/ops/version")
    assert r.status_code == 200
    d = r.json()["data"]
    from pipeline.clinical_contracts.versions import (
        CLINICAL_CONTENT_VERSION,
        EVIDENCE_PACK_VERSION,
        SCORING_VERSION,
    )
    assert d["scoring_version"] == SCORING_VERSION
    assert d["evidence_pack_version"] == EVIDENCE_PACK_VERSION
    assert d["clinical_content_version"] == CLINICAL_CONTENT_VERSION
    assert d["flags"]["content_engine"] in ("v2", "v3_compat")
    assert d["flags"]["judge_live"] == "v2"
    blob = json.dumps(d).lower()
    for banned in ("api_key", "secret", "password", "midtrans", "xendit",
                   "token", "@", "bearer", "hash"):
        assert banned not in blob, f"secret-like token leaked: {banned}"


def test_ops_readiness_shape_and_no_secrets():
    import json
    r = client.get("/api/ops/readiness")
    assert r.status_code == 200
    d = r.json()["data"]
    assert isinstance(d["ready"], bool)
    for k in ("db", "uploads", "catalog", "llm"):
        assert k in d["checks"]
    assert d["checks"]["ok"]["db"] is True
    assert d["checks"]["catalog"]["v2_cases"] >= 1
    assert d["checks"]["llm"]["configured"] is False
    blob = json.dumps(d).lower()
    for banned in ("api_key", "secret", "password", "sk-", "xendit", "midtrans"):
        assert banned not in blob, f"secret-like token leaked: {banned}"


def test_client_errors_requires_auth():
    r = client.post("/api/ops/client-errors",
                    json={"screen": "dashboard", "message": "boom"})
    assert r.status_code == 401


def test_client_errors_validation_bounds():
    import pydantic
    import pytest
    from app.domains.ops.router import ClientErrorIn, _strip_query
    with pytest.raises(pydantic.ValidationError):
        ClientErrorIn(screen="x" * 81, message="m")
    with pytest.raises(pydantic.ValidationError):
        ClientErrorIn(screen="s", message="m" * 1001)
    ok = ClientErrorIn(screen="result", message="TypeError: x is null",
                       url="/result?token=abc#frag")
    assert ok.screen == "result"
    assert _strip_query("/result?token=abc") == "/result"
    assert _strip_query("/result#frag") == "/result"
    assert _strip_query("") == ""


def test_client_errors_happy_path_authenticated():
    H = _auth()
    r = client.post("/api/ops/client-errors",
                    json={"screen": "result", "message": "white screen on iOS",
                          "url": "/result"},
                    headers=H)
    assert r.status_code == 200
    assert r.json()["data"]["received"] is True
    r2 = client.post("/api/ops/client-errors",
                     json={"screen": "s", "message": "m" * 1001}, headers=H)
    assert r2.status_code == 422


def test_ratelimit_table_bounded_by_eviction():
    import time
    ratelimit._hits.clear()
    old = time.time() - 3600
    for i in range(ratelimit._MAX_BUCKETS + 100):
        ratelimit._hits[("auth", f"stale-{i}")] = [old]
    assert ratelimit._check("auth", "fresh-probe", 20, 60) is True
    assert len(ratelimit._hits) <= ((ratelimit._MAX_BUCKETS // 2) + 8)


def test_session_start_and_pf_are_rate_limited_routes():
    """Phase 12 audit: start/pf (incl. compat branches) must carry the AI
    bucket. Inspected at route level so future refactors can't silently
    drop the dependency."""
    from app.domains.sessions import v2_router, v3_router
    ai_dep_names = set()
    for mod in (v2_router, v3_router):
        for route in mod.router.routes:
            deps = getattr(route, "dependencies", []) or []
            if deps and route.path in ("/api/v2/sessions",
                                       "/api/v2/sessions/{session_id}/pf",
                                       "/api/v3/sessions",
                                       "/api/v3/another-patient"):
                ai_dep_names.add(route.path)
    assert ai_dep_names == frozenset({"/api/v2/sessions",
                                      "/api/v2/sessions/{session_id}/pf",
                                      "/api/v3/sessions",
                                      "/api/v3/another-patient"})


def test_flag_snapshot_safe_defaults():
    import json
    snap = feature_flags.snapshot()
    assert snap["content_engine"] == "v2"
    assert snap["judge_live"] == "v2"
    assert snap["mentor_v1_enabled"] is True
    blob = json.dumps(snap).lower()
    for banned in ("api_key", "secret", "password", "token", "@"):
        assert banned not in blob


def test_flag_snapshot_unknown_values_fall_back_safe():
    from app.config import Settings
    st = Settings(case_content_engine="bogus", judge_engine="skynet")
    snap = feature_flags.snapshot(st)
    assert snap["content_engine"] == "v2"
    assert snap["judge_engine"] == "v2"


def test_unhandled_exception_envelope_has_ref_and_no_traceback():
    import asyncio
    import json as _json
    from fastapi import Request
    from app.main import _unhandled_exception_handler
    scope = {"type": "http", "method": "GET", "path": "/api/v2/cases",
             "headers": [], "query_string": b""}
    req = Request(scope)
    req.state.request_id = "probe-ref-1"
    resp = asyncio.get_event_loop().run_until_complete(
        _unhandled_exception_handler(req, RuntimeError("kaboom-secret")))
    assert resp.status_code == 500
    body = _json.loads(resp.body)
    assert body["success"] is False
    assert "kaboom" in body["error"]
    assert "traceback" not in _json.dumps(body).lower()


def test_llm_judge_log_helpers_accept_no_content():
    import inspect
    from app.shared import observability
    for fn in (observability.log_llm_event, observability.log_judge_event):
        params = set(inspect.signature(fn).parameters)
        for banned in ("prompt", "completion", "text", "answer", "rubric",
                       "feedback", "transcript", "body"):
            assert banned not in params, f"{fn} accepts {banned}"
    observability.log_llm_event(role="judge", outcome="timeout", session_id="s1",
                                model="m", error="TimeoutError")
    observability.log_judge_event(engine="v2", outcome="ok", session_id="s1",
                                  content_schema="legacy", scoring_version="qora-score-1.0")
