#!/usr/bin/env python3
"""
merge_and_split_preferences.py — Merge filtered preference pairs from
all three sources (SE, docs, synthetic) and create stratified splits.

Sources:
  1. stackexchange-bioinformatics (filtered by quality_control.py)
  2. docs-deseq2-vignette + docs-qiime2 (Claude-grounded, filtered)
  3. synthetic-methods (coverage-gap topics, filtered)

Splits: 85% train / 5% val / 10% test, stratified by (category, source).

Pinning for future v2: writes SHA1(question) hashes of this test set to
`splits/v1_preference_test_keys.json` so a future v2 merge can anchor
its test set to a strict superset.

Usage:
    python merge_and_split_preferences.py \\
        --se   ../processed/preference_pairs_se_filtered.json \\
        --docs ../processed/preference_pairs_docs_filtered.json \\
        --synth ../processed/preference_pairs_synth_filtered.json \\
        --out_dir ../splits
"""

import argparse
import hashlib
import json
import os
import random
from collections import Counter, defaultdict

random.seed(42)


def ex_id(ex: dict) -> str:
    return hashlib.sha1(ex["question"].strip().encode("utf-8")).hexdigest()


def normalize(pair: dict, default_category: str = "unknown") -> dict:
    q = (pair.get("question") or "").strip()
    ch = (pair.get("chosen") or "").strip()
    rj = (pair.get("rejected") or "").strip()
    source = pair.get("source") or "unknown"

    # Category: SE uses "category"; synth + docs use "tags" (first = primary)
    cat = pair.get("category")
    if not cat:
        tags = pair.get("tags") or []
        if isinstance(tags, list) and tags:
            cat = tags[0]
        else:
            cat = default_category

    return {
        "question": q,
        "chosen": ch,
        "rejected": rj,
        "error_type": pair.get("error_type", "unknown"),
        "category": cat,
        "source": source,
        "rouge_l_similarity": pair.get("rouge_l_similarity"),
    }


def stratified_sample(data, n_target, strat=("category", "source")):
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

    random.shuffle(remainder)
    while len(sampled) < n_target and remainder:
        sampled.append(remainder.pop())
    while len(sampled) > n_target:
        remainder.append(sampled.pop())
    return sampled, remainder


def print_stats(name, data):
    print(f"\n  {name}: {len(data)} examples")
    src = Counter(ex["source"] for ex in data)
    cat = Counter(ex["category"] for ex in data)
    err = Counter(ex["error_type"] for ex in data)
    print(f"    By source:     {dict(sorted(src.items()))}")
    print(f"    By category:   {dict(sorted(cat.items()))}")
    print(f"    By error_type: {dict(sorted(err.items()))}")


def load_or_empty(path):
    if not path or not os.path.exists(path):
        print(f"  (skip) {path} — not found")
        return []
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--se", type=str, default=None)
    parser.add_argument("--docs", type=str, default=None)
    parser.add_argument("--synth", type=str, default=None)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--test_frac", type=float, default=0.10)
    parser.add_argument("--val_frac", type=float, default=0.05)
    args = parser.parse_args()

    print("Loading preference pair sources...")
    se_raw = load_or_empty(args.se)
    docs_raw = load_or_empty(args.docs)
    synth_raw = load_or_empty(args.synth)
    print(f"  SE filtered:    {len(se_raw)}")
    print(f"  Docs filtered:  {len(docs_raw)}")
    print(f"  Synth filtered: {len(synth_raw)}")

    merged = [normalize(p) for p in se_raw + docs_raw + synth_raw]
    merged = [m for m in merged if m["question"] and m["chosen"] and m["rejected"]]

    # Dedupe by question hash
    seen, unique = set(), []
    for ex in merged:
        eid = ex_id(ex)
        if eid in seen:
            continue
        seen.add(eid)
        unique.append(ex)
    print(f"\nTotal merged: {len(merged)}  → unique: {len(unique)}")

    cat_dist = Counter(ex["category"] for ex in unique)
    src_dist = Counter(ex["source"] for ex in unique)
    err_dist = Counter(ex["error_type"] for ex in unique)
    print(f"\nCategory distribution: {dict(sorted(cat_dist.items()))}")
    print(f"Source distribution:   {dict(sorted(src_dist.items()))}")
    print(f"Error-type distribution: {dict(sorted(err_dist.items()))}")

    # Split: test first, then val from remainder, rest is train
    n_total = len(unique)
    n_test = round(n_total * args.test_frac)
    n_val = round(n_total * args.val_frac)

    test, rest = stratified_sample(unique, n_test)
    val, train = stratified_sample(rest, n_val)

    # Leakage self-check
    test_ids = {ex_id(e) for e in test}
    train_ids = {ex_id(e) for e in train}
    val_ids = {ex_id(e) for e in val}
    assert not (test_ids & train_ids), "leak: test∩train"
    assert not (test_ids & val_ids), "leak: test∩val"
    assert not (train_ids & val_ids), "leak: train∩val"
    print("\nLeakage self-check: OK")

    print(f"\nSplit counts: train={len(train)}  val={len(val)}  test={len(test)}")
    print_stats("Train", train)
    print_stats("Val", val)
    print_stats("Test", test)

    os.makedirs(args.out_dir, exist_ok=True)
    for name, split in [("train", train), ("val", val), ("test", test)]:
        path = os.path.join(args.out_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(split, f, indent=2)
        print(f"  saved: {path} ({len(split)})")

    # Content-hash pinning reference for future v2 comparisons
    pin_path = os.path.join(args.out_dir, "v1_preference_test_keys.json")
    pin_data = {
        "train": sorted(train_ids),
        "val": sorted(val_ids),
        "test": sorted(test_ids),
    }
    with open(pin_path, "w") as f:
        json.dump(pin_data, f, indent=2)
    print(f"  saved: {pin_path} (SHA1 anchors for future v2)")

    # Summary manifest
    manifest = {
        "total_unique": len(unique),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_dist),
        "categories": dict(cat_dist),
        "error_types": dict(err_dist),
        "split_fractions": {"test": args.test_frac, "val": args.val_frac},
        "dedup_dropped": len(merged) - len(unique),
    }
    manifest_path = os.path.join(args.out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  saved: {manifest_path}")


if __name__ == "__main__":
    main()
