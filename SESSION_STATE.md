# Session State — 2026-04-17

## Status Checklist

- [x] Step 1: Download Llama 3.2 1B-Instruct tokenizer (cached, vocab=128k)
- [x] Step 2: Commit tokenizer access (aefabb8)
- [x] Step 3: BioInstruct spot-check — found 93% noise, tightened filter
- [x] Step 4: Commit filter fix (b24d92c) — 2,054 → 112 examples
- [x] Step 5: Scrape 10 GEO seed datasets — 10/10 abstracts, 6/10 full text
- [x] Step 6: Claude CLI smoke test — `claude -p "say hi" --model sonnet` works
- [x] Step 7: Synthetic test batch (20/20 success, 0 failures, biology verified)
- [x] Step 8: Scale synthetic gen — 191/200 (95.5%), batch1=97, batch2=94
- [x] Step 9: Filter Mol-Instructions biotext — 327/53,760 kept (0.61%)
- [x] Step 10: Merge all 4 sources → 640 examples, create train/val/test splits
- [x] Step 11: Upload dataset to HuggingFace (tathadn/biolite-interpret-data)
- [ ] Step 12: Fine-tune Llama 3.2 1B-Instruct on merged dataset

## Resume Point

Dataset is ready. Next: fine-tune Llama 3.2 1B-Instruct using LoRA/QLoRA on the merged dataset.

```bash
cd /fs1/scratch/tathadbn/biolite-suite
source .venv/bin/activate
cat SESSION_STATE.md
git log --oneline
```

## Key Decisions

1. **BioInstruct is a clean seed, not the primary volume source.**
   Original filter kept 2,054 examples but spot-check revealed 93% were generic
   medical content (BMI interpretation, article summaries, SOAP notes) triggered
   by overly broad keywords "interpret", "summarize", "summary". Tightened to
   112 domain-relevant examples by removing broad keywords and adding specific
   compound terms (pathway analysis, expression profile, gene regulation, etc.).

2. **Synthetic generation is the primary training volume source.**
   Test batch of 20 achieved 100% success rate. Full run: 191/200 (95.5%).
   7 organisms, 12 conditions, 3 task types. No quality degradation in late runs.

3. **Claude CLI auth works via subscription** (no API key needed).
   `claude -p` with `--model sonnet` confirmed working on this HPC node.

4. **Mol-Instructions as supplementary source.**
   327 examples from open_question/true_or_false after tight filtering.
   Extraction-format files skipped (false positives). Min 20-word output gate
   drops terse multi-choice answers.

5. **Dataset hosted on HuggingFace** at tathadn/biolite-interpret-data.
   Splits: 543 train / 33 val / 64 test (85/5/10, stratified by task_type+source).

## Data Counts

| Source | Count | Location |
|--------|-------|----------|
| BioInstruct (filtered) | 112 | data/raw/bioinstruct_filtered/bioinstruct_filtered.json |
| GEO paper pairs | 10 | data/raw/geo_pairs/geo_paper_pairs.json |
| Mol-Instructions (filtered) | 327 | data/raw/mol_instructions_filtered/mol_instructions_filtered.json |
| Synthetic (merged) | 191 | data/processed/synthetic_interpretations.json |
| **Merged dataset** | **640** | data/processed/merged_dataset.json |
| Train split | 543 | data/splits/train.json |
| Val split | 33 | data/splits/val.json |
| Test split | 64 | data/splits/test.json |

## Commands to Run First Next Session

```bash
cd /fs1/scratch/tathadbn/biolite-suite
source .venv/bin/activate
cat SESSION_STATE.md
git status
git log --oneline
```
