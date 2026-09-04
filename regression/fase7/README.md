# FASE 7 — Evidence-Locked Hybrid Clinical Judge (EXPERIMENTAL, STOP)

Live judges untouched: `judge_v2.evaluate_v2` + `judge_v3.evaluate_v3` remain the
only production paths. No router imports `scoring.hybrid` (pinned by test).
Do NOT globally replace until human calibration is acceptable.

## What was built (additive, deterministic, offline)

- `backend/app/domains/scoring/hybrid.py` (`hybrid_score/0.1`, `0.1-experimental`):
  UPR (transcript user-turns only + PF + investigations + dx/DDx + management/
  pharm/referral/education + overtime + mode + learner level), Evidence Ledger
  per rubric item (expected/observed/source/adjudication/score 0-3/reason,
  no-evidence→no-full-credit), robust ID/EN semantic (synonym/abbrev/typo/
  paraphrase/broad-vs-specific, never substring-alone + negation guard),
  deterministic arithmetic (item 0-3 × routine/important/critical/
  safety-critical × domain × learner weights, overtime −10, safety cap 40,
  LLM never computes), safety gates (shock/unsafe-discharge/no-stabilize/
  dangerous-drug/urgent-referral/contraindication/dangerous-procedure),
  hierarchical dx (exact+severity 3 > family 2 > broad 1 > wrong 0 >
  dangerous-miss 0+gate), management split (priority/stabilization/definitive/
  medication/monitoring/education/referral; late drug ≠ stabilize credit),
  stage-aware pharm detail (preclinical agent-concept; koas dose-gated only
  where truth specifies; Fornas never changes verdict), global rating
  Fail/Borderline/Pass/Superior AFTER scores and safety-capped (explicitly
  NOT BRM — BRM needs cohort/station + human examiners), ledger-only feedback
  composer (well/missed/reasoning/management/expectation/next, no hallucinated
  claims), `to_normalized()` into `contracts.NormalizedScore/1.0` + hybrid
  extension (stored reports never rewritten).
- Domain basis: 8 broad domains as starting point (Anamnesis, PE,
  Investigations/Procedures, Diagnosis & DDx, Non-Pharm, Pharm,
  Communication/Education, Professional Behavior), mapped from V2
  anamnesis/osce_full/classic + V3 learner-profile + contracts core.
  Indonesian OSCE refs = credible-background only; no old doc claimed as
  official-current without human verification.
- `backend/tests/test_hybrid_judge.py`: 15 passed — exact/paraphrase/vague/
  omitted/family-severity/wrong/intl-alternative/dose-detail/unsafe/
  checklist+gaming/verbose-vs-concise/ID-EN-mixed-abbrev-typo/overtime/
  arithmetic-shape + STOP-guard.
- `backend/data/reports/fase7_calibration.json`: fixture expectations, 8-case
  human subset request (domain score, pass/fail, safety agreement, FP credit,
  FN miss), STOP rule.

## Human next (doctors/clinical educators)

Grade the 8-case subset, compare domain score / pass-fail / safety / FP / FN.
Only on acceptable agreement: propose a flagged, reversible cutover (still
preserving V2 detail feedback + examiner summary + per-item UX).
