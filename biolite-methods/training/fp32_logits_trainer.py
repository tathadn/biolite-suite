"""
fp32_logits_trainer.py — DPO trainer with fp32 logit casting.

Prevents NaN overflow in DPO loss computation when training bf16 models.
Originally developed and validated in CodeQ project on simurgh H100 nodes.
Reused here for BioLite-Methods on A100 MIG slices.

TRL 0.29.1 refactor note
------------------------
In earlier TRL versions, DPOTrainer had a `concatenated_forward` method
that callers could override to cast logit-derived values to fp32. TRL
0.29.1 moved that logic inline into `_compute_loss`, so the old hook
point is gone. Instead, this version wraps the policy model's `forward`
so every outputs.logits tensor is upcast from bf16 to fp32 before it
reaches `selective_log_softmax` in the DPO loss path.

The wrap covers both forward passes (policy + reference-via-disabled-
adapter) because PEFT reuses the same underlying model object for both.

Validated on:
    - CodeQ: Qwen2.5-Coder-7B-Instruct DPO on H100 (simurgh, old API)
    - BioLite-Methods: Llama 3.2 1B DPO on A100 MIG 4.8GB slice (TRL 0.29.1)
"""

import torch
from trl import DPOTrainer


class Fp32LogitsDPOTrainer(DPOTrainer):
    """DPO trainer that upcasts model logits to float32.

    The underlying bf16 policy + reference model forward passes can
    produce logits where `beta * (log_ratio_chosen - log_ratio_rejected)`
    overflows, yielding NaN gradients. Casting the raw logits to fp32
    immediately after forward preserves numerical range through
    `selective_log_softmax` and the sigmoid DPO loss.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patch_forward_for_fp32_logits()

    def _patch_forward_for_fp32_logits(self) -> None:
        model = self.model
        if getattr(model, "_fp32_logits_patched", False):
            return
        original_forward = model.forward

        def forward_with_fp32_logits(*args, **kwargs):
            outputs = original_forward(*args, **kwargs)
            # Only upcast during training: gradients through log(sigmoid(beta*Δ))
            # need fp32 to avoid NaN, but eval only needs an approximate metric and
            # the fp32 logits tensor (~1.7 GiB) doesn't fit alongside non-checkpointed
            # eval activations on the 4.75 GiB MIG slice.
            if model.training:
                logits = getattr(outputs, "logits", None)
                if isinstance(logits, torch.Tensor) and logits.dtype == torch.bfloat16:
                    outputs.logits = logits.float()
            return outputs

        model.forward = forward_with_fp32_logits
        model._fp32_logits_patched = True
