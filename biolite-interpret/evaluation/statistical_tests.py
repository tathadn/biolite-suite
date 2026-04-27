#!/usr/bin/env python3
"""Paired Wilcoxon signed-rank tests across the judge-score files of both phases.

Phase 1 comparisons are aligned to the pinned-64 space — v2 judge files (n=126)
are filtered through pinned_64_indices.json to match v1/baseline judge files
(n≈64) so all Phase 1 tests use the same example denominator as the
SESSION_STATE.md scaling table.

Phase 2 comparisons are on the 28-example methods test set (no translation).

For each comparison: paired n, medians of A and B per criterion + overall
(mean across criteria), Wilcoxon statistic, p-value, and a `significant` flag
(p < 0.05). No multiple-comparison correction is applied; raw p-values are
reported and the comparison count is in the output.

Usage:
    python statistical_tests.py [--out PATH]
"""

import argparse
import json
import os
import statistics
import sys
from typing import Optional

try:
    from scipy.stats import wilcoxon
except ImportError:
    print("scipy is required. Install with: pip install scipy", file=sys.stderr)
    raise

ROOT = "/fs1/scratch/tathadbn/biolite-suite"
RESULTS_INTERPRET = f"{ROOT}/biolite-interpret/evaluation/results"
RESULTS_METHODS = f"{ROOT}/biolite-methods/evaluation/results"
PINNED_FILE = f"{ROOT}/biolite-interpret/evaluation/pinned_64_indices.json"

INTERPRET_CRITERIA = ["biological_accuracy", "completeness", "clarity"]
METHODS_CRITERIA = [
    "methodological_accuracy", "assumption_awareness",
    "tradeoff_discussion", "practical_helpfulness",
]

with open(PINNED_FILE) as f:
    PINNED = json.load(f)["pinned_indices"]


def load_judge(path: str, space: str) -> dict:
    """Return dict[logical_index] -> {criterion: score, ..., 'overall': mean}.

    space: 'pinned_64'   — file already indexes pinned 64 (k=0..63)
           'full_126'    — file indexes full v2 test (translate via PINNED)
           '28'          — file indexes the 28-ex methods test (k=0..27)
    """
    with open(path) as f:
        data = json.load(f)
    raw = {}
    for r in data["individual_results"]:
        idx = r["index"]
        crit_scores = {}
        for c, s in r.get("scores", {}).items():
            if isinstance(s, dict) and isinstance(s.get("score"), (int, float)):
                crit_scores[c] = s["score"]
        if crit_scores:
            crit_scores["overall"] = statistics.mean(crit_scores.values())
            raw[idx] = crit_scores

    if space == "full_126":
        translated = {}
        for k, full_idx in enumerate(PINNED):
            if full_idx in raw:
                translated[k] = raw[full_idx]
        return translated
    return raw


def paired_wilcoxon(a_scores: dict, b_scores: dict, criterion: str) -> dict:
    """Run Wilcoxon on paired (A, B) values; return summary dict."""
    common = sorted(
        k for k in (set(a_scores) & set(b_scores))
        if criterion in a_scores[k] and criterion in b_scores[k]
    )
    a = [a_scores[k][criterion] for k in common]
    b = [b_scores[k][criterion] for k in common]

    if len(a) < 2:
        return {"n": len(a), "median_a": None, "median_b": None,
                "mean_a": None, "mean_b": None, "statistic": None,
                "pvalue": None, "significant": False}

    diffs = [ai - bi for ai, bi in zip(a, b)]
    if all(d == 0 for d in diffs):
        return {"n": len(a),
                "median_a": statistics.median(a), "median_b": statistics.median(b),
                "mean_a": statistics.mean(a), "mean_b": statistics.mean(b),
                "statistic": 0.0, "pvalue": 1.0, "significant": False,
                "note": "all-zero diffs (identical scores)"}

    try:
        res = wilcoxon(a, b, zero_method="wilcox")
        stat = float(res.statistic)
        pvalue = float(res.pvalue)
    except ValueError as e:
        return {"n": len(a), "median_a": statistics.median(a),
                "median_b": statistics.median(b),
                "mean_a": statistics.mean(a), "mean_b": statistics.mean(b),
                "statistic": None, "pvalue": None, "significant": False,
                "note": f"wilcoxon failed: {e}"}

    return {"n": len(a),
            "median_a": statistics.median(a), "median_b": statistics.median(b),
            "mean_a": round(statistics.mean(a), 3),
            "mean_b": round(statistics.mean(b), 3),
            "statistic": round(stat, 3),
            "pvalue": pvalue,
            "significant": pvalue < 0.05}


COMPARISONS = [
    # phase, label, file_a, space_a, file_b, space_b, criteria_set
    ("phase1", "baseline-1B vs FT-1B-v2",
     "judge_baseline.json", "pinned_64",
     "judge_finetuned_1b_v2.json", "full_126", "interpret"),
    ("phase1", "FT-1B-v2 vs FT-3B-v2",
     "judge_finetuned_1b_v2.json", "full_126",
     "judge_finetuned_3b_v2.json", "full_126", "interpret"),
    ("phase1", "FT-3B-v1 (640) vs FT-3B-v2 (1262)",
     "judge_finetuned_3b.json", "pinned_64",
     "judge_finetuned_3b_v2.json", "full_126", "interpret"),
    ("phase2", "vanilla-1B vs DPO-1B-from-SFT",
     "judge_vanilla.json", "28",
     "judge_dpo_1b_from_sft.json", "28", "methods"),
    ("phase2", "DPO-1B-from-SFT vs DPO-3B-from-SFT",
     "judge_dpo_1b_from_sft.json", "28",
     "judge_dpo_3b_from_sft.json", "28", "methods"),
    ("phase2", "DPO-3B-from-SFT vs vanilla-3B+RAG",
     "judge_dpo_3b_from_sft.json", "28",
     "judge_vanilla_3b_rag.json", "28", "methods"),
    ("phase2", "vanilla-3B+RAG vs DPO-3B+RAG",
     "judge_vanilla_3b_rag.json", "28",
     "judge_dpo_3b_rag.json", "28", "methods"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=f"{RESULTS_INTERPRET}/statistical_tests.json")
    args = parser.parse_args()

    all_results = []
    for phase, label, fa, sa, fb, sb, criteria_set in COMPARISONS:
        results_dir = RESULTS_INTERPRET if phase == "phase1" else RESULTS_METHODS
        path_a = os.path.join(results_dir, fa)
        path_b = os.path.join(results_dir, fb)
        if not os.path.exists(path_a) or not os.path.exists(path_b):
            print(f"SKIP: {label} (missing file)")
            continue

        scores_a = load_judge(path_a, sa)
        scores_b = load_judge(path_b, sb)

        criteria = (INTERPRET_CRITERIA if criteria_set == "interpret"
                    else METHODS_CRITERIA) + ["overall"]

        per_criterion = {}
        for c in criteria:
            per_criterion[c] = paired_wilcoxon(scores_a, scores_b, c)

        all_results.append({
            "phase": phase,
            "comparison": label,
            "file_a": fa, "space_a": sa,
            "file_b": fb, "space_b": sb,
            "results": per_criterion,
        })

    # Print formatted table
    print(f"{'comparison':<42} {'criterion':<25} {'n':>3} "
          f"{'med_a':>6} {'med_b':>6} {'mean_a':>7} {'mean_b':>7} "
          f"{'p':>9} {'sig'}")
    print("-" * 115)
    for r in all_results:
        for c, s in r["results"].items():
            sig = "*" if s["significant"] else ""
            ma = f"{s['median_a']:.2f}" if s["median_a"] is not None else "NA"
            mb = f"{s['median_b']:.2f}" if s["median_b"] is not None else "NA"
            mna = f"{s['mean_a']:.2f}" if s["mean_a"] is not None else "NA"
            mnb = f"{s['mean_b']:.2f}" if s["mean_b"] is not None else "NA"
            p = f"{s['pvalue']:.4f}" if s["pvalue"] is not None else "NA"
            print(f"{r['comparison']:<42} {c:<25} {s['n']:>3} "
                  f"{ma:>6} {mb:>6} {mna:>7} {mnb:>7} {p:>9} {sig}")
        print()

    n_sig = sum(1 for r in all_results for s in r["results"].values()
                if s["significant"])
    n_total = sum(len(r["results"]) for r in all_results)
    print(f"\nSignificant at p<0.05: {n_sig}/{n_total} tests")
    print(f"({len(all_results)} comparisons; raw p-values, no Bonferroni correction)")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({
            "n_comparisons": len(all_results),
            "n_tests": n_total,
            "n_significant": n_sig,
            "alpha": 0.05,
            "test": "Wilcoxon signed-rank (paired, two-sided)",
            "comparisons": all_results,
        }, f, indent=2)
    print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()
