#!/usr/bin/env python3
"""
train_dpo.py — DPO training for BioLite-Methods.

Usage:
    # Main training — DPO from SFT checkpoint (MIG 0):
    export CUDA_VISIBLE_DEVICES=MIG-<GI-9-uuid>
    python train_dpo.py --base_model tathadn/biolite-interpret-1b

    # Ablation — DPO from base Instruct (MIG 1, concurrent):
    export CUDA_VISIBLE_DEVICES=MIG-<GI-11-uuid>
    python train_dpo.py --base_model meta-llama/Llama-3.2-1B-Instruct --run_name dpo-from-base

    # Beta ablation:
    python train_dpo.py --beta 0.05 --run_name dpo-beta-005
"""

import argparse
import os
import yaml
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, TaskType
from trl import DPOConfig
from fp32_logits_trainer import Fp32LogitsDPOTrainer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--base_model", type=str, default=None)
    parser.add_argument("--beta", type=float, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument("--max_length", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)

    # CLI overrides
    base_model = args.base_model or cfg["model"]["base_model"]
    beta = args.beta or cfg["dpo"]["beta"]
    run_name = args.run_name or cfg["wandb"]["run_name"]
    max_length = args.max_length or cfg["dpo"]["max_length"]

    # --- Quantization ---
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # --- Model ---
    print(f"Loading base model: {base_model}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False

    tokenizer = AutoTokenizer.from_pretrained(base_model)
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
        bias="none",
    )

    # --- Data ---
    print("Loading preference dataset...")
    train_ds = load_dataset("json", data_files=cfg["data"]["train_file"], split="train")
    eval_ds = load_dataset("json", data_files=cfg["data"]["eval_file"], split="train")

    def format_dpo(example):
        """Format preference pair for DPO trainer."""
        question = example["question"]
        return {
            "prompt": question,
            "chosen": example["chosen"],
            "rejected": example["rejected"],
        }

    train_ds = train_ds.map(format_dpo, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(format_dpo, remove_columns=eval_ds.column_names)

    # --- DPO Config ---
    output_dir = f"./checkpoints/biolite-methods-dpo-{run_name}"
    dpo_config = DPOConfig(
        output_dir=output_dir,
        num_train_epochs=cfg["dpo"]["num_train_epochs"],
        per_device_train_batch_size=cfg["dpo"]["per_device_train_batch_size"],
        gradient_accumulation_steps=cfg["dpo"]["gradient_accumulation_steps"],
        learning_rate=cfg["dpo"]["learning_rate"],
        lr_scheduler_type=cfg["dpo"]["lr_scheduler_type"],
        warmup_ratio=cfg["dpo"]["warmup_ratio"],
        beta=beta,
        loss_type=cfg["dpo"]["loss_type"],
        bf16=True,
        max_grad_norm=cfg["dpo"]["max_grad_norm"],
        logging_steps=cfg["dpo"]["logging_steps"],
        eval_strategy="steps",
        eval_steps=cfg["dpo"]["eval_steps"],
        save_strategy="steps",
        save_steps=cfg["dpo"]["save_steps"],
        load_best_model_at_end=True,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        max_length=max_length,
        max_prompt_length=cfg["dpo"]["max_prompt_length"],
        report_to="wandb",
        run_name=run_name,
    )

    # --- Train with Fp32 logits fix ---
    print(f"Starting DPO training (beta={beta}, max_length={max_length})...")
    print(f"Using Fp32LogitsDPOTrainer to prevent bf16 NaN overflow.")

    trainer = Fp32LogitsDPOTrainer(
        model=model,
        args=dpo_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=lora_config,
        tokenizer=tokenizer,
        # ref_model=None shares base weights (only LoRA diff)
    )

    # Log GPU info
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        mem_gb = torch.cuda.get_device_properties(0).total_mem / 1e9
        print(f"GPU Memory: {mem_gb:.2f} GB")

    trainer.train()

    # Log peak memory
    if torch.cuda.is_available():
        peak = torch.cuda.max_memory_allocated(0) / 1e9
        print(f"Peak GPU memory: {peak:.2f} / {mem_gb:.2f} GB")

    # Save
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)

    # Log final reward margins
    logs = trainer.state.log_history
    reward_margins = [
        l.get("rewards/margins", None)
        for l in logs if l.get("rewards/margins") is not None
    ]
    if reward_margins:
        import numpy as np
        final_margin = np.mean(reward_margins[-10:])
        print(f"Final reward margin (last 10 steps): {final_margin:.4f}")

    print("Done!")


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    main()
