#!/usr/bin/env python3
"""
merge_and_split.py — Merge all 4 data sources into a unified dataset
and create stratified train/val/test splits.

Sources:
  1. BioInstruct filtered (112)
  2. GEO paper pairs (10)
  3. Mol-Instructions filtered (327)
  4. Synthetic generation (191)

Splits: 85% train / 5% val / 10% test, stratified by (task_type, source).

Usage:
    python merge_and_split.py
"""

import json
import os
import random
from collections import Counter, defaultdict

random.seed(42)

BASE = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(BASE, "raw")
PROCESSED = os.path.join(BASE, "processed")
SPLITS = os.path.join(BASE, "splits")


# ── Task type classifier for non-synthetic sources ──────────────────

ENRICHMENT_KEYWORDS = [
    "go term", "gene ontology", "kegg", "enrichment analysis",
    "pathway enrichment", "over-representation", "gsea", "gene set",
    "functional enrichment", "enriched terms", "enriched pathways",
    "biological process", "molecular function", "cellular component",
]
DE_KEYWORDS = [
    "differential expression", "differentially expressed", "fold change",
    "log2fc", "log2 fold", "upregulated", "downregulated",
    "upregulation", "downregulation", "de genes", "deg ",
    "overexpressed", "underexpressed", "expression profile",
]


def classify_task_type(text: str) -> str:
    text_lower = text.lower()
    has_enrichment = any(kw in text_lower for kw in ENRICHMENT_KEYWORDS)
    has_de = any(kw in text_lower for kw in DE_KEYWORDS)
    if has_de and has_enrichment:
        return "combined_interpretation"
    if has_enrichment:
        return "enrichment_interpretation"
    return "de_interpretation"


# ── Load and normalize each source ──────────────────────────────────

def load_bioinstruct():
    path = os.path.join(RAW, "bioinstruct_filtered", "bioinstruct_filtered.json")
    with open(path) as f:
        data = json.load(f)
    out = []
    for ex in data:
        combined = f"{ex['instruction']} {ex['input']} {ex['output']}"
        out.append({
            "instruction": ex["instruction"],
            "input": ex.get("input", ""),
            "output": ex["output"],
            "source": "bioinstruct",
            "task_type": classify_task_type(combined),
        })
    return out


def load_geo():
    path = os.path.join(RAW, "geo_pairs", "geo_paper_pairs.json")
    with open(path) as f:
        data = json.load(f)
    out = []
    for ex in data:
        organism = ex.get("organism", "unknown")
        contrast = ex.get("contrast", "")
        gse_id = ex.get("gse_id", "")
        interp = ex.get("interpretation_source", "")
        if not interp or not interp.strip():
            continue
        instruction = (
            f"Interpret the differential expression results from a "
            f"{organism} RNA-seq experiment comparing {contrast}."
        )
        input_text = (
            f"Dataset: {gse_id} | Organism: {organism} | "
            f"Contrast: {contrast}"
        )
        combined = f"{instruction} {input_text} {interp}"
        out.append({
            "instruction": instruction,
            "input": input_text,
            "output": interp.strip(),
            "source": "geo",
            "task_type": classify_task_type(combined),
        })
    return out


def load_mol_instructions():
    path = os.path.join(RAW, "mol_instructions_filtered", "mol_instructions_filtered.json")
    with open(path) as f:
        data = json.load(f)
    out = []
    for ex in data:
        combined = f"{ex['instruction']} {ex.get('input','')} {ex['output']}"
        out.append({
            "instruction": ex["instruction"],
            "input": ex.get("input", ""),
            "output": ex["output"],
            "source": "mol_instructions",
            "task_type": classify_task_type(combined),
        })
    return out


def load_synthetic():
    path = os.path.join(PROCESSED, "synthetic_interpretations.json")
    with open(path) as f:
        data = json.load(f)
    out = []
    for ex in data:
        out.append({
            "instruction": ex["instruction"],
            "input": ex.get("input", ""),
            "output": ex["output"],
            "source": "synthetic",
            "task_type": ex["metadata"]["task_type"],
        })
    return out


# ── Stratified split ────────────────────────────────────────────────

def stratified_split(data, train_frac=0.85, val_frac=0.05, test_frac=0.10):
    """Split data stratified by (task_type, source)."""
    buckets = defaultdict(list)
    for ex in data:
        key = (ex["task_type"], ex["source"])
        buckets[key].append(ex)

    train, val, test = [], [], []

    for key, examples in sorted(buckets.items()):
        random.shuffle(examples)
        n = len(examples)
        n_test = max(1, round(n * test_frac))
        n_val = max(1, round(n * val_frac))
        # Ensure at least 1 in train for very small buckets
        if n <= 3:
            train.extend(examples)
            continue
        n_train = n - n_val - n_test

        test.extend(examples[:n_test])
        val.extend(examples[n_test:n_test + n_val])
        train.extend(examples[n_test + n_val:])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    return train, val, test


# ── Stats ───────────────────────────────────────────────────────────

def print_stats(name, data):
    print(f"\n  {name}: {len(data)} examples")
    src = Counter(ex["source"] for ex in data)
    tt = Counter(ex["task_type"] for ex in data)
    print(f"    By source:    {dict(sorted(src.items()))}")
    print(f"    By task_type: {dict(sorted(tt.items()))}")


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("Loading data sources...")
    bioinstruct = load_bioinstruct()
    geo = load_geo()
    mol = load_mol_instructions()
    synthetic = load_synthetic()

    print(f"  BioInstruct:      {len(bioinstruct)}")
    print(f"  GEO paper pairs:  {len(geo)}")
    print(f"  Mol-Instructions: {len(mol)}")
    print(f"  Synthetic:        {len(synthetic)}")

    merged = bioinstruct + geo + mol + synthetic
    print(f"\nTotal merged: {len(merged)}")

    # Task type distribution after classification
    tt_dist = Counter(ex["task_type"] for ex in merged)
    print(f"\nTask type distribution (after auto-classification):")
    for tt, cnt in sorted(tt_dist.items()):
        print(f"  {tt}: {cnt}")

    # Save merged
    os.makedirs(PROCESSED, exist_ok=True)
    merged_path = os.path.join(PROCESSED, "merged_dataset.json")
    with open(merged_path, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"\nSaved merged: {merged_path}")

    # Split
    train, val, test = stratified_split(merged)
    print(f"\n{'='*55}")
    print(f"Split statistics (85% / 5% / 10%)")
    print_stats("Train", train)
    print_stats("Val", val)
    print_stats("Test", test)

    # Save splits
    os.makedirs(SPLITS, exist_ok=True)
    for name, split in [("train", train), ("val", val), ("test", test)]:
        path = os.path.join(SPLITS, name + ".json")
        with open(path, "w") as f:
            json.dump(split, f, indent=2)
    print(f"\nSaved splits to: {SPLITS}/")


if __name__ == "__main__":
    main()
