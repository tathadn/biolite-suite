# biolite-methods data

Raw and processed datasets are **tracked on HuggingFace, not in git**, to
match the pattern established by biolite-interpret (whose dataset lives at
`tathadn/biolite-interpret-data`). The methods dataset will live at
`tathadn/biolite-methods-data` once uploaded.

This directory contains the **collection scripts** and the **README**;
generated `*.json` data files are gitignored.

## Layout

```
data/
├── scripts/                       # collection + processing pipeline (tracked)
│   ├── scrape_biostars.py        # currently blocked by Cloudflare
│   ├── scrape_stackexchange.py   # bioinformatics.stackexchange.com (working)
│   └── generate_rejects.py       # produces rejected answers via claude -p
├── raw/                           # source dumps (gitignored)
│   └── stackexchange/stackexchange_qa.json
├── processed/                     # filtered + paired outputs (gitignored)
│   └── preference_pairs_test.json
└── splits/                        # train/val/test splits (gitignored)
```

## Sources

| Source | Status | License | Why |
|--------|--------|---------|-----|
| Biostars.org | **blocked** | CC-BY-4.0 | Cloudflare managed challenge defeats `requests`, `cloudscraper`, `curl_cffi`. Would need Playwright. |
| bioinformatics.stackexchange.com | **active** | CC-BY-SA-4.0 | Open API, no Cloudflare. Smaller corpus (~hundreds of methodology Q&A) but cleaner. |

## Pipeline

1. **Scrape** — `scrape_stackexchange.py` pulls top-voted, accepted-answer
   Q&A from a curated tag list, filters for methodology phrasing, and saves
   to `raw/stackexchange/stackexchange_qa.json`.
2. **Generate rejects** — `generate_rejects.py` calls `claude -p sonnet`
   to produce a subtly-wrong "rejected" answer for each Q&A pair, picking
   one of six error types (WRONG_TOOL, MISSING_ASSUMPTION, STAT_CONFUSION,
   OUTDATED, OVERCONFIDENT, DESIGN_FLAW). Output: `processed/preference_pairs*.json`.
3. **Upload** — push the merged dataset to HuggingFace under
   `tathadn/biolite-methods-data` and create train/val/test splits there.

## Quality notes (test batch, 50 pairs, 2026-04-19)

- 0 failures from `claude -p sonnet`
- Error type distribution roughly balanced (6–12 per type)
- Chosen↔rejected text similarity is bimodal: STAT_CONFUSION/OUTDATED/MISSING_ASSUMPTION
  produce near-copies (good DPO signal); WRONG_TOOL/OVERCONFIDENT produce full
  rewrites (weaker signal, learns style instead of correctness)
- Recommended filter for full runs: keep pairs with **0.3 < similarity < 0.97**

## Reproducing the test batch

```bash
cd biolite-methods/data/scripts
python scrape_stackexchange.py
python generate_rejects.py \
    --input ../raw/stackexchange/stackexchange_qa.json \
    --output ../processed/preference_pairs_test.json \
    --model sonnet --max_examples 50
```
