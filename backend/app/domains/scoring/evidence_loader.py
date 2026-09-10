"""Phase PNPK-4 — digest-pinned local evidence loader (brief §7.7, §9).

Loads compiled packs from `build/evidence/<sha256>.json` by digest only
(never by "latest"). Validates filename digest, payload digest, schema
version, scoring compatibility, and pack identity. Bounded per-worker cache
(digest -> pack, small pilot packs). No network, no PDF parsing, no LLM.

Unapproved/draft content can never load: only compiled release packs exist
under build/evidence/, and the loader refuses anything else.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline.clinical_contracts.evidence_clinical import PACK_SCHEMA_VERSION

# Emitted packs live at the repo root `build/evidence/` (where the
# compiler emits them): parents of this file are scoring/domains/app/
# backend/repo-root, hence parents[4]. Overridable via QORA_EVIDENCE_DIR.
DEFAULT_DIR = Path(__file__).resolve().parents[4] / "build" / "evidence"

_cache: dict[str, dict] = {}
_cache_order: list[str] = []
_CACHE_CAP = 8


class PackLoadError(Exception):
    pass


def _digest_of(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def load_pack(pack_sha256: str, *, evidence_dir: Path | None = None,
              expected_scoring: str | None = None) -> dict:
    """Load + validate a compiled pack. Raises PackLoadError (fail closed)."""
    if not pack_sha256 or len(pack_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in pack_sha256):
        raise PackLoadError("bad pack digest")
    # Always (re)read + verify bytes (cheap for small packs): a substituted
    # file must fail even when the digest was cached before.
    root = Path(evidence_dir) if evidence_dir else DEFAULT_DIR
    path = root / f"{pack_sha256}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise PackLoadError(f"unreadable pack {pack_sha256[:12]}: {e}")
    if not isinstance(payload, dict):
        raise PackLoadError("pack payload not an object")
    # Always re-verify bytes (cheap for small packs): a substituted file
    # must fail even when the digest is cached.
    recomputed = _digest_of({k: v for k, v in payload.items()})
    if recomputed != pack_sha256:
        _cache.pop(pack_sha256, None)
        try:
            _cache_order.remove(pack_sha256)
        except ValueError:
            pass
        raise PackLoadError("pack digest mismatch")
    if payload.get("pack_schema_version") != PACK_SCHEMA_VERSION:
        raise PackLoadError(
            f"unsupported pack schema {payload.get('pack_schema_version')!r}")
    if expected_scoring:
        compat = payload.get("compatible_scoring_versions") or []
        if expected_scoring not in compat:
            raise PackLoadError("pack incompatible with scoring version")
    if len(_cache) >= _CACHE_CAP:
        _cache.pop(_cache_order.pop(0), None)
    _cache[pack_sha256] = payload
    _cache_order.append(pack_sha256)
    return payload


def clear_cache() -> None:
    _cache.clear()
    _cache_order.clear()


def resolve_binding(variant_id: str, canonical_hash: str, *,
                    evidence_dir: Path | None = None) -> dict | None:
    """Find the release binding for (variant, hash) in index.json.

    Returns None when unavailable (caller treats enrichment as unavailable —
    never latest-resolution, never raises for missing content).
    """
    root = Path(evidence_dir) if evidence_dir else DEFAULT_DIR
    try:
        index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    for b in index.get("bindings") or []:
        if not isinstance(b, dict):
            continue
        want = str(canonical_hash or "")
        have = str(b.get("canonical_hash") or "")
        # Bindings store the 16-hex sidecar prefix; callers may pass the
        # full canonical hash or the prefix. Compare on the prefix, but
        # never match an empty hash (fail closed -> unavailable).
        if b.get("variant_id") == variant_id and want and have and \
                want[:16] == have[:16]:
            return b
    return None
