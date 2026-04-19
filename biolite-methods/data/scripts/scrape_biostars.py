#!/usr/bin/env python3
"""
scrape_biostars.py — Scrape methodology Q&A from Biostars.org

Biostars content is CC-BY-4.0 licensed.

NOTE (2026-04-19): Biostars now sits behind a Cloudflare managed challenge
that blocks programmatic access from `requests`, `cloudscraper`, and
`curl_cffi` (all return HTTP 403 with the "Just a moment..." JS challenge
page). A real headless browser (Playwright) would be required to bypass.
We instead switched the methodology corpus to bioinformatics.stackexchange.com
— see scrape_stackexchange.py.

Known bug if you do unblock it: fetch_posts_by_tag() silently returns []
on any non-200 status (including 403/429), so failed scrapes report
"Total Q&A pairs: 0" with no error. Add a hard-fail / log on non-200
before relying on this script.

Usage:
    python scrape_biostars.py --output_dir ../raw/biostars --max_pages 50
"""

import argparse
import json
import os
import time
import requests
from bs4 import BeautifulSoup


# Tags targeting methodology questions
TARGET_TAGS = [
    "rna-seq", "deseq2", "edger", "limma", "differential-expression",
    "normalization", "alignment", "star", "hisat2", "microbiome",
    "qiime2", "16s", "splicing", "rmats", "variant-calling",
    "gatk", "experimental-design", "statistics", "enrichment",
    "go-enrichment", "kegg", "batch-effect", "pca", "clustering",
    "salmon", "kallisto", "bowtie2", "bwa", "samtools",
    "single-cell", "scrnaseq", "seurat", "scanpy",
]

# Keywords indicating METHODOLOGY questions (not debugging)
METHOD_KEYWORDS = [
    "which tool", "should i use", "how to choose", "best practice",
    "what is the best", "is it appropriate", "when to use",
    "difference between", "compare", "vs", "versus",
    "recommend", "how many replicates", "what normalization",
    "is it correct to", "appropriate method", "which method",
    "pipeline", "workflow", "best approach",
]

BIOSTARS_API = "https://www.biostars.org/api"
BIOSTARS_BASE = "https://www.biostars.org"


def fetch_posts_by_tag(tag: str, limit: int = 50) -> list[dict]:
    """Fetch posts from Biostars by tag using the API."""
    url = f"{BIOSTARS_API}/post/list/{tag}/"
    posts = []

    try:
        params = {"limit": limit}
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            posts = data if isinstance(data, list) else data.get("results", [])
    except Exception as e:
        print(f"  Warning: Failed to fetch tag '{tag}': {e}")

    return posts


def fetch_post_detail(post_id: int) -> dict | None:
    """Fetch full post details including answers."""
    url = f"{BIOSTARS_API}/post/{post_id}/"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  Warning: Failed to fetch post {post_id}: {e}")
    return None


def is_methodology_question(title: str, content: str) -> bool:
    """Check if a post is a methodology question (not debugging)."""
    combined = f"{title} {content}".lower()
    return any(kw in combined for kw in METHOD_KEYWORDS)


def clean_html(html_text: str) -> str:
    """Strip HTML tags but preserve code blocks."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")

    # Preserve code blocks
    for code_tag in soup.find_all("code"):
        code_tag.string = f"\n```\n{code_tag.get_text()}\n```\n"

    text = soup.get_text(separator="\n")
    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def scrape_biostars(output_dir: str, max_per_tag: int = 30):
    """Main scraping pipeline."""
    os.makedirs(output_dir, exist_ok=True)

    all_qa_pairs = []
    seen_ids = set()

    for tag in TARGET_TAGS:
        print(f"Fetching tag: {tag}...")
        posts = fetch_posts_by_tag(tag, limit=max_per_tag)
        print(f"  Got {len(posts)} posts")

        for post_summary in posts:
            post_id = post_summary.get("id")
            if not post_id or post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            # Check basic filters
            view_count = post_summary.get("view_count", 0)
            answer_count = post_summary.get("answer_count", 0)
            if view_count < 500 or answer_count < 1:
                continue

            # Fetch full post
            detail = fetch_post_detail(post_id)
            if not detail:
                continue

            title = detail.get("title", "")
            content = clean_html(detail.get("content", ""))

            # Filter for methodology questions
            if not is_methodology_question(title, content):
                continue

            # Get accepted or highest-voted answer
            answers = detail.get("answers", [])
            if not answers:
                continue

            # Sort by vote count, prefer accepted
            answers_sorted = sorted(
                answers,
                key=lambda a: (a.get("accepted", False), a.get("vote_count", 0)),
                reverse=True,
            )
            best_answer = answers_sorted[0]
            answer_text = clean_html(best_answer.get("content", ""))

            if len(answer_text) < 50:  # skip very short answers
                continue

            qa_pair = {
                "question": f"{title}\n\n{content}" if content else title,
                "chosen": answer_text,
                "biostars_id": post_id,
                "view_count": view_count,
                "answer_votes": best_answer.get("vote_count", 0),
                "accepted": best_answer.get("accepted", False),
                "tags": detail.get("tags", []),
                "source": "biostars",
            }
            all_qa_pairs.append(qa_pair)

        # Rate limit
        time.sleep(1)

    # Save
    output_path = os.path.join(output_dir, "biostars_qa.json")
    with open(output_path, "w") as f:
        json.dump(all_qa_pairs, f, indent=2)

    print(f"\n=== Scraping complete ===")
    print(f"Total Q&A pairs: {len(all_qa_pairs)}")
    print(f"Saved to: {output_path}")

    # Category distribution
    tag_counts = {}
    for qa in all_qa_pairs:
        for t in qa.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print(f"\nTop tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {tag}: {count}")

    return all_qa_pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="../raw/biostars")
    parser.add_argument("--max_per_tag", type=int, default=30)
    args = parser.parse_args()

    scrape_biostars(args.output_dir, args.max_per_tag)
