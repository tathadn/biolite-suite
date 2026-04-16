#!/usr/bin/env python3
"""
generate_synthetic.py — Generate synthetic interpretation examples for BioLite-Interpret.

Uses Claude Code CLI (claude -p) with your Pro/Max subscription.
No API key required.

Generates:
  1. DE table → narrative interpretation pairs
  2. GO/KEGG enrichment → pathway summary pairs
  3. Combined DE + enrichment → integrated interpretation pairs

Usage:
    python generate_synthetic.py \
        --seed_file ../raw/geo_pairs/geo_paper_pairs.json \
        --output ../processed/synthetic_interpretations.json \
        --count 200

    # Test with a small batch:
    python generate_synthetic.py --seed_file ... --output ... --count 5 --model sonnet
"""

import argparse
import json
import os
import random
import subprocess
import time
from typing import Optional

ORGANISMS = ["human", "mouse", "Drosophila", "zebrafish", "C. elegans", "Arabidopsis", "rat"]
CONDITIONS = [
    "tumor vs normal", "drug-treated vs vehicle control", "knockout vs wild-type",
    "infected vs mock", "aged vs young", "high-fat diet vs control",
    "hypoxia vs normoxia", "stem cell vs differentiated", "resistant vs sensitive",
    "early stage vs late stage", "stressed vs unstressed", "mutant vs wild-type",
]

DE_GENERATION_PROMPT = """You are a computational biologist creating a training example for a bioinformatics AI assistant.

Generate a REALISTIC differential expression results table AND its biological interpretation.

Organism: {organism}
Experimental contrast: {condition}
Task type: {task_type}

{task_specific_instructions}

Output ONLY valid JSON in this exact format:
{{
  "instruction": "<instruction text asking for interpretation>",
  "input": "<the structured table as a markdown table>",
  "output": "<100-250 word biological interpretation paragraph>",
  "metadata": {{
    "organism": "{organism}",
    "contrast": "{condition}",
    "task_type": "{task_type}"
  }}
}}

Make the gene names realistic for the organism. Make the interpretation biologically accurate and insightful. No markdown fences around the JSON."""

TASK_INSTRUCTIONS = {
    "de_interpretation": """Generate a DESeq2 results table with 10-15 genes showing:
| Gene | log2FC | padj | baseMean |
Include a mix of upregulated (positive log2FC) and downregulated (negative) genes.
The interpretation should identify functional themes, connect to biological processes, and note caveats.""",

    "enrichment_interpretation": """Generate a GO/KEGG enrichment results table showing:
| Term | Category | GeneCount | pvalue | p.adjust | GeneRatio |
Include 8-12 enriched terms from GO Biological Process, GO Molecular Function, or KEGG pathways.
The interpretation should explain which biological processes are enriched and why they make sense.""",

    "combined_interpretation": """Generate BOTH a short DE table (top 8 genes) AND a GO enrichment table (top 6 terms).
The interpretation should integrate both: connect specific gene expression changes to the enriched pathways.""",
}


def call_claude_code(prompt: str, model: str = "sonnet") -> Optional[str]:
    """Call Claude Code CLI in print mode."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--model", model,
        "--max-turns", "1",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=180, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def parse_json_response(text: str) -> Optional[dict]:
    """Extract and parse JSON from Claude's response."""
    # Strip markdown fences
    if "```" in text:
        import re
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Find JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass
    return None


def quality_check(example: dict) -> bool:
    """Basic quality filter for generated examples."""
    if not all(k in example for k in ["instruction", "input", "output"]):
        return False
    output = example.get("output", "")
    word_count = len(output.split())
    if word_count < 50 or word_count > 400:
        return False
    if not example.get("input", "").strip():
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_file", type=str, default=None,
                        help="Optional seed file from GEO paper pairs")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--count", type=int, default=200,
                        help="Number of synthetic examples to generate")
    parser.add_argument("--model", type=str, default="sonnet")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    # Task type distribution
    task_weights = {
        "de_interpretation": 0.60,
        "enrichment_interpretation": 0.25,
        "combined_interpretation": 0.15,
    }

    print(f"Generating {args.count} synthetic examples")
    print(f"Model: {args.model} | Using Claude Code CLI (subscription auth)\n")

    examples = []
    failures = 0

    for i in range(args.count):
        # Sample task type, organism, condition
        task_type = random.choices(
            list(task_weights.keys()),
            weights=list(task_weights.values()),
        )[0]
        organism = random.choice(ORGANISMS)
        condition = random.choice(CONDITIONS)

        prompt = DE_GENERATION_PROMPT.format(
            organism=organism,
            condition=condition,
            task_type=task_type,
            task_specific_instructions=TASK_INSTRUCTIONS[task_type],
        )

        print(f"[{i+1}/{args.count}] {task_type[:15]:15s} | {organism:12s} | {condition[:25]:25s} — ", end="", flush=True)

        response = call_claude_code(prompt, model=args.model)

        if response:
            parsed = parse_json_response(response)
            if parsed and quality_check(parsed):
                parsed["source"] = "synthetic"
                parsed.setdefault("metadata", {}).update({
                    "organism": organism,
                    "contrast": condition,
                    "task_type": task_type,
                })
                examples.append(parsed)
                print(f"OK ({len(parsed['output'].split())} words)")
            else:
                failures += 1
                print("PARSE_FAIL")
        else:
            failures += 1
            print("FAILED")

        # Checkpoint every 50
        if (i + 1) % 50 == 0:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(examples, f, indent=2)
            print(f"  [checkpoint: {len(examples)} examples]")

        time.sleep(args.delay)

    # Save
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(examples, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Generated: {len(examples)} / {args.count} attempted")
    print(f"Failures:  {failures}")
    print(f"Saved to:  {args.output}")

    # Distribution
    task_dist = {}
    for ex in examples:
        tt = ex.get("metadata", {}).get("task_type", "unknown")
        task_dist[tt] = task_dist.get(tt, 0) + 1
    print(f"\nTask type distribution:")
    for tt, count in sorted(task_dist.items()):
        print(f"  {tt}: {count}")


if __name__ == "__main__":
    main()
