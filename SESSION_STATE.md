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

### Phase 2 DPO training — completed 2026-04-25
- [x] 5 DPO runs (1B-from-SFT, 3B-from-SFT, 1B-from-base ablation, β=0.05, β=0.20)
- [x] DPO eval with judge rubric on 28-ex pinned methods test set + vanilla baseline (2026-04-26)

## Phase 2 DPO Training Results (2026-04-25)

5 runs × 60 optimizer steps (2 epochs × 234 ex / 8 effective batch). All used QLoRA
(r=16, α=32, paged_adamw_8bit, bf16 + Fp32LogitsDPOTrainer for NaN-safe gradients).

| Run | β | Init | max_len | Train loss | Train margin | Eval loss | Eval margin | Eval acc | Peak GB | Wall time |
|---|---|---|---|---|---|---|---|---|---|---|
| 1b-from-sft     | 0.10 | interpret-1b           | 512 | 0.033 | 6.27 | 0.0811 | 5.17 | 0.929 | 3.54 | 6:00  |
| 3b-from-sft     | 0.10 | interpret-3b           | 384 | 0.057 | 4.63 | **0.0273** | 4.60 | **1.000** | 4.30 | 12:30 |
| 1b-from-base    | 0.10 | Llama-3.2-1B-Instruct  | 512 | 0.034 | 6.22 | 0.0792 | 5.10 | 0.929 | 3.54 | 6:00  |
| 1b-beta005      | 0.05 | interpret-1b           | 512 | 0.079 | 4.03 | 0.1132 | 3.53 | 0.929 | 3.54 | 6:00  |
| 1b-beta02       | 0.20 | interpret-1b           | 512 | 0.019 | 9.29 | 0.0687 | 6.97 | 0.929 | 3.54 | 6:00  |

**Key findings:**
- **SFT-init ≈ base-init for DPO at 1B** (within noise across all 7 metrics). At this dataset
  scale (234 pairs), the contrastive DPO signal dominates over any prior the SFT adapter
  encoded. Reinforces the Phase 1.5 "1B is capacity-bound" headline.
- **β scales margin magnitude but not eval accuracy** (4.03 → 6.27 → 9.29 across
  β ∈ {0.05, 0.1, 0.2}); all three hit the same 0.929 eval acc on val n=14.
  Eval loss is best at β=0.20 (0.0687); judge eval will determine downstream winner.
- **3B advantages on eval** (lower eval_loss 0.027 vs 0.081, perfect 1.000 acc) are real
  but partially confounded by `max_length=384` truncation — 3B couldn't fit at 512 in
  the 4.75 GiB MIG slice (paged-adamw-8bit illegal-address at first optimizer.step()).

**Operational notes added this run:**
- Default `per_device_eval_batch_size=8` × DPO chosen+rejected concat × seq=512 ×
  vocab=128k overflowed the eval upcast on 4.75 GiB. Fix: explicit
  `per_device_eval_batch_size=1` + `eval_accumulation_steps=4`.
- TRL 0.29.1 moved the `concatenated_forward` hook into `_compute_loss`. The
  `Fp32LogitsDPOTrainer` rewrite wraps `model.forward` directly and now guards
  the upcast on `model.training` so eval uses bf16 logits (saves ~840 MB).
- Saved DPO `adapter_config.json` records `base_model_name_or_path` as the bare
  Llama Instruct repo, even when the trainer was started with the SFT adapter
  repo. Naively `PeftModel.from_pretrained(adapter)` would silently drop the SFT
  contribution — `generate_predictions.py` overrides `--base_model` explicitly so
  the SFT-init runs are loaded as `(base + interpret-LoRA + DPO-LoRA)` to match
  training-time policy. Document this when publishing to HF (or merge-and-upload).

## Phase 2 DPO Judge Eval (2026-04-26)

Sonnet judge, methods rubric (4 criteria 1–5: methodological_accuracy,
assumption_awareness, tradeoff_discussion, practical_helpfulness),
n=28 pinned test pairs, reference = `chosen` field.

| Model | method_acc | assumptions | tradeoffs | helpful | overall |
|---|---:|---:|---:|---:|---:|
| Vanilla Llama-3.2-1B-Instruct          | 1.14 | 1.11 | 1.32 | 1.04 | **1.15** |
| DPO 1B-from-SFT (β=0.10)               | 1.07 | 1.00 | 1.14 | 1.00 | 1.05 |
| DPO 3B-from-SFT (β=0.10, ml=384)       | 1.54 | 1.39 | 1.61 | 1.32 | **1.47** |
| DPO 1B-from-base (β=0.10)              | 1.14 | 1.00 | 1.11 | 1.04 | 1.07 |
| DPO 1B β=0.05 (suppl)                  | 1.00 | 1.00 | 1.14 | 1.00 | 1.03 |
| DPO 1B β=0.20 (suppl)                  | 1.14 | 1.00 | 1.14 | 1.07 | 1.09 |

**Headlines (publishable):**
1. **Scale wins.** 3B-from-SFT scores 1.47 overall, +0.32 vs vanilla. Distribution
   shifts from "all 1's" (1B variants) to roughly half 1's / half 2's across all
   four criteria. Robust across train metrics, eval metrics, and judge scores.
2. **DPO at 1B underperforms vanilla.** 1B-from-SFT 1.05, 1B-from-base 1.07, vs
   vanilla 1.15. With 234 mostly-synthetic preference pairs, DPO sharpens the
   trained chosen/rejected boundary but doesn't add capability — and can amplify
   wrong-tool hallucinations (spot-check: 1B-from-SFT recommends `bcftools` for
   strand inference on idx 0).
3. **β has near-zero effect on judge scores at 1B.** β ∈ {0.05, 0.10, 0.20} →
   overall {1.03, 1.05, 1.09}. Faint monotonic uptick but β=0.20 still loses to
   vanilla. Confirms the eval-accuracy plateau (all βs hit 0.929 eval acc).
4. **SFT-init ≈ base-init at 1B for DPO** (1.05 vs 1.07). Same as the train/eval
   metric finding. Interpret-SFT prior is invisible after DPO at this capacity.

**Caveats to disclose in writeup:**
- Absolute scores are low across the board (best 1.47 / 5). Even 3B is below the
  rubric's "mostly correct" threshold. The reference answers in the test set are
  expert-detailed (specific tools, parameter values, citations); small models
  produce generic explanations or wrong-tool recommendations.
- 3B used `max_length=384` while 1B variants used 512 (3B OOM'd at 512 in the
  4.75 GiB MIG slice). This is a ~25% truncation of long answers. Eval/judge
  metrics still favor 3B at this length, so the result holds, but a fully clean
  comparison would need 3B at 512 on a larger slice.
- Test set is 23/28 synthetic, 5/28 real (docs+SE). Synthetic chosen answers
  follow the prompt template's expected detail level; this likely amplifies the
  judge's penalty for generic outputs. Worth re-running judge on a real-question
  subset if a stronger external-validity claim is needed.

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
| DPO adapters (5 runs) | `biolite-methods/training/checkpoints/biolite-methods-dpo-methods-dpo-{1b-from-sft,3b-from-sft,1b-from-base,1b-beta005,1b-beta02}/` |
| DPO training logs | `biolite-methods/training/logs/dpo-{1b-from-sft,3b-from-sft,1b-from-base,1b-beta005,1b-beta02}.log` |
| DPO predictions (6 sets) | `biolite-methods/evaluation/results/predictions_{vanilla,dpo_1b_from_sft,dpo_3b_from_sft,dpo_1b_from_base,dpo_1b_beta005,dpo_1b_beta02}.json` |
| DPO judge scores (6 sets) | `biolite-methods/evaluation/results/judge_{vanilla,dpo_1b_from_sft,dpo_3b_from_sft,dpo_1b_from_base,dpo_1b_beta005,dpo_1b_beta02}.json` |
| Methods predictions script | `biolite-methods/evaluation/generate_predictions.py` |

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
