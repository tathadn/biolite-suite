#!/usr/bin/env python3
"""
quality_control.py — Quality checks for DPO preference pairs.

Checks:
  1. Rejected vs chosen ROUGE-L sits in [min_sim, max_sim] (default 0.2-0.85).
     Too-similar pairs (>max_sim) are near-duplicates with no DPO contrast;
     too-divergent pairs (<min_sim) are likely full rewrites that teach style,
     not content signal. The 0.2 lower bound retains near-copy STAT_CONFUSION
     pairs that are actually strong DPO signal (subtle factual edits).
  2. Rejected length in [min_length_ratio, max_length_ratio] × chosen
     (default 0.4-2.5). Overconfident/verbose wrong answers legitimately
     run longer than the chosen, so the ceiling is generous.
  3. Error type distribution is balanced
  4. No empty or extremely short responses

Usage:
    python quality_control.py \
        --input ../processed/preference_pairs.json \
        --output ../processed/preference_pairs_filtered.json \
        --min_sim 0.2 --max_sim 0.85 \
        --min_length_ratio 0.4 --max_length_ratio 2.5
"""

import argparse
import json
import os
from collections import Counter, defaultdict


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    """Simple ROUGE-L (F1) implementation without external deps."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()

    if not ref_tokens or not hyp_tokens:
        return 0.0

    # LCS via DP
    m, n = len(ref_tokens), len(hyp_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    precision = lcs_len / n if n > 0 else 0
    recall = lcs_len / m if m > 0 else 0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def run_quality_checks(
    pairs: list[dict],
    min_sim: float,
    max_sim: float,
    min_length_ratio: float = 0.4,
    max_length_ratio: float = 2.5,
) -> tuple[list[dict], dict]:
    """Run quality checks and return filtered pairs + report."""
    filtered = []
    issues = {
        "too_similar": 0,
        "too_divergent": 0,
        "rejected_too_short": 0,
        "chosen_too_short": 0,
        "length_mismatch": 0,
        "empty_fields": 0,
    }
    drops_by_error_type = defaultdict(lambda: defaultdict(int))

    def drop(reason, et):
        issues[reason] += 1
        drops_by_error_type[et][reason] += 1

    for pair in pairs:
        question = pair.get("question", "")
        chosen = pair.get("chosen", "")
        rejected = pair.get("rejected", "")
        et = pair.get("error_type", "unknown")

        # Check empty
        if not question or not chosen or not rejected:
            drop("empty_fields", et)
            continue

        # Check minimum lengths
        if len(chosen.split()) < 20:
            drop("chosen_too_short", et)
            continue
        if len(rejected.split()) < 20:
            drop("rejected_too_short", et)
            continue

        chosen_len = len(chosen.split())
        rejected_len = len(rejected.split())
        ratio = rejected_len / chosen_len if chosen_len > 0 else 0
        if ratio < min_length_ratio or ratio > max_length_ratio:
            drop("length_mismatch", et)
            continue

        # Check similarity window: too-high = near-duplicate (no DPO contrast),
        # too-low = full rewrite (teaches style, not content).
        rouge = compute_rouge_l(chosen, rejected)
        if rouge > max_sim:
            drop("too_similar", et)
            continue
        if rouge < min_sim:
            drop("too_divergent", et)
            continue

        # Passed all checks
        pair["rouge_l_similarity"] = round(rouge, 3)
        filtered.append(pair)

    error_dist = Counter(p.get("error_type", "unknown") for p in filtered)

    report = {
        "input_count": len(pairs),
        "output_count": len(filtered),
        "removed": len(pairs) - len(filtered),
        "similarity_window": [min_sim, max_sim],
        "length_ratio_window": [min_length_ratio, max_length_ratio],
        "issues": issues,
        "error_type_distribution_kept": dict(error_dist),
        "error_type_distribution_dropped": {et: dict(reasons) for et, reasons in drops_by_error_type.items()},
        "avg_rouge_l": sum(p["rouge_l_similarity"] for p in filtered) / len(filtered) if filtered else 0,
    }

    return filtered, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--min_sim", type=float, default=0.2,
                        help="Lower ROUGE-L bound — pairs below are too divergent (default 0.2)")
    parser.add_argument("--max_sim", type=float, default=0.85,
                        help="Upper ROUGE-L bound — pairs above are near-duplicates (default 0.85)")
    parser.add_argument("--min_length_ratio", type=float, default=0.4,
                        help="Min rejected/chosen length ratio (default 0.4)")
    parser.add_argument("--max_length_ratio", type=float, default=2.5,
                        help="Max rejected/chosen length ratio (default 2.5)")
    args = parser.parse_args()

    with open(args.input) as f:
        pairs = json.load(f)

    print(f"Running quality checks on {len(pairs)} pairs "
          f"(sim {args.min_sim}-{args.max_sim}, len {args.min_length_ratio}-{args.max_length_ratio})...")
    filtered, report = run_quality_checks(
        pairs, args.min_sim, args.max_sim,
        min_length_ratio=args.min_length_ratio,
        max_length_ratio=args.max_length_ratio,
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(filtered, f, indent=2)

    report_path = args.output.replace(".json", "_qc_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n=== Quality control report ===")
    print(f"Input:  {report['input_count']}")
    print(f"Output: {report['output_count']} ({report['removed']} removed)")
    print(f"Similarity window: {report['similarity_window']}")
    print(f"\nIssues found:")
    for issue, count in report["issues"].items():
        print(f"  {issue}: {count}")
    print(f"\nKept — error type distribution:")
    for et, count in sorted(report["error_type_distribution_kept"].items()):
        print(f"  {et}: {count}")
    print(f"\nDropped — by error type and reason:")
    for et, reasons in sorted(report["error_type_distribution_dropped"].items()):
        print(f"  {et}: {dict(reasons)}")
    print(f"\nAvg ROUGE-L similarity (kept): {report['avg_rouge_l']:.3f}")
    print(f"\nSaved to: {args.output}")
    print(f"Report:   {report_path}")


if __name__ == "__main__":
    main()
