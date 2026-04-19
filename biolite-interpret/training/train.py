#!/usr/bin/env python3
"""
train.py — QLoRA SFT training for BioLite-Interpret.

Usage:
    # On MIG 0 (GI 9):
    export CUDA_VISIBLE_DEVICES=MIG-<uuid>
    python train.py --config config.yaml

    # LoRA rank ablation (parallel on both slices):
    # Terminal 1 (MIG 0): python train.py --config config.yaml --lora_r 8 --run_name interpret-sft-r8
    # Terminal 2 (MIG 1): python train.py --config config.yaml --lora_r 32 --run_name interpret-sft-r32
"""

import argparse
import gc
import json
import os
import yaml
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
    TrainingArguments,
)
from peft import LoraConfig, TaskType, get_peft_model
from trl import SFTTrainer, SFTConfig


class PreEvalCleanupCallback(TrainerCallback):
    """Free cached CUDA memory right before each evaluation to avoid OOM on small MIG slices."""

    def on_step_end(self, args, state, control, **kwargs):
        if (
            state.global_step > 0
            and args.eval_strategy == "steps"
            and args.eval_steps
            and state.global_step % args.eval_steps == 0
        ):
            gc.collect()
            torch.cuda.empty_cache()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def format_instruction(example: dict) -> str:
    """Format example into Llama 3.2 chat template."""
    instruction = example.get("instruction", "")
    input_text = example.get("input", "")
    output = example.get("output", "")

    if input_text:
        user_msg = f"{instruction}\n\n{input_text}"
    else:
        user_msg = instruction

    return user_msg, output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--lora_r", type=int, default=None, help="Override LoRA rank")
    parser.add_argument("--run_name", type=str, default=None, help="Override W&B run name")
    parser.add_argument("--data_fraction", type=float, default=1.0, help="Fraction of training data (for ablation)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Override from CLI
    if args.lora_r:
        cfg["lora"]["r"] = args.lora_r
    if args.run_name:
        cfg["wandb"]["run_name"] = args.run_name

    # --- Quantization ---
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=cfg["quantization"]["load_in_4bit"],
        bnb_4bit_quant_type=cfg["quantization"]["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=getattr(torch, cfg["quantization"]["bnb_4bit_compute_dtype"]),
        bnb_4bit_use_double_quant=cfg["quantization"]["bnb_4bit_use_double_quant"],
    )

    # --- Model ---
    print(f"Loading {cfg['model']['base_model']}...")
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model"]["base_model"],
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False

    tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["base_model"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # --- LoRA ---
    lora_config = LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["lora_alpha"],
        lora_dropout=cfg["lora"]["lora_dropout"],
        target_modules=cfg["lora"]["target_modules"],
        task_type=TaskType.CAUSAL_LM,
        bias=cfg["lora"]["bias"],
    )

    # --- Data ---
    print("Loading dataset...")
    train_ds = load_dataset("json", data_files=cfg["data"]["train_file"], split="train")
    eval_ds = load_dataset("json", data_files=cfg["data"]["eval_file"], split="train")

    # Dataset size ablation
    if args.data_fraction < 1.0:
        n = int(len(train_ds) * args.data_fraction)
        train_ds = train_ds.select(range(n))
        print(f"Using {n}/{len(train_ds)} examples ({args.data_fraction*100:.0f}%)")

    def formatting_func(example):
        """Format a single example into Llama 3.2 Instruct chat template."""
        user_msg, assistant_msg = format_instruction({
            "instruction": example["instruction"],
            "input": example.get("input", ""),
            "output": example["output"],
        })
        messages = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

    # --- Training args ---
    training_args = SFTConfig(
        output_dir=cfg["training"]["output_dir"],
        num_train_epochs=cfg["training"]["num_train_epochs"],
        per_device_train_batch_size=cfg["training"]["per_device_train_batch_size"],
        per_device_eval_batch_size=cfg["training"].get("per_device_eval_batch_size", 1),
        gradient_accumulation_steps=cfg["training"]["gradient_accumulation_steps"],
        eval_accumulation_steps=cfg["training"].get("eval_accumulation_steps"),
        learning_rate=cfg["training"]["learning_rate"],
        lr_scheduler_type=cfg["training"]["lr_scheduler_type"],
        warmup_ratio=cfg["training"]["warmup_ratio"],
        weight_decay=cfg["training"]["weight_decay"],
        bf16=cfg["training"]["bf16"],
        max_grad_norm=cfg["training"]["max_grad_norm"],
        logging_steps=cfg["training"]["logging_steps"],
        eval_strategy=cfg["training"]["eval_strategy"],
        eval_steps=cfg["training"]["eval_steps"],
        save_strategy=cfg["training"]["save_strategy"],
        save_steps=cfg["training"]["save_steps"],
        save_total_limit=cfg["training"].get("save_total_limit"),
        load_best_model_at_end=cfg["training"]["load_best_model_at_end"],
        metric_for_best_model=cfg["training"]["metric_for_best_model"],
        gradient_checkpointing=cfg["training"]["gradient_checkpointing"],
        optim=cfg["training"]["optim"],
        max_length=cfg["training"]["max_seq_length"],
        report_to=cfg["training"]["report_to"],
        run_name=cfg["wandb"]["run_name"],
        packing=False,
    )

    # --- Train ---
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=lora_config,
        formatting_func=formatting_func,
        callbacks=[PreEvalCleanupCallback()],
    )

    # Log GPU memory before training
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"Allocated before training: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")

    gc.collect()
    torch.cuda.empty_cache()

    print("Starting training...")
    trainer.train()

    # Log peak memory
    if torch.cuda.is_available():
        peak_mem = torch.cuda.max_memory_allocated(0) / 1e9
        print(f"Peak GPU memory: {peak_mem:.2f} GB")

    # Save
    print("Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(cfg["training"]["output_dir"])

    # Push to Hub
    if cfg.get("huggingface", {}).get("push_to_hub", False):
        hub_id = cfg["huggingface"]["hub_model_id"]
        print(f"Pushing to HuggingFace Hub: {hub_id}")
        trainer.push_to_hub(hub_id)

    print("Done!")


if __name__ == "__main__":
    main()
