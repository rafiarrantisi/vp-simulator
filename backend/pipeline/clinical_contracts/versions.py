"""Phase 2 — single source of contract versions (minimal restore for FASE 8).

Full history lives in the oracle bytecode; this file restores the constants
the progress data-layer depends on. Pure constants, no I/O.
"""
from __future__ import annotations

EVIDENCE_PACK_VERSION = "1.0.0"
CLINICAL_CONTENT_VERSION = "v3.0"
SCORING_VERSION = "qora-score-1.0"
CONTRACT_DOC_VERSION = "1.0"

SCORING_VERSION_HISTORY = (SCORING_VERSION,)
EVIDENCE_PACK_VERSION_HISTORY = (EVIDENCE_PACK_VERSION,)


def parse_version(v: str) -> tuple:
    s = (v or "").strip()
    for prefix in ("qora-score-", "phase2-", "v", "V"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    parts: list = []
    for chunk in s.replace("-", ".").split("."):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.append(int(chunk) if chunk.isdigit() else chunk)
    return tuple(parts)


def is_compatible(a: str, b: str) -> bool:
    try:
        pa, pb = parse_version(a), parse_version(b)
        if not pa or not pb:
            return False
        return pa[0] == pb[0]
    except Exception:
        return False


def version_stamp() -> dict:
    return {
        "evidence_pack_version": EVIDENCE_PACK_VERSION,
        "clinical_content_version": CLINICAL_CONTENT_VERSION,
        "scoring_version": SCORING_VERSION,
        "contract_doc_version": CONTRACT_DOC_VERSION,
    }
