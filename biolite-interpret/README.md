# BioLite-Interpret: Project Plan

## Supervised Fine-Tuning of Llama 3.2 1B for Bioinformatics Result Interpretation

---

## 1. Project Overview

**Objective:** Fine-tune Llama 3.2 1B with QLoRA to interpret structured bioinformatics outputs (DESeq2 differential expression tables, GO/KEGG enrichment results) and generate biologically accurate natural language summaries.

**Hardware:** NVIDIA A100-PCIE-40GB with MIG enabled — two slices available:

| Slice | MIG Instance | VRAM | SMs |
|-------|-------------|------|-----|
| MIG 0 | GI 9 | ~4.8 GB (4864 MiB) | 14 |
| MIG 1 | GI 11 | ~4.8 GB (4864 MiB) | 14 |

**Slice allocation:** Train on MIG 0, run evaluation inference on MIG 1 (concurrent).

**Base Model:** `meta-llama/Llama-3.2-1B-Instruct`

**HuggingFace Deliverables:**
- Model: `tathadn/biolite-interpret-1b`
- Dataset: `tathadn/biolite-interpret-data`
- W&B training report linked from model card

**Timeline:** 3–4 weeks

---

## 2. Task Definition

**Input format (structured):**
```
Below is a DESeq2 differential expression results table from an RNA-seq
experiment comparing [condition A] vs [condition B] in [organism].

| Gene     | log2FC | padj     | baseMean |
|----------|--------|----------|----------|
| GENE1    | 3.42   | 1.2e-15  | 2841.3   |
| GENE2    | -2.87  | 3.4e-12  | 1523.7   |
| ...      | ...    | ...      | ...      |

Provide a biological interpretation of these results.
```

**Output format (narrative):**
A 100–250 word paragraph that: identifies upregulated and downregulated functional themes, connects gene expression changes to biological processes or pathways, notes the experimental context, and flags any caveats (e.g., small fold changes, few replicates).

**Task variants (3 types within one model):**
1. **DE table → narrative** (primary, ~60% of data)
2. **GO/KEGG enrichment table → pathway summary** (~25% of data)
3. **Combined DE + enrichment → integrated interpretation** (~15% of data)

---

## 3. Dataset Construction

### 3.1 Source 1: BioInstruct Filtering (~1,500–2,000 examples)

**Source:** `bio-nlp-umass/bioinstruct` (25K instructions, CC-BY-4.0 compatible)

**Filtering criteria:**
- Keep instructions involving: interpreting results, summarizing biological findings, explaining gene expression changes, describing pathway enrichment
- Discard: NER tasks, clinical trial eligibility, diagnosis tasks, drug mechanism tasks
- Reformat surviving examples into the structured input → narrative output template

**Script outline:**
```python
from datasets import load_dataset

ds = load_dataset("bio-nlp-umass/bioinstruct")

# Keywords for filtering
KEEP_KEYWORDS = [
    "interpret", "summarize", "differential expression", "enrichment",
    "upregulated", "downregulated", "pathway", "gene expression",
    "fold change", "RNA-seq", "transcriptom", "biological significance",
    "GO term", "KEGG", "functional analysis"
]

filtered = ds.filter(
    lambda x: any(kw in x["instruction"].lower() or kw in x["output"].lower()
                   for kw in KEEP_KEYWORDS)
)
```

**Post-filtering:** Manual review of a 10% sample to remove false positives and assess quality. Reformat all kept examples into the Alpaca-style template.

### 3.2 Source 2: GEO + Published Paper Pairing (~500–800 examples)

**Pipeline:**

Step 1 — Select GEO datasets:
- Query NCBI GEO for RNA-seq Series (GSE) with associated PubMed IDs
- Filter for: human, mouse, or Drosophila; clear 2-group contrasts (e.g., treatment vs control, disease vs normal, KO vs WT); ≥3 replicates per group; published 2018–2025
- Target: 40–60 datasets

Step 2 — Extract DE results:
- Use GEO2R's R API or run DESeq2 locally on the count matrices
- Extract top 15–20 DE genes (by adjusted p-value) per contrast
- Format as the structured table input

Step 3 — Extract interpretations from papers:
- Fetch the linked PubMed abstract + full text (where available via PMC Open Access)
- Use NCBI E-utilities API: `efetch.fcgi?db=pmc&id=PMCID&rettype=full`
- Extract the results/discussion paragraphs that interpret the DE findings
- If full text unavailable, use the abstract's results sentence

Step 4 — Pair and format:
- Match each DE table with the corresponding interpretation paragraph
- Add metadata: organism, experimental condition, contrast description
- Manual review of all pairs for correctness

**Example GEO datasets to start with:**

| GSE ID | Organism | Contrast | PMC Available |
|--------|----------|----------|---------------|
| GSE50760 | Human | Colorectal cancer vs normal | Yes |
| GSE72056 | Human | Melanoma single-cell types | Yes |
| GSE108643 | Mouse | Macrophage polarization M1 vs M2 | Yes |
| GSE132903 | Human | Alzheimer's vs control brain | Yes |
| GSE126848 | Human | NASH vs healthy liver | Yes |

### 3.3 Source 3: Pathway Enrichment Generation (~500–700 examples)

- Run clusterProfiler (GO BP/MF/CC + KEGG) on the DE gene lists from Source 2
- Format enrichment results as structured tables (term, gene count, p.adjust, gene ratio)
- Generate interpretation paragraphs using Claude API with the biological context from the paper
- Prompt template:

```
You are a computational biologist. Given this GO enrichment result from
a [organism] [contrast] experiment, write a 100-200 word biological
interpretation. Focus on: which biological processes are enriched and why
they make sense given the experimental context, connections between
enriched terms, and any surprising findings.

[enrichment table]
```

- Manual verification of 15% sample for biological accuracy

### 3.4 Source 4: Synthetic Expansion (~800–1,000 examples)

Using the ~800 verified real pairs from Sources 2–3 as seeds:
- Vary organism (extend to zebrafish, C. elegans, Arabidopsis)
- Vary experimental conditions (drug treatment, time course, developmental stage)
- Vary the number and identity of top genes
- Generate using Claude API with high temperature (0.7–0.8) for diversity
- Apply automatic quality filter: reject outputs <50 or >300 words, reject outputs missing gene names, reject outputs with hedging language >30% of sentences

### 3.5 Final Dataset Composition

| Source | Examples | Quality Level |
|--------|----------|---------------|
| BioInstruct (filtered + reformatted) | 1,500–2,000 | Medium (automated filter) |
| GEO + paper pairs | 500–800 | High (manually verified) |
| Pathway enrichment (generated) | 500–700 | Medium-High (15% verified) |
| Synthetic expansion | 800–1,000 | Medium (auto-filtered) |
| **Total** | **3,300–4,500** | |

**Train/validation/test split:** 85% / 5% / 10% (stratified by task variant)

**Dataset format:** HuggingFace Datasets, Alpaca-style JSON:
```json
{
  "instruction": "Interpret the following DESeq2 results from a human colorectal cancer vs normal colon RNA-seq experiment.",
  "input": "| Gene | log2FC | padj | baseMean |\n|------|--------|------|----------|\n| MMP7 | 4.21 | 2.1e-18 | 3421 | ...",
  "output": "The differential expression results reveal strong upregulation of matrix metalloproteinases (MMP7, MMP1) and ...",
  "metadata": {
    "organism": "human",
    "contrast": "tumor_vs_normal",
    "task_type": "de_interpretation",
    "source": "geo_paper_pair",
    "geo_id": "GSE50760"
  }
}
```

---

## 4. Training Configuration

### 4.1 Memory Budget (4.8GB MIG slice)

| Component | Memory |
|-----------|--------|
| Base model (4-bit NF4) | ~0.8 GB |
| QLoRA adapters (r=16) | ~50–80 MB |
| Optimizer states (paged AdamW 8-bit) | ~100–150 MB |
| Activations + KV cache (max_seq_len=1024, batch=1) | ~1.5–2.0 GB |
| Gradient checkpointing overhead | ~0.5 GB |
| CUDA overhead + fragmentation | ~0.8 GB |
| **Total estimated** | **~4.0–4.3 GB** |
| **Available** | **4.8 GB** |
| **Headroom** | **~500–800 MB** |

### 4.2 Hardware Setup (MIG Slice Targeting)

```bash
# Step 1: Discover MIG instance UUIDs
nvidia-smi -L
# Expected output includes lines like:
#   GPU 0: NVIDIA A100-PCIE-40GB (UUID: GPU-xxxx)
#     MIG 1g.5gb  Device 0: (UUID: MIG-xxxx-xxxx/.../9/0)
#     MIG 1g.5gb  Device 1: (UUID: MIG-xxxx-xxxx/.../11/0)

# Step 2: Target MIG 0 (GI 9) for training
export CUDA_VISIBLE_DEVICES=MIG-<full-uuid-from-step-1>

# Step 3: Verify — should show ~4864 MiB
python -c "import torch; print(torch.cuda.get_device_properties(0).total_mem / 1e6, 'MB')"

# Step 4 (optional): In a separate terminal, target MIG 1 (GI 11) for eval
export CUDA_VISIBLE_DEVICES=MIG-<second-uuid-from-step-1>
```

**Slice allocation for Phase 1:**

| Task | Slice | When |
|------|-------|------|
| SFT training (main + ablations) | MIG 0 | Week 3 |
| Synthetic data generation (inference) | MIG 1 | Weeks 1–2 |
| LLM-as-Judge evaluation inference | MIG 1 | Week 3 (concurrent with training) |
| LoRA rank ablation (r=8 vs r=32) | MIG 0 + MIG 1 | Week 3 (parallel) |

### 4.3 QLoRA Configuration

```python
from peft import LoraConfig, TaskType

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

### 4.4 Training Hyperparameters

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./biolite-interpret-1b",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,       # effective batch size = 16
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    weight_decay=0.01,
    bf16=True,
    max_grad_norm=1.0,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    max_seq_length=1024,
    report_to="wandb",
)
```

### 4.5 Quantization Configuration

```python
from transformers import BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
```

### 4.6 Key Engineering Considerations

- **MIG slice targeting:** Set `CUDA_VISIBLE_DEVICES` to the specific MIG instance UUID before launching training or inference. Discover UUIDs with `nvidia-smi -L`.
  ```bash
  # Training (MIG 0 — GI 9)
  export CUDA_VISIBLE_DEVICES=MIG-<GPU-UUID>/<GI-9-instance>
  
  # Evaluation inference (MIG 1 — GI 11, concurrent)
  export CUDA_VISIBLE_DEVICES=MIG-<GPU-UUID>/<GI-11-instance>
  ```
- **Pin TRL version:** Use `trl==0.29.1` (known stable from CodeQ)
- **Gradient checkpointing:** Recommended even with ~500MB headroom; provides safety margin against OOM from variable-length sequences
- **Sequence length:** Cap at 1024 tokens; DE tables + interpretations rarely exceed this
- **Paged optimizers:** `paged_adamw_8bit` offloads optimizer states to CPU when GPU memory is tight
- **Monitor GPU memory:** Log `torch.cuda.max_memory_allocated()` per step for model card
- **Dual-slice parallelism:** Train on MIG 0 while running synthetic data generation (inference) or evaluation on MIG 1 — eliminates stop-train-evaluate-restart cycles

---

## 5. Evaluation

### 5.1 LLM-as-Judge (Primary Metric)

**Judge model:** Claude Sonnet via API (or GPT-4o)

**Rubric (each scored 1–5):**

| Criterion | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| **Biological Accuracy** | Factual errors, wrong gene functions | Mostly correct, minor imprecisions | Accurate gene functions, correct pathway associations |
| **Completeness** | Mentions <30% of key findings | Covers major findings, misses nuance | Addresses all significant DE genes, enrichment themes, caveats |
| **Clarity** | Jargon-heavy or incoherent | Understandable but awkward | Clear, well-structured, accessible to biologist audience |

**Evaluation set:** 100 held-out examples (from test split), stratified by task variant.

**Conditions compared:**

| Condition | Model |
|-----------|-------|
| Baseline | Llama 3.2 1B-Instruct (no fine-tuning) |
| BioLite-Interpret | Fine-tuned model |
| Upper bound | Claude Sonnet via API (same prompt) |

**Reporting:** Mean ± std for each criterion per condition. Wilcoxon signed-rank test for statistical significance between baseline and fine-tuned.

### 5.2 Automatic Metrics (Secondary)

- **ROUGE-L** against reference interpretations (for GEO-paper pairs only)
- **BERTScore** (using `microsoft/deberta-xlarge-mnli`)
- **Length compliance:** % of outputs within 50–300 word target range
- **Hallucination rate:** % of outputs mentioning genes not present in the input table (manual check on 50 examples)

### 5.3 Ablation Studies

1. **Dataset size:** Train on 25%, 50%, 75%, 100% of data → plot learning curve
2. **LoRA rank:** Compare r=8 vs r=16 vs r=32
3. **Task mixing:** Train on DE-only vs all 3 task variants → does multi-task help?

---

## 6. HuggingFace Model Card Template

```markdown
# BioLite-Interpret 1B

## Model Description
A Llama 3.2 1B model fine-tuned with QLoRA for interpreting bioinformatics
results (differential expression tables, pathway enrichment) as natural
language summaries.

## Training Details
- **Base model:** meta-llama/Llama-3.2-1B-Instruct
- **Method:** QLoRA (r=16, alpha=32)
- **Hardware:** NVIDIA A100-PCIE-40GB MIG partition (~4.8GB VRAM per slice, 14 SMs)
  - Training on MIG 0, evaluation inference on MIG 1 (concurrent)
  - LoRA rank ablations run in parallel across both slices
- **Dataset:** ~3,500 instruction pairs from BioInstruct + GEO/paper pairs
- **Training time:** ~X hours
- **Peak GPU memory:** X.XX / 4.8 GB

## Evaluation Results
[Table of LLM-as-Judge scores across conditions]

## Limitations
- Trained primarily on human/mouse data; may underperform on plant or
  non-model organisms
- Cannot replace expert biological interpretation; outputs should be
  verified by domain specialists
- Limited to tabular DE/enrichment inputs; does not process raw count
  matrices or FASTQ files

## Citation
[BibTeX]
```

---

## 7. Week-by-Week Timeline

### Week 1: Dataset Construction (Part 1)
- [ ] Filter BioInstruct dataset, reformat to template
- [ ] Select 40–60 GEO datasets, verify PMC access for linked papers
- [ ] Set up GEO2R automation script (R)
- [ ] Begin extracting DE tables + paper interpretation pairs

### Week 2: Dataset Construction (Part 2)
- [ ] Complete GEO-paper pairing
- [ ] Run clusterProfiler enrichment on DE gene lists
- [ ] Generate pathway interpretation examples via Claude API
- [ ] Run synthetic expansion
- [ ] Manual verification pass (10–15% of generated data)
- [ ] Finalize train/val/test splits, upload dataset to HuggingFace

### Week 3: Training + Evaluation
- [ ] Set up training environment on MIG 0 (GI 9)
- [ ] Run main training (3 epochs, ~6–10 hours) on MIG 0
- [ ] **In parallel on MIG 1 (GI 11):** Run LLM-as-Judge evaluation on intermediate checkpoints
- [ ] Run ablation experiments (dataset size on MIG 0, LoRA rank on MIG 1 — parallel)
- [ ] Compute automatic metrics (ROUGE-L, BERTScore) on MIG 1

### Week 4: Documentation + Release
- [ ] Write HuggingFace model card with full results
- [ ] Write dataset card
- [ ] Upload model checkpoint + merged weights
- [ ] Log W&B training curves
- [ ] Create minimal Gradio/Spaces demo (optional)

---

## 8. Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| GEO-paper interpretation extraction is noisy | High | Use only abstracts + manual verification; accept smaller but cleaner dataset |
| 4.8GB VRAM insufficient with gradient checkpointing | Low | ~500MB headroom at 4.8GB; reduce max_seq_len to 768; reduce r to 8; drop double quantization |
| Model generates hallucinated gene names | Medium | Post-hoc filter checking output genes against input table; report hallucination rate |
| BioInstruct filtering yields too few relevant examples | Medium | Broaden keyword list; supplement with Mol-Instructions biotext subset |
| Low ROUGE scores due to legitimate paraphrase variation | High | Rely primarily on LLM-as-Judge; report ROUGE as secondary only |

---

## 9. Repository Structure

```
biolite-interpret/
├── data/
│   ├── scripts/
│   │   ├── filter_bioinstruct.py
│   │   ├── scrape_geo_papers.py
│   │   ├── run_deseq2.R
│   │   ├── run_enrichment.R
│   │   ├── generate_synthetic.py
│   │   └── quality_filter.py
│   ├── raw/
│   ├── processed/
│   └── splits/
├── training/
│   ├── train.py
│   ├── config.yaml
│   └── requirements.txt
├── evaluation/
│   ├── llm_judge.py
│   ├── auto_metrics.py
│   ├── ablation_runner.py
│   └── results/
├── demo/
│   └── app.py (Gradio)
├── README.md
└── LICENSE
```
