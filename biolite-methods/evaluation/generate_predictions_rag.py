#!/usr/bin/env python3
"""Generate RAG-augmented predictions on the methods test set.

For each test question:
  1. Embed the question with all-MiniLM-L6-v2.
  2. Retrieve top-k chunks from the FAISS knowledge base (default k=3).
  3. Build an instruction prompt that includes the retrieved chunks.
  4. Generate with the (optionally adapter-wrapped) policy LLM.

Usage:
    # Vanilla 3B + RAG:
    python generate_predictions_rag.py \
        --test_file ../data/splits/test.json \
        --output results/predictions_vanilla_3b_rag.json \
        --model_name vanilla-llama-3.2-3b-instruct-rag \
        --base_model meta-llama/Llama-3.2-3B-Instruct

    # DPO 3B + RAG:
    python generate_predictions_rag.py \
        --test_file ../data/splits/test.json \
        --output results/predictions_dpo_3b_rag.json \
        --model_name methods-dpo-3b-from-sft-rag \
        --base_model tathadn/biolite-interpret-3b \
        --adapter_path ../training/checkpoints/biolite-methods-dpo-methods-dpo-3b-from-sft
"""

import argparse
import gc
import json
import os
import time
from pathlib import Path

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


KB_DIR = Path("/fs1/scratch/tathadbn/biolite-suite/biolite-methods/rag/faiss_index")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

PROMPT_TEMPLATE = (
    "Use the following reference material to answer the question. "
    "Cite specific tools, parameters, and best practices from the references.\n\n"
    "{context}\n\n"
    "Question: {question}"
)


def load_kb():
    index = faiss.read_index(str(KB_DIR / "index.faiss"))
    with open(KB_DIR / "chunks.json") as f:
        chunks = json.load(f)
    assert index.ntotal == len(chunks), (
        f"index has {index.ntotal} vectors but chunks.json has {len(chunks)} entries"
    )
    return index, chunks


def retrieve(index, chunks, embedder, question: str, k: int):
    q_emb = embedder.encode([question], normalize_embeddings=True)
    q_emb = np.asarray(q_emb, dtype="float32")
    D, I = index.search(q_emb, k)
    return [
        {"score": float(D[0][r]), "source": chunks[I[0][r]]["source"], "text": chunks[I[0][r]]["text"]}
        for r in range(k)
    ]


def build_user_message(question: str, hits: list[dict]) -> str:
    context = "\n\n---\n\n".join(h["text"] for h in hits)
    return PROMPT_TEMPLATE.format(context=context, question=question)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--max_input_tokens", type=int, default=4096,
                        help="Truncation for very long context+question (Llama 3.2 supports 128k)")
    args = parser.parse_args()

    print(f"Loading KB from {KB_DIR}")
    index, chunks = load_kb()
    print(f"  {index.ntotal} vectors, {len(chunks)} chunks")

    print(f"Loading embedder {EMBED_MODEL}")
    embedder = SentenceTransformer(EMBED_MODEL)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading policy model {args.base_model}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if args.adapter_path:
        from peft import PeftModel
        print(f"Stacking DPO adapter from {args.adapter_path}...")
        model = PeftModel.from_pretrained(model, args.adapter_path)

    model.eval()
    gc.collect()
    torch.cuda.empty_cache()

    with open(args.test_file) as f:
        test = json.load(f)

    print(f"\nGenerating RAG predictions for {len(test)} examples ({args.model_name}, k={args.top_k})...")
    predictions = []
    start = time.time()
    for i, ex in enumerate(test):
        question = ex["question"]
        reference = ex["chosen"]
        category = ex.get("category", "")
        source = ex.get("source", "")

        hits = retrieve(index, chunks, embedder, question, args.top_k)
        user_msg = build_user_message(question, hits)
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": user_msg}],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(
            prompt, return_tensors="pt",
            truncation=True, max_length=args.max_input_tokens,
        ).to(model.device)
        prompt_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        gen_tokens = out[0, prompt_len:]
        prediction = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        predictions.append({
            "input": question,
            "prediction": prediction,
            "reference": reference,
            "model": args.model_name,
            "category": category,
            "source": source,
            "retrieved": [
                {"rank": r + 1, "score": h["score"], "source": h["source"], "text_head": h["text"][:200]}
                for r, h in enumerate(hits)
            ],
        })

        elapsed = time.time() - start
        eta = (elapsed / (i + 1)) * (len(test) - i - 1)
        print(f"  [{i+1}/{len(test)}] {len(gen_tokens)} tok | prompt {prompt_len} tok | elapsed {elapsed:.0f}s | eta {eta:.0f}s")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"\nSaved {len(predictions)} predictions to {args.output}")
    print(f"Peak GPU: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
