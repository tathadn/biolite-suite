"""
fp32_logits_trainer.py — DPO trainer with fp32 logit casting.

Prevents NaN overflow in DPO loss computation when training bf16 models.
Originally developed and validated in CodeQ project on simurgh H100 nodes.
Reused here for BioLite-Methods on A100 MIG slices.

Pin TRL version: trl==0.29.1
"""

import torch
from trl import DPOTrainer


class Fp32LogitsDPOTrainer(DPOTrainer):
    """DPO trainer that casts logits to float32 before loss computation.

    The standard DPOTrainer computes log-probabilities in whatever dtype
    the model outputs (bf16 when training with bf16=True). For DPO, the
    loss involves computing log(sigmoid(beta * (log_ratio_chosen - log_ratio_rejected))),
    which can overflow in bf16 when beta * delta is large.

    This fix casts all logit-derived values to fp32 before the loss
    computation, preventing NaN gradients.

    Validated on:
        - CodeQ: Qwen2.5-Coder-7B-Instruct DPO on H100 (simurgh)
        - BioLite-Methods: Llama 3.2 1B DPO on A100 MIG 4.8GB slice
    """

    def concatenated_forward(self, model, batch):
        """Override to cast logit-derived values to fp32."""
        outputs = super().concatenated_forward(model, batch)

        # Cast all bf16 tensors to fp32 to prevent overflow in DPO loss
        return {
            k: v.float() if isinstance(v, torch.Tensor) and v.dtype == torch.bfloat16 else v
            for k, v in outputs.items()
        }
