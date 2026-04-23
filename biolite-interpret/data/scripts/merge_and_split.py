#!/usr/bin/env python3
"""
merge_and_split.py — Merge all 4 data sources into a unified dataset
and create stratified train/val/test splits.

Sources (v2):
  1. BioInstruct filtered (112)
  2. GEO paper pairs (26, expanded from initial 10)
  3. Mol-Instructions filtered (327)
  4. Synthetic generation (797 = batch1+2 (191) + batch3 (606))

Splits: 85% train / 5% val / 10% test, stratified by (task_type, source).

Usage:
    python merge_and_split.py
"""

import hashlib
import json
import os
import random
from collections import Counter, defaultdict

random.seed(42)


# ── Example identity (content hash, for pinning/exclusion) ──────────

def ex_id(ex: dict) -> str:
    s = f"{ex.get('instruction','')}|{ex.get('input','')}|{ex.get('output','')}"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

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


SYNTHETIC_SOURCE_FILES = [
    "synthetic_interpretations.json",         # batch 1+2 (191)
    "synthetic_interpretations_batch3.json",  # batch 3   (606)
]


def load_synthetic():
    """Concatenate all synthetic batches and also persist the combined
    view to synthetic_interpretations_all.json for downstream tooling."""
    combined_raw = []
    for fname in SYNTHETIC_SOURCE_FILES:
        with open(os.path.join(PROCESSED, fname)) as f:
            combined_raw.extend(json.load(f))

    out = []
    for ex in combined_raw:
        out.append({
            "instruction": ex["instruction"],
            "input": ex.get("input", ""),
            "output": ex["output"],
            "source": "synthetic",
            "task_type": ex["metadata"]["task_type"],
        })

    all_path = os.path.join(PROCESSED, "synthetic_interpretations_all.json")
    with open(all_path, "w") as f:
        json.dump(combined_raw, f, indent=2)
    print(f"  Wrote combined synthetic file: {all_path} ({len(combined_raw)})")

    return out


# ── Stratified helpers ──────────────────────────────────────────────

def stratified_sample(data, n_target, strat=("task_type", "source")):
    """Draw ~n_target examples stratified by `strat`.

    Returns (sampled, remainder). Actual sample size is within ±len(buckets)/2
    of n_target due to rounding in each bucket."""
    buckets = defaultdict(list)
    for ex in data:
        buckets[tuple(ex[k] for k in strat)].append(ex)

    total = len(data)
    sampled, remainder = [], []
    for key, examples in sorted(buckets.items()):
        random.shuffle(examples)
        take = round(n_target * len(examples) / total) if total else 0
        take = max(0, min(take, len(examples)))
        sampled.extend(examples[:take])
        remainder.extend(examples[take:])

    # Nudge toward exact n_target if rounding left us short/long.
    random.shuffle(remainder)
    while len(sampled) < n_target and remainder:
        sampled.append(remainder.pop())
    while len(sampled) > n_target:
        remainder.append(sampled.pop())
    return sampled, remainder


def stratified_train_val(data, val_target, strat=("task_type", "source")):
    """Split data into (train, val) stratified by `strat`, aiming for
    val_target examples in val."""
    val, train = stratified_sample(data, val_target, strat=strat)
    random.shuffle(train)
    random.shuffle(val)
    return train, val


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

    # ── Pinned split: v1 test examples anchor v2 test ──────────────
    #
    # Why: naive re-splitting reshuffles everything when bucket sizes change.
    # A v1 test example can end up in v2 train (leakage for v2 evals on v1 test),
    # and a v1 train example can end up in v2 test (leakage for v1 evals on v2 test).
    # Pinning v1 test as a subset of v2 test, and restricting v2 test extensions
    # to examples not in any v1 split, keeps both v1 and v2 models evaluable on
    # the same v2 test set with no train-test overlap for either.
    v1_keys_path = os.path.join(SPLITS, "v1_split_keys.json")
    with open(v1_keys_path) as f:
        v1_keys = json.load(f)
    v1_train_k = set(v1_keys["train"])
    v1_val_k   = set(v1_keys["val"])
    v1_test_k  = set(v1_keys["test"])

    pinned_test, new_pool, old_pool = [], [], []
    for ex in merged:
        eid = ex_id(ex)
        if eid in v1_test_k:
            pinned_test.append(ex)
        elif eid in v1_train_k or eid in v1_val_k:
            old_pool.append(ex)        # goes only to v2 train or val
        else:
            new_pool.append(ex)        # test-eligible (batch3 + new GEO)

    assert len(pinned_test) == len(v1_test_k), (
        f"v1 test anchor incomplete: found {len(pinned_test)} of {len(v1_test_k)}"
    )
    print(f"\nPartition vs v1:  pinned_test={len(pinned_test)}  "
          f"new_pool={len(new_pool)}  old_pool={len(old_pool)}")

    # Target 85/5/10 overall.
    total = len(merged)
    n_test_target = round(total * 0.10)
    n_val_target  = round(total * 0.05)
    n_extra_test  = max(0, n_test_target - len(pinned_test))

    # Extend test from new_pool only (held out from v1 train ∪ val).
    extra_test, new_remainder = stratified_sample(new_pool, n_extra_test)
    test = pinned_test + extra_test
    random.shuffle(test)

    # Remaining pool → train/val (old_pool excluded from test by construction).
    trainval_pool = new_remainder + old_pool
    train, val = stratified_train_val(trainval_pool, n_val_target)

    # ── Leakage self-check ─────────────────────────────────────────
    test_ids = {ex_id(e) for e in test}
    train_ids = {ex_id(e) for e in train}
    val_ids = {ex_id(e) for e in val}
    assert not (test_ids & train_ids), "leak: test∩train"
    assert not (test_ids & val_ids), "leak: test∩val"
    assert not (train_ids & val_ids), "leak: train∩val"
    # Against v1:
    assert v1_test_k.issubset(test_ids), "v1 test must be subset of v2 test"
    assert not (test_ids & v1_train_k), "leak: v2 test contains v1 train examples"
    assert not (test_ids & v1_val_k),   "leak: v2 test contains v1 val examples"
    print("Leakage self-check: OK (v1 train/val disjoint from v2 test; v1 test ⊆ v2 test)")

    print(f"\n{'='*55}")
    print(f"Split statistics (target 85/5/10, with v1-test pin)")
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
