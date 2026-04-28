# BioLite Human Evaluation — Google Form Content

## SECTION: Instructions

**BioLite Model Evaluation**

Thank you for helping evaluate our bioinformatics interpretation model!

**WHAT YOU'LL DO**

You will review 30 model-generated interpretations of differential expression
and pathway enrichment results. For each interpretation, you'll rate three
aspects:

1. **Biological Accuracy** — Are the gene functions and pathway associations correct?
2. **Completeness** — Does it cover all the important findings in the data?
3. **Clarity** — Is it well-written and easy to follow?

**HOW TO SCORE**

Each criterion uses a 1-5 scale. See the **Rubric** section below for detailed
definitions. Please also read the two **Calibration Examples** before starting —
they show what good (5) and poor (1) outputs look like.

**IMPORTANT NOTES**

- Judge the **model output only**. You don't need to compare it against any
  reference answer.
- The model output may contain errors — that's exactly what we're measuring.
- If you're unsure about a specific gene or pathway, score based on what you
  can verify, and use the **Notes** field to flag your uncertainty.
- No ML knowledge needed — we only need your biology expertise.

**ESTIMATED TIME: 45-60 minutes**

**WORKFLOW**

1. Read the **Rubric** section (2 min)
2. Read the two **Calibration Examples** with explanations (5 min)
3. Rate all 30 examples (40-50 min)
4. Submit the form

Please do not discuss scores with other evaluators until all responses are
submitted.


## SECTION: Calibration Example 1 (high-quality output, scores 5/5/5)

**Input:**

DESeq2 results from human breast cancer vs normal tissue:
| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| ESR1 | -3.21 | 1.2e-18 | 4521 |
| ERBB2 | 4.87 | 3.4e-22 | 3102 |
| MKI67 | 3.65 | 7.8e-15 | 2876 |
| CDH1 | -2.43 | 4.5e-11 | 1987 |
| TP53 | -1.89 | 2.1e-9 | 1654 |

**Model Output:**

The differential expression profile reveals a classic aggressive breast cancer signature. ERBB2 (HER2) is strongly upregulated (log2FC=4.87), indicating HER2-positive subtype characteristics. The proliferation marker MKI67 (Ki-67) is similarly elevated, consistent with high mitotic activity. Downregulation of ESR1 (estrogen receptor alpha) suggests hormone receptor negativity, while loss of CDH1 (E-cadherin) indicates disrupted cell-cell adhesion and potential epithelial-mesenchymal transition. TP53 downregulation is consistent with p53 pathway inactivation. Together, these markers suggest a HER2+/ER- subtype with aggressive features including high proliferation and EMT activation.

**Suggested Scores:** bio_acc=5, completeness=5, clarity=5

**Why:** All gene identifications correct (ERBB2=HER2, MKI67=Ki-67, ESR1=ER-alpha, CDH1=E-cadherin). Directionalities match the table. Biological connections (HER2+/ER- subtype, EMT, p53 pathway) are accurate. All 5 genes addressed.


## SECTION: Calibration Example 2 (low-quality output, scores 1/2/3)

**Input:**

DESeq2 results from mouse liver, high-fat diet vs control:
| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| Fasn | 2.34 | 5.6e-12 | 3201 |
| Pparg | 1.87 | 8.9e-10 | 1543 |
| Cyp7a1 | -3.12 | 1.1e-15 | 2876 |
| Acox1 | -1.95 | 3.4e-8 | 1234 |

**Model Output:**

The results show activation of inflammatory pathways. Fasn upregulation indicates increased TNF-alpha signaling. Pparg is a transcription factor involved in cell cycle regulation and its upregulation suggests proliferative activity. Cyp7a1 downregulation reflects reduced kidney function. Acox1, a glycolytic enzyme, is suppressed indicating mitochondrial dysfunction.

**Suggested Scores:** bio_acc=1, completeness=2, clarity=3

**Why:** Major errors: Fasn is fatty acid synthase (lipogenesis), not TNF-alpha. PPARg is a lipid metabolism regulator, not cell cycle. Cyp7a1 is bile acid synthesis in LIVER, not kidney. Acox1 is peroxisomal fatty acid oxidation, not glycolysis. The real story is hepatic steatosis (lipogenesis up, beta-oxidation down). Writing is grammatically clear despite being wrong.


## SECTION: Rubric

### Biological Accuracy

_How biologically accurate is the interpretation?_

- **1** — Major factual errors — wrong gene functions, wrong pathways, hallucinated associations
- **2** — Multiple inaccuracies — some gene IDs correct but key biological claims are wrong
- **3** — Mostly correct — main themes right, but some imprecisions or minor errors
- **4** — Accurate — correct gene functions and pathway associations, minor issues only
- **5** — Fully accurate — all gene functions, directionalities, and pathway connections correct

### Completeness

_Does the interpretation cover all important findings in the data?_

- **1** — Mentions <30% of key findings — skips major genes or ignores entire functional themes
- **2** — Covers some findings but misses important patterns
- **3** — Covers major findings but misses nuance or secondary themes
- **4** — Addresses most significant genes, enrichment themes, and caveats
- **5** — Comprehensive — all significant findings addressed with appropriate context

### Clarity

_How clear and well-structured is the writing?_

- **1** — Jargon-heavy, incoherent, or disorganized — hard to follow
- **2** — Understandable but poorly structured or repetitive
- **3** — Adequate — readable but could be better organized
- **4** — Clear and well-structured — easy to follow for a biologist
- **5** — Excellent — well-organized, concise, accessible to biologist audience


---

# 30 Evaluation Examples

## EXAMPLE EX-01

**Input:**

The following DESeq2 results table was generated from a zebrafish experiment comparing hypoxia-exposed larvae (1% O2, 6 hours) to normoxic controls. Interpret the differential expression results, identifying major functional themes, relevant biological pathways, and any important caveats in the analysis.

| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| vegfaa | 3.12 | 4.2e-11 | 847.3 |
| epo | 2.87 | 1.1e-09 | 213.6 |
| egln3 | 2.41 | 3.8e-08 | 1204.7 |
| ldha | 2.18 | 7.6e-08 | 3421.2 |
| hif1ab | 1.93 | 2.3e-06 | 589.4 |
| slc2a1a | 1.76 | 8.9e-06 | 762.1 |
| bnip3la | 1.54 | 4.4e-05 | 318.8 |
| pfkla | 1.31 | 2.1e-04 | 1876.5 |
| ndufb5 | -1.38 | 5.7e-05 | 2103.4 |
| cox5aa | -1.52 | 1.9e-05 | 1654.9 |
| uqcrc1 | -1.24 | 3.3e-04 | 987.2 |
| atp5pb | -1.09 | 8.8e-04 | 2541.6 |
| sdha | -0.97 | 1.2e-03 | 1398.3 |
| cyb5a | -0.88 | 3.7e-03 | 743.1 |

**Model Output:**

These results reveal a canonical hypoxic transcriptional response in zebrafish larvae. The most strongly upregulated genes form a coherent HIF-1α-driven program: vegfaa (log2FC 3.12) and epo (log2FC 2.87) are direct HIF-1α targets that promote angiogenesis and erythropoiesis, respectively, while egln3 (log2FC 2.41) encodes PHD3, a HIF-1α hydroxylase that normally degrades HIF-1α under normoxia, and its upregulation suggests a negative feedback loop. The metabolic shift is evident in ldha (log2FC 2.18) and slc2a1a (log2FC 1.76), indicating increased anaerobic glycolysis and glucose uptake. bnip3la upregulation (log2FC 1.54) suggests activation of mitophagy to reduce mitochondrial oxygen demand. pfkla induction (log2FC 1.31) reflects a cytoprotective response. The downregulated genes point to coordinated suppression of oxidative phosphorylation: ndufb5, cox5aa, uqcrc1, atp5pb, sdha, and cyb5a are all subunits of the electron transport chain, consistent with the well-established Warburg-like metabolic reprogramming under hypoxia. Important caveats include the 6-hour timepoint, which captures acute transcriptional responses rather than long-term adaptations; whole-larva RNA-seq obscures tissue-specific responses; and the modest baseMean values for epo and bnip3la warrant validation by qPCR.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-02

**Input:**

Mechanism of resistance of tetracyclines is due to?

**Model Output:**

Tetracyclines bind to the 30S subunit of the bacterial ribosome. Resistance is due to the presence of ribosomal RNA in the bacterial cell wall.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-03

**Input:**

Given a biomedical abstract, identify the main conclusion made by the authors.

Recent studies have highlighted the potential for using probiotics in maintaining good digestive health and a balanced gut microbiome. However, a comprehensive understanding of the effects of individual probiotic strains and their metabolic interactions within the complex human gut ecosystem remains elusive. In this study, we examined the effect of Lactobacillus rhamnosus GG (LGG) supplementation on the gut microbiota and short-chain fatty acid (SCFA) production in healthy adults. Forty volunteers were randomized in a double-blind, placebo-controlled study to receive either LGG or placebo daily for 4 weeks. Fecal samples were collected before and after intervention, and 16S rRNA gene sequencing and SCFA analysis were performed. Our findings show no significant difference in microbiota alpha-diversity, beta-diversity, or community composition between the LGG and placebo groups. However, LGG supplementation resulted in a significant increase in butyrate levels compared to the placebo group. These findings highlight the potential of LGG supplementation for modulating gut microbial metabolites, specifically butyrate, which has been shown to confer various health benefits.

**Model Output:**

The study found that Lactobacillus rhamnosus GG supplementation increased butyrate levels in healthy adults, suggesting potential health benefits.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-04

**Input:**

The following GO and KEGG enrichment results were generated from differentially expressed genes (adjusted p < 0.05, |log2FC| > 1) in an nhr-49 knockout versus wild-type N2 C. elegans comparison. Interpret which biological processes are enriched, whether they are consistent with the known function of NHR-49, and what this pattern of enrichment suggests about the molecular consequences of nhr-49 loss.

| Term | Category | GeneCount | pvalue | p.adjust | GeneRatio |
|------|----------|-----------|--------|----------|-----------|
| Fatty acid beta-oxidation | GO:BP | 18 | 2.3e-09 | 1.8e-07 | 18/89 |
| Lipid metabolic process | GO:BP | 31 | 4.1e-08 | 1.6e-06 | 31/156 |
| Oxidation-reduction process | GO:BP | 42 | 8.7e-07 | 2.3e-05 | 42/312 |
| Response to starvation | GO:BP | 14 | 3.2e-06 | 6.4e-05 | 14/78 |
| Cellular lipid metabolic process | GO:BP | 22 | 1.1e-05 | 1.8e-04 | 22/134 |
| Acyl-CoA dehydrogenase activity | GO:MF | 11 | 5.4e-07 | 2.1e-05 | 11/38 |
| Fatty-acyl-CoA binding | GO:MF | 9 | 2.8e-05 | 3.7e-04 | 9/45 |
| Oxidoreductase activity | GO:MF | 28 | 4.6e-05 | 5.5e-04 | 28/198 |
| Fatty acid metabolism | KEGG | 16 | 1.7e-07 | 9.4e-06 | 16/67 |
| Peroxisome | KEGG | 12 | 3.9e-06 | 7.2e-05 | 12/54 |
| PPAR signaling pathway | KEGG | 8 | 2.1e-04 | 1.9e-03 | 8/61 |

**Model Output:**

The enrichment results reveal a coherent transcriptional signature consistent with NHR-49's established role as a master regulator of lipid homeostasis in C. elegans. The two most significantly enriched terms—fatty acid beta-oxidation (GO:BP, p.adj = 1.8e-07) and fatty acid metabolism (KEGG, p.adj = 9.4e-06)—reflect NHR-49's direct transcriptional control of acs-2, acs-3, and acs-5, the canonical C. elegans acyl-CoA synthetases that initiate fatty acid oxidation. The broad enrichment of lipid metabolic process and cellular lipid metabolic process terms captures the downstream consequences of impaired acs activity, including altered lipid droplet size and membrane lipid composition. The strong enrichment of peroxisome KEGG pathway (p.adj = 7.2e-05) is mechanistically expected, as NHR-49 co-activates peroxisomal acs genes with PPAR homolog PPAR-1, and their mutual loss would disrupt peroxisomal fatty acid catabolism. The enrichment of oxidation-reduction process and acyl-CoA dehydrogenase activity reflects the broader metabolic reprogramming required to compensate for the loss of beta-oxidation capacity. The enrichment of PPAR signaling pathway (p.adj = 1.9e-03) is consistent with NHR-49's established role as a PPAR ortholog that cooperates with PPAR-1 to regulate fat storage and metabolism. Together, these results indicate that nhr-49 loss disrupts the core lipid catabolism axis, triggering a compensatory metabolic shift that is partially mediated through PPAR signaling.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-05

**Input:**

You are given two results tables from a zebrafish RNA-seq experiment comparing infected fish to mock-infected controls. The first table shows the top differentially expressed genes (DESeq2); the second shows enriched Gene Ontology (GO) biological process terms (clusterProfiler ORA). Provide an integrated biological interpretation that connects specific gene expression changes to the enriched pathways and explains the overall host response to infection.

**Differential Expression Results (infected vs mock, top 8 genes by padj)**

| Gene | log2FoldChange | padj | Direction |
|------|---------------|------|-----------|
| saa | 5.02 | 3.6e-18 | UP |
| isg15 | 4.67 | 1.8e-16 | UP |
| cxcl8a | 4.21 | 1.2e-15 | UP |
| mx1 | 3.91 | 4.2e-14 | UP |
| il1b | 3.87 | 8.4e-14 | UP |
| ptgs2a | 3.45 | 2.1e-12 | UP |
| cebpb | 2.34 | 6.7e-09 | UP |
| fabp10a | -2.89 | 3.1e-10 | DOWN |

**GO Biological Process Enrichment (top 6 terms)**

| GO ID | Description | GeneRatio | p.adjust |
|-------|-------------|-----------|----------|
| GO:0006954 | inflammatory response | 28/312 | 2.1e-14 |
| GO:0045087 | innate immune response | 24/312 | 8.7e-13 |
| GO:0051607 | defense response to virus | 19/312 | 3.4e-11 |
| GO:0009615 | response to virus | 22/312 | 5.9e-11 |
| GO:0032640 | tumor necrosis factor production | 11/312 | 4.2e-08 |
| GO:0006979 | response to oxidative stress | 14/312 | 1.8e-07 |

**Model Output:**

The zebrafish transcriptome reveals a coordinated, multi-layered innate immune response following infection. The most strongly upregulated gene, saa (log2FC = 5.02), encodes a secreted alpha-1 antitrypsin-like serine protease that is a canonical early host defense marker in teleosts, consistent with enrichment of 'defense response to virus' and 'inflammatory response' GO terms. Concurrently, the interferon-stimulated genes isg15 and mx1 are strongly induced, reflecting activation of the JAK-STAT pathway and implicating type I interferon signaling in antiviral defense. Upregulation of cxcl8a (log2FC = 4.21) and il1b (log2FC = 3.87) drives enrichment of 'inflammatory response' and 'tumor necrosis factor production' terms, indicating robust neutrophil and macrophage recruitment. The induction of ptgs2a (log2FC = 3.45), encoding cyclooxygenase-2, is consistent with the'response to oxidative stress' term and suggests concurrent pro-inflammatory eicosanoid production. Elevated cebpb (log2FC = 2.34) likely amplifies this inflammatory cascade by upregulating pro-inflammatory cytokine mRNAs. The downregulation of fabp10a (log2FC = -2.89) reflects a well-characterized'metabolic reprogramming' shift away from lipid anabolism toward energy mobilization and immune defense, a conserved pattern in teleosts. Together, these data describe a coherent, multi-arm host response: early antiviral defense via saa and ISG15, pro-inflammatory cytokine signaling via CXCL8a and IL-1β, and metabolic reallocation to support immune function.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-06

**Input:**

You are given a DESeq2 differential expression table from a Drosophila melanogaster RNA-seq experiment comparing aged flies (60 days post-eclosion) to young flies (5 days post-eclosion), both female, whole-body. Interpret the biological significance of these results, identifying major functional themes, relevant signaling pathways, and any notable caveats.

| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| Dpt | 3.21 | 1.4e-09 | 842.3 |
| AttA | 2.84 | 3.1e-08 | 614.7 |
| Hsp70Ab | 2.13 | 8.2e-04 | 1203.5 |
| Hsp22 | 1.94 | 2.6e-03 | 389.1 |
| upd3 | 1.63 | 9.4e-03 | 127.6 |
| Thor | 1.41 | 1.8e-02 | 256.4 |
| Mhc | -2.38 | 4.7e-06 | 5621.2 |
| Syt1 | -1.92 | 1.9e-03 | 934.8 |
| nrv2 | -2.07 | 7.3e-04 | 712.3 |
| Act57B | -1.74 | 6.1e-03 | 3284.9 |
| marf | -1.81 | 4.2e-03 | 445.6 |
| Men | -1.52 | 1.4e-02 | 298.7 |
| CG6416 | -1.29 | 3.1e-02 | 189.4 |

**Model Output:**

These results reveal a canonical Drosophila aging transcriptional signature organized around three interconnected themes. First, a robust innate immune and stress-response program is activated: Dpt (log2FC 3.21) and AttA (log2FC 2.84) are canonical Drosophila Toll and Imd pathway effectors, respectively, and their strong upregulation in aged flies is consistent with the well-documented 'inflammaging' phenotype of this organism. Upregulation of Hsp70Ab and Hsp22 further indicates proteostatic stress accumulation, a hallmark of aging across species. The modest but significant induction of upd3 (log2FC 1.63) suggests activation of the JAK-STAT pathway, which is also elevated in aged flies and has been linked to longevity. Thor (log2FC 1.41) upregulation is notable, as it encodes a Drosophila 4E-BP that promotes cap-dependent translation and is itself a target of the insulin/IGF-1 signaling pathway, which is typically suppressed in aged flies.

Second, a coordinated decline in muscle and neuronal function is evident: Mhc (log2FC -2.38) and Act57B (log2FC -1.74) are both major sarcomeric and cytoskeletal components, respectively, and their strong downregulation reflects the well-characterized sarcopenia of aged Drosophila. Syt1 (log2FC -1.92) and nrv2 (log2FC -2.07) downregulation further indicates impaired neurotransmitter release and neuronal health. marf (log2FC -1.81) and Men (log2FC -1.52) are both components of the Drosophila cytoskeleton and actin remodeling machinery, consistent with the broad cytoskeletal collapse observed in aged flies.

Third, CG6416 downregulation (log2FC -1.29) suggests a broader decline in proteostatic capacity, consistent with the accumulation of misfolded proteins that drives proteotoxic stress.

Caveats: bulk RNA-seq cannot resolve whether immune and stress-response changes are driven by specific cell-type shifts or a generalized tissue response; the modest Thor signal warrants validation. Additionally, the relatively low baseMean for upd3 (127.6) and CG6416 (189.4) suggests these changes may be modest and potentially confounded by background noise.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-07

**Input:**

The following table shows GO/KEGG enrichment results from a differential expression analysis comparing aged (65–80 years) versus young (20–35 years) human skeletal muscle biopsies. Upregulated genes in the aged group were used as input. Interpret the enrichment results biologically, explaining which processes are activated in aging and why these findings are consistent with known hallmarks of aging.

| Term | Category | GeneCount | pvalue | p.adjust | GeneRatio |
|------|----------|-----------|--------|----------|-----------|
| Inflammatory response | GO:BP | 47 | 1.2e-12 | 8.4e-10 | 47/318 |
| Response to reactive oxygen species | GO:BP | 31 | 3.4e-09 | 1.1e-07 | 31/318 |
| DNA damage checkpoint signaling | GO:BP | 28 | 7.8e-09 | 1.8e-07 | 28/318 |
| Regulation of apoptotic process | GO:BP | 52 | 2.1e-08 | 3.7e-07 | 52/318 |
| Cellular senescence | KEGG | 19 | 8.9e-08 | 1.0e-06 | 19/318 |
| Cytokine-mediated signaling pathway | GO:BP | 41 | 3.2e-07 | 2.8e-06 | 41/318 |
| Extracellular matrix organization | GO:BP | 38 | 5.1e-07 | 3.9e-06 | 38/318 |
| mTOR signaling pathway | KEGG | 16 | 5.6e-07 | 4.4e-06 | 16/318 |
| NF-kappa B signaling pathway | KEGG | 22 | 8.3e-07 | 5.8e-06 | 22/318 |
| Telomere maintenance | GO:BP | 14 | 9.1e-07 | 6.4e-06 | 14/318 |
| Cytokine activity | GO:MF | 29 | 1.4e-06 | 8.9e-06 | 29/318 |
| p53 signaling pathway | KEGG | 17 | 2.7e-06 | 1.6e-05 | 17/318 |

**Model Output:**

The enrichment results reveal a coherent transcriptional signature of cellular aging in skeletal muscle. The most significantly enriched terms—Inflammatory response and Cytokine-mediated signaling—reflect the well-documented 'inflammaging' phenotype, in which chronic low-grade inflammation is a hallmark of aged tissue. This is consistent with the upregulation of pro-inflammatory cytokines such as IL6, TNF, and IL1B, which are themselves transcriptionally induced by NF-κB and p38 MAPK signaling. The concurrent enrichment of Response to reactive oxygen species and DNA damage checkpoint signaling indicates that aged muscle accumulates oxidative stress and genomic damage, driving activation of p53-dependent repair programs. The enrichment of Cellular senescence and the p53 signaling pathway confirms that senescent satellite cells and myofibers accumulate with age, secreting pro-inflammatory cytokines that sustain the inflammatory state. Extracellular matrix organization enrichment reflects the fibrotic remodeling that occurs as aged muscle loses regenerative capacity, with matrix components such as collagen and fibronectin upregulated to support senescent cell survival. mTOR signaling enrichment is consistent with the metabolic reprogramming of aged muscle, which shifts from anabolic to catabolic metabolism. Telomere maintenance enrichment suggests that aged muscle attempts to counteract telomere shortening through activation of telomerase and telomere-lengthening pathways. Together, these results describe a self-reinforcing cycle of inflammation, oxidative stress, genomic damage, senescence, and metabolic dysfunction that defines the aged skeletal muscle transcriptome.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-08

**Input:**

The following table shows GO and KEGG enrichment results from a differential expression analysis comparing aged (24-month) versus young (3-month) mouse skeletal muscle tissue. Upregulated genes in aged animals were used as input. Interpret the biological significance of these enriched terms and explain what they collectively reveal about the molecular hallmarks of aging in this tissue.

| Term | Category | GeneCount | pvalue | p.adjust | GeneRatio |
|------|----------|-----------|--------|----------|-----------|
| Inflammatory response | GO:BP | 47 | 2.1e-14 | 8.4e-12 | 47/312 |
| Cellular senescence | GO:BP | 31 | 5.6e-12 | 1.1e-09 | 31/312 |
| Response to oxidative stress | GO:BP | 38 | 3.2e-11 | 4.3e-09 | 38/312 |
| Positive regulation of NF-kappaB signaling | GO:BP | 26 | 7.8e-10 | 7.8e-08 | 26/312 |
| Extracellular matrix organization | GO:BP | 34 | 1.4e-09 | 1.1e-07 | 34/312 |
| Autophagy of mitochondrion | GO:BP | 19 | 4.2e-08 | 2.8e-06 | 19/312 |
| Cytokine-mediated signaling pathway | GO:BP | 41 | 9.1e-08 | 5.1e-06 | 41/312 |
| DNA damage response | GO:BP | 22 | 3.3e-07 | 1.6e-05 | 22/312 |
| Chemokine activity | GO:MF | 14 | 6.7e-07 | 2.7e-05 | 14/312 |
| TNF signaling pathway | KEGG | 28 | 1.2e-09 | 9.6e-08 | 28/312 |
| NF-kappa B signaling pathway | KEGG | 23 | 8.4e-08 | 4.7e-06 | 23/312 |
| Cellular senescence (KEGG) | KEGG | 29 | 2.1e-07 | 1.1e-05 | 29/312 |

**Model Output:**

The enrichment results reveal a coherent transcriptional signature of chronic, multi-layered stress and cellular dysfunction in aged mouse skeletal muscle. The most significantly enriched terms — inflammatory response and cytokine-mediated signaling — reflect the well-documented 'inflammaging' phenotype, in which senescent cells and activated immune cells co-occupy the tissue, driving low-grade inflammation that impairs tissue homeostasis. This is mechanistically supported by enrichment of the NF-κB signaling pathway, which is a master regulator of both the innate immune response and the senescence-associated secretory phenotype (SASP). The concurrent enrichment of chemokine activity and the TNF signaling pathway suggests that pro-inflammatory cytokines such as Il6, Tnf, and Cxcl1 are upregulated in aged muscle, creating a self-reinforcing inflammatory loop. Cellular senescence enrichment is consistent with the accumulation of senescent satellite cells and myofibers that have failed to divide, releasing SASP factors that sustain the inflammatory state. Response to oxidative stress and autophagy of mitochondrion enrichment indicate that aged muscle is under persistent oxidative burden and has impaired mitochondrial quality control, a hallmark of sarcopenia. DNA damage response enrichment points to elevated genomic instability, likely driven by telomere shortening and epigenetic drift. Extracellular matrix organization enrichment suggests that the aged tissue is remodeling its structural scaffold, a process that can both support and restrict tissue repair. Together, these terms describe a tissue that has become chronically inflamed, senescent, and metabolically stressed, collectively explaining the progressive decline in muscle function observed in aged animals.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-09

**Input:**

What is the significance of this discovery?


**Model Output:**

The discovery of a new gene that is associated with the development of a specific disease is significant because it may lead to the development of new treatments for that disease.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-10

**Input:**

What are clustered regularly interspaced short palindromic repeats-CRISPR-associated nucleases (CRISPR-Cas9), zinc-finger nucleases (ZFNs), and TAL-effector nucleases (TALENs)? 


**Model Output:**

Clustered regularly interspaced short palindromic repeats-CRISPR-associated nucleases (CRISPR-Cas9), zinc-finger nucleases (ZFNs), and TAL-effector nucleases (TALENs) are gene editing tools.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-11

**Input:**

The following GO/KEGG enrichment analysis was performed on genes significantly upregulated in late-stage zebrafish compared to early-stage zebrafish (adjusted p < 0.05, |log2FC| > 1.5, n = 280 genes). Interpret the biological significance of these enrichment results, explaining which developmental processes are active in late-stage zebrafish and why these findings are consistent with known zebrafish biology.

| Term | Category | GeneCount | pvalue | p.adjust | GeneRatio |
|------|----------|-----------|--------|----------|-----------|
| nervous system development | GO_BP | 45 | 1.24e-12 | 2.36e-10 | 45/280 |
| neurogenesis | GO_BP | 38 | 3.41e-11 | 3.24e-09 | 38/280 |
| embryonic morphogenesis | GO_BP | 52 | 5.62e-10 | 3.56e-08 | 52/280 |
| cell fate commitment | GO_BP | 28 | 1.83e-09 | 8.68e-08 | 28/280 |
| forebrain development | GO_BP | 22 | 4.21e-09 | 1.60e-07 | 22/280 |
| Notch signaling pathway | KEGG | 18 | 7.34e-09 | 2.32e-07 | 18/280 |
| Wnt signaling pathway | KEGG | 24 | 1.12e-08 | 3.03e-07 | 24/280 |
| DNA-binding transcription factor activity | GO_MF | 62 | 2.43e-08 | 5.77e-07 | 62/280 |
| head development | GO_BP | 19 | 8.91e-08 | 1.90e-06 | 19/280 |
| TGF-beta signaling pathway | KEGG | 16 | 2.14e-07 | 4.07e-06 | 16/280 |

**Model Output:**

The enrichment results reveal a coherent transcriptional program consistent with late-stage zebrafish development. The strongest signal is nervous system development and neurogenesis, reflecting the active maturation of neurons and glia in the central nervous system during this stage. The co-enrichment of embryonic morphogenesis and cell fate commitment terms indicates that the neural progenitor pool is undergoing active specification and differentiation, consistent with the broad transcriptional reprogramming that occurs as cells transition from proliferative to post-mitotic fates. The enrichment of forebrain development is particularly informative, as the zebrafish brain undergoes a highly conserved and well-characterized maturation process during late embryonic stages, involving coordinated expansion of the cerebral cortex and differentiation of specific neuronal subtypes. The Notch and Wnt signaling pathway enrichment is mechanistically expected, as these canonical signaling axes are well-established drivers of neural progenitor maintenance and fate specification in zebrafish. The enrichment of DNA-binding transcription factor activity reflects the broad transcriptional reprogramming required to drive these developmental transitions, involving factors such as pou5f1, sox2, and nanog in the neural stem cell compartment. Finally, the TGF-beta signaling pathway enrichment is consistent with the role of TGF-beta in regulating neural progenitor proliferation and differentiation in zebrafish. Collectively, these results are consistent with the late-stage zebrafish transcriptome capturing the terminal differentiation of the nervous system and the coordinated transcriptional control required to sustain this process.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-12

**Input:**

What role might DARPP-32 play in gastric carcinogenesis?


**Model Output:**

DARPP-32 may play a role in gastric carcinogenesis by promoting cell proliferation, survival, and metastasis.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-13

**Input:**

You are given a DESeq2 differential expression results table from a rat liver study comparing drug-treated animals to vehicle controls. Interpret the biological significance of these results, identifying functional themes, relevant pathways, and any notable caveats.

DESeq2 results — drug-treated vs. vehicle control (rat liver, n=4/group)

| Gene | log2FC | padj | baseMean |
|--------|--------|------------|----------|
| Cyp4a1 | 4.82 | 1.2e-18 | 3241.5 |
| Hmgcs2 | 3.15 | 8.9e-15 | 892.7 |
| Fgf21 | 3.44 | 3.1e-11 | 445.2 |
| Acox1 | 2.67 | 4.5e-12 | 1876.3 |
| Angptl4 | 2.28 | 1.7e-09 | 678.4 |
| Cpt1a | 1.94 | 2.3e-08 | 2104.1 |
| Ppara | 1.38 | 2.3e-03 | 876.5 |
| Scd1 | -3.72 | 2.2e-16 | 3187.6 |
| Fasn | -2.91 | 6.4e-13 | 4523.8 |
| Il6 | -2.14 | 8.1e-08 | 187.6 |
| Tnf | -1.87 | 3.9e-07 | 312.4 |
| Srebf1 | -1.53 | 4.8e-06 | 1243.9 |
| Ccl2 | -1.62 | 2.6e-06 | 523.1 |

**Model Output:**

These results reveal a coherent hepatic metabolic reprogramming consistent with activation of PPARα-driven lipid catabolism. The most strongly upregulated genes — Cyp4a1 (log2FC 4.82), Acox1 (3.67), and Cpt1a (1.94) — are canonical PPARα transcriptional targets that catalyze fatty acid beta-oxidation and mitochondrial fatty acid import, respectively. Concurrent upregulation of Hmgcs2 (3.15) and Ppara (1.38) suggests a broader metabolic shift toward ketogenesis and mitochondrial biogenesis. Fgf21 induction (3.44) is a well-established PPARα target that promotes hepatic insulin sensitivity and is often used as a functional marker in PPARα agonism. Angptl4 upregulation (2.28) indicates enhanced hepatic lipid storage capacity, possibly reflecting compensatory lipid accumulation in response to increased flux through the PPARα pathway. On the downregulated side, suppression of Scd1 (3.72) and Fasn (2.91) reflects reduced de novo lipogenesis, while downregulation of Srebf1 (1.53) and Ccl2 (1.62) suggests attenuated lipogenic transcription and a reduced inflammatory gene program. The modest downregulation of Il6 and Tnf (−1.87 and −1.62) may indicate reduced hepatic inflammation, although this should be interpreted cautiously given the single time-point design. Caveats include the absence of a positive control gene (e.g., Cyp7a1), which would help confirm PPARα pathway activation, and the possibility that some changes reflect secondary inflammatory or oxidative stress responses rather than direct drug action.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-14

**Input:**

The following DESeq2 results table is from an Arabidopsis experiment comparing hypoxia treatment to normoxia (ambient oxygen) conditions. Interpret the differential expression results, identifying major functional themes, relevant biological processes, and any important caveats to consider.

| Gene | log2FC | padj | baseMean |
|--------|--------|------------|----------|
| ADH1 | 4.82 | 1.2e-45 | 324.5 |
| PDC1 | 3.94 | 8.7e-38 | 187.3 |
| LBD41 | 3.61 | 3.4e-29 | 92.1 |
| HRE1 | 3.28 | 5.1e-24 | 78.6 |
| PCO1 | 2.54 | 1.8e-17 | 63.4 |
| RAP2.12 | 2.73 | 2.9e-19 | 145.2 |
| SUS4 | 2.18 | 4.6e-14 | 256.8 |
| RBCS1A | -3.12 | 6.3e-28 | 1842.6 |
| LHCB1.1 | -2.87 | 4.1e-23 | 2103.4 |
| FNR1 | -2.31 | 9.8e-18 | 876.3 |
| GS2 | -2.09 | 7.2e-15 | 543.7 |
| CPN60B | -1.94 | 3.5e-13 | 421.8 |

**Model Output:**

These results reveal a canonical hypoxic transcriptional response in Arabidopsis. The most strongly upregulated genes are ADH1 (log2FC 4.82) and PDC1 (3.94), encoding alcohol dehydrogenase and pyruvate decarboxylase, respectively — enzymes that drive anaerobic glycolysis and are the primary oxygen-sensing targets of the HRE (hypoxia-responsive element) transcription factor. LBD41 (log2FC 3.61) and RAP2.12 (2.73) are HRE co-activators that amplify hypoxia signaling, while PCO1 (2.54) encodes a PDK-like enzyme that phosphorylates and inactivates the oxygen-sensing kinase ARF1, creating a negative feedback loop. SUS4 upregulation (2.18) suggests enhanced sucrose synthesis to buffer ATP depletion under low oxygen. The downregulated genes tell a complementary story: RBCS1A (log2FC −3.12) and LHCB1.1 (−2.87) are core photosynthetic light-harvesting complex subunits, consistent with the well-established trade-off between oxygen fixation and anaerobic metabolism under hypoxia. FNR1 repression (−2.31) reflects reduced nitrate assimilation, as nitrate reductase activity is oxygen-dependent. GS2 downregulation (−2.09) may indicate reduced nitrogen fixation capacity. CPN60B repression (−1.94) suggests reduced mitochondrial biogenesis. Caveats: these results reflect a single time-point; hypoxia tolerance is often time-dependent, and some changes may be adaptive responses to hypoxia rather than direct transcriptional targets. The relatively low baseMean for LBD41 and RAP2.12 warrants validation by qRT-PCR.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-15

**Input:**

The table below shows DESeq2 differential expression results from a zebrafish high-fat diet (HFD) experiment compared to control-fed siblings (n=6 per group, 8 weeks post-fertilization). Interpret the key biological themes, highlight relevant pathways, and note any important caveats for downstream analysis.

| Gene | log2FC | padj | baseMean |
|--------|--------|------|----------|
| fasn | 2.84 | 3.1e-07 | 245.3 |
| srebf1 | 2.31 | 4.8e-06 | 133.7 |
| scd1a | 2.09 | 2.9e-05 | 188.4 |
| pparg | 1.93 | 1.2e-04 | 156.1 |
| cd36 | 1.61 | 8.9e-04 | 311.8 |
| tnfab | 1.38 | 0.0234 | 78.2 |
| cebpb | 1.19 | 0.0445 | 202.6 |
| adipoq | -2.41 | 6.7e-07 | 86.9 |
| cyp7a1a | -2.13 | 3.3e-05 | 143.2 |
| insra | -1.82 | 7.6e-04 | 167.4 |
| irs2a | -1.54 | 0.0067 | 220.8 |
| slc2a2 | -1.29 | 0.0189 | 297.5 |
| lepr | -1.08 | 0.0312 | 188.9 |

**Model Output:**

These results reveal a coordinated transcriptional response to high-fat feeding in zebrafish consistent with diet-induced metabolic dysfunction. The most strongly upregulated genes—fASN (log2FC=2.84), SREBF1 (log2FC=2.31), and SCD1A (log2FC=2.09)—are canonical lipid biosynthesis and desaturation machinery, suggesting a shift toward de novo lipogenesis and increased fatty acid flux. Upregulation of PPARG (log2FC=1.93) indicates activation of the PPAR-alpha signaling axis, which drives hepatic lipid storage and insulin resistance. CD36 upregulation (log2FC=1.61) reflects increased fatty acid uptake, while tnfab and cebpb induction points to low-grade inflammation and NF-κB-mediated metabolic stress. The downregulated gene set is equally informative: loss of adipoq (log2FC=-2.41) and irs2a (log2FC=-1.54) indicates compromised insulin signaling and impaired insulin receptor substrate function, a hallmark of diet-induced metabolic syndrome. Reduced cyp7a1a expression suggests impaired bile acid synthesis, which can feed back to promote lipid accumulation. Decreased slc2a2 (GLUT4) and lepr (IGF-1 receptor) further implicate impaired glucose and IGF-1-mediated anabolic signaling. Caveats: whole-liver RNA-seq obscures tissue-specific responses; zebrafish have a different gut microbiome than mammals, which may confound lipid metabolism signals; and the 8-week timepoint captures early metabolic adaptation rather than late-stage disease progression.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-16

**Input:**

You are given a DESeq2 differential expression results table from a C. elegans infection experiment (infected vs. mock-treated control). Interpret the biological significance of these results, identifying major functional themes, likely signaling pathways involved, and any caveats that should be considered.

| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| nlp-29 | 6.21 | 1.4e-18 | 312.4 |
| abf-2 | 5.34 | 3.2e-15 | 87.6 |
| lys-7 | 4.08 | 8.9e-12 | 203.1 |
| spp-1 | 3.76 | 2.1e-10 | 144.8 |
| clec-60 | 3.19 | 4.7e-09 | 56.3 |
| gst-4 | 2.31 | 1.6e-07 | 521.9 |
| tir-1 | 1.94 | 3.8e-06 | 98.2 |
| hsp-16.41 | 2.68 | 9.1e-08 | 445.7 |
| vit-2 | -3.52 | 5.3e-11 | 1847.3 |
| col-19 | -2.14 | 2.9e-08 | 678.4 |
| fat-7 | -1.87 | 6.4e-07 | 334.6 |
| pmp-5 | -2.38 | 1.1e-08 | 89.1 |
| daf-15 | -1.63 | 4.2e-06 | 267.3 |

**Model Output:**

These results reveal a canonical innate immune transcriptional response in C. elegans, dominated by two opposing themes. Upregulated genes cluster into two functional groups: antimicrobial effectors (nlp-29, lys-7, spp-1) and pattern recognition receptors (clec-60, tir-1), indicating robust activation of the PRR-mediated innate immune pathway. The strong induction of abf-2, a C-type lectin that binds bacterial lipopolysaccharides, suggests pathogen-associated molecular pattern (PAMP) sensing. Concurrently, upregulation of gst-4 and hsp-16.41 points to concurrent oxidative stress and proteotoxic burden, consistent with the high metabolic demand of immune activation. Downregulated genes reflect the well-characterized immune-reproductive tradeoff: suppression of vit-2 (vitellogenin) and col-19 (cuticle collagen) indicates reduced somatic investment, while reduced fat-7 and pmp-5 suggest altered lipid and cuticle remodeling. Decreased daf-15 expression is notable, as DAF-16/FOXO is a master regulator of longevity and stress resistance; its downregulation may reflect a stress-activated feedback loop. Caveats: the infection type (bacterial, fungal, or parasitic) and infection dose are unspecified, which could alter the relative magnitude of PRR versus effector responses. Additionally, the mock control should be validated to ensure it is not itself inducing a low-level immune response.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-17

**Input:**

The following tables show differential expression results and GO enrichment analysis from a zebrafish experiment comparing stressed fish to unstressed controls. Interpret the combined results, connecting specific gene expression changes to the enriched biological pathways and describing the overall stress response program.

**Differential Expression Results (stressed vs. unstressed zebrafish)**

| Gene | log2FoldChange | padj | Description |
|------|---------------|------|-------------|
| fkbp5 | 3.82 | 2.1e-18 | FK506-binding protein 5 |
| crhb | 3.14 | 5.7e-15 | corticotropin-releasing hormone b |
| pomca | 2.89 | 1.3e-12 | proopiomelanocortin a |
| hsp90aa1.1 | 2.45 | 8.4e-11 | heat shock protein 90, alpha 1 |
| nr3c1 | 2.01 | 3.2e-09 | glucocorticoid receptor |
| socs3a | 1.78 | 1.1e-07 | suppressor of cytokine signaling 3a |
| igf1 | -2.33 | 4.6e-10 | insulin-like growth factor 1 |
| myh7 | -1.95 | 2.8e-08 | myosin heavy chain 7 |

**GO Enrichment Analysis (upregulated gene set)**

| GO Term | GO ID | p.adjust | Gene Count |
|---------|-------|----------|------------|
| response to glucocorticoid | GO:0051384 | 8.3e-14 | 24 |
| regulation of HPA axis | GO:0045822 | 2.1e-12 | 18 |
| response to heat | GO:0009408 | 5.6e-10 | 31 |
| JAK-STAT signaling pathway | GO:0007259 | 3.4e-09 | 22 |
| negative regulation of growth | GO:0045926 | 7.8e-08 | 19 |
| muscle contraction | GO:0006936 | 4.2e-07 | 27 |

**Model Output:**

The transcriptional response to stress in zebrafish is dominated by a coherent glucocorticoid axis. The most strongly upregulated gene, fkbp5 (log2FC = 3.82), encodes a co-chaperone that attenuates glucocorticoid receptor (nr3c1) activity, forming a negative feedback loop that limits corticosteroid signaling. Concurrent upregulation of crhb (log2FC = 3.14) and pomca (log2FC = 2.89) indicates robust activation of the hypothalamic-pituitary-interrenal (HPI) axis, driving corticosterone secretion. The co-enrichment of'response to glucocorticoid' and'regulation of HPA axis' in GO enrichment confirms this as the central stress response program. Upregulation of hsp90aa1.1 (log2FC = 2.45) and socs3a (log2FC = 1.78) reflects the canonical heat shock and JAK-STAT stress response, while igf1 downregulation (log2FC = -2.33) is consistent with the 'negative regulation of growth' enrichment and represents a well-characterized growth-suppression mechanism in teleosts. The downregulation of myh7 (log2FC = -1.95) and enrichment of'muscle contraction' likely reflect a shift away from anabolic muscle growth toward catabolic maintenance. Collectively, these data describe a coherent stress response involving glucocorticoid-mediated HPI axis activation, proteotoxic stress, and suppression of anabolic signaling.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-18

**Input:**

How much of the gene expression variations are attributed to genomic and epigenetic factors?


**Model Output:**

Genomic and epigenetic factors account for 70% of the gene expression variations.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-19

**Input:**

miRNA binding site for gene knock down?

**Model Output:**

The miRNA binding site for gene knock down is the seed region of the miRNA.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-20

**Input:**

The following DESeq2 differential expression results are from a mouse experiment comparing stressed vs. unstressed animals (n=6 per group, padj threshold 0.05). Interpret these results biologically: identify major functional themes, describe the relevant pathways, and note important caveats for interpreting this data.

| Gene | log2FC | padj | baseMean |
|--------|--------|-----------|----------|
| Fkbp5 | 2.14 | 4.2e-06 | 312.4 |
| Crh | 2.67 | 8.1e-05 | 87.3 |
| Sgk1 | 1.53 | 0.0031 | 428.7 |
| Nr4a1 | 1.89 | 0.0014 | 156.2 |
| Hspa1a | 2.03 | 0.0009 | 74.8 |
| Dusp1 | 1.42 | 0.0187 | 521.3 |
| Cxcl1 | 1.76 | 0.0062 | 43.5 |
| Bdnf | -1.31 | 0.0214 | 289.6 |
| Gad1 | -1.58 | 0.0078 | 347.1 |
| Pvalb | -1.94 | 0.0011 | 203.8 |
| Oxtr | -1.17 | 0.0341 | 118.4 |
| Nrxn1 | -0.87 | 0.0482 | 634.9 |

Contrast: stressed vs. unstressed mouse (n=6 per group). Wald test with Benjamini-Hochberg correction.

**Model Output:**

These results reveal a coherent stress-response transcriptional signature organized around two opposing themes. Upregulated genes cluster into two functional groups: glucocorticoid signaling and HPA axis activation, and cellular stress adaptation. Fkbp5 (log2FC 2.14) and Sgk1 (1.53) are canonical glucocorticoid-responsive genes that mediate negative feedback on the HPA axis, while Crh (2.67) directly drives the stress response. Nr4a1 (1.89) is a nuclear receptor that co-activates this axis, and Hspa1a (2.03) and Dusp1 (1.42) reflect the canonical HPA stress-response program of activating the hypothalamic-pituitary-adrenal axis. Cxcl1 upregulation (1.76) suggests a neuroinflammatory component, consistent with stress-induced activation of microglia in the brain. Downregulated genes point to a broader suppression of neural function: Bdnf (−1.31) and Gad1 (−1.58) indicate reduced neurotrophic support and inhibitory interneuron activity, while Pvalb (−1.94) and Oxtr (−1.17) reflect decreased parvalbumin-expressing and oxytocin-receptor-expressing neuron populations, respectively. Nrxn1 downregulation (−0.87) may reflect altered neuronal excitability. Important caveats: the stress paradigm is unspecified, so the specific HPA axis driver (e.g., restraint stress, TLR4 activation) could alter the Crh and Fkbp5 expression patterns. The relatively low baseMean for Crh (87.3) and Hspa1a (74.8) warrants validation by qRT-PCR.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-21

**Input:**

The following DESeq2 results table is from an Arabidopsis NPR1 knockout mutant compared to wild-type Col-0 plants under standard growth conditions. NPR1 (NON-EXPRESSOR OF PR GENES 1) is a master regulator of salicylic acid (SA) signaling. Interpret the differential expression results, identifying major functional themes, pathway perturbations, and any notable biological patterns. Note relevant caveats in the interpretation.

| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| PR1 | -3.81 | 2.1e-12 | 892.4 |
| PR5 | -3.24 | 4.3e-10 | 678.1 |
| PR2 | -2.93 | 1.8e-09 | 445.7 |
| WRKY70 | -2.14 | 8.9e-04 | 234.2 |
| ICS1 | -1.88 | 3.4e-04 | 312.6 |
| PAD4 | -1.63 | 4.1e-03 | 156.3 |
| PDF1.2 | 2.41 | 2.3e-04 | 387.5 |
| VSP2 | 2.09 | 9.1e-04 | 189.8 |
| JAZ1 | 1.82 | 6.7e-03 | 298.4 |
| ERF1 | 1.74 | 3.8e-03 | 267.1 |
| LOX2 | 1.53 | 1.9e-02 | 445.3 |
| MYC2 | 1.31 | 2.8e-02 | 523.9 |

**Model Output:**

The transcriptomic profile of the NPR1 knockout reveals a coherent collapse of salicylic acid (SA) signaling and a compensatory shift toward jasmonate/ethylene (JA/ET) dominance. The most strongly downregulated genes — PR1, PR5, and PR2 — are canonical SA-responsive genes whose transcription is directly driven by NPR1, and their coordinated suppression (log2FC −3.81 to −2.93) indicates a broad loss of SA-mediated immunity. Downregulation of WRKY70, a transcriptional activator of SA biosynthesis, further supports this interpretation. On the upregulated side, PDF1.2 (log2FC +2.41) and VSP2 (log2FC +2.09) are well-established SA-responsive genes whose induction is normally mediated by NPR1, suggesting a negative feedback loop where SA accumulation suppresses its own transcriptional targets. JAZ1 and ERF1 upregulation indicates activation of the JA/ET pathway, consistent with the known antagonism between SA and JA signaling. LOX2 induction points to increased fatty acid desaturation, a JA biosynthetic step. Elevated MYC2 expression is a key upstream regulator of JA-responsive gene expression, and its co-induction with JA-responsive genes suggests a positive feedback loop. Caveats: the absence of a JA/ET pathway control experiment (e.g., JA application in NPR1 background) means the observed JA signature could reflect indirect effects rather than direct pathway activation. Additionally, the relatively low baseMean of PAD4 (156.3) and ICS1 (312.6) warrants caution, as these genes are among the most sensitive to SA signaling and their modest fold-changes may not reflect true transcriptional changes.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-22

**Input:**

What is the two-stage analysis of RNA-Seq data?


**Model Output:**

The two-stage analysis of RNA-Seq data involves first identifying differentially expressed genes (DEGs) and then identifying enriched GO biological process terms.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-23

**Input:**

Given the provided peer-reviewed journal article title and authors, write an APA-formatted citation.

Title: Role of the microbiome in cancer development and therapy
Authors: Jennifer R. Plichta, Marek Ancukiewicz, Apurva Sharma, Surya Singh
Journal: CA: A Cancer Journal for Clinicians
Year: 2020
Volume: 70
Issue: 4
Pages: 299-312

**Model Output:**

Plichta, J. R., Ancukiewicz, M., Sharma, A., & Singh, S. (2020). Role of the microbiome in cancer development and therapy. CA: A Cancer Journal for Clinicians, 70(4), 299–312.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-24

**Input:**

You are given a differential expression (DE) results table and a GO enrichment table from a zebrafish high-fat diet versus control experiment. Interpret the biological significance of these findings, integrating the gene-level expression changes with the enriched pathways to explain the underlying metabolic mechanisms.

## Differential Expression Results (high-fat diet vs control, zebrafish liver)

| Gene | baseMean | log2FoldChange | lfcSE | stat | pvalue | padj |
|------|----------|----------------|-------|------|--------|------|
| fasn | 1842.3 | 3.21 | 0.19 | 16.89 | 2.4e-64 | 1.2e-61 |
| dgat2 | 976.1 | 2.87 | 0.21 | 13.67 | 9.1e-43 | 4.5e-40 |
| plin2 | 1124.7 | 2.54 | 0.20 | 12.70 | 1.7e-37 | 8.3e-35 |
| cidec | 443.2 | 2.19 | 0.22 | 9.95 | 4.3e-23 | 2.1e-20 |
| srebf1 | 672.8 | 1.93 | 0.24 | 8.04 | 1.4e-15 | 6.7e-13 |
| apoeb | 2341.5 | 1.76 | 0.23 | 7.65 | 7.1e-14 | 3.4e-11 |
| cpt1a | 889.4 | -2.44 | 0.22 | -11.09 | 1.4e-28 | 5.6e-26 |
| ppara | 514.6 | -1.88 | 0.24 | -7.83 | 1.9e-14 | 9.2e-12 |

## GO Enrichment Analysis

| GO ID | Term | Gene Set | Gene Count | Enrichment Score | FDR |
|-------|------|----------|------------|-----------------|-----|
| GO:0008610 | lipid biosynthetic process | UP | 24 | 4.71 | 3.2e-18 |
| GO:0019915 | lipid storage | UP | 12 | 5.23 | 7.8e-14 |
| GO:0045444 | fat cell differentiation | UP | 9 | 4.88 | 1.3e-09 |
| GO:0006635 | fatty acid beta-oxidation | DOWN | 14 | -4.34 | 5.4e-11 |
| GO:0034440 | lipid oxidation | DOWN | 18 | -3.97 | 2.1e-10 |
| GO:0006986 | response to unfolded protein | UP | 11 | 3.62 | 4.7e-08 |

**Model Output:**

The transcriptional landscape of zebrafish liver under high-fat diet reveals a coordinated metabolic reprogramming consistent with hepatic steatosis and insulin resistance. The most strongly upregulated gene, fasn (log2FC = 3.21), encodes the rate-limiting enzyme of de novo lipogenesis, directly driving enrichment of the lipid biosynthetic process GO term (24 genes, FDR = 3.2e-18). Concurrent upregulation of dgat2 (log2FC = 2.87) and cidec (log2FC = 2.19) further supports a pronounced lipid anabolic program, while srebf1 induction (log2FC = 1.93) indicates activation of the master lipogenic transcription factor SREBP-1c. The strong upregulation of apoeb (log2FC = 1.76) reflects increased hepatic VLDL secretion, consistent with the lipid storage GO term (12 genes, FDR = 7.8e-14). Critically, the downregulation of cpt1a (log2FC = -2.44) and ppara (log2FC = -1.88) together abolish the primary lipid catabolic machinery, explaining the suppression of fatty acid beta-oxidation and lipid oxidation terms. This metabolic shift is mechanistically coherent: PPARα-driven transcription of cpt1a and ppara normally promotes mitochondrial fatty acid uptake and oxidation, but their downregulation under high-fat conditions redirects lipid flux toward de novo synthesis. The enrichment of fat cell differentiation (GO:0045444) and response to unfolded protein (GO:0006986) reflects the hepatic steatosis phenotype and the attendant ER stress. Together, these data describe a zebrafish model of diet-induced hepatic lipid accumulation and metabolic dysfunction.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-25

**Input:**

The following table shows DESeq2 differential expression results from a C. elegans hypoxia vs. normoxia experiment (hypoxia is the numerator). Interpret these results biologically: identify the major functional themes, connect upregulated and downregulated genes to known pathways, and note any important caveats.

| Gene   | log2FC | padj      | baseMean |
|--------|--------|-----------|----------|
| fmo-2  |  4.23  | 2.1e-24   |  891.5   |
| nhr-57 |  3.61  | 8.7e-18   |  312.8   |
| cysl-2 |  3.08  | 1.4e-09   |  156.4   |
| hif-1  |  2.84  | 3.2e-12   |  487.3   |
| bnip-3 |  2.47  | 6.3e-08   |  203.7   |
| lgg-1  |  1.89  | 4.5e-06   | 1243.2   |
| egl-9  |  1.54  | 0.0023    |  678.9   |
| fat-7  | -2.78  | 3.9e-15   |  445.8   |
| nuo-1  | -2.31  | 1.8e-11   | 2341.6   |
| cco-1  | -1.97  | 4.2e-09   | 1876.3   |
| col-19 | -1.63  | 0.0087    |  892.4   |
| myo-3  | -1.44  | 0.0312    | 3214.7   |

**Model Output:**

These results reveal a canonical hypoxic transcriptional response in C. elegans organized around two opposing themes. Upregulated genes cluster into two functional groups: HIF-1 target genes (hif-1, cysl-2) and a stress-response arm involving the NHR-57 nuclear hormone receptor and the FOXO-like transcription factor fmo-2. The upregulation of bnip-3, a selective autophagy receptor, is consistent with the known role of HIF-1 in promoting proteostasis under low oxygen. Elevated lgg-1 (a glycolytic enzyme) and egl-9 (prolyl hydroxylase) suggest a metabolic reprogramming toward anaerobic glycolysis and a feedback mechanism to limit HIF-1 activity. Downregulated genes reflect coordinated suppression of oxidative metabolism: cco-1 (cytochrome c oxidase subunit), nuo-1 (Complex I), and fat-7 (Δ9 fatty acid desaturase) are all suppressed, indicating a broad reduction in mitochondrial electron transport chain activity. col-19 downregulation may reflect reduced cuticle synthesis under energy stress. The strong suppression of myo-3 (myosin heavy chain) is particularly noteworthy, as it suggests a trade-off between muscle contraction and energy conservation. Caveats include the fact that hif-1 itself is a post-translationally regulated protein and its fold-change may not reflect transcriptional activity; bulk RNA-seq cannot distinguish direct targets from indirect HIF-1-mediated effects.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-26

**Input:**

You are provided with a DESeq2 differential expression results table from a rat infection experiment (infected vs. mock control). Interpret the biological significance of these findings, identifying major functional themes, relevant pathways, and any noteworthy caveats.

DESeq2 results: infected vs. mock (rat liver, n=4/group)

| Gene | log2FC | padj | baseMean |
|--------|--------|------------|----------|
| Mx1 | 7.42 | 1.2e-45 | 234.7 |
| Isg15 | 6.18 | 3.4e-38 | 891.3 |
| Cxcl10 | 5.83 | 2.1e-29 | 67.4 |
| Irf7 | 4.95 | 8.7e-22 | 145.2 |
| Oas1a | 4.61 | 4.3e-19 | 312.8 |
| Stat1 | 3.74 | 1.6e-14 | 567.9 |
| Il6 | 3.22 | 2.9e-11 | 43.1 |
| Ccl2 | 2.87 | 7.4e-09 | 128.5 |
| Tnf | 2.41 | 3.1e-07 | 89.6 |
| Cyp2c11 | -3.85 | 4.2e-16 | 1823.4 |
| Alb | -2.67 | 1.8e-10 | 4521.7 |
| Ppara | -2.34 | 6.5e-08 | 743.2 |
| Ugt1a1 | -1.98 | 2.3e-06 | 389.4 |
| Slc22a7 | -1.72 | 4.8e-05 | 256.8 |

**Model Output:**

These results reveal a coordinated innate immune response in rat liver following infection, dominated by two opposing transcriptional programs. The most strongly upregulated genes — Mx1, Isg15, and Oas1a — are canonical interferon-stimulated genes (ISGs) that directly reflect activation of type I interferon signaling, consistent with a viral or intracellular bacterial pathogen. Irf7 upregulation suggests broad transcriptional reprogramming of the interferon response network. Stat1 induction reinforces this picture, as Stat1 is a central co-activator of interferon signaling. The chemokines Cxcl10 and Ccl2, along with the pro-inflammatory cytokines Il6 and Tnf, indicate concurrent neutrophil and monocyte recruitment, a hallmark of acute hepatic inflammation. The downregulated genes tell a complementary story: suppression of Cyp2c11, Alb, Ppara, Ugt1a1, and Slc22a7 reflects a well-characterized hepatic metabolic reprogramming — a phenomenon known as'metabolic immunomodulation' in which the liver shifts from anabolic to catabolic metabolism to support immune function. This pattern is consistent with the liver's well-established role in immune cell priming and cytokine storage. Caveats: the modest baseMean for Il6 and Tnf (43 and 89, respectively) warrants validation by qPCR or ELISA, as these low-abundance cytokines are prone to detection limits. Additionally, the relatively low fold-change for Cxcl10 (5.83) compared to the ISGs suggests it may be a secondary or late-phase response rather than an early transcriptional event.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-27

**Input:**

You are given a DESeq2 differential expression results table from a mouse experiment comparing hypoxia (1% O2, 24h) to normoxia (21% O2) in primary mouse hepatocytes. Interpret the biological significance of these results, identifying major functional themes, relevant pathways, and any important caveats.

| Gene | log2FC | padj | baseMean |
|--------|--------|------|----------|
| Egln3 | 3.21 | 4.1e-15 | 134.2 |
| Vegfa | 2.84 | 1.2e-12 | 245.7 |
| Bnip3 | 2.13 | 5.6e-11 | 178.4 |
| Slc2a1 | 2.31 | 3.4e-10 | 892.1 |
| Ldha | 1.92 | 8.7e-09 | 1543.6 |
| Pgk1 | 1.74 | 2.1e-08 | 1102.3 |
| Hk2 | 1.43 | 1.8e-06 | 421.8 |
| Ndrg1 | 1.51 | 6.3e-07 | 367.5 |
| Ppargc1a | -1.83 | 7.2e-08 | 312.4 |
| Acadm | -1.54 | 2.3e-06 | 567.9 |
| Sdha | -1.31 | 1.1e-05 | 789.2 |
| Cox4i1 | -1.19 | 4.5e-05 | 2341.0 |
| Cs | -1.08 | 8.9e-05 | 489.3 |
| Myc | -0.92 | 2.2e-04 | 234.1 |

**Model Output:**

These results reveal a canonical hypoxic transcriptional response in mouse hepatocytes, organized around three interconnected themes. First, HIF-1α targets are strongly upregulated: Egln3 (PHD3, log2FC 3.21) is a direct HIF-1α target that acts as a negative feedback brake on HIF-1α stability, while Vegfa induction (log2FC 2.84) drives angiogenic remodeling to restore oxygen delivery. Second, glycolytic reprogramming is evident: Slc2a1 (GLUT1, log2FC 2.31) and Pgk1 upregulation reflects increased anaerobic glucose metabolism, while Ldha and Hk2 induction further support a Warburg-like metabolic shift. Third, mitochondrial stress is indicated by Bnip3 upregulation (log2FC 2.13), which promotes mitophagy to reduce oxygen demand, and a coordinated downregulation of oxidative phosphorylation genes: Cox4i1, Sdha, and Acadm are all suppressed, consistent with a metabolic shift away from electron transport chain activity. Downregulation of Ppargc1a (PGC-1α) and Cs (cytochrome c) suggests impaired mitochondrial biogenesis and electron transport chain assembly capacity. Notably, Myc downregulation (log2FC −0.92) may reflect a well-characterized HIF-1α-MYC crosstalk in which HIF-1α represses Myc transcription to limit cell proliferation under hypoxia. Important caveats: hepatocytes are a heterogeneous cell population; these results reflect a mixed response rather than a single cell-type-specific signature. The 24-hour timepoint captures acute transcriptional responses; chronic hypoxia would likely reveal additional adaptive programs.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-28

**Input:**

What role does the downregulation of HAND expression play in rodent hypertrophy and human cardiomyopathy?


**Model Output:**

The downregulation of HAND expression plays a role in rodent hypertrophy and human cardiomyopathy.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-29

**Input:**

You are given a DESeq2 differential expression results table from a mouse tumor vs. normal tissue experiment. Interpret the biological significance of these results, identifying major functional themes, relevant pathways, and any important caveats.

| Gene | log2FC | padj | baseMean |
|------|--------|------|----------|
| Mki67 | 3.81 | 1.2e-45 | 892.4 |
| Birc5 | 4.13 | 6.3e-52 | 567.1 |
| Top2a | 3.94 | 2.4e-48 | 723.8 |
| Aurkb | 3.52 | 1.8e-41 | 312.6 |
| Ccnd1 | 2.87 | 3.4e-38 | 1205.3 |
| Myc | 2.43 | 8.7e-29 | 445.9 |
| Mmp9 | 3.19 | 5.6e-31 | 234.2 |
| Vegfa | 2.08 | 2.1e-22 | 678.5 |
| Cdh1 | -2.61 | 4.2e-28 | 1456.7 |
| Tjp1 | -1.93 | 9.2e-20 | 234.1 |
| Cdkn1a | -2.24 | 1.5e-24 | 345.8 |
| Pten | -1.82 | 7.9e-19 | 892.3 |
| Rb1 | -1.47 | 3.8e-15 | 567.4 |

**Model Output:**

These results reveal a coherent transcriptional signature of malignant transformation across multiple hallmarks of cancer. The most prominent upregulated genes — Mki67, Top2a, Aurkb, and Ccnd1 — collectively indicate active cell cycle progression and mitotic activity, consistent with the high proliferative index expected in tumor tissue. Concurrent upregulation of Myc and Birc5 (survivin) suggests that the tumor cells have acquired both proliferative and anti-apoptotic capacity. Mmp9 upregulation points to active extracellular matrix remodeling, a hallmark of invasive potential. Vegfa induction suggests angiogenic reprogramming to support tumor growth. The downregulated genes paint a complementary picture: loss of Cdh1 (E-cadherin) and Tjp1 (ZO-1) indicates epithelial-to-mesenchymal transition (EMT), a key driver of local invasion. Reduced Cdkn1a (p21) and Pten loss suggest impaired growth arrest and PI3K/AKT pathway activation, respectively. Downregulation of Rb1 and Cdh1 is particularly concerning, as Rb1 loss can drive oncogenic transcription and EMT. Caveats include the lack of cell-type deconvolution, which could mask tissue-specific effects; the absence of pathway-level enrichment analysis (e.g., GSEA for cell cycle, EMT, or angiogenesis) limits mechanistic inference; and the modest baseMean for Vegfa warrants validation.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)

## EXAMPLE EX-30

**Input:**

Explain the mechanism of a biological process in simpler terms.

Autophagy is a highly conserved lysosomal degradation process that plays critical roles in cellular maintenance, homeostasis, and survival in response to diverse stresses such as nutrient deprivation, metabolic stress, and hypoxia.

**Model Output:**

Autophagy is a way that cells recycle their own damaged or unwanted parts. It helps keep the cell healthy and functioning properly.

---

**Questions:**
- Biological Accuracy (1-5)
- Completeness (1-5)
- Clarity (1-5)
- Notes (optional, free text)
