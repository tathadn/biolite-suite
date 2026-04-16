#!/bin/bash
# =============================================================================
# BioLite Suite — HPC Setup Script
# Run this on discovery-c34 (or any machine with internet access)
# =============================================================================
#
# Usage:
#   chmod +x setup_hpc.sh
#   ./setup_hpc.sh
#
# This script:
#   1. Installs Python dependencies
#   2. Downloads BioInstruct dataset from HuggingFace
#   3. Downloads Mol-Instructions biotext subset
#   4. Downloads Llama 3.2 1B-Instruct tokenizer (model downloaded at train time)
#   5. Runs the BioInstruct filtering script
#   6. Prints summary

set -e

SUITE_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== BioLite Suite Setup ==="
echo "Suite directory: $SUITE_DIR"
echo ""

# ---------- Step 1: Python environment ----------
echo "[1/6] Setting up Python environment..."
if [ -d "$SUITE_DIR/.venv" ]; then
    echo "  Virtual environment already exists, activating..."
else
    python3 -m venv "$SUITE_DIR/.venv"
    echo "  Created virtual environment."
fi
source "$SUITE_DIR/.venv/bin/activate"

pip install --upgrade pip -q
pip install -r "$SUITE_DIR/biolite-interpret/training/requirements.txt" -q
pip install -r "$SUITE_DIR/biolite-methods/training/requirements.txt" -q
echo "  Dependencies installed."
echo ""

# ---------- Step 2: Download BioInstruct ----------
echo "[2/6] Downloading BioInstruct dataset..."
BIOINSTRUCT_DIR="$SUITE_DIR/biolite-interpret/data/raw"
mkdir -p "$BIOINSTRUCT_DIR"

python3 -c "
from datasets import load_dataset
import json, os

out_dir = '$BIOINSTRUCT_DIR'
cache_dir = os.path.expanduser('~/.cache/huggingface')

print('  Downloading bio-nlp-umass/bioinstruct...')
ds = load_dataset('bio-nlp-umass/bioinstruct', split='train', cache_dir=cache_dir)
print(f'  Downloaded {len(ds)} examples.')

ds.to_json(os.path.join(out_dir, 'bioinstruct_raw.jsonl'))
print(f'  Saved to {out_dir}/bioinstruct_raw.jsonl')
print(f'  Columns: {ds.column_names}')
"
echo ""

# ---------- Step 3: Download Mol-Instructions biotext subset ----------
echo "[3/6] Downloading Mol-Instructions (biotext subset)..."
MOLINST_DIR="$SUITE_DIR/biolite-interpret/data/raw"

python3 -c "
from datasets import load_dataset
import json, os

out_dir = '$MOLINST_DIR'
cache_dir = os.path.expanduser('~/.cache/huggingface')

print('  Downloading zjunlp/Mol-Instructions (Biomolecular Text Instructions)...')
try:
    ds = load_dataset(
        'zjunlp/Mol-Instructions',
        name='Biomolecular Text Instructions',
        split='train',
        cache_dir=cache_dir,
    )
    print(f'  Downloaded {len(ds)} examples.')
    ds.to_json(os.path.join(out_dir, 'mol_instructions_biotext.jsonl'))
    print(f'  Saved to {out_dir}/mol_instructions_biotext.jsonl')
except Exception as e:
    print(f'  Warning: Could not download Mol-Instructions biotext: {e}')
    print('  You can manually download from: https://huggingface.co/datasets/zjunlp/Mol-Instructions')
"
echo ""

# ---------- Step 4: Download Llama 3.2 1B tokenizer ----------
echo "[4/6] Downloading Llama 3.2 1B-Instruct tokenizer..."
python3 -c "
from transformers import AutoTokenizer
import os

cache_dir = os.path.expanduser('~/.cache/huggingface')
model_id = 'meta-llama/Llama-3.2-1B-Instruct'

print(f'  Downloading tokenizer for {model_id}...')
try:
    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
    print(f'  Tokenizer downloaded. Vocab size: {tokenizer.vocab_size}')
except Exception as e:
    print(f'  Warning: Could not download tokenizer: {e}')
    print('  You may need to accept the Llama license at:')
    print('  https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct')
    print('  Then run: huggingface-cli login')
"
echo ""

# ---------- Step 5: Run BioInstruct filter ----------
echo "[5/6] Running BioInstruct filter..."
cd "$SUITE_DIR/biolite-interpret/data/scripts"
python3 filter_bioinstruct.py \
    --output_dir "$SUITE_DIR/biolite-interpret/data/raw/bioinstruct_filtered" \
    --cache_dir ~/.cache/huggingface
echo ""

# ---------- Step 6: Summary ----------
echo "[6/6] Setup complete!"
echo ""
echo "=== Directory contents ==="
echo ""
echo "--- biolite-interpret/data/raw/ ---"
ls -lh "$SUITE_DIR/biolite-interpret/data/raw/" 2>/dev/null || echo "  (empty)"
echo ""
echo "--- biolite-interpret/data/raw/bioinstruct_filtered/ ---"
ls -lh "$SUITE_DIR/biolite-interpret/data/raw/bioinstruct_filtered/" 2>/dev/null || echo "  (empty)"
echo ""

echo "=== Next steps ==="
echo "1. Review filtered BioInstruct examples in data/raw/bioinstruct_filtered/"
echo "2. Start GEO dataset selection (see data/scripts/scrape_geo_papers.py)"
echo "3. Accept Llama license if tokenizer download failed:"
echo "   https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct"
echo ""
echo "=== MIG slice check ==="
echo "Run: nvidia-smi -L"
echo "to discover your MIG instance UUIDs for CUDA_VISIBLE_DEVICES."
