# Session State — 2026-04-15

## Status Checklist

- [x] Step 1: Download Llama 3.2 1B-Instruct tokenizer (cached, vocab=128k)
- [x] Step 2: Commit tokenizer access (aefabb8)
- [x] Step 3: BioInstruct spot-check — found 93% noise, tightened filter
- [x] Step 4: Commit filter fix (b24d92c) — 2,054 → 112 examples
- [x] Step 5: Scrape 10 GEO seed datasets — 10/10 abstracts, 6/10 full text
- [x] Step 6: Claude CLI smoke test — `claude -p "say hi" --model sonnet` works
- [x] Step 7: Synthetic test batch (20/20 success, 0 failures, biology verified)
- [ ] Step 8: Scale synthetic generation to --count 200, commit with success rate

## Resume Point

Run `generate_synthetic.py --count 200` and commit results.

```bash
source .venv/bin/activate
cd biolite-interpret/data/scripts
python generate_synthetic.py \
  --seed_file ../raw/geo_pairs/geo_paper_pairs.json \
  --output ../processed/synthetic_interpretations.json \
  --count 200 \
  --model sonnet
```

## Key Decisions

1. **BioInstruct is a clean seed, not the primary volume source.**
   Original filter kept 2,054 examples but spot-check revealed 93% were generic
   medical content (BMI interpretation, article summaries, SOAP notes) triggered
   by overly broad keywords "interpret", "summarize", "summary". Tightened to
   112 domain-relevant examples by removing broad keywords and adding specific
   compound terms (pathway analysis, expression profile, gene regulation, etc.).

2. **Synthetic generation is the primary training volume source.**
   Test batch of 20 achieved 100% success rate. JSON parses clean, word counts
   178–218 (mean 199), biology is accurate and organism-specific. Ready to scale.

3. **Claude CLI auth works via subscription** (no API key needed).
   `claude -p` with `--model sonnet` confirmed working on this HPC node.

## Data Counts

| Source | Count | Location |
|--------|-------|----------|
| BioInstruct (filtered) | 112 | data/raw/bioinstruct_filtered/bioinstruct_filtered.json |
| GEO paper pairs | 10 | data/raw/geo_pairs/geo_paper_pairs.json |
| Mol-Instructions biotext | 6 files (~28M) | data/raw/Biomolecular_Text_Instructions/ |
| Synthetic (test batch) | 20 | data/processed/synthetic_interpretations_test.json |
| Synthetic (full, pending) | 0/200 | data/processed/synthetic_interpretations.json |

## Commands to Run First Next Session

```bash
cd /fs1/scratch/tathadbn/biolite-suite
source .venv/bin/activate
cat SESSION_STATE.md
git status
git log --oneline
```
