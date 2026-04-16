#!/usr/bin/env python3
"""
generate_rejects.py — Generate subtly incorrect answers for DPO training.

Uses Claude Code CLI (claude -p) with your Pro/Max subscription.
No API key required — authenticates via your existing browser OAuth.

Usage:
    python generate_rejects.py \
        --input ../raw/biostars/biostars_qa.json \
        --output ../processed/preference_pairs.json

    # Limit examples for testing:
    python generate_rejects.py --input ../raw/biostars/biostars_qa.json \
        --output ../processed/preference_pairs.json --max_examples 10

    # Use Sonnet (saves subscription quota):
    python generate_rejects.py --input ... --output ... --model sonnet
"""

import argparse
import json
import os
import random
import subprocess
import time
from typing import Optional

ERROR_TYPES = [
    "WRONG_TOOL",
    "MISSING_ASSUMPTION",
    "STAT_CONFUSION",
    "OUTDATED",
    "OVERCONFIDENT",
    "DESIGN_FLAW",
]

ERROR_DESCRIPTIONS = {
    "WRONG_TOOL": "Recommends an inappropriate tool for the stated constraints (e.g., suggests DESeq2 for already-normalized data, or a tool that doesn't support the organism/data type).",
    "MISSING_ASSUMPTION": "Ignores a critical assumption of the recommended method (e.g., doesn't mention that DESeq2 requires raw counts, or ignores the independence assumption).",
    "STAT_CONFUSION": "Conflates or misinterprets statistical concepts (e.g., confuses p-value with effect size, treats adjusted p-value like raw p-value, misunderstands FDR).",
    "OUTDATED": "Recommends a deprecated workflow or outdated best practice (e.g., suggests RPKM instead of TPM, recommends rarefying microbiome data without caveats).",
    "OVERCONFIDENT": "Gives a single recommendation without discussing trade-offs or alternatives, claims a tool 'always works' regardless of constraints.",
    "DESIGN_FLAW": "Ignores experimental design issues like batch effects, confounders, pseudoreplication, or insufficient replicates.",
}

PROMPT_TEMPLATE = """You are generating training data for preference optimization of a bioinformatics methodology advisor.

Given the bioinformatics question and the CORRECT answer below, generate an INCORRECT answer that sounds plausible but contains exactly ONE subtle error.

ERROR TYPE TO INTRODUCE: {error_type}
ERROR DESCRIPTION: {error_description}

The rejected answer MUST:
- Be approximately the same length as the correct answer (±20%)
- Sound confident and well-written (not obviously wrong)
- Contain exactly ONE subtle error of the specified type
- Be wrong in a way that a novice might not catch but an expert would

QUESTION:
{question}

CORRECT ANSWER:
{chosen}

Generate ONLY the rejected answer text. No preamble, no explanation of what's wrong. No markdown formatting."""


def call_claude_code(prompt: str, model: str = "sonnet", max_turns: int = 1) -> Optional[str]:
    """Call Claude Code CLI in print mode using subscription auth.

    Uses `claude -p` which authenticates via your Pro/Max subscription
    OAuth token — no API key needed.
    """
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--model", model,
        "--max-turns", str(max_turns),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
        return None
    except FileNotFoundError:
        print("  ERROR: 'claude' CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
        print("  Then authenticate: claude (follow browser login)")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True,
                        help="Path to Q&A pairs JSON (from scrape_biostars.py)")
    parser.add_argument("--output", type=str, required=True,
                        help="Output path for preference pairs")
    parser.add_argument("--max_examples", type=int, default=None,
                        help="Limit number of examples (for testing)")
    parser.add_argument("--model", type=str, default="sonnet",
                        choices=["sonnet", "opus", "haiku"],
                        help="Claude model to use (sonnet recommended for quota)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between calls (respect rate limits)")
    parser.add_argument("--resume_from", type=int, default=0,
                        help="Resume from this index (skip already processed)")
    args = parser.parse_args()

    # Verify claude CLI is available
    check = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if check.returncode != 0:
        print("ERROR: 'claude' CLI not found in PATH.")
        print("Make sure Claude Code is installed and authenticated:")
        print("  nvm use 18  # or your node version")
        print("  npm install -g @anthropic-ai/claude-code")
        print("  claude  # follow browser auth")
        return

    # Load Q&A pairs
    with open(args.input) as f:
        qa_pairs = json.load(f)

    if args.max_examples:
        qa_pairs = qa_pairs[:args.max_examples]

    print(f"Generating rejected answers for {len(qa_pairs)} pairs")
    print(f"Model: {args.model}")
    print(f"Using Claude Code CLI (subscription auth, no API key)")
    print(f"Starting from index: {args.resume_from}")
    print()

    # Load existing results if resuming
    preference_pairs = []
    if args.resume_from > 0 and os.path.exists(args.output):
        with open(args.output) as f:
            preference_pairs = json.load(f)
        print(f"Loaded {len(preference_pairs)} existing pairs")

    failures = 0

    for i, qa in enumerate(qa_pairs):
        if i < args.resume_from:
            continue

        error_type = random.choice(ERROR_TYPES)

        prompt = PROMPT_TEMPLATE.format(
            error_type=error_type,
            error_description=ERROR_DESCRIPTIONS[error_type],
            question=qa["question"][:1500],
            chosen=qa["chosen"][:2000],
        )

        print(f"[{i+1}/{len(qa_pairs)}] {error_type} — ", end="", flush=True)

        rejected = call_claude_code(prompt, model=args.model)

        if rejected:
            preference_pairs.append({
                "question": qa["question"],
                "chosen": qa["chosen"],
                "rejected": rejected,
                "error_type": error_type,
                "category": qa.get("tags", ["unknown"])[0] if qa.get("tags") else "unknown",
                "source": qa.get("source", "unknown"),
            })
            print(f"OK ({len(rejected.split())} words)")
        else:
            failures += 1
            print("FAILED")

        # Save checkpoint every 25 examples
        if (i + 1) % 25 == 0:
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(preference_pairs, f, indent=2)
            print(f"  [checkpoint saved: {len(preference_pairs)} pairs]")

        time.sleep(args.delay)

    # Final save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(preference_pairs, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Generation complete!")
    print(f"Generated: {len(preference_pairs)}")
    print(f"Failures:  {failures}")
    print(f"Saved to:  {args.output}")

    error_dist = {}
    for p in preference_pairs:
        et = p["error_type"]
        error_dist[et] = error_dist.get(et, 0) + 1
    print(f"\nError type distribution:")
    for et, count in sorted(error_dist.items()):
        print(f"  {et}: {count}")


if __name__ == "__main__":
    main()
