#!/usr/bin/env python3
"""Generate predictions on the methods test set for baseline or DPO-trained model.

Usage:
    # Vanilla baseline (no adapter):
    python generate_predictions.py \
        --test_file ../data/splits/test.json \
        --output results/baseline_predictions.json \
        --model_name vanilla-llama-3.2-1b-instruct \
        --base_model meta-llama/Llama-3.2-1B-Instruct

    # DPO-from-SFT (base must be the SFT adapter repo so interpret-LoRA loads first,
    # then we stack the DPO adapter on top):
    python generate_predictions.py \
        --test_file ../data/splits/test.json \
        --output results/dpo_1b_from_sft_predictions.json \
        --model_name methods-dpo-1b-from-sft \
        --base_model tathadn/biolite-interpret-1b \
        --adapter_path ../training/checkpoints/biolite-methods-dpo-methods-dpo-1b-from-sft

    # DPO-from-base (Llama Instruct base + DPO LoRA):
    python generate_predictions.py \
        --test_file ../data/splits/test.json \
        --output results/dpo_1b_from_base_predictions.json \
        --model_name methods-dpo-1b-from-base \
        --base_model meta-llama/Llama-3.2-1B-Instruct \
        --adapter_path ../training/checkpoints/biolite-methods-dpo-methods-dpo-1b-from-base

The --base_model choice is load-bearing: PEFT auto-detects the SFT adapter on
`tathadn/biolite-interpret-{1b,3b}` and stacks it before the DPO adapter. The DPO
adapter_config.json records the bare-base model and would silently strip the SFT
contribution if used to drive loading, so we override it explicitly here.
"""

import argparse
import gc
import json
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def build_prompt(tokenizer, question: str) -> str:
    messages = [{"role": "user", "content": question}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    args = parser.parse_args()

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading base model {args.base_model}...")
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

    print(f"Generating predictions for {len(test)} test examples ({args.model_name})...")
    predictions = []
    start = time.time()
    for i, ex in enumerate(test):
        question = ex["question"]
        reference = ex["chosen"]
        category = ex.get("category", "")
        source = ex.get("source", "")

        prompt = build_prompt(tokenizer, question)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(model.device)
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
        })

        elapsed = time.time() - start
        eta = (elapsed / (i + 1)) * (len(test) - i - 1)
        print(f"  [{i+1}/{len(test)}] {len(gen_tokens)} tok | elapsed {elapsed:.0f}s | eta {eta:.0f}s")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"\nSaved {len(predictions)} predictions to {args.output}")
    print(f"Peak GPU: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
