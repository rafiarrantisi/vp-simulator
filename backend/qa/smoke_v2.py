"""Manual smoke for the v2 runtime against the REAL model (pivot-v4).

Verifies the live pipeline on oph_dry_eye_001: (1) answer-restraint to a greeting,
(2) a complaint when asked, (3) a scored mini-session with the answer key.
Needs a real LLM_API_KEY; skips cleanly under StubLLM.

  python -m qa.smoke_v2
"""
from __future__ import annotations

from app.domains.cases.v2_catalog import load_v2_case
from app.rag import engine_v2
from app.rag.judge_v2 import evaluate_v2
from app.rag.llm import is_stub

CASE = "oph_dry_eye_001"


def main() -> int:
    if is_stub():
        print("StubLLM active (no LLM_API_KEY) — skipping live smoke.")
        return 0

    print("=" * 64)
    print(f"v2 live smoke · {CASE}")
    print("=" * 64)

    greet = engine_v2.respond(CASE, [], "Good morning, please have a seat.")
    print(f"\n[1] Greeting -> (should NOT dump symptoms)\n    {greet}")

    hist = [{"role": "user", "content": "Good morning"},
            {"role": "patient", "content": greet}]
    comp = engine_v2.respond(CASE, hist, "What brings you in today?")
    print(f"\n[2] 'What brings you in?' -> (one chief complaint)\n    {comp}")

    case = load_v2_case(CASE)
    transcript = hist + [{"role": "user", "content": "What brings you in today?"},
                         {"role": "patient", "content": comp}]
    report = evaluate_v2(case, transcript)
    dims = {k: v["score"] for k, v in report["per_dimension"].items()}
    print(f"\n[3] Score (short transcript) -> overall {report['overall']}/100")
    print(f"    per-dimension: {dims}")
    print(f"    answer-key working dx: {report['answer_key']['expected_ddx']['working_diagnosis']}")
    print(f"    answer-key red flags: {len(report['answer_key']['red_flags'])} items")
    print("\nOK — v2 runtime works against the real model.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
