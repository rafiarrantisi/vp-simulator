"""Schema-v2 case catalog (pivot-v4 §8.1) — loads English multi-specialty cases
from `content/cases/`. Read-only; only lint-clean cases are served. Summaries
NEVER include Part A scoring ground truth (no leakage to the catalogue)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from pipeline.case_v2 import CaseV2, lint, parse_case_v2


def _dir() -> Path:
    return Path(get_settings().content_cases_dir)


def load_v2_case(case_id: str) -> CaseV2:
    fp = _dir() / f"{case_id}.md"
    if not fp.exists():
        raise FileNotFoundError(case_id)
    return parse_case_v2(fp)


@lru_cache(maxsize=8)
def _catalog_cached(specialty: str | None, published_only: bool) -> tuple[CaseV2, ...]:
    """Catalog parses 82+ markdown files — cache by (specialty, published_only).

    v0.16.1: sebelumnya parse ulang SEMUA file per request (~2s + 2x per call
    via specialties_present) -> bottleneck concurrency. Kasus berubah hanya
    saat deploy (backend restart) → lru_cache aman. CaseV2 read-only di path
    catalog (summary/lint tidak memutasi).
    """
    out: list[CaseV2] = []
    for fp in sorted(_dir().glob("*.md")):
        try:
            c = parse_case_v2(fp)
        except Exception:  # noqa: BLE001 — a broken file must not break the catalogue
            continue
        if not lint(c).ok:
            continue
        if specialty and c.frontmatter.get("specialty") != specialty:
            continue
        if published_only and c.frontmatter.get("status") != "published":
            continue
        out.append(c)
    return tuple(out)


def list_v2_cases(*, specialty: str | None = None, published_only: bool = False) -> list[CaseV2]:
    return list(_catalog_cached(specialty, published_only))


def summary(c: CaseV2) -> dict:
    """Catalogue card — metadata only, no Part A scoring content."""
    fm = c.frontmatter
    return {
        "id": c.id,
        "specialty": fm.get("specialty"),
        "system": fm.get("system"),
        "presentation": fm.get("presentation"),
        "presentation_id": fm.get("presentation_id"),
        "first_impression": fm.get("first_impression"),
        "first_impression_id": fm.get("first_impression_id"),
        "target_condition": fm.get("target_condition"),
        "difficulty": fm.get("difficulty"),
        "mode": fm.get("mode_default"),
        "estimated_minutes": fm.get("estimated_minutes"),
        "status": fm.get("status"),
        "chief_complaint": fm.get("chief_complaint"),
    }


@lru_cache(maxsize=1)
def specialties_present() -> list[str]:
    return sorted({c.frontmatter.get("specialty") for c in _catalog_cached(None, False) if c.frontmatter.get("specialty")})
