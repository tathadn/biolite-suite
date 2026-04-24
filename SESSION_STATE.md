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

### Phase 2 DPO data — completed 2026-04-24
- [x] StackExchange full scrape: 60 methodology Q&A
- [x] SE rejects generated (60 pairs), filter yield **23** (sim 0.2–0.85, length 0.4–2.5)
- [x] Docs Q&A (DESeq2 vignette 40 + QIIME 2 tutorials 50 → combined 90 → paired 74), filter yield **53** at max_sim 0.90 (docs pairs cluster tight, avg kept sim 0.793)
- [x] Synthetic methodology pairs: **200/200** across 7 buckets (splicing 30, microbiome 30, exp-design 30, stats 30, normalization 25, alignment 25, general 30) with weighted error-type choice (STAT_CONFUSION 2×, MISSING_ASSUMPTION 1.5×, OVERCONFIDENT 0.5×) and inline QC. All drops (259) were `too_similar`; length_mismatch and reject_fail were both 0.
- [x] Merge + 85/5/10 split: **276 unique pairs** → train 234 / val 14 / test 28. SHA1 pinning in `v1_preference_test_keys.json`. Leakage self-check OK.
- [x] Upload `tathadn/biolite-methods-preferences` to HuggingFace (3 splits + manifest + pinning file)

### Next up (DPO phase)
- [ ] DPO training on `tathadn/biolite-methods-preferences` (train 234, val 14) — 1B and 3B variants
- [ ] DPO eval with judge rubric against `biolite-interpret-{1b,3b}` v2 on pinned methods test set

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
| SE preference pairs (filtered) | `biolite-methods/data/processed/preference_pairs_se_filtered.json` (23) |
| Docs preference pairs (filtered) | `biolite-methods/data/processed/preference_pairs_docs_filtered.json` (53) |
| Synthetic preference pairs | `biolite-methods/data/processed/preference_pairs_synthetic.json` (200) |
| Merged splits | `biolite-methods/data/splits/{train,val,test}.json` (234/14/28) |
| Split pinning | `biolite-methods/data/splits/v1_preference_test_keys.json` (SHA1 anchors) |
| HF methods dataset | `tathadn/biolite-methods-preferences` |
| Methods data scripts | `biolite-methods/data/scripts/{extract_from_docs,generate_synthetic_methods,generate_rejects,quality_control,merge_and_split_preferences,upload_to_hf}.py` |

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

5. **Relaxed QC thresholds (0.2–0.85 sim, 0.4–2.5 len) are the new defaults** in
   `quality_control.py`. Rationale: the tight 0.3–0.8 window dropped 73% of SE
   pairs, including near-copy STAT_CONFUSION edits that are exactly the subtle
   factual contrast DPO is designed for. Length ceiling raised because
   OVERCONFIDENT rejects are legitimately verbose. SE pairs recovered from
   16 → 23; docs pairs filter 74 → 31 (docs drops are all `too_similar`, a
   known artifact of reference-answer-derived Q&A).
