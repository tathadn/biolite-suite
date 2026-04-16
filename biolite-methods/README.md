# BioLite-Methods: Project Plan

## DPO Alignment of Llama 3.2 1B for Bioinformatics Methodology Advising

---

## 1. Project Overview

**Objective:** Align Llama 3.2 1B using Direct Preference Optimization (DPO) to accurately answer bioinformatics methodology questions — tool selection, parameter choices, experimental design decisions, and common pitfall avoidance.

**Hardware:** NVIDIA A100-PCIE-40GB with MIG enabled — two slices available:

| Slice | MIG Instance | VRAM | SMs |
|-------|-------------|------|-----|
| MIG 0 | GI 9 | ~4.8 GB (4864 MiB) | 14 |
| MIG 1 | GI 11 | ~4.8 GB (4864 MiB) | 14 |

**Slice allocation:** Run DPO-from-SFT on MIG 0 and DPO-from-base ablation on MIG 1 simultaneously.

**Base Model:** `tathadn/biolite-interpret-1b` (Phase 1 SFT checkpoint) OR `meta-llama/Llama-3.2-1B-Instruct` (for ablation)

**HuggingFace Deliverables:**
- Model: `tathadn/biolite-methods-1b-dpo`
- Dataset: `tathadn/biolite-methods-preferences`
- W&B training report linked from model card

**Timeline:** 2 weeks (starts after Phase 1 completion)

**Key differentiator:** Demonstrates DPO transfer from code debugging (CodeQ) to scientific methodology advising — same alignment technique, entirely different domain.

---

## 2. Task Definition

**Input:** A bioinformatics methodology question in natural language.

**Output (chosen):** An accurate, nuanced answer that recommends appropriate tools/approaches, explains assumptions, discusses trade-offs, and flags common mistakes.

**Output (rejected):** A plausible-sounding but subtly incorrect answer that makes one or more of the following errors:
- Recommends a tool without checking its assumptions
- Ignores experimental design constraints (batch effects, confounders)
- Conflates statistical and biological significance
- Uses deprecated or inappropriate workflows
- Gives overconfident single-tool recommendations without discussing alternatives
- Misinterprets statistical outputs (p-value, FDR, fold change)

### Question categories (8 domains):

| Category | Example Question | % of Dataset |
|----------|-----------------|--------------|
| DE analysis | "Should I use DESeq2 or edgeR for my 2-replicate RNA-seq experiment?" | 20% |
| Normalization | "When should I use TPM vs FPKM vs raw counts?" | 12% |
| Splicing analysis | "What's the difference between rMATS and SUPPA2 for detecting differential splicing?" | 10% |
| Microbiome/16S | "What alpha diversity metric should I use for my 16S amplicon study?" | 12% |
| Alignment/mapping | "HISAT2 vs STAR for RNA-seq alignment — when does it matter?" | 10% |
| Variant calling | "Should I use GATK HaplotypeCaller or DeepVariant for my WGS data?" | 10% |
| Experimental design | "How many biological replicates do I need for a DE experiment?" | 14% |
| Statistics/interpretation | "What does an adjusted p-value of 0.06 mean? Is my gene significant?" | 12% |

---

## 3. Dataset Construction

### 3.1 Source 1: Biostars Q&A Mining (~600–800 pairs)

**Source:** Biostars.org (CC-BY-4.0 licensed community content)

**Scraping pipeline:**

Step 1 — Identify relevant threads:
```python
# Target tags on Biostars
TARGET_TAGS = [
    "rna-seq", "deseq2", "edger", "limma", "differential-expression",
    "normalization", "alignment", "star", "hisat2", "microbiome",
    "qiime2", "16s", "splicing", "rmats", "variant-calling",
    "gatk", "experimental-design", "statistics", "enrichment",
    "go-enrichment", "kegg", "batch-effect", "pca", "clustering"
]

# Filtering criteria
MIN_VIEWS = 500
MIN_ANSWERS = 1
HAS_ACCEPTED_ANSWER = True  # preferred but not required
MIN_ANSWER_VOTES = 2
```

Step 2 — Extract Q&A pairs:
- Question = thread title + body (truncated to the core question)
- Chosen answer = accepted answer or highest-voted answer
- Clean HTML tags, code blocks (keep short code snippets, remove long scripts)
- Normalize formatting to plain text + minimal markdown

Step 3 — Filter for methodology questions:
- Keep: "which tool should I use", "how do I choose between", "what's the best practice for", "is it appropriate to", "should I", "when to use"
- Discard: pure debugging questions ("my code throws error X"), data requests ("where to download genome X"), and questions with no clear methodology component

Step 4 — Generate rejected answers:
For each (question, chosen_answer) pair, prompt a larger model to generate a rejected answer:

```
You are generating training data for preference optimization. Given the
bioinformatics question and the correct answer below, generate an
INCORRECT answer that sounds plausible but contains exactly ONE of the
following error types:

Error types (pick one randomly):
1. WRONG_TOOL: Recommends an inappropriate tool for the stated constraints
2. MISSING_ASSUMPTION: Ignores a critical assumption of the recommended method
3. STAT_CONFUSION: Conflates or misinterprets statistical concepts
4. OUTDATED: Recommends a deprecated workflow or outdated best practice
5. OVERCONFIDENT: Gives a single recommendation without discussing trade-offs
6. DESIGN_FLAW: Ignores experimental design issues like batch effects

The rejected answer should:
- Be approximately the same length as the correct answer
- Sound confident and well-written (not obviously wrong)
- Contain exactly one subtle error (not multiple)
- Be wrong in a way that a novice might not catch

Question: {question}
Correct answer: {chosen_answer}
Error type to introduce: {randomly_selected_error_type}

Generate the rejected answer:
```

**Quality control:** For each rejected answer, verify that (a) it actually contains the intended error and (b) the error is meaningfully wrong, not just a stylistic difference. Review 20% of generated rejects manually.

### 3.2 Source 2: Bioinformatics Stack Exchange (~200–300 pairs)

Same pipeline as Biostars but applied to the Bioinformatics Stack Exchange (CC-BY-SA licensed). This site tends to have more technical, well-moderated answers. Focus on questions tagged `best-practices`, `methods`, `tool-selection`.

### 3.3 Source 3: Documentation-Derived Q&A (~300–400 pairs)

Convert authoritative documentation into Q&A format:

**Sources:**
- DESeq2 vignette (Bioconductor) — parameter choice guidance, design formula construction
- limma User's Guide — when to use limma-voom vs limma-trend
- QIIME 2 documentation — diversity metrics, normalization, rarefaction decisions
- STAR manual — alignment parameter selection
- GATK best practices — variant calling pipeline decisions
- clusterProfiler documentation — ORA vs GSEA, background gene set selection
- Harvard Chan Bioinformatics Core training materials (CC-BY licensed)
- Galaxy Training Network materials (CC-BY licensed)

**Extraction method:**
- Identify decision points in documentation ("when to use X", "if your data has property Y, then...")
- Convert to question form
- Use the documentation's recommendation as the chosen answer
- Generate rejected answer using the same prompting pipeline as 3.1

### 3.4 Source 4: Review Paper Methodological Guidance (~100–200 pairs)

Key review papers to mine:

| Paper | Year | Topics |
|-------|------|--------|
| Conesa et al., "A survey of best practices for RNA-seq data analysis" (Genome Biology) | 2016 | End-to-end RNA-seq methodology |
| Love et al., DESeq2 paper (Genome Biology) | 2014 | DE analysis methodology |
| McMurdie & Holmes, "Waste not, want not: why rarefying microbiome data is inadmissible" (PLoS Comp Bio) | 2014 | Microbiome normalization |
| Soneson & Robinson, "Bias, robustness and scalability in single-cell differential expression analysis" (Nature Methods) | 2018 | scRNA-seq DE methods |
| Van den Berge et al., "RNA Sequencing Data: Hitchhiker's Guide to Expression Analysis" (Annu Rev Biomed Data Sci) | 2019 | RNA-seq best practices |

Extract methodological recommendations, convert to Q&A format, generate rejects.

### 3.5 Final Dataset Composition

| Source | Pairs | Quality Level |
|--------|-------|---------------|
| Biostars Q&A | 600–800 | High (community-vetted chosen, verified rejects) |
| Bioinformatics SE | 200–300 | High |
| Documentation-derived | 300–400 | High (authoritative source) |
| Review paper-derived | 100–200 | High |
| **Total** | **1,200–1,700** | |

**Train/validation/test split:** 85% / 5% / 10% (stratified by category)

**Dataset format:**
```json
{
  "question": "I have an RNA-seq experiment with 2 biological replicates per condition. Should I use DESeq2 or edgeR?",
  "chosen": "With only 2 replicates per condition, both DESeq2 and edgeR will struggle to estimate dispersion reliably. However, edgeR with its quasi-likelihood framework (glmQLFit) tends to be slightly more conservative and may perform better with very low replicate counts. DESeq2's shrinkage estimator can over-shrink dispersions when sample sizes are very small. That said, neither tool is ideal with n=2 — your power to detect differential expression will be very limited regardless of the tool. If possible, consider adding replicates. If not, use edgeR's QL F-test pipeline, apply a lenient FDR threshold (0.1 rather than 0.05), and validate top hits with qPCR or an independent dataset.",
  "rejected": "DESeq2 is the gold standard for differential expression analysis and works great even with 2 replicates. Its negative binomial model and Wald test are robust to small sample sizes. Just run the standard DESeq2 pipeline with default parameters and filter for padj < 0.05. There's no need to adjust your significance threshold — the Benjamini-Hochberg correction handles multiple testing automatically regardless of sample size. edgeR is an older tool and generally not recommended anymore.",
  "error_type": "OVERCONFIDENT",
  "category": "de_analysis",
  "source": "biostars"
}
```

---

## 4. Training Configuration

### 4.1 DPO Training Setup

**Starting checkpoint options (run both simultaneously on separate MIG slices):**
- **MIG 0 (GI 9):** Option A — `tathadn/biolite-interpret-1b` (SFT from Phase 1)
- **MIG 1 (GI 11):** Option B — `meta-llama/Llama-3.2-1B-Instruct` (base instruct model)

Running both ablation arms in parallel cuts wall-clock time from ~8–12 hours to ~4–6 hours.

```bash
# Terminal 1 — DPO from SFT checkpoint (MIG 0)
export CUDA_VISIBLE_DEVICES=MIG-<GI-9-uuid>
python train_dpo.py \
    --base_model tathadn/biolite-interpret-1b \
    --output_dir ./dpo-from-sft \
    --run_name dpo_from_sft

# Terminal 2 — DPO from base Instruct (MIG 1, concurrent)
export CUDA_VISIBLE_DEVICES=MIG-<GI-11-uuid>
python train_dpo.py \
    --base_model meta-llama/Llama-3.2-1B-Instruct \
    --output_dir ./dpo-from-base \
    --run_name dpo_from_base
```

**Slice allocation for Phase 2:**

| Task | Slice | When |
|------|-------|------|
| DPO-from-SFT (main model) | MIG 0 | Week 2, Day 1 |
| DPO-from-base (ablation) | MIG 1 | Week 2, Day 1 (parallel) |
| Beta ablation β=0.05 | MIG 0 | Week 2, Day 2 |
| Beta ablation β=0.2 | MIG 1 | Week 2, Day 2 (parallel) |
| Beta ablation β=0.5 | MIG 0 | Week 2, Day 2 |
| 5-way evaluation inference | MIG 1 | Week 2, Day 3 |

### 4.2 Memory Budget (4.8GB MIG slice)

| Component | Memory |
|-----------|--------|
| Base model (4-bit NF4) | ~0.8 GB |
| Reference model (4-bit, frozen, shared base weights) | ~0 GB (shared) + LoRA diff ~50 MB |
| QLoRA adapters (r=16) | ~50–80 MB |
| Optimizer states (paged AdamW 8-bit) | ~100–150 MB |
| Activations — 2 forward passes (max_seq_len=512, batch=1) | ~1.2 GB |
| Gradient checkpointing overhead | ~0.3 GB |
| CUDA overhead | ~0.5 GB |
| **Total estimated** | **~3.1–3.4 GB** |
| **Available** | **4.8 GB** |
| **Headroom** | **~1.4–1.7 GB** |

**Note:** DPO requires two forward passes (policy + reference) per step, making it more memory-intensive than SFT. The reference model is frozen and shares the base weights with the policy model (only the LoRA adapters differ), which saves significant memory. With max_length=512 (reduced from 768 in the original plan), headroom is comfortable. If memory allows after profiling, increase to max_length=640 or 768.

**Parallel ablation advantage:** With two MIG slices, the DPO-from-SFT and DPO-from-base ablation runs can execute simultaneously — one per slice — cutting ablation wall-clock time in half.

### 4.3 DPO Configuration

```python
from trl import DPOConfig, DPOTrainer
# Pin TRL version: trl==0.29.1

dpo_config = DPOConfig(
    output_dir="./biolite-methods-1b-dpo",
    num_train_epochs=2,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,        # effective batch size = 8
    learning_rate=5e-5,                   # lower LR than SFT for DPO
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    beta=0.1,                             # DPO temperature parameter
    loss_type="sigmoid",                  # standard DPO loss
    bf16=True,
    max_grad_norm=1.0,
    logging_steps=5,
    eval_strategy="steps",
    eval_steps=50,
    save_strategy="steps",
    save_steps=50,
    load_best_model_at_end=True,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    max_length=512,                       # conservative for 4.8GB; increase to 640/768 after profiling
    max_prompt_length=256,
    report_to="wandb",
)
```

### 4.4 Fp32 Logits Fix (from CodeQ)

```python
# Critical: prevent NaN overflow in DPO loss with bf16 models
# Reuse the Fp32LogitsDPOTrainer fix from CodeQ

class Fp32LogitsDPOTrainer(DPOTrainer):
    """Cast logits to float32 before DPO loss computation to prevent
    NaN overflow when training bf16 models."""

    def concatenated_forward(self, model, batch):
        outputs = super().concatenated_forward(model, batch)
        # Cast all logit-derived values to fp32
        return {k: v.float() if v.dtype == torch.bfloat16 else v
                for k, v in outputs.items()}
```

### 4.5 QLoRA Configuration (same as Phase 1)

```python
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    task_type=TaskType.CAUSAL_LM,
    bias="none",
)
```

### 4.6 Key Engineering Considerations

- **MIG slice targeting:** Set `CUDA_VISIBLE_DEVICES` to the specific MIG instance UUID. Discover UUIDs with `nvidia-smi -L`.
  ```bash
  # DPO-from-SFT (MIG 0 — GI 9)
  export CUDA_VISIBLE_DEVICES=MIG-<GPU-UUID>/<GI-9-instance>
  python train_dpo.py --base_model tathadn/biolite-interpret-1b
  
  # DPO-from-base ablation (MIG 1 — GI 11, concurrent)
  export CUDA_VISIBLE_DEVICES=MIG-<GPU-UUID>/<GI-11-instance>
  python train_dpo.py --base_model meta-llama/Llama-3.2-1B-Instruct
  ```
- **TRL pinning:** `trl==0.29.1` — same version validated in CodeQ
- **Reference model sharing:** Use `ref_model=None` in DPOTrainer with `model_init_kwargs` to share base weights; only LoRA weights differ between policy and reference
- **max_length:** Start conservative at 512 tokens; profile actual GPU usage in the first 50 steps, then increase if headroom allows (640 or 768)
- **Beta tuning:** Start with β=0.1; if reward margins are too small, try β=0.05
- **Monitor reward margins:** Log `chosen_reward - rejected_reward` per step; should increase during training and stabilize >0
- **Parallel beta ablation:** After main training completes, run β sensitivity sweeps on both slices simultaneously (β=0.05 on MIG 0, β=0.2 on MIG 1, then swap to β=0.5)

---

## 5. Evaluation

### 5.1 LLM-as-Judge (Primary Metric)

**Judge model:** Claude Sonnet via API

**Rubric (each scored 1–5):**

| Criterion | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| **Methodological Accuracy** | Recommends wrong tools, ignores assumptions | Mostly correct, misses some nuance | Accurate recommendations with proper caveats |
| **Assumption Awareness** | Ignores critical assumptions entirely | Mentions some assumptions | Explicitly discusses all relevant assumptions and when they're violated |
| **Trade-off Discussion** | Single recommendation, no alternatives | Mentions alternatives briefly | Substantive comparison of pros/cons for the specific scenario |
| **Practical Helpfulness** | Vague or textbook-only answer | Reasonable advice, some gaps | Actionable, specific to the user's stated constraints |

**Evaluation set:** 100 held-out questions from test split, stratified by category.

**Conditions compared (5-way):**

| Condition | Description |
|-----------|-------------|
| Base Llama | Llama 3.2 1B-Instruct, no fine-tuning |
| SFT-only (Phase 1) | BioLite-Interpret checkpoint |
| DPO from base | DPO applied to base Llama 3.2 1B-Instruct |
| DPO from SFT | DPO applied to Phase 1 SFT checkpoint |
| Upper bound | Claude Sonnet via API |

This 5-way comparison answers: Does SFT help DPO? Does domain SFT transfer to methodology questions? This is the core ablation story.

### 5.2 Preference Win Rate (DPO-specific metric)

**Setup:** For 100 test questions, generate answers from all model conditions. Present (question, answer_A, answer_B) pairs to the LLM judge and ask which answer is better. Compute pairwise win rates.

**Reporting format:**
```
DPO-from-SFT vs Base:      XX% win / XX% tie / XX% loss
DPO-from-SFT vs SFT-only:  XX% win / XX% tie / XX% loss
DPO-from-SFT vs DPO-from-base: XX% win / XX% tie / XX% loss
```

### 5.3 Error Type Detection (DPO-specific metric)

**Setup:** Present the model with 50 deliberately flawed methodology statements and ask it to identify the error. Measure accuracy by error type.

**Example:**
```
Input: "A researcher normalizes their RNA-seq data with TPM before running
DESeq2. Is this approach correct?"

Expected: The model should identify that DESeq2 expects raw counts, not
TPM-normalized data, and explain why pre-normalization interferes with
DESeq2's internal normalization.
```

**Error types tested:** WRONG_TOOL, MISSING_ASSUMPTION, STAT_CONFUSION, OUTDATED, DESIGN_FLAW (10 examples each)

### 5.4 Ablation Studies

1. **SFT-then-DPO vs DPO-only:** Does the Phase 1 SFT checkpoint improve DPO outcomes?
2. **Beta sensitivity:** β ∈ {0.05, 0.1, 0.2, 0.5}
3. **Dataset size:** Train on 50% vs 100% of preference data

---

## 6. HuggingFace Model Card Template

```markdown
# BioLite-Methods 1B (DPO)

## Model Description
A Llama 3.2 1B model aligned via DPO to provide accurate bioinformatics
methodology guidance — tool selection, parameter choices, experimental
design decisions, and common pitfall identification.

## Training Details
- **Base model:** tathadn/biolite-interpret-1b (Phase 1 SFT checkpoint)
- **Method:** DPO with QLoRA (r=16, alpha=32, β=0.1)
- **Hardware:** NVIDIA A100-PCIE-40GB MIG partition (~4.8GB VRAM per slice, 14 SMs)
  - DPO-from-SFT and DPO-from-base ablation trained simultaneously on two MIG slices
- **Dataset:** ~1,500 preference pairs from Biostars, Bioinformatics SE,
  and documentation-derived Q&A
- **Training time:** ~X hours
- **Peak GPU memory:** X.XX / 4.8 GB

## DPO Training Details
- **Fp32 logits fix applied:** Yes (prevents bf16 NaN overflow)
- **TRL version:** 0.29.1 (pinned for stability)
- **Reference model:** Shared base weights with policy model
- **Final reward margin (chosen - rejected):** X.XX ± X.XX

## Evaluation Results
[Table of LLM-as-Judge scores across 5 conditions]
[Preference win rate matrix]
[Error type detection accuracy by category]

## Ablation: SFT-then-DPO vs DPO-only
[Results table showing both paths]

## Limitations
- Coverage biased toward common tools (DESeq2, edgeR, STAR, GATK);
  may give less reliable advice on niche tools
- Trained on methodology Q&A from 2014–2025; some recommendations may
  not reflect very recent tool releases
- Should not replace reading the actual tool documentation for
  edge cases

## Citation
[BibTeX]
```

---

## 7. Week-by-Week Timeline

### Week 1: Dataset Construction
- [ ] Scrape Biostars threads by target tags (600–800 Q&A pairs)
- [ ] Scrape Bioinformatics SE threads (200–300 pairs)
- [ ] Extract methodology Q&A from documentation sources (300–400 pairs)
- [ ] Mine review papers for methodological recommendations (100–200 pairs)
- [ ] Generate rejected answers for all chosen answers via LLM prompting
- [ ] Quality control: verify 20% of rejected answers manually
- [ ] Finalize train/val/test splits
- [ ] Upload dataset to HuggingFace

### Week 2: Training + Evaluation
- [ ] **Parallel on both slices:** Run DPO-from-SFT on MIG 0 + DPO-from-base on MIG 1 simultaneously (~4–6 hours)
- [ ] **Parallel beta ablation:** β=0.05 on MIG 0 + β=0.2 on MIG 1 (~2 hours), then β=0.5 on MIG 0 (~2 hours)
- [ ] Run 5-way LLM-as-Judge evaluation (100 test examples) — inference on MIG 1
- [ ] Compute preference win rates
- [ ] Run error type detection evaluation
- [ ] Write model card with full results
- [ ] Write dataset card
- [ ] Upload model checkpoint to HuggingFace

---

## 8. Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| DPO loss becomes NaN | Medium | Apply Fp32LogitsDPOTrainer fix (already validated in CodeQ) |
| 4.8GB insufficient for dual forward pass | Low | ~1.4GB headroom at max_length=512; increase max_length after profiling; fallback: reduce r to 8 or drop double quantization |
| Rejected answers are too obviously wrong | High | Include error type label in generation prompt; manually review 20%; re-generate rejects that are too blatant |
| Rejected answers are too similar to chosen | Medium | Compute ROUGE between chosen/rejected; re-generate pairs with ROUGE-L > 0.8 |
| Biostars scraping yields mostly debugging Q&A | Medium | Strict keyword filtering on methodology-related terms; manual curation pass |
| DPO training collapses (reward margin doesn't increase) | Low | Monitor reward margin per step; reduce beta; try different learning rates |
| SFT-then-DPO shows no benefit over DPO-only | Medium | This is still a publishable finding — report honestly, discuss why |

---

## 9. Repository Structure

```
biolite-methods/
├── data/
│   ├── scripts/
│   │   ├── scrape_biostars.py
│   │   ├── scrape_bioinformatics_se.py
│   │   ├── extract_from_docs.py
│   │   ├── extract_from_papers.py
│   │   ├── generate_rejects.py
│   │   ├── quality_control.py
│   │   └── compute_pair_similarity.py
│   ├── raw/
│   ├── processed/
│   └── splits/
├── training/
│   ├── train_dpo.py
│   ├── fp32_logits_trainer.py
│   ├── config.yaml
│   └── requirements.txt
├── evaluation/
│   ├── llm_judge.py
│   ├── preference_winrate.py
│   ├── error_detection_eval.py
│   ├── ablation_runner.py
│   └── results/
├── README.md
└── LICENSE
```

---

## 10. Connection to CodeQ (Portfolio Narrative)

This project explicitly reuses and extends CodeQ infrastructure:

| Component | CodeQ | BioLite-Methods |
|-----------|-------|-----------------|
| DPO trainer | Fp32LogitsDPOTrainer | Same class, same fix |
| TRL version | 0.29.1 | 0.29.1 |
| Training infra | simurgh H100 nodes | A100 MIG 4.8GB slices (×2) |
| Domain | Code debugging | Bioinformatics methodology |
| Preference data | Correct vs buggy code | Accurate vs subtly flawed advice |
| Evaluation | DebugBench pass rate | LLM-as-Judge + error detection |

The portfolio story: "I developed a DPO training pipeline for code debugging, then transferred it to scientific methodology advising on MIG-partitioned hardware with <5GB per slice — proving the approach generalizes across domains and scales down to constrained infrastructure."

---

## 11. Publication Angle

**Target venues:**
- BioNLP Workshop (at ACL/EMNLP)
- ISMB/ECCB proceedings
- Bioinformatics Applications Notes (Oxford)

**Paper framing:** "Small Language Models as Bioinformatics Methodology Advisors: Domain-Specialized SLMs via DPO under Hardware Constraints"

**Core contributions:**
1. First preference dataset for bioinformatics methodology advising (released publicly)
2. Demonstration that sub-2B parameter models can provide meaningful methodological guidance after targeted DPO alignment
3. Empirical analysis of SFT-then-DPO vs DPO-only for domain transfer
4. Complete reproducibility under 4.8GB GPU memory constraint (MIG-partitioned A100)

**What makes it publishable (even as a workshop paper):**
- Novel dataset (no existing bioinformatics preference dataset for methodology)
- Clear ablation structure (5-way comparison + beta sensitivity)
- Practical relevance (bioinformatics methodology is a real bottleneck)
- Reproducibility story (4.8GB MIG constraint, all data public, all code released)
- Parallel ablation on dual MIG slices demonstrates practical hardware-aware ML engineering
