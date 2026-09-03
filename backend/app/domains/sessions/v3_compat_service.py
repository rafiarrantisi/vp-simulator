"""Phase B — V3 compatibility service (backend facade).

Called from the V2 routing layer (`v2_router.py`) whenever a request resolves
to a V3 family / a session whose persisted `content_schema == 'new'`.

NOMENCLATURE: `content_schema` value `'new'` is the OFFICIAL, documented marker
for V3 content in this codebase (models.py: `legacy | new`). It is used
consistently by `v3_service.py` and `v3_router.py` (already shipped + read by
analytics/STEP-9 pilot). We deliberately KEEP `'new'` = V3 — renaming to 'v3'
would break existing `v3_router` filters (risky migration, no functional gain).
Do not "fix" this to 'v3'.

Everything here produces EXACT V2-compatible external shapes:
  start  -> {sessionId, caseId, mode, language, openingLine}
  resume -> {turns, case_id, language, status, opening_line}
  turn   -> {reply, audioUrl}            (fallback, non-stream)
  stream -> raw text/plain token stream
  pf     -> {findings, examined, available_areas}
  score  -> V2 `report` (answer_key, per_dimension, safety_gates, overall, ...)

Internally it drives the V3 runtime (SelectionPolicy -> ClinicalVariant ->
persona -> engine_v3) exactly like `v3_service`, and honors the SAME
immutability + billing + idempotency rules as V2 (no silent bypass).
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.domains.auth.models import User
from app.domains.sessions.models import SessionRow, SessionTurn
from app.domains.sessions.router import _history, _next_turn_no, _owned
from app.domains.sessions.v3_compat_schemas import (
    default_registry, family_type, variant_opening_line,
)
from pipeline.case_v3.loader import CaseRegistry
from pipeline.case_v3.persona import persona_from_constraints
from pipeline.case_v3.runtime import (
    SelectionPolicy, SelectionRequest, ScoreInput, VariantUnavailable,
    build_debrief, score_encounter,
)
from pipeline.case_v3.models import PersonaConstraints


# ── catalog (feature flag: v3_compat only) ────────────────────────────────
def library_cards(*, learner_stage: str = "koas") -> list[dict]:
    """V3 family cards in exact V2 CaseCard shape (Phase C adapter item)."""
    from app.domains.sessions.v3_compat_schemas import (
        family_to_card, family_variant_count,
    )
    reg = default_registry()
    out = []
    for fid, fam in reg.families.items():
        if fam.status in ("draft",):
            continue
        out.append(family_to_card(reg, fam, family_variant_count(reg, fam, learner_stage)))
    return out


# ── create ────────────────────────────────────────────────────────────────
def start(db: OrmSession, user: User, *, case_id: str, language: str) -> dict:
    """Create a V3-backed session from a V3 family public ref. Returns V2 DTO."""
    from pipeline.case_v3.models import SessionInstance  # noqa: F401
    from pipeline.case_v3.persona import build_session_instance
    from app.domains.billing import service as billing

    reg = default_registry()
    fam = reg.families.get(case_id)
    if fam is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"V3 family '{case_id}' not found")
    interaction_mode = family_type(fam)  # disease->targeted, presentation->blind

    gate = billing.can_start_session(db, user.id)
    if not gate["allowed"]:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={"reason": gate.get("reason"), "usage": gate.get("usage"),
                    "limit": gate.get("limit"),
                    "message": "Free session limit reached — upgrade to continue."})

    # select one eligible variant NOW (not on card click) — Phase E.
    # Presentation (blind) families resolve their curated cross-family refs;
    # disease families use the family-scoped policy. Either way an empty set
    # is a clear 404 — never a silent downgrade to a V2 patient.
    from app.domains.sessions.v3_compat_schemas import resolve_start_variants
    v = None
    entry_point = None
    reason = ""
    if fam.family_type.value == "presentation":
        cands = resolve_start_variants(reg, fam, "koas")
        if not cands:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                "No eligible variant for this family")
        v = cands[0]
        entry_point = f"presentation:{fam.id}"
        reason = f"presentation resolve: eligible={len(cands)}, seed=0"
    else:
        policy = SelectionPolicy(reg)
        try:
            result = policy.select(SelectionRequest(
                mode=interaction_mode, family_id=case_id,
                learner_stage="koas", seed=0))
        except VariantUnavailable:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                "No eligible variant for this family")
        v = result.variant
        entry_point = result.entry_point
        reason = result.reason

    constraints = PersonaConstraints(relationship="self",
                                     allow_name_generation=True,
                                     anxiety_level="range", verbosity="range")
    try:
        persona = persona_from_constraints(v, constraints, 0)
    except Exception:  # noqa: BLE001
        # Display-only fallback. Never carries the working diagnosis — the
        # engine already holds the variant truth, and in blind mode even a
        # server-side dx string is one refactor away from a client leak.
        persona = {"name": "", "occupation": "", "relationship": "self",
                   "chief_complaint": v.chief_complaint}
    build_session_instance(v, persona_seed=0, language=language,
                           learner_stage="koas", mode=interaction_mode,
                           entry_point=entry_point)

    # persist into the existing sessions table (content_schema='v3')
    s = SessionRow(
        user_id=user.id, institution_id=user.institution_id,
        case_id=case_id, mode=interaction_mode, status="active",
        language=language, content_schema="new",
        family_id=v.family_id, variant_id=v.id, persona_seed=0,
        persona=persona, learner_level="koas",
        interaction_mode=interaction_mode,
        competency_category=v.competency.category if v.competency else None,
        legacy_skdi_level=v.competency.legacy_level if v.competency else None,
        presentation_path=entry_point, selection_reason=reason,
        variant_canonical_hash=v.canonical_hash(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    try:
        billing.record_usage(db, user.id, "session_start", case_id)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()

    return {
        "sessionId": s.id,
        "caseId": case_id,
        "mode": s.mode,
        "language": s.language,
        "openingLine": variant_opening_line(v),
        "_contentSchema": "new",  # internal hint; V2 ignores unknown keys
    }


def _frozen_variant(db: OrmSession, s: SessionRow) -> tuple:
    """Load the frozen variant for a persisted session (no re-selection)."""
    if not s.variant_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "v3 session has no frozen variant")
    reg = default_registry()
    v = reg.variants.get(s.variant_id)
    if v is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"v3 variant '{s.variant_id}' not found")
    if s.variant_canonical_hash and s.variant_canonical_hash != v.canonical_hash():
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "session clinical truth changed since start; refusing")
    return reg, v


def _persona(s: SessionRow) -> dict | None:
    if not s.persona:
        return None
    if isinstance(s.persona, str):
        try:
            return json.loads(s.persona)
        except Exception:  # noqa: BLE001
            return None
    return dict(s.persona)


# ── resume / turns ────────────────────────────────────────────────────────
def get_turns(db: OrmSession, session_id: str, user: User) -> dict:
    s = _owned(db, session_id, user)
    _, v = _frozen_variant(db, s)
    return {
        "turns": _history(db, session_id),
        "case_id": s.case_id,
        "language": s.language,
        "status": s.status,
        "opening_line": variant_opening_line(v),
    }


def turn(db: OrmSession, user: User, session_id: str, text: str,
         input_type: str = "text") -> dict:
    """Non-stream fallback patient turn (exact V2 `{reply, audioUrl}`)."""
    from app.rag.engine_v3 import respond as v3_respond
    from app.domains.billing import service as billing
    s = _owned(db, session_id, user)
    _, v = _frozen_variant(db, s)
    history = _history(db, session_id)
    n = _next_turn_no(db, session_id)
    db.add(SessionTurn(session_id=s.id, turn_number=n, role="user",
                       content=text, input_type=input_type))
    try:
        reply = v3_respond(v, history, text, language=s.language or "en",
                           persona=_persona(s))
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"patient LLM failed: {e}")
    db.add(SessionTurn(session_id=s.id, turn_number=n + 1, role="patient",
                       content=reply))
    db.commit()
    try:
        tokens_in = (sum(len(h.get("content") or "") for h in history) + len(text)) // 4
        billing.record_session_cost(db, s.id, user.id, tokens_in, len(reply) // 4)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
    return {"reply": reply, "audioUrl": None}


def stream_turn(db: OrmSession, user: User, session_id: str, text: str,
                input_type: str = "text") -> Iterator[str]:
    """Token-by-token raw text/plain stream (exact V2 streaming contract)."""
    from app.rag.engine_v3 import stream_respond as v3_stream
    from app.domains.billing import service as billing
    s = _owned(db, session_id, user)
    _, v = _frozen_variant(db, s)
    history = _history(db, session_id)
    n = _next_turn_no(db, session_id)
    user_id = user.id
    sid = s.id
    lang = s.language or "en"
    persona = _persona(s)
    # persist the user turn before streaming (mirror v2)
    db.add(SessionTurn(session_id=s.id, turn_number=n, role="user",
                       content=text, input_type=input_type))
    db.commit()

    def gen() -> Iterator[str]:
        parts: list[str] = []
        try:
            for chunk in v3_stream(v, history, text, language=lang, persona=persona):
                if chunk:
                    parts.append(chunk)
                    yield chunk
        except Exception as e:  # noqa: BLE001
            yield f"(error: patient LLM failed — {(getattr(e, 'message', None) or e)})"
            return
        reply = "".join(parts).strip()
        from app.database import SessionLocal
        db2 = SessionLocal()
        try:
            db2.add(SessionTurn(session_id=sid, turn_number=n + 1,
                                role="patient", content=reply))
            db2.commit()
            tokens_in = (sum(len(h.get("content") or "") for h in history) + len(text)) // 4
            billing.record_session_cost(db2, sid, user_id, tokens_in, len(reply) // 4)
            db2.commit()
        except Exception:  # noqa: BLE001
            db2.rollback()
        finally:
            db2.close()

    return gen()


# ── physical exam ─────────────────────────────────────────────────────────
def pf(db: OrmSession, user: User, session_id: str, *,
       notes: str = "", areas: list[str] | None = None) -> dict:
    """Reveal ONLY the areas the student examined (isolation rule, V2 contract)."""
    s = _owned(db, session_id, user)
    _, v = _frozen_variant(db, s)
    system_findings = v.physical_exam.system_findings or {}
    # area key -> human label
    all_areas = {
        "general": "General appearance",
        "skin": "Skin",
        "head_neck": "Head & neck",
        "chest": "Chest",
        "abdomen": "Abdomen",
        "limbs": "Limbs",
        "neuro": "Neurological",
    }
    examined = [a for a in (areas or []) if a in system_findings]
    findings = {a: str(system_findings[a]) for a in examined}
    # always expose vitals + general appearance under 'general' if available
    if not findings and v.physical_exam.vitals:
        vitals_txt = "; ".join(
            f"{vt.name} {vt.value}{vt.unit.value if vt.unit else ''}"
            for vt in v.physical_exam.vitals if vt.value is not None)
        findings["general"] = (v.physical_exam.general_appearance or "") + (
            (" — " + vitals_txt) if vitals_txt else "")
        examined = ["general"]
    return {
        "findings": findings,
        "examined": examined,
        "available_areas": sorted(set(system_findings.keys()) | set(all_areas.keys())),
    }


# ── score (idempotent, V2 report shape) ───────────────────────────────────
def _map_v2_assessment_to_score(v, ddx: dict | None, management: dict | None) -> ScoreInput:
    dx = ""
    if isinstance(ddx, dict):
        dx = " ".join(str(x) for x in ddx.values() if x)
    collected = {}
    stabilization = None
    referral = None
    if isinstance(management, dict):
        collected["management_complete"] = bool(management.get("complete")
                                                or management.get("management"))
        stabilization = bool(management.get("stabilized")) if management.get("stabilized") is not None else None
        referral = bool(management.get("referral")) if management.get("referral") is not None else None
    return ScoreInput(variant=v, learner_stage="koas", collected_items=collected,
                      stabilized=stabilization, gave_referral=referral,
                      diagnosis_submitted=dx)


def score(db: OrmSession, user: User, session_id: str, *,
          ddx: dict | None = None, management: dict | None = None,
          mode: str | None = None, overtime: bool = False,
          pf_notes: str | None = None, pf_areas: list[str] | None = None) -> dict:
    """Score using the PERSISTED variant + the LLM judge over the REAL transcript.

    Mirrors `judge_v2.evaluate_v2`: the judge reads every question/answer (so a
    session with only 3 questions is scored honestly), produces per-item
    hit/miss with evidence, honest per-dimension scores, safety gates and a
    narrative examiner summary. Idempotent (returns stored report on retry).
    """
    from app.rag.judge_v3 import evaluate_v3
    from app.domains.billing import service as billing
    s = _owned(db, session_id, user)
    if s.status == "completed" and s.report:
        return s.report
    _, v = _frozen_variant(db, s)
    transcript = _history(db, session_id)
    is_osce = (mode or "").lower() == "osce"
    judge = evaluate_v3(
        v, transcript, learner_stage=s.learner_level or "koas",
        ddx=ddx, management=management,
        pf_notes=pf_notes, pf_areas=pf_areas, with_pf=is_osce)
    # deterministic safety-gate complement (rule 3: red-flags/urgency)
    inp = _map_v2_assessment_to_score(v, ddx, management)
    try:
        det = score_encounter(inp)
    except Exception:  # noqa: BLE001
        det = None
    debrief = build_debrief(v, score=det, family_title=v.family_id)

    # V2 answer key + per_item overlay (QV2Result consumes these)
    ak = _v2_answer_key(v)
    judge_per_item = judge.get("per_item") or []
    ak_per_item = _v2_per_item(v, det) if det else []
    merged_per_item = _merge_per_item(ak, judge_per_item, ak_per_item)

    report = {
        "overall": int(round(judge.get("overall", 0) or 0)),
        "score": judge.get("overall_raw", 0) or 0,
        "max_score": judge.get("max_score", 100) or 100,
        "per_dimension": judge.get("per_dimension") or {},
        "per_item": merged_per_item,
        "safety_gates": judge.get("safety_gates") or [],
        "summary": judge.get("summary") or "",   # narrative examiner paragraph
        "answer_key": ak,
        "debrief": debrief,
        "overtime_penalty": None,
        "schema": "new",
        "variantId": v.id,
        "familyId": v.family_id,
    }
    if not report["summary"]:
        # LLM unavailable / stub — honest deterministic fallback (no fake 100%)
        report["summary"] = _v2_summary(v, det, debrief) if det else \
            (f"Overall you scored {report['overall']}%. This session was scored "
             "without a live judge. Review the model answer below.")
    if overtime:
        report["overall"] = max(0, report["overall"] - 10)
        report["overtime_penalty"] = 10
    s.total_score = report["overall"]
    s.report = report
    s.status = "completed"
    if s.ended_at is None:
        s.ended_at = datetime.now(timezone.utc)
    db.commit()
    return report


def _merge_per_item(ak: dict, judge_items: list[dict], det_items: list[dict]) -> list[dict]:
    """Answer-key items overlaid with the judge's hit/miss status. Every item in
    the V2 answer key gets a status (judge's, else deterministic, else not_asked)."""
    out = []
    judge_map = {str(i.get("item", "")).lower(): i.get("status", "miss")
                 for i in judge_items if isinstance(i, dict)}
    det_map = {str(i.get("item", "")).lower(): i.get("status", "miss")
               for i in det_items if isinstance(i, dict)}
    # anamnesis checklist items + red flags
    for grp in (ak.get("anamnesis_checklist") or []):
        for it in (grp.get("items") or []):
            txt = str(it.get("item", "")).lower()
            status = judge_map.get(txt, det_map.get(txt, "not_asked"))
            out.append({"dimension": "info_gathering", "item": it.get("item", ""),
                        "status": status, "evidence": ""})
    for it in (ak.get("red_flags") or []):
        txt = str(it.get("item", "")).lower()
        status = judge_map.get(txt, det_map.get(txt, "not_asked"))
        out.append({"dimension": "management_safety", "item": it.get("item", ""),
                    "status": status, "evidence": ""})
    return out


def _dims_to_v2(by_dimension: dict) -> dict:
    """V3 by_dimension -> V2 per_dimension {name: {score, max, label}}."""
    out = {}
    for k, val in (by_dimension or {}).items():
        if isinstance(val, dict):
            out[k] = {"name": k, "score": val.get("score", 0),
                      "max": val.get("max", val.get("max_score", 0)),
                      "label": val.get("label", k)}
        else:
            out[k] = {"name": k, "score": val, "max": 0, "label": k}
    return out


# ── V2 answer_key adapter (§9/§I) — QV2Result consumes the V2 shape ───────
def _v2_answer_key(v) -> dict:
    """Translate a V3 ClinicalVariant into the EXACT V2 `answer_key` shape that
    `QV2Result` renders (anamnesis_checklist / red_flags / expected_ddx /
    investigations / management). This is the compatibility DTO — do NOT swap
    it for the V3-native answer key, or the V2 debrief UI breaks."""
    fm = v

    # working diagnosis + differentials
    dd = v.diagnostic or type("D", (), {"working_diagnosis": "", "differentials": [], "synonyms": []})()
    diffs = [d.name if isinstance(d, dict) else getattr(d, "name", str(d))
             for d in (getattr(dd, "differentials", None) or [])]
    working = getattr(dd, "working_diagnosis", "") or ""

    # anamnesis checklist from V3 history groups (group -> items)
    checklist = []
    for g in (getattr(v, "history", None) or []):
        items = []
        for f in (getattr(g, "facts", None) or []):
            items.append({
                "item": (getattr(f, "key", None) or "").replace("_", " ").strip() or str(getattr(f, "value", "")),
                "critical": False,
            })
        if items:
            checklist.append({"group": getattr(g, "name", "history").replace("_", " "),
                              "items": items})

    # red flags
    red = []
    for r in (getattr(v, "red_flags", None) or []):
        it = getattr(r, "fact", None) or str(r)
        red.append({"item": it, "critical": True})

    # investigations: appropriate vs inappropriate by appropriateness
    inv_ok, inv_no = [], []
    for i in (getattr(v, "investigations", None) or []):
        name = getattr(i, "name", None) or ""
        expected = getattr(i, "expected_result", None) or ""
        ap = getattr(i, "appropriateness", None)
        apv = getattr(ap, "value", ap) if ap is not None else "appropriate"
        entry = {"name": name, "expected": expected}
        (inv_ok if apv in ("appropriate",) else inv_no).append(entry)

    # management buckets
    mgmt = getattr(v, "management", None) or type("M", (), {})()
    def _arr(name):
        return [x for x in (getattr(mgmt, name, None) or [])]
    pharmacological = _arr("pharmacologic") or _arr("pharmacological")
    non_pharmacological = _arr("non_pharmacologic") or _arr("non_pharmacological")
    education_safety_netting = (_arr("education_safety_netting")
                                or _arr("education_netting") or [])

    return {
        "case_id": v.id,
        "presentation": _v2_presentation(v),
        "chief_complaint": v.chief_complaint or "",
        "anamnesis_checklist": checklist,
        "red_flags": red,
        "expected_ddx": {"working_diagnosis": working, "differentials": diffs},
        "investigations": {"appropriate": inv_ok, "inappropriate": inv_no},
        "management": {
            "pharmacological": pharmacological,
            "non_pharmacological": non_pharmacological,
            "education_safety_netting": education_safety_netting,
        },
    }


def _v2_summary(v, result, debrief) -> str:
    """Compose a V2-style examiner paragraph from the V3 score + debrief.
    Deterministic (no extra LLM token spend). QV2Result renders this as the
    leading examiner verdict (report.summary)."""
    overall = result.total
    maxscore = result.max_score or 1.0
    pct = int(round((overall / maxscore) * 100))
    dx = (debrief.get("overall_summary") or {}).get("target_diagnosis", "") or \
        getattr(v.diagnostic, "working_diagnosis", "")

    # strongest / weakest dimension from by_dimension (score/max as pct)
    dim_pct = {}
    for k, val in (result.by_dimension or {}).items():
        if isinstance(val, dict):
            mx = val.get("max") or val.get("max_score") or 1.0
            dim_pct[k] = int(round((val.get("score", 0) / mx) * 100))
    dims_sorted = sorted(dim_pct.items(), key=lambda kv: kv[1], reverse=True)
    strong = dims_sorted[0] if dims_sorted else None
    weak = dims_sorted[-1] if len(dims_sorted) > 1 else None

    parts = []
    parts.append(f"Overall you scored {pct}%.")
    if dx:
        parts.append(f"The candidate's working diagnosis (case family '{v.family_id}') was assessed against {dx}.")
    if strong:
        sn = strong[0].replace("_", " ")
        parts.append(f"Your strongest area was {sn} ({strong[1]}%).")
    if weak:
        wn = weak[0].replace("_", " ")
        parts.append(f"Your weakest area was {wn} ({weak[1]}%) — review this and spend more time there next attempt.")
    else:
        parts.append("Keep practising the full history → diagnosis → management arc for consistency.")
    # safety flags -> explicit actionable feedback
    gates = result.safety_flags or []
    if gates:
        labels = []
        for g in gates:
            gv = g.get("gate") if isinstance(g, dict) else getattr(g, "gate", str(g))
            if gv:
                labels.append(str(gv).replace("_", " "))
        if labels:
            parts.append("⚠️ Safety concerns flagged: " + ", ".join(labels) +
                         ". Prioritize red-flag screening and urgent steps in OSCE conditions.")
    else:
        parts.append("No critical safety gate triggered — good red-flag awareness.")
    # management exposure
    labels2 = None
    if debrief and isinstance(debrief.get("management_review"), dict):
        labels2 = debrief.get("management_review")
    if labels2:
        mg = ", ".join(str(x) for x in (labels2 if isinstance(labels2, list) else labels2.keys()))
        parts.append("Management review: " + mg)

    return " ".join(parts)


def _v2_presentation(v) -> str:
    return v.blind_candidate_brief or v.chief_complaint or (
        v.targeted_title or v.family_id)


def _v2_per_item(v, result) -> list[dict]:
    """Derive a V2 `per_item` overlay from the V3 score so answer-key item rows
    show hit/partial/miss. Best-effort: from safety_flags + score dimensions."""
    # mark critical red-flag misses as 'miss'
    items = []
    flags = set()
    for f in (result.safety_flags or []):
        g = f.get("gate") if isinstance(f, dict) else getattr(f, "gate", None)
        if g:
            flags.add(g)
    for r in (getattr(v, "red_flags", None) or []):
        it = getattr(r, "fact", None) or str(r)
        items.append({"item": it, "status": "miss" if flags else "not_asked"})
    return items