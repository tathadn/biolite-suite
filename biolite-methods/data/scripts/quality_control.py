#!/usr/bin/env python3
"""
quality_control.py — Quality checks for DPO preference pairs.

Checks:
  1. Rejected answers aren't too similar to chosen (ROUGE-L < 0.8)
  2. Rejected answers aren't too obviously wrong (length check)
  3. Error type distribution is balanced
  4. No empty or extremely short responses

Usage:
    python quality_control.py \
        --input ../processed/preference_pairs.json \
        --output ../processed/preference_pairs_filtered.json
"""

import argparse
import json
import os
from collections import Counter


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


def run_quality_checks(pairs: list[dict]) -> tuple[list[dict], dict]:
    """Run quality checks and return filtered pairs + report."""
    filtered = []
    issues = {
        "too_similar": 0,
        "rejected_too_short": 0,
        "chosen_too_short": 0,
        "length_mismatch": 0,
        "empty_fields": 0,
    }

    for pair in pairs:
        question = pair.get("question", "")
        chosen = pair.get("chosen", "")
        rejected = pair.get("rejected", "")

        # Check empty
        if not question or not chosen or not rejected:
            issues["empty_fields"] += 1
            continue

        # Check minimum lengths
        if len(chosen.split()) < 20:
            issues["chosen_too_short"] += 1
            continue
        if len(rejected.split()) < 20:
            issues["rejected_too_short"] += 1
            continue

        # Check similarity (reject if too similar — DPO needs contrast)
        rouge = compute_rouge_l(chosen, rejected)
        if rouge > 0.8:
            issues["too_similar"] += 1
            continue

        # Check length ratio (rejected should be ±50% of chosen length)
        chosen_len = len(chosen.split())
        rejected_len = len(rejected.split())
        ratio = rejected_len / chosen_len if chosen_len > 0 else 0
        if ratio < 0.5 or ratio > 2.0:
            issues["length_mismatch"] += 1
            continue

        # Passed all checks
        pair["rouge_l_similarity"] = round(rouge, 3)
        filtered.append(pair)

    # Error type distribution
    error_dist = Counter(p.get("error_type", "unknown") for p in filtered)

    report = {
        "input_count": len(pairs),
        "output_count": len(filtered),
        "removed": len(pairs) - len(filtered),
        "issues": issues,
        "error_type_distribution": dict(error_dist),
        "avg_rouge_l": sum(p["rouge_l_similarity"] for p in filtered) / len(filtered) if filtered else 0,
    }

    return filtered, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    with open(args.input) as f:
        pairs = json.load(f)

    print(f"Running quality checks on {len(pairs)} pairs...")
    filtered, report = run_quality_checks(pairs)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(filtered, f, indent=2)

    report_path = args.output.replace(".json", "_qc_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n=== Quality control report ===")
    print(f"Input:  {report['input_count']}")
    print(f"Output: {report['output_count']} ({report['removed']} removed)")
    print(f"\nIssues found:")
    for issue, count in report["issues"].items():
        print(f"  {issue}: {count}")
    print(f"\nError type distribution:")
    for et, count in sorted(report["error_type_distribution"].items()):
        print(f"  {et}: {count}")
    print(f"\nAvg ROUGE-L similarity: {report['avg_rouge_l']:.3f}")
    print(f"\nSaved to: {args.output}")
    print(f"Report:   {report_path}")


if __name__ == "__main__":
    main()
