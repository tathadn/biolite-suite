#!/usr/bin/env python3
"""
filter_bioinstruct.py — Filter BioInstruct dataset for interpretation-relevant examples.

Source: bio-nlp-umass/bioinstruct (25K instructions, HuggingFace)
Target: ~1,500-2,000 examples relevant to interpreting biological results.

Usage:
    python filter_bioinstruct.py --output_dir ../raw/bioinstruct_filtered
"""

import argparse
import json
import os
from datasets import load_dataset


# Keywords indicating interpretation/summarization tasks
KEEP_KEYWORDS = [
    "interpret", "summarize", "summary", "differential expression",
    "enrichment", "upregulated", "downregulated", "upregulation",
    "downregulation", "pathway", "gene expression", "fold change",
    "rna-seq", "rnaseq", "transcriptom", "biological significance",
    "go term", "gene ontology", "kegg", "functional analysis",
    "functional annotation", "overexpressed", "underexpressed",
    "significantly expressed", "differentially expressed",
    "biological process", "molecular function", "cellular component",
    "enriched", "depleted", "abundance", "microbiome", "metagenom",
    "amplicon", "16s", "metabolic pathway", "signaling pathway",
    "gene set", "gsea", "over-representation",
]

# Keywords indicating tasks to EXCLUDE (NER, clinical, drug-related)
EXCLUDE_KEYWORDS = [
    "named entity", "ner ", "extract entities",
    "clinical trial", "eligibility", "diagnosis",
    "drug interaction", "medication", "dosage",
    "icd code", "cpt code", "billing",
    "de-identify", "anonymize", "phi ",
]

ALPACA_TEMPLATE = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""


def matches_keywords(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def filter_and_format(dataset, output_dir: str):
    """Filter BioInstruct and save in Alpaca format."""
    os.makedirs(output_dir, exist_ok=True)

    kept = []
    excluded_count = 0
    total = 0

    for example in dataset:
        total += 1
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output_text = example.get("output", "")

        combined = f"{instruction} {input_text} {output_text}"

        # Exclude unwanted task types first
        if matches_keywords(combined, EXCLUDE_KEYWORDS):
            excluded_count += 1
            continue

        # Keep if matches interpretation keywords
        if matches_keywords(combined, KEEP_KEYWORDS):
            kept.append({
                "instruction": instruction,
                "input": input_text,
                "output": output_text,
                "source": "bioinstruct",
                "task_type": "interpretation",  # will be refined later
            })

    # Save filtered dataset
    output_path = os.path.join(output_dir, "bioinstruct_filtered.json")
    with open(output_path, "w") as f:
        json.dump(kept, f, indent=2)

    # Save stats
    stats = {
        "total_examples": total,
        "kept": len(kept),
        "excluded_by_keywords": excluded_count,
        "filtered_out": total - len(kept) - excluded_count,
        "keep_rate": f"{len(kept)/total*100:.1f}%",
    }
    stats_path = os.path.join(output_dir, "filter_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Filtering complete:")
    print(f"  Total examples:     {total}")
    print(f"  Kept:               {len(kept)} ({len(kept)/total*100:.1f}%)")
    print(f"  Excluded (clinical): {excluded_count}")
    print(f"  Filtered out:       {total - len(kept) - excluded_count}")
    print(f"  Saved to:           {output_path}")

    return kept


def main():
    parser = argparse.ArgumentParser(
        description="Filter BioInstruct dataset for interpretation tasks"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="../raw/bioinstruct_filtered",
        help="Directory to save filtered dataset",
    )
    parser.add_argument(
        "--cache_dir",
        type=str,
        default=None,
        help="HuggingFace cache directory (useful on HPC)",
    )
    args = parser.parse_args()

    print("Loading BioInstruct dataset from HuggingFace...")
    ds = load_dataset(
        "bio-nlp-umass/bioinstruct",
        split="train",
        cache_dir=args.cache_dir,
    )
    print(f"Loaded {len(ds)} examples.")

    filtered = filter_and_format(ds, args.output_dir)

    # Print sample examples
    print(f"\n--- Sample filtered examples (first 3) ---")
    for i, ex in enumerate(filtered[:3]):
        print(f"\n[{i+1}] Instruction: {ex['instruction'][:120]}...")
        print(f"    Output:      {ex['output'][:120]}...")


if __name__ == "__main__":
    main()
