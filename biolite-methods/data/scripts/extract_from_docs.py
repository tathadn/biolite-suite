#!/usr/bin/env python3
"""
extract_from_docs.py — Generate methodology Q&A pairs grounded in
authoritative bioinformatics documentation.

Uses Claude Code CLI (claude -p) to produce Q&A pairs that mirror
decision-point guidance actually given in the documentation. Topic
lists reference specific sections of each source so the generated
"chosen" answers stay anchored to what the docs actually say.

Output is in the same Q&A format as scrape_stackexchange.py so that
generate_rejects.py can be run on it unchanged.

Currently supports:
  - DESeq2 vignette (Bioconductor) — DE analysis, normalization
  - QIIME 2 documentation — microbiome / 16S methodology

Usage:
    python extract_from_docs.py \
        --source deseq2 --n_pairs 40 \
        --output ../raw/docs/docs_deseq2_qa.json

    python extract_from_docs.py \
        --source qiime2 --n_pairs 50 \
        --output ../raw/docs/docs_qiime2_qa.json
"""

import argparse
import json
import os
import re
import subprocess
import time
from typing import Optional


SOURCES = {
    "deseq2": {
        "display_name": "DESeq2 vignette (Bioconductor)",
        "source_tag": "docs-deseq2-vignette",
        "primary_category": "deseq2",
        "topic_hints": [
            ("Count matrix input",                "raw counts only; never pre-normalize; why TPM/FPKM break DESeq2", ["normalization", "deseq2"]),
            ("Design formula construction",       "factor order, controlling for batch, additive vs interaction models",  ["experimental-design", "deseq2"]),
            ("Interaction terms",                 "when to use ~batch+condition+batch:condition; interpreting results",  ["experimental-design", "deseq2"]),
            ("Pre-filtering low-count genes",     "why keep >=10 counts across N samples; effect on multiple testing",  ["deseq2", "differential-expression"]),
            ("Independent filtering",             "how it works; when to disable; relation to alpha parameter",          ["deseq2", "statistics"]),
            ("Dispersion estimation",             "gene-wise vs fitted; outlier flagging; plotDispEsts diagnostics",     ["deseq2", "statistics"]),
            ("Size factor estimation",            "median of ratios; when default fails (e.g., very few common genes)",  ["normalization", "deseq2"]),
            ("LFC shrinkage — apeglm",            "when apeglm is appropriate; why it needs MLE estimates; citation",    ["deseq2", "differential-expression"]),
            ("LFC shrinkage — normal vs ashr",    "tradeoffs between shrinkage priors; when to use which",               ["deseq2", "differential-expression"]),
            ("results() contrast specification",  "using contrast=c(col, level, ref) vs name=; pairwise comparisons",    ["deseq2", "differential-expression"]),
            ("Multiple testing alpha",            "default alpha=0.1; when to lower; interaction with independent filt", ["deseq2", "statistics"]),
            ("Cook's distance outlier handling",  "automatic flagging; minReplicatesForReplace; row-level replacement",  ["deseq2", "statistics"]),
            ("p-value histogram diagnostics",     "what healthy/unhealthy histograms look like; when to be suspicious",  ["deseq2", "statistics"]),
            ("Time course / LRT",                 "likelihood ratio test vs Wald; reduced design for time series",       ["deseq2", "experimental-design"]),
            ("Variance stabilizing transformation", "vst vs rlog; when each is preferred; downstream uses (PCA, clustering)", ["deseq2", "normalization"]),
            ("Batch effects and known covariates", "including in design vs removing with limma::removeBatchEffect",     ["experimental-design", "deseq2"]),
            ("Single-cell vs bulk",               "why DESeq2 defaults don't fit sc data; when to switch tools",         ["deseq2", "differential-expression"]),
            ("Log-fold-change reporting",         "shrunken vs unshrunken for ranking vs reporting; effect sizes",       ["deseq2", "differential-expression"]),
            ("Zero-count genes and all-zero rows", "filtering behavior; independentFiltering consequences",              ["deseq2", "differential-expression"]),
            ("lfcThreshold for effect-size tests", "altHypothesis options; 'biological significance' via effect size",   ["deseq2", "statistics"]),
        ],
    },
    "qiime2": {
        "display_name": "QIIME 2 documentation",
        "source_tag": "docs-qiime2",
        "primary_category": "microbiome",
        "topic_hints": [
            ("Denoising: DADA2 vs Deblur",                    "exact sequence variants; read-length requirements; pros/cons",        ["microbiome", "qiime2"]),
            ("Primer trimming before denoising",              "why required; cutadapt integration",                                  ["microbiome", "qiime2"]),
            ("Quality filtering cutoffs",                     "interactive quality plot; trunc-len-f / trunc-len-r choice",          ["microbiome", "qiime2"]),
            ("Taxonomic classification — Naive Bayes",        "q2-feature-classifier; pre-trained vs custom classifier",             ["microbiome", "qiime2"]),
            ("Reference database version control",            "SILVA vs Greengenes2; matching primers to region",                    ["microbiome", "qiime2"]),
            ("Rarefaction vs proportions vs CSS",             "sampling depth selection; alpha/beta metric interactions",            ["microbiome", "normalization"]),
            ("Core diversity metrics phylogenetic",           "what's computed; required rooted tree; sampling-depth parameter",     ["microbiome", "qiime2"]),
            ("Alpha diversity metric choice",                 "Shannon vs observed features vs Faith's PD; assumptions",             ["microbiome", "statistics"]),
            ("Beta diversity metric choice",                  "Bray-Curtis vs weighted/unweighted UniFrac; abundance vs presence",   ["microbiome", "statistics"]),
            ("Differential abundance — ANCOM",                "compositionality; assumptions; interpreting W statistic",             ["microbiome", "differential-expression"]),
            ("Differential abundance — LEfSe vs q2-composition", "why LEfSe is discouraged; composition-aware alternatives",        ["microbiome", "differential-expression"]),
            ("Sampling depth selection",                      "reading the alpha-rarefaction plot; tradeoff with sample retention",  ["microbiome", "qiime2"]),
            ("Filtering low-frequency features",              "q2-feature-table filter-features; min-frequency / min-samples",       ["microbiome", "qiime2"]),
            ("Phylogenetic tree construction",                "MAFFT + FastTree default; SEPP fragment insertion alternative",       ["microbiome", "qiime2"]),
            ("PERMANOVA for group comparisons",               "assumptions; dispersion confound; beta-disper pre-check",             ["microbiome", "statistics"]),
            ("Longitudinal microbiome analysis",              "q2-longitudinal; paired samples; linear mixed models",                ["microbiome", "experimental-design"]),
            ("Sequencing depth heterogeneity",                "why raw counts can't be compared; downstream implications",           ["microbiome", "normalization"]),
            ("Reading the taxa bar plot",                     "collapse to rank; when taxa look artefactual",                        ["microbiome", "qiime2"]),
            ("Contamination and negative controls",           "q2-quality-control; deblur --p-no-hashed-feature-ids",                ["microbiome", "experimental-design"]),
            ("Classifier confidence threshold",               "--p-confidence default; tradeoff with unclassified reads",            ["microbiome", "qiime2"]),
        ],
    },
}


BATCH_PROMPT = """You are generating training data (methodology Q&A pairs) for a bioinformatics advisor model, grounded in the **{source_name}**.

Produce exactly {n} Q&A pairs. For each pair:
- The QUESTION should be a realistic methodology question a researcher might ask — something they'd post on a forum or ask a bioinformatics consultant.
- The CHOSEN answer must reflect the guidance actually given in the {source_name}. Do NOT invent behavior that contradicts the documentation. If you are unsure about a specific claim, stick to well-established guidance that is unambiguously covered in the docs.
- Chosen answers must be 120-280 words. Include specific mechanism/justification, not just "use X".
- Prefer answers that discuss trade-offs, assumptions, and when the default is wrong.

Topics to cover (use each topic at most twice; spread questions across topics):
{topic_block}

Respond with ONLY a JSON array, nothing else (no preamble, no markdown fences):
[
  {{
    "question": "<question text>",
    "chosen": "<answer text, 120-280 words>",
    "tags": ["<primary-category>", "<secondary-tag>"],
    "doc_section": "<section of {source_name} the answer draws from>"
  }},
  ...
]
"""


def call_claude(prompt: str, model: str = "sonnet", timeout: int = 240) -> Optional[str]:
    cmd = ["claude", "-p", prompt, "--output-format", "text",
           "--model", model, "--max-turns", "1"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, encoding="utf-8")
        if result.returncode != 0 or not result.stdout.strip():
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def parse_json_array(text: str) -> Optional[list]:
    """Extract first top-level JSON array from Claude's response."""
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return None


def normalize_pair(pair: dict, source_tag: str, primary_category: str) -> Optional[dict]:
    q = pair.get("question", "").strip()
    a = pair.get("chosen", "").strip()
    if not q or not a:
        return None
    if len(a.split()) < 50:
        return None
    tags = pair.get("tags") or [primary_category]
    if not isinstance(tags, list):
        tags = [tags]
    return {
        "question": q,
        "chosen": a,
        "tags": tags,
        "source": source_tag,
        "doc_section": pair.get("doc_section", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=list(SOURCES.keys()), required=True)
    parser.add_argument("--n_pairs", type=int, required=True,
                        help="Target number of Q&A pairs to generate")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=10,
                        help="Pairs per Claude call (default 10 keeps prompts manageable)")
    parser.add_argument("--model", type=str, default="sonnet")
    parser.add_argument("--delay", type=float, default=3.0)
    args = parser.parse_args()

    cfg = SOURCES[args.source]
    topic_block = "\n".join(
        f"- [{primary}, {secondary}] {title}: {desc}"
        for title, desc, (primary, secondary) in cfg["topic_hints"]
    )

    pairs = []
    seen_qs = set()
    calls_needed = (args.n_pairs + args.batch_size - 1) // args.batch_size
    print(f"Target: {args.n_pairs} pairs from {cfg['display_name']}")
    print(f"Batches: {calls_needed} x {args.batch_size}")

    for i in range(calls_needed):
        remaining = args.n_pairs - len(pairs)
        if remaining <= 0:
            break
        batch_n = min(args.batch_size, remaining)

        prompt = BATCH_PROMPT.format(
            source_name=cfg["display_name"],
            n=batch_n,
            topic_block=topic_block,
        )

        print(f"\n[batch {i+1}/{calls_needed}] requesting {batch_n} pairs...", flush=True)
        raw = call_claude(prompt, model=args.model)
        if raw is None:
            print("  FAILED — moving on")
            time.sleep(args.delay)
            continue

        parsed = parse_json_array(raw)
        if parsed is None:
            print("  couldn't parse JSON — skipping batch")
            time.sleep(args.delay)
            continue

        added = 0
        for p in parsed:
            norm = normalize_pair(p, cfg["source_tag"], cfg["primary_category"])
            if norm is None:
                continue
            qkey = norm["question"][:120].lower()
            if qkey in seen_qs:
                continue
            seen_qs.add(qkey)
            pairs.append(norm)
            added += 1

        print(f"  added {added} / {len(parsed)} parsed (deduped + normalized)")

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(pairs, f, indent=2)

        time.sleep(args.delay)

    print(f"\n=== Extraction complete ===")
    print(f"Total pairs: {len(pairs)}")
    from collections import Counter
    tag_counts = Counter(t for p in pairs for t in p["tags"])
    print(f"Tag distribution:")
    for tag, n in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {n}")
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
