#!/usr/bin/env python3
"""3-shot baseline: vanilla Llama-3.2-3B-Instruct with 3 in-context demonstrations.

Tests whether fine-tuning beats in-context learning on the same 64 pinned test
examples. Demonstrations are 3 random train examples (seed=42, fixed for repro).

Usage:
    python generate_predictions_fewshot.py \\
        --test_file ../data/splits/test.json \\
        --train_file ../data/splits/train.json \\
        --pinned_indices pinned_64_indices.json \\
        --output results/predictions_3b_fewshot.json
"""

import argparse
import gc
import json
import os
import random
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

DEFAULT_BASE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"


def build_user_msg(ex: dict) -> str:
    instruction = ex.get("instruction", "")
    input_text = ex.get("input", "")
    return f"{instruction}\n\n{input_text}" if input_text else instruction


def build_fewshot_prompt(tokenizer, demos: list, test_ex: dict) -> str:
    messages = []
    for d in demos:
        messages.append({"role": "user", "content": build_user_msg(d)})
        messages.append({"role": "assistant", "content": d.get("output", "")})
    messages.append({"role": "user", "content": build_user_msg(test_ex)})
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", required=True)
    parser.add_argument("--train_file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pinned_indices", default=None)
    parser.add_argument("--base_model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--model_name", default="llama-3.2-3b-3shot")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_shots", type=int, default=3)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--max_input_length", type=int, default=4096)
    args = parser.parse_args()

    with open(args.train_file) as f:
        train = json.load(f)
    with open(args.test_file) as f:
        test = json.load(f)
    if args.pinned_indices:
        with open(args.pinned_indices) as f:
            pinned = json.load(f)["pinned_indices"]
        test = [test[i] for i in pinned]

    rng = random.Random(args.seed)
    demo_indices = rng.sample(range(len(train)), args.n_shots)
    demos = [train[i] for i in demo_indices]
    print(f"Demo indices (seed={args.seed}): {demo_indices}")
    for i, d in enumerate(demos):
        print(f"  shot {i}: idx={demo_indices[i]} task_type={d.get('task_type','')}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"\nLoading {args.base_model}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model.eval()
    gc.collect()
    torch.cuda.empty_cache()

    print(f"Generating {args.n_shots}-shot predictions for {len(test)} test ex ({args.model_name})...")
    predictions = []
    start = time.time()
    for i, ex in enumerate(test):
        prompt = build_fewshot_prompt(tokenizer, demos, ex)
        inputs = tokenizer(
            prompt, return_tensors="pt",
            truncation=True, max_length=args.max_input_length,
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

        instruction = ex.get("instruction", "")
        input_text = ex.get("input", "")
        predictions.append({
            "input": f"{instruction}\n\n{input_text}".strip() if input_text else instruction,
            "prediction": prediction,
            "reference": ex.get("output", ""),
            "model": args.model_name,
            "task_type": ex.get("task_type", ""),
        })

        elapsed = time.time() - start
        eta = (elapsed / (i + 1)) * (len(test) - i - 1)
        print(f"  [{i+1}/{len(test)}] prompt_tok={prompt_len} gen_tok={len(gen_tokens)} | elapsed {elapsed:.0f}s | eta {eta:.0f}s")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"\nSaved {len(predictions)} predictions to {args.output}")
    print(f"Peak GPU: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
    print(f"Demo indices used: {demo_indices}")


if __name__ == "__main__":
    main()
