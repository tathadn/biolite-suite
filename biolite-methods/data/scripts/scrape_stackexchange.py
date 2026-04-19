#!/usr/bin/env python3
"""
scrape_stackexchange.py — Scrape methodology Q&A from bioinformatics.stackexchange.com

Stack Exchange content is CC-BY-SA-4.0 licensed.

Used as the substitute for scrape_biostars.py after Biostars went behind a
Cloudflare managed challenge that blocks programmatic access.

Usage:
    python scrape_stackexchange.py --output_dir ../raw/stackexchange --max_pages_per_tag 1
"""

import argparse
import json
import os
import re
import time
from html import unescape

import requests


API = "https://api.stackexchange.com/2.3"
SITE = "bioinformatics"

TARGET_TAGS = [
    "rna-seq", "deseq2", "edger", "limma", "differential-expression",
    "normalization", "alignment", "star", "hisat2", "microbiome",
    "qiime2", "16s", "splicing", "rmats", "variant-calling",
    "gatk", "experimental-design", "statistics", "enrichment",
    "go-enrichment", "kegg", "batch-effect", "pca", "clustering",
    "salmon", "kallisto", "bowtie2", "bwa", "samtools",
    "single-cell", "scrnaseq", "seurat", "scanpy",
]

METHOD_KEYWORDS = [
    "which tool", "should i use", "how to choose", "best practice",
    "what is the best", "is it appropriate", "when to use",
    "difference between", "compare", "vs", "versus",
    "recommend", "how many replicates", "what normalization",
    "is it correct to", "appropriate method", "which method",
    "pipeline", "workflow", "best approach",
]


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<pre><code>(.*?)</code></pre>", r"\n```\n\1\n```\n", s, flags=re.DOTALL)
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s, flags=re.DOTALL)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def is_methodology(title: str, body: str) -> bool:
    combined = f"{title} {body}".lower()
    return any(kw in combined for kw in METHOD_KEYWORDS)


def se_get(path: str, params: dict, retries: int = 3) -> dict | None:
    """Hard-fail on non-200 (no silent zeros). Honor SE backoff."""
    url = f"{API}/{path.lstrip('/')}"
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            backoff = data.get("backoff")
            if backoff:
                print(f"    backoff requested: sleep {backoff}s")
                time.sleep(int(backoff))
            return data
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "30"))
            print(f"    HTTP 429 — sleeping {wait}s (attempt {attempt+1}/{retries})")
            time.sleep(wait)
            continue
        print(f"    HTTP {r.status_code}: {r.text[:200]}")
        return None
    return None


def fetch_questions_for_tag(tag: str, max_pages: int) -> list[dict]:
    """Fetch top-voted questions for a tag with bodies inline."""
    out = []
    for page in range(1, max_pages + 1):
        d = se_get("questions", {
            "site": SITE,
            "tagged": tag,
            "sort": "votes",
            "order": "desc",
            "pagesize": 100,
            "page": page,
            "filter": "withbody",
        })
        if not d:
            break
        items = d.get("items", [])
        out.extend(items)
        if not d.get("has_more"):
            break
        time.sleep(0.2)
    return out


def fetch_answers(answer_ids: list[int]) -> dict[int, dict]:
    """Batch-fetch answer bodies by id (up to 100 per call)."""
    by_id: dict[int, dict] = {}
    for i in range(0, len(answer_ids), 100):
        batch = answer_ids[i:i + 100]
        ids_str = ";".join(str(x) for x in batch)
        d = se_get(f"answers/{ids_str}", {
            "site": SITE,
            "filter": "withbody",
        })
        if not d:
            continue
        for a in d.get("items", []):
            by_id[a["answer_id"]] = a
        time.sleep(0.2)
    return by_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="../raw/stackexchange")
    parser.add_argument("--max_pages_per_tag", type=int, default=1,
                        help="API pages per tag (each page = up to 100 questions)")
    parser.add_argument("--min_score", type=int, default=1,
                        help="Minimum question score")
    parser.add_argument("--require_accepted", action="store_true", default=True,
                        help="Only keep questions with an accepted answer")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    seen_qids: set[int] = set()
    candidates: dict[int, dict] = {}  # accepted_answer_id -> question metadata

    for tag in TARGET_TAGS:
        print(f"Tag: {tag}")
        questions = fetch_questions_for_tag(tag, args.max_pages_per_tag)
        print(f"  fetched {len(questions)} raw")
        kept = 0
        for q in questions:
            qid = q.get("question_id")
            if not qid or qid in seen_qids:
                continue
            seen_qids.add(qid)
            if q.get("score", 0) < args.min_score:
                continue
            aid = q.get("accepted_answer_id")
            if args.require_accepted and not aid:
                continue
            title = q.get("title", "")
            body = strip_html(q.get("body", ""))
            if not is_methodology(title, body):
                continue
            candidates[aid] = {
                "qid": qid,
                "title": title,
                "body": body,
                "tags": q.get("tags", []),
                "score": q.get("score", 0),
                "answer_count": q.get("answer_count", 0),
            }
            kept += 1
        print(f"  kept {kept} methodology questions")
        time.sleep(0.3)

    print(f"\nFetching {len(candidates)} accepted answers in batches of 100...")
    answers = fetch_answers(list(candidates.keys()))
    print(f"  got {len(answers)} answer bodies")

    qa_pairs = []
    for aid, q in candidates.items():
        a = answers.get(aid)
        if not a:
            continue
        answer_text = strip_html(a.get("body", ""))
        if len(answer_text) < 50:
            continue
        qa_pairs.append({
            "question": f"{q['title']}\n\n{q['body']}" if q['body'] else q['title'],
            "chosen": answer_text,
            "se_question_id": q["qid"],
            "se_answer_id": aid,
            "question_score": q["score"],
            "answer_score": a.get("score", 0),
            "tags": q["tags"],
            "source": "stackexchange-bioinformatics",
        })

    out_path = os.path.join(args.output_dir, "stackexchange_qa.json")
    with open(out_path, "w") as f:
        json.dump(qa_pairs, f, indent=2)

    print(f"\n=== Scraping complete ===")
    print(f"Total Q&A pairs: {len(qa_pairs)}")
    print(f"Saved to: {out_path}")

    tag_counts: dict[str, int] = {}
    for qa in qa_pairs:
        for t in qa.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print("\nTop tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {tag}: {count}")


if __name__ == "__main__":
    main()
