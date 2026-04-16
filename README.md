# BioLite Suite

Specialized Small Language Models for Computational Biology on Constrained Hardware.

## Overview

BioLite Suite is a collection of domain-adapted Llama 3.2 1B models for bioinformatics, trained entirely on a MIG-partitioned NVIDIA A100 with ~4.8GB VRAM per slice.

| Model | Task | Method | HuggingFace |
|-------|------|--------|-------------|
| **BioLite-Interpret** | DE table → biological narrative | QLoRA SFT | `tathadn/biolite-interpret-1b` |
| **BioLite-Methods** | Bioinformatics methodology Q&A | QLoRA DPO | `tathadn/biolite-methods-1b-dpo` |

## Hardware

```
GPU: NVIDIA A100-PCIE-40GB (MIG enabled)
MIG 0 (GI 9):  ~4.8 GB VRAM, 14 SMs
MIG 1 (GI 11): ~4.8 GB VRAM, 14 SMs
```

## Quick Start

```bash
# 1. Clone and setup
chmod +x setup_hpc.sh
./setup_hpc.sh

# 2. Train Phase 1 (BioLite-Interpret)
cd biolite-interpret/training
export CUDA_VISIBLE_DEVICES=MIG-<GI-9-uuid>
python train.py --config config.yaml

# 3. Train Phase 2 (BioLite-Methods) — parallel ablation
# Terminal 1 (MIG 0):
cd biolite-methods/training
export CUDA_VISIBLE_DEVICES=MIG-<GI-9-uuid>
python train_dpo.py --base_model tathadn/biolite-interpret-1b

# Terminal 2 (MIG 1):
export CUDA_VISIBLE_DEVICES=MIG-<GI-11-uuid>
python train_dpo.py --base_model meta-llama/Llama-3.2-1B-Instruct --run_name dpo-from-base
```

## Project Structure

```
biolite-suite/
├── setup_hpc.sh                    # One-command HPC setup
├── biolite-interpret/              # Phase 1: SFT for result interpretation
│   ├── data/scripts/               # Dataset construction pipeline
│   ├── training/                   # QLoRA SFT training
│   ├── evaluation/                 # LLM-as-Judge + auto metrics
│   └── demo/                       # Gradio demo app
├── biolite-methods/                # Phase 2: DPO for methodology advising
│   ├── data/scripts/               # Biostars scraping + reject generation
│   ├── training/                   # DPO with Fp32LogitsDPOTrainer
│   └── evaluation/                 # 5-way comparison + win rates
└── README.md
```

## Timeline

| Week | Phase | GPU Slices Needed |
|------|-------|-------------------|
| 1–2 | Dataset curation (Interpret) | 0–1 |
| 3 | SFT training + ablations | 2 (parallel) |
| 4 | Documentation + release | 0 |
| 5 | Dataset curation (Methods) | 0–1 |
| 6 | DPO training + ablations + eval | 2 (parallel) |

## Citation

```bibtex
@misc{debnath2026biolite,
  title={BioLite Suite: Domain-Specialized Small Language Models for Bioinformatics under Hardware Constraints},
  author={Tathagata Debnath},
  year={2026},
  url={https://github.com/tathadn/biolite-suite}
}
```

## License

MIT
