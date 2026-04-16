#!/usr/bin/env python3
"""
llm_judge.py — LLM-as-Judge evaluation using Claude Code CLI.

Uses `claude -p` with your Pro/Max subscription. No API key needed.

Supports both rubrics:
  - interpret: biological accuracy, completeness, clarity
  - methods: methodological accuracy, assumptions, trade-offs, helpfulness

Usage:
    python llm_judge.py \
        --predictions results/predictions.json \
        --rubric interpret \
        --output results/judge_scores.json

    # Use specific model:
    python llm_judge.py --predictions ... --rubric methods --model sonnet
"""

import argparse
import json
import os
import subprocess
import time
import re
from typing import Optional

RUBRICS = {
    "interpret": {
        "criteria": {
            "biological_accuracy": "Rate the biological accuracy. 1=factual errors, 3=mostly correct, 5=accurate gene functions and pathway associations.",
            "completeness": "Rate completeness. 1=mentions <30% of key findings, 3=covers major findings, 5=addresses all significant genes and caveats.",
            "clarity": "Rate clarity. 1=jargon-heavy or incoherent, 3=understandable but awkward, 5=clear and well-structured.",
        },
        "task_description": "interpreting bioinformatics results as natural language summaries",
    },
    "methods": {
        "criteria": {
            "methodological_accuracy": "Rate accuracy. 1=recommends wrong tools, 3=mostly correct, 5=accurate with proper caveats.",
            "assumption_awareness": "Rate assumption awareness. 1=ignores assumptions, 3=mentions some, 5=discusses all relevant assumptions.",
            "tradeoff_discussion": "Rate trade-off discussion. 1=single recommendation, 3=mentions alternatives, 5=substantive comparison.",
            "practical_helpfulness": "Rate helpfulness. 1=vague, 3=reasonable advice, 5=actionable and specific to constraints.",
        },
        "task_description": "answering bioinformatics methodology questions",
    },
}

JUDGE_PROMPT = """You are an expert bioinformatics reviewer. Evaluate this model output.

TASK: {task_description}

INPUT:
{input_text}

MODEL OUTPUT:
{prediction}

{reference_section}

Score each criterion 1-5 with a brief justification.

{criteria_text}

Respond ONLY in this exact JSON format, no other text:
{{
  {json_template}
}}"""


def call_claude_judge(prompt: str, model: str = "sonnet") -> Optional[dict]:
    """Call Claude Code CLI as judge."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--model", model,
        "--max-turns", "1",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=120, encoding="utf-8",
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        text = result.stdout.strip()

        # Extract JSON from response (handle markdown fences)
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        # Try to find JSON object in text
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            text = text[brace_start:brace_end]

        return json.loads(text)

    except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"  Parse/timeout error: {e}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def build_prompt(input_text, prediction, rubric_name, reference=None):
    rubric = RUBRICS[rubric_name]
    criteria_text = "\n".join(
        f"- {name}: {desc}" for name, desc in rubric["criteria"].items()
    )
    json_template = ",\n  ".join(
        f'"{name}": {{"score": <1-5>, "justification": "<brief>"}}'
        for name in rubric["criteria"]
    )
    ref_section = f"REFERENCE ANSWER:\n{reference}\n" if reference else ""

    return JUDGE_PROMPT.format(
        task_description=rubric["task_description"],
        input_text=input_text[:1500],
        prediction=prediction[:2000],
        reference_section=ref_section,
        criteria_text=criteria_text,
        json_template=json_template,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=str, required=True)
    parser.add_argument("--rubric", type=str, required=True, choices=["interpret", "methods"])
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, default="sonnet")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    with open(args.predictions) as f:
        predictions = json.load(f)

    print(f"Evaluating {len(predictions)} predictions")
    print(f"Rubric: {args.rubric} | Model: {args.model}")
    print(f"Using Claude Code CLI (subscription auth)\n")

    results = []
    for i, pred in enumerate(predictions):
        print(f"[{i+1}/{len(predictions)}] ", end="", flush=True)

        prompt = build_prompt(
            input_text=pred["input"],
            prediction=pred["prediction"],
            rubric_name=args.rubric,
            reference=pred.get("reference"),
        )

        scores = call_claude_judge(prompt, args.model)
        if scores:
            results.append({
                "index": i,
                "model": pred.get("model", "unknown"),
                "scores": scores,
            })
            score_vals = [s["score"] for s in scores.values() if isinstance(s, dict)]
            avg = sum(score_vals) / len(score_vals) if score_vals else 0
            print(f"avg={avg:.1f}")
        else:
            print("FAILED")

        time.sleep(args.delay)

    # Aggregate
    criteria = list(RUBRICS[args.rubric]["criteria"].keys())
    aggregates = {}
    for c in criteria:
        vals = [r["scores"][c]["score"] for r in results if c in r.get("scores", {})]
        if vals:
            import statistics
            aggregates[c] = {
                "mean": round(statistics.mean(vals), 2),
                "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0,
                "n": len(vals),
            }

    output_data = {
        "rubric": args.rubric,
        "model_used_as_judge": args.model,
        "n_evaluated": len(results),
        "aggregates": aggregates,
        "individual_results": results,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nAggregate scores:")
    for c, stats in aggregates.items():
        print(f"  {c}: {stats['mean']:.2f} ± {stats['std']:.2f} (n={stats['n']})")
    print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
