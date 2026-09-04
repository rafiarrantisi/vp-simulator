# FASE 8 — Unified Progress, Longitudinal Data & Readiness Engine

Canonical vocabulary for Result, Dashboard, Progress, Mentor (§36).
V3 sessions no longer under-count; historical raw reports never rewritten.

## What was built (additive, no live-contract break)

- `backend/pipeline/clinical_contracts/{versions,scoring_output}.py` (minimal
  restore): `OSCE_CORE_DOMAINS` (8), `V2_DIM_TO_CORE` / `V3_DIM_TO_CORE`,
  `QORA_LEARNING_DIMS`, version constants (`qora-score-1.0`).
- `backend/pipeline/progress/longitudinal.py` (Task A): `NormalizedSession`
  + `adapt_report` (V2 `overall/per_dimension` → `v2`; V3-compat same shape
  with `content_schema=new` → `v3_compat`; native `total/by_dimension` →
  `v3_native`, ratio-aware `_dim_pct`) + `adapt_session` (plain-dict row,
  OSCE iff mode ∈ {osce, osce_full}, variant/family backfill, no report →
  overall from `total_score`). Raw dicts never mutated.
- `backend/pipeline/progress/progress.py` (Task B): `compute_progress`
  (totalSessions = completed scored sessions; avg = plain mean, unscored
  excluded; skill = recency-weighted mean over last 20, linear rank weights,
  n<2 → low_evidence, excluded from strongest/weakest; coverage = explicit
  counts specialties/families/variants/distinctCases/osce vs practice;
  `recentImprovement` = mean(last3) − mean(prev3), needs ≥4 sessions) +
  `apply_progress_for_session` (pure, mirrors legacy `_record_progress`
  keys/streak/caps exactly; shared by V2 AND V3).
- `backend/pipeline/progress/readiness.py` (Tasks C/D/E): `compute_readiness`
  over normalized sessions. Components: proficiency (native-dim weights
  renormalized), coverage (domains/8, blend 0.10), safety (recent-window
  factor + hard cap 59 on last-3 trigger), consistency (days/span),
  trajectory (last-5 bonus 0.9–1.1), recency (≤7d 1.0, ≤30d 0.95, ≤60d
  0.9+stale, else 0.85+stale), integrated OSCE (0 OSCE → cap 74),
  evidence caps (n=1 → 59 Building, n=2 → 69), critical-error penalty
  (2/case, cap 10). Confidence: 0 → insufficient_data, <3 → low, ≥3 → low,
  ≥5 → medium, ≥10 → high (stale downgrades high→medium). State: No
  evidence / Building (n<3) / interpretation level otherwise. Every output
  carries `drivers`, `strengths/needs_work` (min-2-obs), `components`,
  `evidence`, `interpretation`. No `target 75%` emitted (no empirical basis).
- Wiring (`backend/app/domains/sessions/progress_adapter.py` + edits):
  `specialty_for_session` (V2 frontmatter / V3 family registry, never
  raises), `row_to_normalized`, `completed_normalized`,
  `record_progress_for_session`, `critical_errors_recent`.
  `v2_router._record_progress` → shared pure updater (same keys).
  `v3_compat_service.score` → records progress (was: 0 XP, invisible).
  `GET /api/v2/progress` → unified (legacy keys kept; additive: readiness,
  coverage, dataSource{engines,sessionsIncluded,excludedNoScore},
  dimensionDetail, strongest/weakestSkill, recentImprovement, definitions,
  hasEvidence). `mentor.get_readiness/readiness_report` → same engine as
  Dashboard (§36 parity; legacy keys kept). `complete_case` journey
  readiness → unified when evidence exists, else legacy average.

## Metric definitions (audited, §43)

- total_sessions: COMPLETED sessions with a stored report (all-time unless
  `window_days`). Started/abandoned/unscored never inflate; unscored counted
  in `excludedNoScore`.
- average score: mean of `overall_0_100` over scored sessions (V2 + V3-compat
  both examiner-style 0–100 → plain mean, documented).
- specialty coverage: explicit counts only (sessions/specialty, distinct
  families, distinct variants, distinct cases, osce vs practice). Never
  labelled mastery.
- skill score: recency-weighted mean per native dim, last 20, linear rank
  weights; dims with <2 observations flagged `low_evidence`, excluded from
  strongest/weakest.
- readiness: evidence model (see above). One excellent session → Building,
  capped 59. Many easy Practice → OSCE cap 74. Safety fail → cap 59.
  Stale → recency decay + confidence downgrade. No evidence → honest
  `insufficient_data` / `No evidence`, never a fake percentage.

## Evidence

- `backend/tests/test_fase8_unified_progress.py`: 22 passed (isolated
  sqlite, stub LLM) — adapter labels/immutability/fold/safety+OSCE;
  progress empty/mixed/min-evidence/parity; readiness none/one/many-mediocre/
  safety/practice-only/OSCE-heavy/stale/V2-band/V3-real/explainability;
  endpoints V2+V3 mix, cross-product parity, new-user empty, V3 lifecycle.
- Regression: `test_mentor.py` 20 passed (legacy readiness band preserved),
  `test_v2_runtime` + `test_phase_b_v3_compat` + `test_presentation_family_compat`
  green (V2 contract untouched, V3 facade intact).

## STOP / next (human-gated)

- Model stable, pipeline canonical, no generated files touched, no migration.
  Broader V3 rollout + adaptive Mentor may now proceed; judge calibration
  (FASE 7) stays the separate gate before any scoring cutover.
