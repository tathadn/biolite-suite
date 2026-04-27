#!/usr/bin/env python3
"""Claude upper-bound predictions via `claude -p`.

Establishes the API-model ceiling for each task by sending the same prompt the
local fine-tuned model receives to Claude Sonnet (subscription auth). Output
schema matches generate_predictions.py so llm_judge.py runs unchanged.

Usage:
    # Phase 1 (interpret), pinned 64 subset:
    python generate_claude_predictions.py \\
        --test_file ../data/splits/test.json \\
        --pinned_indices pinned_64_indices.json \\
        --phase interpret \\
        --output results/predictions_claude_sonnet.json

    # Phase 2 (methods), full 28:
    python generate_claude_predictions.py \\
        --test_file ../../biolite-methods/data/splits/test.json \\
        --phase methods \\
        --output ../../biolite-methods/evaluation/results/predictions_claude_sonnet.json
"""

import argparse
import json
import os
import subprocess
import time


def call_claude(question: str, model: str, timeout: int) -> str:
    cmd = [
        "claude", "-p", question,
        "--output-format", "text",
        "--model", model,
        "--max-turns", "1",
        "--tools", "",
    ]
    # Run from a clean directory so the project's CLAUDE.md / auto-memory does
    # not prime the model toward tool_use on short or ambiguous prompts.
    clean_cwd = os.environ.get("CLAUDE_CLEAN_CWD", "/tmp/claude_clean_dir")
    os.makedirs(clean_cwd, exist_ok=True)
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=timeout, encoding="utf-8",
        cwd=clean_cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude rc={result.returncode}: {result.stderr[:500]}")
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("empty stdout")
    return text


def build_record(ex: dict, phase: str) -> tuple[str, str, dict]:
    if phase == "interpret":
        instruction = ex.get("instruction", "")
        input_text = ex.get("input", "")
        question = f"{instruction}\n\n{input_text}" if input_text else instruction
        reference = ex.get("output", "")
        extra = {"task_type": ex.get("task_type", "")}
    else:
        question = ex["question"]
        reference = ex["chosen"]
        extra = {
            "category": ex.get("category", ""),
            "source": ex.get("source", ""),
        }
    return question, reference, extra


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--phase", choices=["interpret", "methods"], required=True)
    parser.add_argument("--pinned_indices", default=None,
                        help="JSON file with {'pinned_indices': [...]} (interpret only)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--model_name", default="claude-sonnet")
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max_retries", type=int, default=2)
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap number of examples (smoke test)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip indices already present in --output")
    args = parser.parse_args()

    with open(args.test_file) as f:
        test = json.load(f)

    if args.pinned_indices:
        with open(args.pinned_indices) as f:
            pinned = json.load(f)["pinned_indices"]
        test = [test[i] for i in pinned]
        print(f"Filtered to {len(test)} pinned examples")

    if args.limit:
        test = test[:args.limit]

    existing = []
    done_inputs = set()
    if args.resume and os.path.exists(args.output):
        with open(args.output) as f:
            existing = json.load(f)
        done_inputs = {r["input"] for r in existing}
        print(f"Resuming: {len(existing)} already done")

    print(f"Generating {len(test)} predictions via claude -p --model {args.model}")

    predictions = list(existing)
    failures = 0
    start = time.time()
    for i, ex in enumerate(test):
        question, reference, extra = build_record(ex, args.phase)

        if question in done_inputs:
            continue

        prediction = ""
        last_err = None
        for attempt in range(args.max_retries + 1):
            try:
                prediction = call_claude(question, args.model, args.timeout)
                break
            except Exception as e:
                last_err = e
                if attempt < args.max_retries:
                    time.sleep(5 * (attempt + 1))

        if not prediction:
            failures += 1
            print(f"  [{i+1}/{len(test)}] FAILED after retries: {last_err}")

        record = {
            "input": question,
            "prediction": prediction,
            "reference": reference,
            "model": args.model_name,
            **extra,
        }
        predictions.append(record)

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(predictions, f, indent=2)

        elapsed = time.time() - start
        done = i + 1
        eta = (elapsed / done) * (len(test) - done) if done else 0
        n_chars = len(prediction)
        print(f"  [{done}/{len(test)}] {n_chars} chars | elapsed {elapsed:.0f}s | eta {eta:.0f}s")

        time.sleep(args.delay)

    print(f"\nSaved {len(predictions)} predictions to {args.output}")
    if failures:
        print(f"WARNING: {failures} failures (empty predictions)")


if __name__ == "__main__":
    main()
