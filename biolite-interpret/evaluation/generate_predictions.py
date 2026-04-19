#!/usr/bin/env python3
"""Generate predictions on the test set for baseline or fine-tuned model.

Usage:
    # Baseline (no adapter):
    python generate_predictions.py \
        --test_file ../data/splits/test.json \
        --output results/baseline_predictions.json \
        --model_name llama-3.2-1b-base

    # Fine-tuned (with LoRA adapter):
    python generate_predictions.py \
        --test_file ../data/splits/test.json \
        --adapter_path ../training/checkpoints/biolite-interpret-1b/checkpoint-102 \
        --output results/finetuned_predictions.json \
        --model_name biolite-interpret-1b
"""

import argparse
import gc
import json
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE_MODEL = "meta-llama/Llama-3.2-1B-Instruct"


def build_prompt(tokenizer, instruction: str, input_text: str) -> str:
    user_msg = f"{instruction}\n\n{input_text}" if input_text else instruction
    messages = [{"role": "user", "content": user_msg}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    args = parser.parse_args()

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading base model {BASE_MODEL}...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if args.adapter_path:
        from peft import PeftModel
        print(f"Loading LoRA adapter from {args.adapter_path}...")
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
        instruction = ex.get("instruction", "")
        input_text = ex.get("input", "")
        reference = ex.get("output", "")
        task_type = ex.get("task_type", "")

        prompt = build_prompt(tokenizer, instruction, input_text)
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
            "input": f"{instruction}\n\n{input_text}".strip() if input_text else instruction,
            "prediction": prediction,
            "reference": reference,
            "model": args.model_name,
            "task_type": task_type,
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
