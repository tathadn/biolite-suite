#!/usr/bin/env python3
"""Build the RAG knowledge base for methods QA.

Sources:
  1. Local Q&A JSONs (DESeq2 40 + QIIME2 50): each entry indexed as one chunk
     of "Q: ...\\n\\nA: ..." form.
  2. DESeq2 vignette HTML (Bioconductor) — chunked to ~300 words.
  3. STAR README (GitHub) — chunked to ~300 words.

Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384-dim, CPU-fine).
Index: FAISS IndexFlatIP on L2-normalized vectors (= cosine similarity).

Output:
  biolite-methods/rag/faiss_index/index.faiss
  biolite-methods/rag/faiss_index/chunks.json   (parallel list, index i ↔ row i)
"""

import json
import re
import urllib.request
from pathlib import Path

import faiss
import numpy as np
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

ROOT = Path("/fs1/scratch/tathadbn/biolite-suite/biolite-methods")
DOCS = ROOT / "data/raw/docs"
RAG_DIR = ROOT / "rag"
KB_DIR = RAG_DIR / "faiss_index"
EXTRA_DIR = RAG_DIR / "raw_extra"

CHUNK_WORDS = 300
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_qa_chunks() -> list[dict]:
    out = []
    for fname in ["docs_deseq2_qa.json", "docs_qiime2_qa.json"]:
        with open(DOCS / fname) as f:
            for entry in json.load(f):
                text = f"Q: {entry['question']}\n\nA: {entry['chosen']}"
                out.append({
                    "text": text,
                    "source": entry["source"],
                    "section": entry.get("doc_section", ""),
                    "kind": "qa",
                })
    return out


def chunk_paragraphs(text: str, n_words: int = CHUNK_WORDS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur, cur_words = [], [], 0
    for p in paragraphs:
        wc = len(p.split())
        if cur_words + wc > n_words and cur:
            chunks.append("\n\n".join(cur))
            cur, cur_words = [], 0
        cur.append(p)
        cur_words += wc
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def download(url: str, dest: Path) -> str:
    if dest.exists():
        return dest.read_text(encoding="utf-8", errors="replace")
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "biolite-rag/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", errors="replace")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body)
    print(f"  saved {len(body)} chars -> {dest}")
    return body


def html_to_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def main():
    chunks: list[dict] = []

    qa = load_qa_chunks()
    chunks.extend(qa)
    print(f"Loaded {len(qa)} Q&A entries (deseq2 + qiime2)")

    deseq_html = download(
        "https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html",
        EXTRA_DIR / "DESeq2_vignette.html",
    )
    deseq_text = html_to_text(deseq_html)
    deseq_chunks = chunk_paragraphs(deseq_text)
    for c in deseq_chunks:
        chunks.append({"text": c, "source": "docs-deseq2-vignette-full", "section": "", "kind": "doc"})
    print(f"DESeq2 vignette: {len(deseq_chunks)} chunks (~{CHUNK_WORDS}w each)")

    star_md = download(
        "https://raw.githubusercontent.com/alexdobin/STAR/master/README.md",
        EXTRA_DIR / "STAR_README.md",
    )
    star_chunks = chunk_paragraphs(star_md)
    for c in star_chunks:
        chunks.append({"text": c, "source": "docs-star-readme", "section": "", "kind": "doc"})
    print(f"STAR README: {len(star_chunks)} chunks")

    print(f"\nLoading embedder: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(chunks)} chunks...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
        batch_size=64,
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"\nFAISS index: {index.ntotal} vectors, dim={dim}")

    KB_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(KB_DIR / "index.faiss"))
    with open(KB_DIR / "chunks.json", "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"Wrote {KB_DIR}/index.faiss and chunks.json ({len(chunks)} chunks)")

    # Quick self-test: retrieve top-3 for one of the test questions
    test_q = "Should I use DESeq2 or edgeR for my 2-replicate RNA-seq experiment?"
    q_emb = model.encode([test_q], normalize_embeddings=True)
    q_emb = np.asarray(q_emb, dtype="float32")
    D, I = index.search(q_emb, 3)
    print(f"\nSelf-test query: {test_q!r}")
    for rank, (score, i) in enumerate(zip(D[0], I[0]), 1):
        c = chunks[i]
        snippet = c["text"][:140].replace("\n", " ")
        print(f"  [{rank}] sim={score:.3f} src={c['source']:32s} | {snippet}...")


if __name__ == "__main__":
    main()
