#!/usr/bin/env python3
"""
upload_to_hf.py — Push the merged preference-pair splits to HuggingFace.

Uploads the three JSON split files as a single DatasetDict so it's loadable
with `load_dataset("tathadn/biolite-methods-preferences")`.

Also uploads the manifest + pinning-keys file to the dataset root for
reproducibility.

Usage:
    python upload_to_hf.py \\
        --splits_dir ../splits \\
        --repo_id tathadn/biolite-methods-preferences
"""

import argparse
import json
import os

from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits_dir", type=str, required=True)
    parser.add_argument("--repo_id", type=str, required=True)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    splits = {}
    for name in ("train", "val", "test"):
        p = os.path.join(args.splits_dir, f"{name}.json")
        with open(p) as f:
            rows = json.load(f)
        splits[name] = Dataset.from_list(rows)
        print(f"  {name}: {len(rows)} examples")

    ds = DatasetDict(splits)
    print(f"\nPushing to hub: {args.repo_id}")
    ds.push_to_hub(args.repo_id, private=args.private)
    print("  DatasetDict pushed.")

    # Attach manifest + pinning keys for reproducibility
    api = HfApi()
    for fname in ("manifest.json", "v1_preference_test_keys.json"):
        src = os.path.join(args.splits_dir, fname)
        if not os.path.exists(src):
            print(f"  (skip) {src}")
            continue
        api.upload_file(
            path_or_fileobj=src,
            path_in_repo=fname,
            repo_id=args.repo_id,
            repo_type="dataset",
        )
        print(f"  uploaded: {fname}")

    print(f"\nDone. Load with:")
    print(f'  from datasets import load_dataset')
    print(f'  ds = load_dataset("{args.repo_id}")')


if __name__ == "__main__":
    main()
