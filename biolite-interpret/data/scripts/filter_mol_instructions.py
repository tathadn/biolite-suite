#!/usr/bin/env python3
"""
filter_mol_instructions.py — Filter Mol-Instructions Biomolecular Text data
for interpretation-relevant examples using the same keyword set as filter_bioinstruct.py.

Source: 6 JSON files in data/raw/Biomolecular_Text_Instructions/
Target: Supplementary training data (even 50-100 good examples help).

Usage:
    python filter_mol_instructions.py \
        --input_dir ../raw/Biomolecular_Text_Instructions \
        --output_dir ../raw/mol_instructions_filtered
"""

import argparse
import json
import os
import random

# Same keyword sets as filter_bioinstruct.py
KEEP_KEYWORDS = [
    "differential expression", "enrichment", "upregulated", "downregulated",
    "upregulation", "downregulation", "gene expression", "fold change",
    "rna-seq", "rnaseq", "transcriptom", "biological significance",
    "go term", "gene ontology", "kegg", "functional analysis",
    "functional annotation", "overexpressed", "underexpressed",
    "significantly expressed", "differentially expressed",
    "biological process", "molecular function", "cellular component",
    "abundance", "microbiome", "metagenom",
    "amplicon", "16s", "metabolic pathway", "signaling pathway",
    "gene set", "gsea", "over-representation",
    "pathway analysis", "pathway enrichment", "expression profile",
    "gene regulation", "sequencing data", "omics",
]

EXCLUDE_KEYWORDS = [
    "named entity", "ner ", "extract entities",
    "clinical trial", "eligibility", "diagnosis",
    "drug interaction", "medication", "dosage",
    "icd code", "cpt code", "billing",
    "de-identify", "anonymize", "phi ",
]

# Extraction-format files produce (Subject, Relation, Object) tuples,
# not interpretive text — skip them entirely.
SKIP_FILES = {
    "chemical_protein_interaction_extraction.json",
    "chemical_disease_interaction_extraction.json",
    "chemical_entity_recognition.json",
}

# Multi-choice outputs are too terse ("The final answer is (A).")
# to serve as interpretation training data.
MIN_OUTPUT_WORDS = 20


def matches_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def filter_file(filepath: str) -> tuple[list[dict], int, int]:
    """Filter a single Mol-Instructions JSON file. Returns (kept, excluded, total)."""
    fname = os.path.basename(filepath)
    if fname in SKIP_FILES:
        with open(filepath) as f:
            data = json.load(f)
        return [], 0, len(data)

    with open(filepath) as f:
        data = json.load(f)

    kept = []
    excluded = 0

    for example in data:
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output_text = example.get("output", "")
        combined = f"{instruction} {input_text} {output_text}"

        if matches_keywords(combined, EXCLUDE_KEYWORDS):
            excluded += 1
            continue

        if matches_keywords(combined, KEEP_KEYWORDS):
            if len(output_text.split()) < MIN_OUTPUT_WORDS:
                continue
            kept.append({
                "instruction": instruction,
                "input": input_text,
                "output": output_text,
                "source": "mol_instructions",
                "source_file": fname,
                "task_type": "interpretation",
            })

    return kept, excluded, len(data)


def main():
    parser = argparse.ArgumentParser(
        description="Filter Mol-Instructions biotext for interpretation tasks"
    )
    parser.add_argument("--input_dir", type=str,
                        default="../raw/Biomolecular_Text_Instructions")
    parser.add_argument("--output_dir", type=str,
                        default="../raw/mol_instructions_filtered")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    all_kept = []
    total_all = 0
    excluded_all = 0
    per_file_stats = {}

    json_files = sorted(f for f in os.listdir(args.input_dir) if f.endswith(".json"))
    print(f"Processing {len(json_files)} Mol-Instructions files\n")

    for fname in json_files:
        fpath = os.path.join(args.input_dir, fname)
        kept, excluded, total = filter_file(fpath)
        all_kept.extend(kept)
        total_all += total
        excluded_all += excluded
        per_file_stats[fname] = {"total": total, "kept": len(kept), "excluded": excluded}
        skipped = "(SKIPPED — extraction format)" if fname in SKIP_FILES else ""
        print(f"  {fname:50s}  {total:6d} total → {len(kept):4d} kept  ({excluded} excluded) {skipped}")

    # Save filtered data
    output_path = os.path.join(args.output_dir, "mol_instructions_filtered.json")
    with open(output_path, "w") as f:
        json.dump(all_kept, f, indent=2)

    # Save stats
    stats = {
        "total_examples": total_all,
        "kept": len(all_kept),
        "excluded_by_keywords": excluded_all,
        "filtered_out": total_all - len(all_kept) - excluded_all,
        "keep_rate": f"{len(all_kept)/total_all*100:.2f}%" if total_all else "0%",
        "per_file": per_file_stats,
    }
    stats_path = os.path.join(args.output_dir, "filter_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Total across all files: {total_all}")
    print(f"Kept:                   {len(all_kept)} ({len(all_kept)/total_all*100:.2f}%)")
    print(f"Excluded (clinical):    {excluded_all}")
    print(f"Filtered out:           {total_all - len(all_kept) - excluded_all}")
    print(f"Saved to:               {output_path}")

    # Spot-check: show 5 random kept examples
    if all_kept:
        print(f"\n--- Spot-check: 5 random kept examples ---")
        samples = random.sample(all_kept, min(5, len(all_kept)))
        for i, ex in enumerate(samples, 1):
            print(f"\n[{i}] Source: {ex['source_file']}")
            print(f"    Instruction: {ex['instruction'][:120]}...")
            print(f"    Output:      {ex['output'][:120]}...")


if __name__ == "__main__":
    main()
