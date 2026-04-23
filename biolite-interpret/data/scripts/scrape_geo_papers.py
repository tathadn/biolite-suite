#!/usr/bin/env python3
"""
scrape_geo_papers.py — Pair GEO RNA-seq datasets with published interpretations.

Pipeline:
  1. Query GEO for RNA-seq Series with linked PubMed IDs
  2. Extract top DE genes via GEO2R / DESeq2
  3. Fetch paper abstract + discussion from PMC
  4. Pair structured table with interpretation paragraph

Usage:
    python scrape_geo_papers.py --output_dir ../raw/geo_pairs --max_datasets 50
"""

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from typing import Optional

import requests

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GEO_SEARCH = f"{NCBI_BASE}/esearch.fcgi"
GEO_SUMMARY = f"{NCBI_BASE}/esummary.fcgi"
PUBMED_FETCH = f"{NCBI_BASE}/efetch.fcgi"

# Curated seed datasets with known good interpretations
SEED_DATASETS = [
    {"gse": "GSE50760",  "organism": "human", "contrast": "colorectal cancer vs normal colon",      "pmid": "25049118"},
    {"gse": "GSE108643", "organism": "mouse", "contrast": "M1 vs M2 macrophage polarization",       "pmid": "30018073"},
    {"gse": "GSE132903", "organism": "human", "contrast": "Alzheimer's vs control brain",            "pmid": "31768066"},
    {"gse": "GSE126848", "organism": "human", "contrast": "NASH vs healthy liver",                   "pmid": "31648789"},
    {"gse": "GSE150316", "organism": "human", "contrast": "COVID-19 vs normal lung",                 "pmid": "32707573"},
    {"gse": "GSE102746", "organism": "mouse", "contrast": "high-fat diet vs control liver",          "pmid": "29237824"},
    {"gse": "GSE164073", "organism": "human", "contrast": "tumor vs normal breast tissue",           "pmid": "33597543"},
    {"gse": "GSE147507", "organism": "human", "contrast": "SARS-CoV-2 infected vs mock lung cells",  "pmid": "32416070"},
    {"gse": "GSE116250", "organism": "human", "contrast": "dilated cardiomyopathy vs donor heart",   "pmid": "30535219"},
    {"gse": "GSE89632",  "organism": "human", "contrast": "NAFLD steatosis vs healthy liver",        "pmid": "28859095"},

    # Drosophila — added to address organism gap
    {"gse": "GSE317804", "organism": "Drosophila",  "contrast": "starved vs fed follicle stem cells",                  "pmid": "41648421"},
    {"gse": "GSE313293", "organism": "Drosophila",  "contrast": "TORC1-active vs TORC1-deficient oocytes",             "pmid": "41588113"},
    {"gse": "GSE297750", "organism": "Drosophila",  "contrast": "H3.2K9me2-deficient vs wild-type heterochromatin",    "pmid": "41755642"},
    {"gse": "GSE308015", "organism": "Drosophila",  "contrast": "CP190 architectural protein KO vs wild-type",          "pmid": "41444637"},
    {"gse": "GSE299646", "organism": "Drosophila",  "contrast": "IntS11 maternal KO vs wild-type embryos",              "pmid": "41955115"},

    # Arabidopsis
    {"gse": "GSE293194", "organism": "Arabidopsis", "contrast": "cambium-activated vs quiescent root tissue",           "pmid": "41823877"},
    {"gse": "GSE303753", "organism": "Arabidopsis", "contrast": "enhanced tocopherol biosynthesis vs control leaves",    "pmid": "41446143"},
    {"gse": "GSE277320", "organism": "Arabidopsis", "contrast": "thermotolerance transgene vs wild-type under heat",     "pmid": "41675614"},
    {"gse": "GSE255301", "organism": "Arabidopsis", "contrast": "met1-derived epiRIL vs wild-type",                      "pmid": "41700090"},
    {"gse": "GSE309559", "organism": "Arabidopsis", "contrast": "sORF peptide signaling vs control phloem",              "pmid": "41937606"},

    # C. elegans
    {"gse": "GSE306611", "organism": "C. elegans",  "contrast": "fasted H3K27ac-deficient vs wild-type",                 "pmid": "40950206"},
    {"gse": "GSE307065", "organism": "C. elegans",  "contrast": "Vitamin B12-treated PUF60 mutant vs untreated",         "pmid": "41333426"},
    {"gse": "GSE318477", "organism": "C. elegans",  "contrast": "dauer vs reproductive development",                     "pmid": "39229130"},
    {"gse": "GSE285634", "organism": "C. elegans",  "contrast": "PERK-induced ER stress vs unstressed adults",           "pmid": "41176528"},
    {"gse": "GSE279559", "organism": "C. elegans",  "contrast": "Urolithin A-treated vs control aged worms",             "pmid": "40944367"},
    {"gse": "GSE317801", "organism": "C. elegans",  "contrast": "3D enriched habitat vs standard plate-reared",          "pmid": "41622909"},
]


def search_geo_rnaseq(query: str = "RNA-seq", max_results: int = 200, api_key: str = None) -> list[str]:
    """Search GEO for RNA-seq datasets with linked publications."""
    params = {
        "db": "gds",
        "term": f"{query}[All Fields] AND gse[Entry Type] AND Homo sapiens[Organism]",
        "retmax": max_results,
        "retmode": "json",
    }
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(GEO_SEARCH, params=params, timeout=30)
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"GEO search error: {e}")
        return []


def fetch_pubmed_abstract(pmid: str, api_key: str = None) -> Optional[str]:
    """Fetch abstract text from PubMed."""
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "text",
    }
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(PUBMED_FETCH, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception as e:
        print(f"  PubMed fetch error for {pmid}: {e}")
    return None


def fetch_pmc_fulltext(pmcid: str, api_key: str = None) -> Optional[str]:
    """Fetch full text from PMC (Open Access subset)."""
    params = {
        "db": "pmc",
        "id": pmcid,
        "rettype": "xml",
        "retmode": "xml",
    }
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(PUBMED_FETCH, params=params, timeout=60)
        if resp.status_code == 200:
            # Parse XML to extract results/discussion sections
            root = ET.fromstring(resp.content)
            sections = []
            for sec in root.iter("sec"):
                title_elem = sec.find("title")
                if title_elem is not None:
                    title = title_elem.text or ""
                    if any(kw in title.lower() for kw in ["result", "discussion", "interpretation"]):
                        paragraphs = [p.text for p in sec.iter("p") if p.text]
                        sections.extend(paragraphs)
            return "\n\n".join(sections) if sections else None
    except Exception as e:
        print(f"  PMC fetch error for {pmcid}: {e}")
    return None


def pmid_to_pmcid(pmid: str, api_key: str = None) -> Optional[str]:
    """Convert PubMed ID to PMC ID."""
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    params = {"ids": pmid, "format": "json"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        records = data.get("records", [])
        if records and "pmcid" in records[0]:
            return records[0]["pmcid"]
    except Exception:
        pass
    return None


def process_seed_datasets(output_dir: str, api_key: str = None):
    """Process curated seed datasets."""
    os.makedirs(output_dir, exist_ok=True)
    pairs = []

    for seed in SEED_DATASETS:
        print(f"Processing {seed['gse']} ({seed['contrast']})...")

        # Fetch abstract
        abstract = fetch_pubmed_abstract(seed["pmid"], api_key)
        if not abstract:
            print(f"  Skipping — no abstract found")
            continue

        # Try PMC full text
        pmcid = pmid_to_pmcid(seed["pmid"], api_key)
        fulltext_sections = None
        if pmcid:
            print(f"  Found PMC: {pmcid}, fetching full text...")
            fulltext_sections = fetch_pmc_fulltext(pmcid, api_key)

        interpretation = fulltext_sections or abstract

        pair = {
            "gse_id": seed["gse"],
            "organism": seed["organism"],
            "contrast": seed["contrast"],
            "pmid": seed["pmid"],
            "pmcid": pmcid,
            "has_fulltext": fulltext_sections is not None,
            "interpretation_source": interpretation[:2000],  # truncate
            "de_table_placeholder": f"[Run GEO2R on {seed['gse']} to extract top DE genes]",
        }
        pairs.append(pair)
        print(f"  OK — {'full text' if fulltext_sections else 'abstract only'}")

        time.sleep(0.5)  # NCBI rate limit

    output_path = os.path.join(output_dir, "geo_paper_pairs.json")
    with open(output_path, "w") as f:
        json.dump(pairs, f, indent=2)

    print(f"\n=== Done ===")
    print(f"Processed: {len(pairs)} / {len(SEED_DATASETS)} seed datasets")
    print(f"With full text: {sum(1 for p in pairs if p['has_fulltext'])}")
    print(f"Saved to: {output_path}")
    print(f"\nNext step: Run data/scripts/run_deseq2.R to extract DE tables for each GSE.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="../raw/geo_pairs")
    parser.add_argument("--api_key", type=str, default=None, help="NCBI API key (optional, increases rate limit)")
    args = parser.parse_args()

    process_seed_datasets(args.output_dir, args.api_key)
