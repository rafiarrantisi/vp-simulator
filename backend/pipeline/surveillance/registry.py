"""Phase 11 Task A — watched-source registry (plan §30–31, Phase 11-A).

Authoritative sources Qora monitors, by tier:

- Tier 0 — competency scope: KKI / SKD Dokter Indonesia.
- Tier 1 — national guidance + societies: Kemenkes PNPK, PAPDI, IDAI, PERKI.
- Tier 2 — formulary context ONLY: Farmalkes / e-Fornas. A formulary source
  MUST NOT claim disease-management truth (Fornas isolation — enforced in
  validate_registry, diff severity caps, and impact mapping).
- Tier 3 — international: WHO, NICE, GINA, relevant societies. International
  updates are stored as accepted alternatives / review signals; they NEVER
  auto-override local (Tier 0–1) guidance — a clinical reviewer decides
  Indonesia applicability, resources, GP scope and exam relevance.

Seed honesty: organization homepages are real; version/date/hash baselines
are the last-known snapshot and MUST be confirmed by a human on first run
(review_state per target; default 'unverified-seed' unless stated).
Pure data layer: stdlib only, no app/DB/network/LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

TIERS = frozenset({"0", "1", "2", "3"})

SOURCE_KINDS = frozenset({"guideline", "formulary", "competency", "international", "society"})

CLAIM_AREAS = frozenset({
    "history", "physical_exam", "investigations", "diagnosis",
    "management", "medications", "safety", "communication",
})

_CHANGE_KINDS = frozenset({
    "no_change", "new_version", "focused_update", "superseded", "effective_date_change",
})


@dataclass
class SurveillanceTarget:
    """One watched source document/series (metadata only — never content)."""

    target_id: str = ""
    title: str = ""
    organization: str = ""
    tier: str = "1"
    kind: str = "guideline"
    current_version: str = ""
    revision_hash: str = ""
    publication_date: str = ""
    effective_date: str = ""
    last_checked: str = ""
    source_url: str = ""
    superseded_date: str = ""
    watched_families: list = field(default_factory=list)
    claim_areas: list = field(default_factory=list)
    jurisdiction: str = "ID"
    review_state: str = "monitored"

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id, "title": self.title,
            "organization": self.organization, "tier": str(self.tier),
            "kind": self.kind, "current_version": self.current_version,
            "revision_hash": self.revision_hash,
            "publication_date": self.publication_date,
            "effective_date": self.effective_date,
            "last_checked": self.last_checked, "source_url": self.source_url,
            "superseded_date": self.superseded_date,
            "watched_families": list(self.watched_families or []),
            "claim_areas": list(self.claim_areas or []),
            "jurisdiction": self.jurisdiction, "review_state": self.review_state,
        }


def _is_iso_day(value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return False
    try:
        date(*map(int, value.split("-")))
        return True
    except ValueError:
        return False


def _as_targets(registry) -> list:
    if registry is None:
        return []
    if hasattr(registry, "targets"):
        try:
            return list(registry.targets)
        except TypeError:
            return []
    if isinstance(registry, dict):
        return list(registry.values())
    try:
        return list(registry)
    except TypeError:
        return []


def validate_registry(registry) -> tuple[list, list]:
    """Validate the watched-source registry.

    Returns (errors, normalized_targets). Empty errors == clean. Rules:
    non-empty; unique ids; required identity fields; tier/kind vocab;
    tracked version present; ISO dates; claim areas in vocab; Fornas
    isolation (formulary sources must not claim management).
    """
    targets = _as_targets(registry)
    if not targets:
        return (["surveillance registry is empty"], [])
    errors: list[str] = []
    seen: dict[str, int] = {}
    for t in targets:
        tid = getattr(t, "target_id", "") or ""
        if tid:
            seen[tid] = seen.get(tid, 0) + 1
    for tid, n in sorted(seen.items()):
        if n > 1:
            errors.append(f"duplicate target_id '{tid}' ({n} entries)")
    for t in targets:
        tid = getattr(t, "target_id", "") or "<missing-id>"
        if not getattr(t, "target_id", ""):
            errors.append("target missing target_id")
            continue
        if not (getattr(t, "title", "") or "").strip():
            errors.append(f"target '{tid}': missing title")
        if not (getattr(t, "organization", "") or "").strip():
            errors.append(f"target '{tid}': missing organization")
        if str(getattr(t, "tier", "")) not in TIERS:
            errors.append(f"target '{tid}': unknown tier '{getattr(t, 'tier', '')}'")
        if getattr(t, "kind", "") not in SOURCE_KINDS:
            errors.append(f"target '{tid}': unknown kind '{getattr(t, 'kind', '')}'")
        if not (getattr(t, "current_version", "") or "").strip():
            errors.append(f"target '{tid}': missing current_version")
        for f in ("publication_date", "effective_date", "last_checked", "superseded_date"):
            v = getattr(t, f, "") or ""
            if v and not _is_iso_day(v):
                errors.append(f"target '{tid}': {f} is not ISO YYYY-MM-DD ('{v}')")
        areas = getattr(t, "claim_areas", None) or []
        if not areas:
            errors.append(f"target '{tid}': missing claim_areas")
        else:
            unknown = [a for a in areas if a not in CLAIM_AREAS]
            if unknown:
                errors.append(f"target '{tid}': unknown claim_areas {unknown}")
            if getattr(t, "kind", "") == "formulary" and "management" in areas:
                errors.append(
                    f"target '{tid}': formulary (Fornas) source must not claim "
                    f"'management' as disease-management guidance")
    return (errors, targets)


def get_target(registry, target_id: str):
    """Return the target with this id, or None (never raises)."""
    try:
        for t in _as_targets(registry):
            if getattr(t, "target_id", None) == target_id:
                return t
    except Exception:
        return None
    return None


def default_surveillance_registry() -> list:
    """Seeded watchlist covering tiers 0–3 and every source class.

    Baselines are last-known snapshots for the watcher to compare against;
    a human confirms each on first operational run (review_state).
    """
    def t(**kw):
        kw.setdefault("review_state", "unverified-seed")
        return SurveillanceTarget(**kw)

    return [
        t(target_id="skd_dokter_2026", title="SKD Dokter Indonesia 2026",
          organization="KKI", tier="0", kind="competency",
          current_version="2026", revision_hash="skd2026-seed",
          publication_date="2025-01-01", effective_date="2025-01-01",
          source_url="https://kki.go.id",
          watched_families=[], claim_areas=["history", "diagnosis", "management"],
          jurisdiction="ID"),
        t(target_id="pnpk_dengue", title="PNPK Tata Laksana DBD",
          organization="Kemenkes", tier="1", kind="guideline",
          current_version="2023", revision_hash="pnpk-dbd-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://kemenkes.go.id",
          watched_families=["fam_dengue"], claim_areas=["management", "safety"],
          jurisdiction="ID"),
        t(target_id="pnpk_tb", title="PNPK Tuberkulosis",
          organization="Kemenkes", tier="1", kind="guideline",
          current_version="2023", revision_hash="pnpk-tb-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://kemenkes.go.id",
          watched_families=["fam_tb"], claim_areas=["management", "medications"],
          jurisdiction="ID"),
        t(target_id="papdi_im", title="PAPDI Panduan Praktik Penyakit Dalam",
          organization="PAPDI", tier="1", kind="society",
          current_version="2023", revision_hash="papdi-im-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://papdi.or.id",
          watched_families=["fam_dengue", "fam_typhoid"],
          claim_areas=["diagnosis", "management"],
          jurisdiction="ID"),
        t(target_id="idai_anak", title="IDAI Pedoman Pelayanan Anak",
          organization="IDAI", tier="1", kind="society",
          current_version="2023", revision_hash="idai-anak-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://idai.or.id",
          watched_families=["fam_child_pneumonia"],
          claim_areas=["diagnosis", "management"],
          jurisdiction="ID"),
        t(target_id="perki_kardio", title="PERKI Pedoman Kardiovaskular",
          organization="PERKI", tier="1", kind="society",
          current_version="2023", revision_hash="perki-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://inaheart.org",
          watched_families=["fam_hf"],
          claim_areas=["diagnosis", "management"],
          jurisdiction="ID"),
        t(target_id="fornas_farmalkes", title="Formularium Nasional (e-Fornas)",
          organization="Farmalkes Kemenkes", tier="2", kind="formulary",
          current_version="2023", revision_hash="fornas-2023-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://kemenkes.go.id",
          watched_families=[], claim_areas=["medications"],
          jurisdiction="ID"),
        t(target_id="who_dengue", title="WHO Guideline for Dengue",
          organization="WHO", tier="3", kind="international",
          current_version="2024", revision_hash="who-dengue-2024-seed",
          publication_date="2024-01-01", effective_date="2024-01-01",
          source_url="https://www.who.int",
          watched_families=["fam_dengue"], claim_areas=["management", "safety"],
          jurisdiction="global"),
        t(target_id="nice_uti", title="NICE Guideline: UTI",
          organization="NICE", tier="3", kind="international",
          current_version="NG109", revision_hash="nice-ng109-seed",
          publication_date="2023-01-01", effective_date="2023-01-01",
          source_url="https://www.nice.org.uk",
          watched_families=["fam_uti"], claim_areas=["diagnosis", "management"],
          jurisdiction="UK"),
        t(target_id="gina_asthma", title="GINA Asthma Strategy",
          organization="GINA", tier="3", kind="international",
          current_version="2024", revision_hash="gina-2024-seed",
          publication_date="2024-01-01", effective_date="2024-01-01",
          source_url="https://ginasthma.org",
          watched_families=["fam_asthma"], claim_areas=["diagnosis", "management"],
          jurisdiction="global"),
    ]
