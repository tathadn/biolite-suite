---
license: mit
task_categories:
  - text-generation
  - text2text-generation
language:
  - en
tags:
  - bioinformatics
  - gene-expression
  - differential-expression
  - pathway-analysis
  - biology
  - interpretation
size_categories:
  - 1K<n<10K
configs:
  - config_name: default
    data_files:
      - split: train
        path: train.json
      - split: validation
        path: val.json
      - split: test
        path: test.json
---

# BioLite-Interpret Data (v2)

Training data for **BioLite-Interpret**, a fine-tuned language model that generates biological interpretations of differential expression (DE) tables, GO/KEGG enrichment results, and combined analyses.

## Dataset Summary

| Metric | Value |
|--------|-------|
| Total examples | 1,262 |
| Train / Val / Test | 1,073 / 63 / 126 |
| Split ratio | 85% / 5% / 10% |
| Stratification | By `task_type` and `source` |

## Version History

- **v2 (this release)**: 1,262 examples. Expanded GEO seeds (10 → 26 across Drosophila, Arabidopsis, C. elegans) and scaled synthetic generation by +606 examples (batch3).
- **v1**: 640 examples. Retained here as an evaluation anchor: all 64 v1 test examples are pinned as a subset of v2 test, and v2 test is held out from both v1 train and v2 train, enabling leak-free comparison of models trained on either release.

## Sources

| Source | Count | Description |
|--------|-------|-------------|
| `synthetic` | 797 | Generated via Claude Sonnet with realistic DE/enrichment tables and biologically accurate interpretations across 7 model organisms and 12 experimental conditions. Batches 1+2 contributed 191 (95.5% success); batch 3 added 606 (99.5% success). |
| `mol_instructions` | 327 | Filtered from [Mol-Instructions](https://github.com/zjunlp/Mol-Instructions) Biomolecular Text Instructions (53,760 total). Kept open-question examples matching bioinformatics keywords; excluded extraction-format files and terse outputs (<20 words). |
| `bioinstruct` | 112 | Filtered from [BioInstruct](https://huggingface.co/datasets/bio-nlp-umass/bioinstruct) (25K total). Tight keyword filter for DE/enrichment/pathway interpretation; broad terms removed after spot-check revealed 93% noise. |
| `geo` | 26 | GEO dataset + published paper pairs. Each example pairs a GEO series (GSE ID, organism, contrast) with interpretation text from the associated publication. Expanded in v2 to include Drosophila (+5), Arabidopsis (+5), and C. elegans (+6) to address organism imbalance in the initial 10-seed set. |

## Filtering Methodology

All non-synthetic sources were filtered with the same tight keyword set:

**Keep keywords** (36 terms): `differential expression`, `enrichment`, `upregulated`, `downregulated`, `gene expression`, `fold change`, `rna-seq`, `transcriptom`, `go term`, `gene ontology`, `kegg`, `functional analysis`, `pathway analysis`, `expression profile`, `gene regulation`, `omics`, and others.

**Exclude keywords** (14 terms): `named entity`, `clinical trial`, `drug interaction`, `icd code`, `de-identify`, and others targeting NER, clinical, and billing tasks.

**Additional gates for Mol-Instructions:**
- Skipped 3 extraction-format files (chemical_protein, chemical_disease, chemical_entity) that produce relation tuples, not interpretive text.
- Required minimum 20-word output to drop terse multi-choice answers.

## Task Types

| Task Type | Count | Description |
|-----------|-------|-------------|
| `de_interpretation` | 896 | Interpret a differential expression results table |
| `enrichment_interpretation` | 234 | Interpret GO/KEGG enrichment results |
| `combined_interpretation` | 132 | Integrate both DE and enrichment results |

## Example Format

```json
{
  "instruction": "Interpret the following differential expression results...",
  "input": "| Gene | log2FC | padj | baseMean |\n|------|--------|------|----------|...",
  "output": "The expression profile reveals activation of immune signaling...",
  "source": "synthetic",
  "task_type": "de_interpretation"
}
```

## Synthetic Generation Details

- **Model**: Claude Sonnet via Claude Code CLI (subscription auth)
- **Organisms**: human, mouse, Drosophila, zebrafish, C. elegans, Arabidopsis, rat
- **Conditions**: tumor vs normal, drug-treated vs vehicle control, knockout vs wild-type, infected vs mock, aged vs young, high-fat diet vs control, hypoxia vs normoxia, stem cell vs differentiated, resistant vs sensitive, early stage vs late stage, stressed vs unstressed, mutant vs wild-type
- **Quality gates**: JSON parse validation, 50-400 word output range, required non-empty input
- **Aggregate success rate**: 797/815 attempted (97.8%) across 3 batches

## Split Methodology

Splits are stratified by `(task_type, source)` with a pinned v1-test anchor:

1. All 64 v1 test examples are required to appear in v2 test.
2. v2 test is extended only with examples introduced in v2 (batch3 synthetic + new GEO seeds), so that no v1 training example ends up in v2 test.
3. The remaining pool (v1 train/val + unused v2-new examples) is stratified-split into v2 train and v2 val.

This guarantees that both Phase 1 (640-data) and Phase 2 (1,262-data) models can be evaluated on v2 test without train/test leakage, making scaling comparisons apples-to-apples.

A content-hash reference of v1 splits is committed alongside the data at `v1_split_keys.json`, and `v1_test_fixed.json` contains the 64 anchor examples in human-readable form.

## Split Statistics

### Train (1,073 examples)
- By source: bioinstruct 96, geo 23, mol_instructions 277, synthetic 677
- By task_type: de_interpretation 761, enrichment_interpretation 199, combined_interpretation 113

### Validation (63 examples)
- By source: bioinstruct 5, geo 1, mol_instructions 17, synthetic 40
- By task_type: de_interpretation 45, enrichment_interpretation 12, combined_interpretation 6

### Test (126 examples)
- By source: bioinstruct 11, geo 2, mol_instructions 33, synthetic 80
- By task_type: de_interpretation 90, enrichment_interpretation 23, combined_interpretation 13
- Includes all 64 v1 test examples (pinned) + 62 new test examples drawn from v2 additions

## Intended Use

Fine-tuning small language models (e.g., Llama 3.2 1B/3B-Instruct) for automated biological interpretation of omics analysis outputs. Part of the BioLite Suite project.

## Citation

If you use this dataset, please cite:

```bibtex
@misc{biolite-interpret-data-2026,
  title={BioLite-Interpret Training Data},
  author={Tathagata Debnath},
  year={2026},
  publisher={HuggingFace},
  url={https://huggingface.co/datasets/tathadn/biolite-interpret-data}
}
```
