"""Run the release gate.

    python -m app.cli --baseline v1_production --candidate v2_candidate
    python -m app.cli --baseline v1_production --candidate v1_production   # PASS
    python -m app.cli ... --deepeval        # also run DeepEval custom metrics

Exits non-zero on FAIL so CI blocks the merge.
"""
from __future__ import annotations

import argparse
import sys

from .gate import decide
from .report import write_reports
from .runner import diff_cases, load_golden, run_prompt
from .storage import save_run
from .alert import notify_slack


def _run_deepeval(cases, baseline, candidate):
    from .deepeval_metrics import build_test_cases, SchemaValidityMetric, FieldAccuracyMetric
    from .prompts import load_prompt
    print("\n[DeepEval] running custom metrics on candidate...")
    tcs = build_test_cases(cases, load_prompt(candidate))
    metrics = [SchemaValidityMetric(), FieldAccuracyMetric()]
    for m in metrics:
        scores = [m.measure(tc) for tc in tcs]
        print(f"  {m.__name__}: mean={sum(scores)/len(scores):.3f} "
              f"pass={sum(m2.measure(tc) >= m2.threshold for m2 in [m] for tc in tcs)}/{len(tcs)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prompt Release Safety Gate")
    ap.add_argument("--baseline", default="v1_production")
    ap.add_argument("--candidate", default="v2_candidate")
    ap.add_argument("--deepeval", action="store_true")
    args = ap.parse_args()

    cases = load_golden()
    base = run_prompt(args.baseline, cases)
    cand = run_prompt(args.candidate, cases)
    decision = decide(base, cand)
    diff = diff_cases(base, cand)

    rep = write_reports(base, cand, decision, diff)
    save_run(base, cand, decision)
    sent = notify_slack(decision, args.baseline, args.candidate)

    print(rep["markdown"])
    print(f"\nReports: {rep['md_path']} , {rep['html_path']}")
    if sent:
        print("Slack alert sent.")
    if args.deepeval:
        _run_deepeval(cases, args.baseline, args.candidate)

    print(f"\nVERDICT: {decision.verdict}  (exit {decision.exit_code})")
    return decision.exit_code


if __name__ == "__main__":
    sys.exit(main())
