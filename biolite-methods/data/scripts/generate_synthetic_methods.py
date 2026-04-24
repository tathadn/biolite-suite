#!/usr/bin/env python3
"""
generate_synthetic_methods.py — End-to-end synthetic methodology DPO pairs.

Produces preference pairs in one pass: chosen answer → weighted-random
rejected answer → inline quality filter (same thresholds as quality_control.py
defaults: 0.2 < ROUGE-L < 0.85, 0.4 < length ratio < 2.5).

Covers 7 buckets (total target 200):
    splicing            30
    microbiome          30
    experimental-design 30
    statistics          30
    normalization       25
    alignment           25
    general             30

Error-type weighting (biases for high-signal, low-length-loss classes):
    STAT_CONFUSION     2.0   (subtle factual edits; strongest DPO contrast)
    MISSING_ASSUMPTION 1.5   (strong signal, moderate count so far)
    WRONG_TOOL         1.0
    DESIGN_FLAW        1.0
    OUTDATED           1.0
    OVERCONFIDENT      0.5   (verbose → high length-mismatch loss)

Checkpoints after every kept pair. Resume by re-running with --resume.

Usage:
    python generate_synthetic_methods.py \
        --output ../processed/preference_pairs_synthetic.json \
        --model sonnet --resume
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quality_control import compute_rouge_l


COVERAGE_BUCKETS = {
    "splicing": {
        "target": 30,
        "description": "alternative splicing detection, differential exon usage, isoform quantification, short- vs long-read tradeoffs",
        "seed_topics": [
            "Choosing between rMATS and SUPPA2 for alternative splicing — read depth and replicate requirements",
            "leafcutter for intron excision quantification — when preferable to exon-based DEXSeq",
            "DEXSeq for differential exon usage — interpretation vs whole-transcript DE",
            "MAJIQ local splice variation quantification — strengths for complex events",
            "IsoSeq (PacBio) and direct-RNA nanopore for full-length isoform discovery",
            "Minimum replicate / read-depth requirements for reliable PSI estimation",
            "Aligner choice for splicing — STAR --outSAMstrandField vs HISAT2 --rna-strandness",
            "Handling novel junctions in reference-guided splicing analyses",
            "Quality control for splicing data: junction saturation, inner-distance, SJ.out.tab",
            "Isoform-level quantification with Salmon + tximport — gene- vs transcript-level DE",
            "Event-based (rMATS) vs transcript-based (DRIMSeq) differential splicing — trade-offs",
            "Interpreting PSI changes in low-coverage cases — inclusion vs exclusion bias",
        ],
    },
    "microbiome": {
        "target": 30,
        "description": "16S rRNA and shotgun metagenomics — rarefaction, diversity, QIIME 2 choices, compositional analysis",
        "seed_topics": [
            "Rarefaction vs CSS vs compositional methods — current best practice for 16S",
            "Alpha diversity metrics: Shannon vs Faith's PD vs observed ASVs — what each captures",
            "Beta diversity: Bray-Curtis vs weighted/unweighted UniFrac — when each is appropriate",
            "DADA2 vs Deblur in QIIME 2 — amplicon variant inference trade-offs",
            "Classifier choice for 16S taxonomy — SILVA vs GreenGenes2 vs GTDB",
            "Differential abundance for compositional data — ALDEx2, ANCOM-BC, LEfSe",
            "PERMANOVA assumptions and when dispersion confounds the test",
            "Shotgun assembly vs read-based profiling — when each is appropriate",
            "HUMAnN3 vs MetaPhlAn for functional profiling — reference DB choices",
            "Short-read limitations for strain-level microbiome resolution",
            "Handling low-biomass samples — contamination controls, decontam, SCRuB",
            "Absolute vs relative abundance — spike-in normalization for microbiome",
            "Primer choice for 16S (V3-V4 vs V4 vs full-length) — resolution trade-offs",
            "Integrating 16S with metabolomics/transcriptomics — multi-omics pitfalls",
        ],
    },
    "experimental-design": {
        "target": 30,
        "description": "replicates, batch effects, confounders, blocking, power",
        "seed_topics": [
            "Biological vs technical replicates — how many of each and why",
            "Completely confounded batch vs condition — salvageable vs doomed",
            "Paired/matched design — when blocking on subject buys power",
            "Pseudoreplication in cell-culture experiments — technical vs biological units",
            "Randomization and blocking for plate/run effects in sequencing",
            "Sample size for case-control microbiome — effect-size uncertainty",
            "Pooled vs individual sequencing in pilot studies",
            "Sex as a biological variable — stratification, subset, interaction terms",
            "Longitudinal / repeated-measures design — lme4, limma::duplicateCorrelation",
            "Balanced vs unbalanced factorial designs — interpretation of main effects",
            "Power analysis for RNA-seq DE — RNASeqPower, ssizeRNA, PROPER",
            "Known covariates vs surrogate-variable analysis (SVA, RUV)",
            "Blocking for technical batches when lanes/flowcells partially overlap conditions",
            "Minimum replicates for DE in low-effect biological contrasts",
        ],
    },
    "statistics": {
        "target": 30,
        "description": "FDR interpretation, p-value vs effect size, power, multiple testing scope",
        "seed_topics": [
            "FDR vs FWER vs uncorrected p — picking the correction for genome-wide screens",
            "Benjamini-Hochberg vs Storey q-value vs BH-Yekutieli — when each applies",
            "Effect size vs significance — fold-change cutoffs in the presence of FDR",
            "Over-representation (hypergeometric) vs GSEA — background gene set selection",
            "Meta-analysis across RNA-seq studies — Fisher vs random-effects on effect sizes",
            "Survival analysis with gene expression — Cox PH assumptions, continuous vs dichotomized",
            "p-value histograms as a QC diagnostic — uniform vs anti-conservative distributions",
            "Zero-inflation — ZINB in single-cell vs bulk; when to worry",
            "Multiple comparisons: across genes, contrasts, conditions — scoping the correction",
            "Power vs FDR trade-off — pi0 estimation and interpretation",
            "Moderated t (limma) vs DESeq2 Wald vs edgeR QL — when each is preferable",
            "Interpreting adjusted p-values near the significance threshold — edge cases",
            "Continuous vs categorical covariates — losing power by dichotomizing",
            "Bayesian shrinkage of effect sizes (apeglm, ashr) — when it helps",
        ],
    },
    "normalization": {
        "target": 25,
        "description": "TPM vs FPKM vs counts, size factors, library and batch normalization",
        "seed_topics": [
            "TPM vs FPKM vs RPKM — why TPM replaced the others for most comparisons",
            "Raw counts vs normalized values for DE — DESeq2, edgeR, limma-voom expectations",
            "Library-size normalization for DE — TMM (edgeR) vs RLE (DESeq2) vs upperquartile",
            "Normalizing for gene length — when it matters (intra-sample) vs not (inter-sample)",
            "Quantile normalization — microarray legacy vs modern RNA-seq use",
            "Batch normalization: ComBat vs ComBat-seq vs limma removeBatchEffect — when to use which",
            "Spike-in normalization — ERCC, SIRV, when biology invalidates default normalization",
            "Single-cell normalization: scran vs SCnorm vs sctransform",
            "CPM for visualization vs counts for DE — why the workflow differs",
            "Filtering low-count genes — thresholds and their effect on normalization",
            "Global scaling (Seurat::NormalizeData) vs regularized negative binomial residuals",
        ],
    },
    "alignment": {
        "target": 25,
        "description": "STAR, HISAT2, bwa, minimap2, Salmon — mapping choices and parameters",
        "seed_topics": [
            "STAR vs HISAT2 for RNA-seq — splice-aware mapping differences",
            "bwa-mem vs bowtie2 for DNA alignment — when each is the right default",
            "minimap2 for long-read alignment — presets (map-ont, splice, asm5)",
            "Two-pass STAR vs one-pass — when the annotation build pays off",
            "Quantification: featureCounts vs HTSeq vs Salmon in alignment mode",
            "Pseudoalignment (Salmon, kallisto) vs full alignment — when each is appropriate",
            "Multi-mapping reads — RNA-seq, smallRNA, ChIP-seq handling",
            "Soft-clipping vs global alignment — when you need each",
            "MAPQ thresholds — interpretation across aligners (STAR ≠ bwa ≠ bowtie2)",
            "Duplicate marking (Picard MarkDuplicates) — RNA-seq vs DNA-seq conventions",
            "Alignment QC: insert size, duplication rate, strand specificity",
            "Reference genome and annotation choices — GRCh38 primary vs full, GENCODE vs Ensembl",
        ],
    },
    "general": {
        "target": 30,
        "description": "general methodology — workflow choices, reproducibility, reporting, integration",
        "seed_topics": [
            "Snakemake vs Nextflow vs WDL — what drives the choice",
            "Conda vs Docker vs Singularity for bioinformatics reproducibility",
            "Parameter-sweep workflows — structuring for downstream meta-analysis",
            "When to publish raw data vs processed — SRA/ENA vs GEO norms",
            "Pipeline QC at each stage — what to report in a methods section",
            "Missing data (NAs in gene matrices) — imputation vs drop",
            "Version pinning — tool, reference DB, genome build",
            "Reporting standards: MIQE, MIAME, MINSEQE — when each applies",
            "Collaborator deliverables with RNA-seq — what to hand off",
            "Re-analysis of public data — harmonizing old experiments",
            "Choosing a reference genome / annotation — GRCh38 vs T2T; GENCODE vs RefSeq vs Ensembl",
            "Multi-omics integration — MOFA, mixOmics, when to use which",
            "Preregistration for bioinformatics analyses — what makes sense",
            "Interpreting pathway enrichment results critically — redundancy, annotation bias",
        ],
    },
}


ERROR_WEIGHTS = {
    "STAT_CONFUSION": 2.0,
    "MISSING_ASSUMPTION": 1.5,
    "WRONG_TOOL": 1.0,
    "DESIGN_FLAW": 1.0,
    "OUTDATED": 1.0,
    "OVERCONFIDENT": 0.5,
}

ERROR_DESCRIPTIONS = {
    "WRONG_TOOL": "Recommends an inappropriate tool for the stated constraints (e.g., suggests DESeq2 for already-normalized data, or a tool that doesn't support the organism/data type).",
    "MISSING_ASSUMPTION": "Ignores a critical assumption of the recommended method (e.g., doesn't mention that DESeq2 requires raw counts, or ignores the independence assumption).",
    "STAT_CONFUSION": "Conflates or misinterprets statistical concepts (e.g., confuses p-value with effect size, treats adjusted p-value like raw p-value, misunderstands FDR).",
    "OUTDATED": "Recommends a deprecated workflow or outdated best practice (e.g., suggests RPKM instead of TPM, recommends rarefying microbiome data without caveats).",
    "OVERCONFIDENT": "Gives a single recommendation without discussing trade-offs or alternatives, claims a tool 'always works' regardless of constraints.",
    "DESIGN_FLAW": "Ignores experimental design issues like batch effects, confounders, pseudoreplication, or insufficient replicates.",
}

CHOSEN_PROMPT = """You are generating high-quality methodology Q&A pairs for training a bioinformatics advisor. Each pair will later be turned into a DPO preference pair.

BUCKET: {bucket_name}
BUCKET SCOPE: {bucket_description}

Produce exactly {n} Q&A pairs within this bucket. Each pair MUST:
- Have a realistic QUESTION: what a researcher would ask a consultant or post on a forum. Include specific constraints (sample sizes, experimental structure, tool versions) when natural.
- Have an accurate CHOSEN answer: 140-240 words, grounded in current community best practice and documented tool behavior. Discuss tradeoffs, assumptions, and failure modes. Do NOT invent tool capabilities.
- Include at least one "when NOT to use this" or caveat clause.
- Avoid trivial "read the manual" questions.
- Each pair should cover a DIFFERENT subtopic within the bucket — no duplicates.

SEED TOPICS (pick diverse ones, may adapt or invent variants; cover no more than one per pair):
{seed_list}

Respond with ONLY a JSON array. No preamble, no markdown fences:
[
  {{
    "question": "<question text>",
    "chosen": "<answer text, 140-240 words>",
    "tags": ["{bucket_name}", "<specific subtopic>"]
  }}
]
"""

REJECT_PROMPT = """You are generating training data for preference optimization of a bioinformatics methodology advisor.

Given the question and the CORRECT answer, generate an INCORRECT answer that sounds plausible but contains exactly ONE subtle error.

ERROR TYPE: {error_type}
ERROR DESCRIPTION: {error_description}

The rejected answer MUST:
- Be approximately the same length as the correct answer (±30%)
- Sound confident and well-written (not obviously wrong)
- Contain exactly ONE subtle error of the specified type
- Be wrong in a way that a novice might not catch but an expert would

QUESTION:
{question}

CORRECT ANSWER:
{chosen}

Generate ONLY the rejected answer text. No preamble, no explanation of what's wrong. No markdown formatting."""


def call_claude(prompt: str, model: str = "sonnet", timeout: int = 240,
                retries: int = 3) -> str | None:
    cmd = ["claude", "-p", prompt, "--output-format", "text",
           "--model", model, "--max-turns", "1"]
    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, encoding="utf-8")
            if r.returncode != 0 or not r.stdout.strip():
                if r.stderr:
                    print(f"    stderr: {r.stderr[:180]}", flush=True)
                time.sleep(5)
                continue
            return r.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"    TIMEOUT (attempt {attempt+1}/{retries})", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"    ERROR (attempt {attempt+1}/{retries}): {e}", flush=True)
            time.sleep(5)
    return None


def parse_json_array(text: str) -> list | None:
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def weighted_error_choice() -> str:
    types = list(ERROR_WEIGHTS.keys())
    weights = [ERROR_WEIGHTS[t] for t in types]
    return random.choices(types, weights=weights, k=1)[0]


def check_pair_quality(chosen: str, rejected: str,
                       min_sim: float = 0.2, max_sim: float = 0.85,
                       min_ratio: float = 0.4, max_ratio: float = 2.5
                       ) -> tuple[bool, str, float]:
    cl = len(chosen.split())
    rl = len(rejected.split())
    if cl < 20:
        return False, "chosen_too_short", 0.0
    if rl < 20:
        return False, "rejected_too_short", 0.0
    ratio = rl / cl
    if ratio < min_ratio or ratio > max_ratio:
        return False, "length_mismatch", 0.0
    sim = compute_rouge_l(chosen, rejected)
    if sim > max_sim:
        return False, "too_similar", sim
    if sim < min_sim:
        return False, "too_divergent", sim
    return True, "kept", sim


def save_checkpoint(pairs: list, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(pairs, f, indent=2)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str,
                        default="../processed/preference_pairs_synthetic.json")
    parser.add_argument("--batch_size", type=int, default=5,
                        help="Number of chosen Q&A per Claude call")
    parser.add_argument("--max_attempts_per_bucket", type=int, default=40,
                        help="Max Claude calls per bucket before giving up")
    parser.add_argument("--model", type=str, default="sonnet")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between Claude calls (rate-limit respect)")
    parser.add_argument("--resume", action="store_true",
                        help="Pick up from existing --output")
    parser.add_argument("--only_bucket", type=str, default=None,
                        help="Process only this bucket name (debugging)")
    args = parser.parse_args()

    check = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if check.returncode != 0:
        print("ERROR: 'claude' CLI not found in PATH.", file=sys.stderr)
        sys.exit(1)

    random.seed()

    pairs: list[dict] = []
    seen_questions: set[str] = set()
    stats: dict[str, Counter] = defaultdict(Counter)

    if args.resume and os.path.exists(args.output):
        with open(args.output) as f:
            pairs = json.load(f)
        for p in pairs:
            seen_questions.add(p["question"][:120].lower())
            stats[p.get("bucket", "unknown")]["kept"] += 1
        print(f"RESUME: loaded {len(pairs)} existing pairs")

    total_target = sum(b["target"] for b in COVERAGE_BUCKETS.values())
    print(f"Target: {total_target} pairs across {len(COVERAGE_BUCKETS)} buckets", flush=True)

    for bucket_name, bucket in COVERAGE_BUCKETS.items():
        if args.only_bucket and bucket_name != args.only_bucket:
            continue
        target = bucket["target"]
        kept = stats[bucket_name]["kept"]
        print(f"\n=== bucket: {bucket_name} ({kept}/{target}) ===", flush=True)
        attempts = 0
        while kept < target and attempts < args.max_attempts_per_bucket:
            attempts += 1
            need = target - kept
            batch_n = min(args.batch_size, need + 2)

            seeds = random.sample(
                bucket["seed_topics"],
                min(batch_n, len(bucket["seed_topics"])),
            )
            chosen_prompt = CHOSEN_PROMPT.format(
                n=batch_n,
                bucket_name=bucket_name,
                bucket_description=bucket["description"],
                seed_list="\n".join(f"  - {s}" for s in seeds),
            )
            print(f"  [attempt {attempts}] requesting {batch_n} chosen answers "
                  f"(kept {kept}/{target})...", flush=True)

            raw = call_claude(chosen_prompt, args.model, timeout=300)
            if not raw:
                print("    chosen-batch FAILED", flush=True)
                time.sleep(args.delay)
                continue
            parsed = parse_json_array(raw)
            if not parsed:
                print("    chosen-batch JSON parse failed", flush=True)
                time.sleep(args.delay)
                continue

            for item in parsed:
                if kept >= target:
                    break
                q = (item.get("question") or "").strip()
                chosen = (item.get("chosen") or "").strip()
                if not q or not chosen or len(chosen.split()) < 50:
                    stats[bucket_name]["chosen_invalid"] += 1
                    continue
                key = q[:120].lower()
                if key in seen_questions:
                    stats[bucket_name]["duplicate"] += 1
                    continue

                error_type = weighted_error_choice()
                rej_prompt = REJECT_PROMPT.format(
                    error_type=error_type,
                    error_description=ERROR_DESCRIPTIONS[error_type],
                    question=q[:1500],
                    chosen=chosen[:2000],
                )
                rejected = call_claude(rej_prompt, args.model, timeout=180)
                time.sleep(args.delay)
                if not rejected:
                    stats[bucket_name]["reject_fail"] += 1
                    continue

                ok, detail, sim = check_pair_quality(chosen, rejected)
                if not ok:
                    stats[bucket_name][detail] += 1
                    continue

                seen_questions.add(key)
                tags = item.get("tags") or [bucket_name]
                if not isinstance(tags, list):
                    tags = [tags]
                pairs.append({
                    "question": q,
                    "chosen": chosen,
                    "rejected": rejected,
                    "error_type": error_type,
                    "category": bucket_name,
                    "bucket": bucket_name,
                    "source": "synthetic-methods",
                    "rouge_l_similarity": round(sim, 3),
                    "tags": tags,
                })
                stats[bucket_name]["kept"] += 1
                kept += 1
                save_checkpoint(pairs, args.output)
                print(f"    kept pair #{kept} ({error_type}, sim={sim:.2f})", flush=True)

        if kept < target:
            print(f"  WARNING: hit max_attempts at {kept}/{target} for {bucket_name}", flush=True)
        else:
            print(f"  DONE: {bucket_name} {kept}/{target}", flush=True)

    print("\n=== Summary ===", flush=True)
    print(f"Total pairs kept: {len(pairs)} / {total_target}")
    for bucket_name in COVERAGE_BUCKETS:
        s = stats[bucket_name]
        print(f"  {bucket_name}: kept={s['kept']}  "
              f"too_sim={s['too_similar']}  too_div={s['too_divergent']}  "
              f"len_mismatch={s['length_mismatch']}  rej_fail={s['reject_fail']}  "
              f"dup={s['duplicate']}")

    err_dist = Counter(p["error_type"] for p in pairs)
    print("\nError type distribution (kept):")
    for et, n in sorted(err_dist.items(), key=lambda x: -x[1]):
        print(f"  {et}: {n}")

    save_checkpoint(pairs, args.output)
    print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
