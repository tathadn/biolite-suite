# Session State — 2026-04-23

## Status Checklist

### Phase 1 (v1 dataset, 640 examples)
- [x] 4 data sources filtered and merged → 640 examples (commit eb13a67-ish)
- [x] Dataset uploaded to HuggingFace (tathadn/biolite-interpret-data)
- [x] 1B + 3B QLoRA SFT on v1 data (commit f6e0129)
- [x] Judge eval (Sonnet, interpret rubric) on 64-ex v1 test (commit 556adb3)

### Phase 2 (v2 dataset, 1,262 examples) — completed 2026-04-23
- [x] Synthetic batch3: +606 examples (99.5% success rate)
- [x] GEO expansion: 10 → 26 seeds (added Drosophila, Arabidopsis, C. elegans)
- [x] Merge + stratified 85/5/10 split with **pinned v1-test anchor** (all 64 v1 test ex ⊆ v2 test)
- [x] v2 dataset pushed to HuggingFace (commit 54d6273)
- [x] 1B + 3B retrained on v2 data (commit 5962dd8)
- [x] v2 predictions + judge eval on full 126 v2 test
- [x] 5-row scaling comparison table (v1 vs v2, pinned 64 subset)

### Next up (DPO phase)
- [ ] DPO preference-pair generation pipeline (Biostars scrape validated on 50-pair test batch, commit a38ef48)
- [ ] Scale preference-pair generation
- [ ] DPO training run

## Scaling Comparison Results (v1 vs v2, pinned 64 ex)

| Model | bio_acc | completeness | clarity |
|---|---|---|---|
| Baseline 1B | 1.95 | 1.73 | 2.71 |
| FT 1B @ 640 | 2.30 | 1.86 | 3.17 |
| FT 3B @ 640 | 2.53 | 2.20 | 3.73 |
| FT 1B @ v2  | 2.16 | 1.92 | 3.20 |
| FT 3B @ v2  | **2.78** | **2.31** | **3.97** |

**Headline:** 3B scales positively (+0.25 bio, +0.11 comp, +0.24 clar).
1B is capacity-bound — doubling data didn't improve bio_acc (−0.14, within 1σ).

Supplementary (v2 models on full 126 and new-62-only subsets) in
`biolite-interpret/evaluation/results/scaling_comparison_summary.json`.

## Artifacts & Locations

| Artifact | Path |
|---|---|
| v2 train/val/test splits | `biolite-interpret/data/splits/{train,val,test}.json` |
| Pinned 64-ex filter | `biolite-interpret/evaluation/pinned_64_indices.json` (regeneratable from v1_split_keys.json) |
| v1 reproducibility anchor | `biolite-interpret/data/splits/v1_split_keys.json` (SHA1 content-hashes) |
| v1 adapters (archived) | `biolite-interpret/training/checkpoints_v1_archive/biolite-interpret-{1b,3b}/` |
| v2 adapters (live) | `biolite-interpret/training/checkpoints/biolite-interpret-{1b,3b}/` |
| Predictions (v2) | `biolite-interpret/evaluation/results/finetuned_{1b,3b}_v2_predictions.json` |
| Judge scores (v2) | `biolite-interpret/evaluation/results/judge_finetuned_{1b,3b}_v2.json` |

## HuggingFace Hub

- Dataset: `tathadn/biolite-interpret-data` (v2, 1,262 ex, 85/5/10 pinned)
- Models:  `tathadn/biolite-interpret-1b` (v2), `tathadn/biolite-interpret-3b` (v2)

## Resume Commands

```bash
cd /fs1/scratch/tathadbn/biolite-suite
source .venv/bin/activate
cat SESSION_STATE.md
git log --oneline -10
```

## Key Decisions (persistent)

1. **Pinned v1-test anchor split** — v2 test is a strict superset of v1 test
   (all 64 v1 test examples pinned). Guarantees leak-free scaling comparison
   without resorting to two separate test denominators. v1_split_keys.json
   is the committed SHA1 content-hash reference.

2. **5-row comparison uses pinned 64** — apples-to-apples with existing v1
   judge scores (which were on v1 test = pinned 64 of v2 test). Supplementary
   scores on full 126 and new-62-only reported separately.

3. **1B is capacity-bound** at 1,262 training examples — scaling didn't help
   biological_accuracy. Future data work should prioritize 3B or move to DPO.

4. **v1 adapters preserved at checkpoints_v1_archive/** so the v1 3B model
   can still be run on v2 test for spot-checks and re-evaluation if needed.
