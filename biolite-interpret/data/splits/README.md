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
  - n<1K
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

# BioLite-Interpret Data

Training data for **BioLite-Interpret**, a fine-tuned language model that generates biological interpretations of differential expression (DE) tables, GO/KEGG enrichment results, and combined analyses.

## Dataset Summary

| Metric | Value |
|--------|-------|
| Total examples | 640 |
| Train / Val / Test | 543 / 33 / 64 |
| Split ratio | 85% / 5% / 10% |
| Stratification | By `task_type` and `source` |

## Sources

| Source | Count | Description |
|--------|-------|-------------|
| `synthetic` | 191 | Generated via Claude Sonnet with realistic DE/enrichment tables and biologically accurate interpretations across 7 model organisms and 12 experimental conditions. 95.5% success rate (191/200). |
| `mol_instructions` | 327 | Filtered from [Mol-Instructions](https://github.com/zjunlp/Mol-Instructions) Biomolecular Text Instructions (53,760 total). Kept open-question examples matching bioinformatics keywords; excluded extraction-format files and terse outputs (<20 words). |
| `bioinstruct` | 112 | Filtered from [BioInstruct](https://huggingface.co/datasets/bio-nlp-umass/bioinstruct) (25K total). Tight keyword filter for DE/enrichment/pathway interpretation; broad terms removed after spot-check revealed 93% noise. |
| `geo` | 10 | GEO dataset + published paper pairs. Each example pairs a GEO series (GSE ID, organism, contrast) with interpretation text from the associated publication. |

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
| `de_interpretation` | 520 | Interpret a differential expression results table |
| `enrichment_interpretation` | 92 | Interpret GO/KEGG enrichment results |
| `combined_interpretation` | 28 | Integrate both DE and enrichment results |

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
- **Success rate**: 191/200 (95.5%) across 2 batches

## Split Statistics

### Train (543 examples)
- By source: bioinstruct 96, geo 8, mol_instructions 277, synthetic 162
- By task_type: de_interpretation 441, enrichment_interpretation 78, combined_interpretation 24

### Validation (33 examples)
- By source: bioinstruct 5, geo 1, mol_instructions 17, synthetic 10
- By task_type: de_interpretation 27, enrichment_interpretation 5, combined_interpretation 1

### Test (64 examples)
- By source: bioinstruct 11, geo 1, mol_instructions 33, synthetic 19
- By task_type: de_interpretation 52, enrichment_interpretation 9, combined_interpretation 3

## Intended Use

Fine-tuning small language models (e.g., Llama 3.2 1B-Instruct) for automated biological interpretation of omics analysis outputs. Part of the BioLite Suite project.

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
