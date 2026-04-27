#!/usr/bin/env python3
"""Render the Phase 4 summary tables (markdown) for SESSION_STATE.md.

Reads the judge JSONs for the new experiments + the existing scaling results
and prints two markdown tables: Phase 1 (interpret rubric, pinned 64) and
Phase 2 (methods rubric, 28 pairs).
"""

import argparse
import json
import os
import statistics

ROOT = "/fs1/scratch/tathadbn/biolite-suite"
INTERPRET_RES = f"{ROOT}/biolite-interpret/evaluation/results"
METHODS_RES = f"{ROOT}/biolite-methods/evaluation/results"
PINNED_FILE = f"{ROOT}/biolite-interpret/evaluation/pinned_64_indices.json"

with open(PINNED_FILE) as f:
    PINNED = set(json.load(f)["pinned_indices"])


def load_means(path: str, criteria: list, filter_to_pinned: bool = False):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    per_idx = {}
    for r in data["individual_results"]:
        idx = r["index"]
        if filter_to_pinned and idx not in PINNED:
            continue
        scores = {}
        for c, s in r.get("scores", {}).items():
            if isinstance(s, dict) and isinstance(s.get("score"), (int, float)):
                scores[c] = s["score"]
        per_idx[idx] = scores

    out = {"n": len(per_idx)}
    for c in criteria:
        vals = [s.get(c) for s in per_idx.values() if c in s]
        if vals:
            out[c] = round(statistics.mean(vals), 2)
        else:
            out[c] = None
    return out


def fmt_row(label: str, values: dict, criteria: list, n_expected=None) -> str:
    if values is None:
        cells = ["—"] * len(criteria) + ["—"]
        return f"| {label} | {' | '.join(cells)} |"
    cells = []
    for c in criteria:
        v = values.get(c)
        cells.append(f"{v:.2f}" if v is not None else "—")
    n_str = str(values.get("n", "?"))
    if n_expected is not None and values.get("n") != n_expected:
        n_str = f"{values['n']}/{n_expected}"
    cells.append(n_str)
    return f"| {label} | {' | '.join(cells)} |"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="Write markdown to this file in addition to stdout")
    args = ap.parse_args()

    p1_crit = ["biological_accuracy", "completeness", "clarity"]
    p2_crit = ["methodological_accuracy", "assumption_awareness",
               "tradeoff_discussion", "practical_helpfulness"]

    p1_rows = [
        ("Baseline 1B (existing)",
         load_means(f"{INTERPRET_RES}/judge_baseline.json", p1_crit), 64),
        ("FT 1B @ v2 (existing)",
         load_means(f"{INTERPRET_RES}/judge_finetuned_1b_v2.json", p1_crit, True), 64),
        ("FT 3B @ v2 (existing)",
         load_means(f"{INTERPRET_RES}/judge_finetuned_3b_v2.json", p1_crit, True), 64),
        ("3B 3-shot (NEW)",
         load_means(f"{INTERPRET_RES}/judge_3b_fewshot.json", p1_crit), 64),
        ("Claude Sonnet (NEW)",
         load_means(f"{INTERPRET_RES}/judge_claude_sonnet.json", p1_crit), 64),
        ("Claude Opus (NEW)",
         load_means(f"{INTERPRET_RES}/judge_claude_opus.json", p1_crit), 64),
    ]

    p2_rows = [
        ("Vanilla 1B (existing)",
         load_means(f"{METHODS_RES}/judge_vanilla.json", p2_crit), 28),
        ("DPO 1B-from-SFT (existing)",
         load_means(f"{METHODS_RES}/judge_dpo_1b_from_sft.json", p2_crit), 28),
        ("DPO 3B-from-SFT (existing)",
         load_means(f"{METHODS_RES}/judge_dpo_3b_from_sft.json", p2_crit), 28),
        ("Vanilla 3B + RAG (existing)",
         load_means(f"{METHODS_RES}/judge_vanilla_3b_rag.json", p2_crit), 28),
        ("DPO 3B + RAG (existing)",
         load_means(f"{METHODS_RES}/judge_dpo_3b_rag.json", p2_crit), 28),
        ("Claude Sonnet (NEW)",
         load_means(f"{METHODS_RES}/judge_claude_sonnet.json", p2_crit), 28),
        ("Claude Opus (NEW)",
         load_means(f"{METHODS_RES}/judge_claude_opus.json", p2_crit), 28),
    ]

    out_lines = []
    out_lines.append("## Phase 1 — interpret rubric (pinned 64 ex)\n")
    out_lines.append("| Model | bio_acc | completeness | clarity | n |")
    out_lines.append("|---|---|---|---|---|")
    for label, vals, n_exp in p1_rows:
        out_lines.append(fmt_row(label, vals, p1_crit, n_exp))
    out_lines.append("\n## Phase 2 — methods rubric (28 ex)\n")
    out_lines.append("| Model | method_acc | assumptions | tradeoffs | helpful | n |")
    out_lines.append("|---|---|---|---|---|---|")
    for label, vals, n_exp in p2_rows:
        out_lines.append(fmt_row(label, vals, p2_crit, n_exp))

    text = "\n".join(out_lines)
    print(text)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
