#!/usr/bin/env Rscript
# run_deseq2.R — Extract top DE genes from GEO datasets via GEO2R-style pipeline.
#
# Usage:
#   Rscript run_deseq2.R GSE50760 "tumor" "normal" output/GSE50760_de.csv
#
# Prerequisites:
#   BiocManager::install(c("DESeq2", "GEOquery"))

suppressPackageStartupMessages({
  library(GEOquery)
  library(DESeq2)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 4) {
  cat("Usage: Rscript run_deseq2.R <GSE_ID> <condition_A> <condition_B> <output_csv>\n")
  cat("Example: Rscript run_deseq2.R GSE50760 tumor normal output/GSE50760_de.csv\n")
  quit(status = 1)
}

gse_id <- args[1]
cond_a <- args[2]
cond_b <- args[3]
output_file <- args[4]

cat(sprintf("Processing %s: %s vs %s\n", gse_id, cond_a, cond_b))

# Download GEO dataset
gse <- getGEO(gse_id, GSEMatrix = TRUE, getGPL = FALSE)

if (length(gse) == 0) {
  stop("Failed to download dataset")
}

eset <- gse[[1]]
expr_data <- exprs(eset)
pheno_data <- pData(eset)

cat(sprintf("  Samples: %d, Features: %d\n", ncol(expr_data), nrow(expr_data)))
cat(sprintf("  Phenotype columns: %s\n", paste(colnames(pheno_data), collapse=", ")))

# NOTE: This is a skeleton. For each GSE, you need to:
# 1. Identify the correct phenotype column for grouping
# 2. Assign samples to condition_A and condition_B
# 3. For RNA-seq count data: use DESeq2
# 4. For microarray data: use limma
#
# The specifics depend on each dataset's annotation structure.
# See the GEO2R R script tab for each GSE for guidance.

cat("\n=== Manual steps required ===\n")
cat("1. Inspect pheno_data to identify the grouping column\n")
cat("2. Assign conditions based on sample annotations\n")
cat("3. Run DESeq2 or limma as appropriate\n")
cat(sprintf("4. Save top 20 DE genes to %s\n", output_file))
cat("\nExample for limma (microarray):\n")
cat("  design <- model.matrix(~0 + group)\n")
cat("  fit <- lmFit(expr_data, design)\n")
cat("  contrast <- makeContrasts(groupA - groupB, levels=design)\n")
cat("  fit2 <- contrasts.fit(fit, contrast)\n")
cat("  fit2 <- eBayes(fit2)\n")
cat("  results <- topTable(fit2, number=20, adjust.method='BH')\n")
